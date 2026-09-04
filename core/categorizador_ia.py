"""
Módulo de categorização médica inteligente utilizando a API Gemini com fallback em camadas.

Garantias de segurança e economia:
1. Cache incremental atômico ('saida/cache_categorizacao.json'): cada questão classificada
   é salva imediatamente e nunca mais consome requisições ou tokens da API.
2. Custo ultra-baixo: payload enxuto com maxOutputTokens=60, custando frações de centavo
   por questão (~R$ 0,15 para o banco inteiro) no tier pago, e R$ 0,00 no tier gratuito.
3. Fallback inteligente em camadas:
   - Chave Primária (GEMINI_API_KEY)
   - Chave Gratuita alternativa (GEMINI_API_KEY_FREE, se configurada no .env)
   - Throttling automático para respeitar o limite gratuito (15 RPM)
   - Fallback final imediato para o classificador heurístico local (core.classificador)
     caso os créditos se esgotem ou ocorram erros de rede/cota (429/402/403/RESOURCE_EXHAUSTED).
"""

import json
import time
import urllib.request
import re
from pathlib import Path

from .classificador import classificar_questao, normalizar_texto
from .utils import salvar_json_atomico, carregar_json_seguro

CAMINHO_CACHE_PADRAO = Path("saida/cache_categorizacao.json")

# Modelos em ordem de preferência (do mais rápido/econômico com suporte a json estruturado)
MODELOS_IA = [
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-2.5-flash"
]


def carregar_chaves_api(arquivo_env: Path = Path(".env")):
    """Carrega as chaves de API primária e gratuita (fallback) do .env."""
    chave_primaria = None
    chave_gratis = None
    
    if arquivo_env.exists():
        try:
            for linha in arquivo_env.read_text(encoding="utf-8").splitlines():
                linha = linha.strip()
                if not linha or linha.startswith("#"):
                    continue
                if linha.startswith("GEMINI_API_KEY="):
                    chave_primaria = linha.split("=", 1)[1].strip().strip('"').strip("'")
                elif linha.startswith("GEMINI_API_KEY_FREE=") or linha.startswith("GEMINI_FREE_API_KEY="):
                    chave_gratis = linha.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
            
    return chave_primaria, chave_gratis


def carregar_cache_categorizacao(caminho_cache: Path = CAMINHO_CACHE_PADRAO):
    """Carrega o cache de categorizações de forma segura."""
    return carregar_json_seguro(caminho_cache, default={})


def salvar_cache_categorizacao(cache: dict, caminho_cache: Path = CAMINHO_CACHE_PADRAO):
    """Persiste o cache no disco com escrita atômica."""
    caminho_cache.parent.mkdir(parents=True, exist_ok=True)
    return salvar_json_atomico(caminho_cache, cache, indent=2)


def montar_prompt_categorizacao(enunciado, alternativas):
    """Cria um prompt médico focado e conciso para minimizar tokens de entrada."""
    texto_resumido = enunciado.strip()
    if len(texto_resumido) > 800:
        texto_resumido = texto_resumido[:800] + " [...]"
        
    alts_str = json.dumps(alternativas, ensure_ascii=False) if alternativas else "{}"
    
    return f"""Classifique a questão médica de Residência/Revalida.
ENUNCIADO:
{texto_resumido}

ALTERNATIVAS:
{alts_str}

DIRETRIZES DE TAXONOMIA:
1. "especialidade": Exatamente UMA das 5 grandes áreas:
   - Clínica Médica
   - Cirurgia Geral
   - Pediatria
   - Ginecologia e Obstetrícia
   - Medicina Preventiva e Social / MFC
2. "tema": Especialidades puras sem barras (ex: Cardiologia, Pneumologia, Gastroenterologia & Hepatologia, Nefrologia, Endocrinologia & Metabologia, Reumatologia, Infectologia, Hematologia, Neurologia, Dermatologia, Psiquiatria, Emergência e Cuidados Críticos, Angiologia & Vascular). Nunca use barras combinadas. Cirúrgicas (Urologia, Ortopedia) pertencem a Cirurgia Geral.
3. "subtema": A condição central. Para Gastroenterologia & Hepatologia, use estritamente um dos 7 blocos sindrômicos:
   - Esôfago e Estômago
   - Doenças Intestinais & Disabsortivas
   - Fígado e Cirrose
   - Hepatites Virais
   - Vias Biliares e Pâncreas
   - Hemorragia Digestiva
   - Neoplasias Gastrointestinais

Responda em formato JSON:
{{"especialidade": "...", "tema": "...", "subtema": "..."}}"""


def chamar_api_gemini(prompt: str, api_key: str, modelo: str = "gemini-flash-lite-latest", timeout: int = 15):
    """Executa a chamada HTTP REST pura ao Gemini com payload ultraleve e JSON estruturado."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 60,
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        texto = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return json.loads(texto)


def classificar_com_fallback(questao: dict, cache: dict, api_key_primaria: str = None, api_key_gratis: str = None, delay_entre_chamadas: float = 0.5):
    """
    Classifica uma questão com estratégia de 4 camadas:
    1. Cache local em disco (instantâneo, sem gasto)
    2. API Gemini com chave primária (rápida)
    3. API Gemini com chave gratuita/fallback (com controle de 15 RPM)
    4. Classificador heurístico local aprimorado (100% offline, seguro contra pane de créditos)
    """
    q_key = f"{questao.get('origem', 'Q')}_{questao.get('numero', '0')}"
    
    # Camada 1: Cache local
    if q_key in cache and cache[q_key].get("especialidade") and cache[q_key].get("tema"):
        return cache[q_key]["especialidade"], cache[q_key]["tema"], cache[q_key]["subtema"], "cache"

    prompt = montar_prompt_categorizacao(questao.get("enunciado", ""), questao.get("alternativas", {}))
    
    # Lista de chaves ordenadas para tentativa
    chaves = []
    if api_key_primaria:
        chaves.append(("primaria", api_key_primaria))
    if api_key_gratis and api_key_gratis != api_key_primaria:
        chaves.append(("gratis_fallback", api_key_gratis))

    # Camadas 2 e 3: Tentativas na API Gemini
    for rotulo_chave, key in chaves:
        for modelo in MODELOS_IA:
            try:
                res_json = chamar_api_gemini(prompt, key, modelo=modelo)
                esp = res_json.get("especialidade", "").strip()
                tema = res_json.get("tema", "").strip()
                subtema = res_json.get("subtema", "").strip()
                
                # Valida se a especialidade é uma das 5 grandes áreas oficiais
                grandes_areas = [
                    "Clínica Médica",
                    "Cirurgia Geral",
                    "Pediatria",
                    "Ginecologia e Obstetrícia",
                    "Medicina Preventiva e Social / MFC"
                ]
                
                if esp not in grandes_areas:
                    # Mapeamento de flexibilidade
                    esp_norm = normalizar_texto(esp)
                    for ga in grandes_areas:
                        if normalizar_texto(ga) in esp_norm or esp_norm in normalizar_texto(ga):
                            esp = ga
                            break
                    if esp not in grandes_areas:
                        esp = "Clínica Médica"

                if esp and tema:
                    cache[q_key] = {
                        "especialidade": esp,
                        "tema": tema,
                        "subtema": subtema or tema,
                        "fonte": f"gemini_{rotulo_chave}"
                    }
                    if delay_entre_chamadas > 0:
                        time.sleep(delay_entre_chamadas)
                    return esp, tema, subtema or tema, f"gemini_{rotulo_chave}"

            except Exception as e:
                err_msg = str(e)
                # Se for cota esgotada (429 / RESOURCE_EXHAUSTED / 402 / 403), tenta a próxima chave ou modelo
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    # Se for chave gratuita, aguarda 4 segundos (15 RPM free tier)
                    if rotulo_chave == "gratis_fallback":
                        time.sleep(4.0)
                    else:
                        time.sleep(1.0)
                    continue
                elif "404" in err_msg:
                    continue
                else:
                    break

    # Camada 4: Fallback 100% Offline e Heurístico
    texto_completo = questao.get("enunciado", "") + " " + " ".join(questao.get("alternativas", {}).values())
    esp_h, tema_h, subtema_h = classificar_questao(texto_completo)
    
    cache[q_key] = {
        "especialidade": esp_h,
        "tema": tema_h,
        "subtema": subtema_h,
        "fonte": "heuristica_fallback"
    }
    return esp_h, tema_h, subtema_h, "heuristica_fallback"

"""
Enriquecedor de Negrito Semântico In-Place via API Gemini.
Aplica destaques inteligentes em negrito (**) diretamente sobre o texto
médico de alta qualidade já existente no cache, preservando 100% da
profundidade e do conteúdo clínico, com altíssima velocidade e consumo
mínimo de tokens na API gratuita.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Configuração de saída UTF-8 para Windows
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
PASTA_SAIDA = BASE_DIR / "saida"
CACHE_PATH = PASTA_SAIDA / "cache_explicacoes.json"
BANCO_PATH = PASTA_SAIDA / "banco_questoes_cache.json"

from core.utils import salvar_json_atomico, carregar_json_seguro
from recompilar import recompilar


def carregar_api_key():
    """Carrega a chave de API do Gemini a partir do ambiente ou do arquivo .env."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY_GRATIS")
    env_file = BASE_DIR / ".env"
    if not api_key and env_file.exists():
        try:
            chaves = {}
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    chaves[k.strip()] = v.strip().strip('"').strip("'")
            return chaves.get("GEMINI_API_KEY") or chaves.get("GEMINI_API_KEY_GRATIS")
        except Exception:
            pass
    return api_key


def construir_prompt_negrito_in_place(explicacao_original):
    return f"""Você é um editor médico sênior. Sua única tarefa é aplicar DESTAQUES EM NEGRITO SEMÂNTICO (usando **) na explicação médica oficial abaixo, sem alterar o conteúdo clínico nem reescrever o texto.

DIRETRIZES ESTRUTURAIS DE NEGRITO:
1. MANTENHA O TEXTO ORIGINAL: Não resuma, não exclua e não altere as palavras ou o significado. Mantenha os mesmos parágrafos e tópicos.
2. APLIQUE NEGRITO (**) APENAS EM:
   - Títulos de seções e tópicos (ex: **Justificativa detalhada:**, **Análise dos distratores:**, **Alternativa A (Correta):**, **Alternativa B (Incorreta):**).
   - Termos médicos decisivos: o diagnóstico principal (ex: **úlcera gástrica**), drogas/condutas de escolha (ex: **biópsias múltiplas**), e bactérias/fatores etiológicos (ex: **Helicobacter pylori**).
3. NEGRITO CIRÚRGICO: Destaque apenas os termos-chave isolados (2 a 4 palavras no máximo por destaque). NUNCA coloque frases inteiras em negrito.
4. NUNCA utilize caracteres '#', '##' ou '###'. Use estritamente negrito simples: '**Título:**'.

EXPLICAÇÃO ORIGINAL:
{explicacao_original}

Responda exclusivamente em formato JSON com o texto completo devidamente formatado:
{{
  "explicacao": "o mesmo texto da explicação, com os destaques em **negrito** aplicados"
}}"""


def chamar_gemini(prompt, api_key, modelo="gemini-3.5-flash", max_tentativas=4):
    modelos_tentativa = [modelo, "gemini-3.8-flash", "gemini-3.6-flash"]
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2
        }
    }).encode("utf-8")

    for mod in modelos_tentativa:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
        for tentativa in range(1, max_tentativas + 1):
            try:
                headers = {
                    "Content-Type": "application/json"
                }
                req = urllib.request.Request(url, data=payload, headers=headers)
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    texto = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if "```json" in texto:
                        texto = texto.split("```json")[1].split("```")[0].strip()
                    elif "```" in texto:
                        texto = texto.split("```")[1].split("```")[0].strip()

                    try:
                        res_json = json.loads(texto)
                        if "explicacao" in res_json and len(res_json["explicacao"]) > 40:
                            return res_json.get("explicacao"), None
                    except Exception:
                        if len(texto) > 60:
                            return texto, None
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait_time = (2 ** tentativa) * 4
                    print(f" [!] Rate limit (429). Aguardando {wait_time}s...", flush=True)
                    time.sleep(wait_time)
                elif e.code == 503:
                    wait_time = 3 * tentativa
                    print(f" [!] 503 em {mod}. Tentando novamente em {wait_time}s...", flush=True)
                    time.sleep(wait_time)
                elif e.code == 404:
                    break
                else:
                    time.sleep(2 * tentativa)
            except Exception as e:
                time.sleep(2 * tentativa)

    return None, "Falha após tentativas"


def processar_negrito_otimizado(prova="TODAS", limite=None, delay=1.8, forcar=False):
    api_key = carregar_api_key()
    if not api_key:
        print("[!] Erro: GEMINI_API_KEY não encontrada no arquivo .env.")
        return

    banco = carregar_json_seguro(BANCO_PATH, default=[])
    cache = carregar_json_seguro(CACHE_PATH, default={})

    if prova.upper() == "TODAS":
        questoes_alvo = [
            q for q in banco 
            if q.get("gabarito") and q.get("gabarito") != "ANULADA"
        ]
        print(f"[*] Modo BANCO COMPLETO: {len(questoes_alvo)} questões válidas carregadas.")
    else:
        questoes_alvo = [
            q for q in banco 
            if q.get("origem") == prova and q.get("gabarito") and q.get("gabarito") != "ANULADA"
        ]
        print(f"[*] Total de questões encontradas para '{prova}': {len(questoes_alvo)}")

    if limite:
        questoes_alvo = questoes_alvo[:limite]
        print(f"[*] Processando limite de {limite} questões para teste...")

    sucessos = 0
    puladas = 0
    erros = 0

    print(f"[*] Iniciando Negrito Inteligente In-Place (Modelo Lite, Delay={delay}s)...")

    for idx, q in enumerate(questoes_alvo, 1):
        q_id = f"{q.get('origem')}_{q.get('numero')}"
        gab = q.get("gabarito")
        item_cache = cache.get(q_id, {})
        exp_atual = item_cache.get("explicacao", "")

        if not exp_atual or len(exp_atual.strip()) < 30:
            print(f"[{idx}/{len(questoes_alvo)}] Questão {q_id} sem explicação base no cache. Pulando...")
            puladas += 1
            continue

        # Verifica se a explicação já possui marcações semânticas de negrito consistentes
        ja_formatada = exp_atual.count("**") >= 8

        if not forcar and ja_formatada:
            puladas += 1
            if puladas <= 5 or puladas % 100 == 0:
                print(f"[{idx}/{len(questoes_alvo)}] Questão {q_id} já possui negrito inteligente. Pulando...")
            continue

        print(f"[{idx}/{len(questoes_alvo)}] Aplicando negrito em {q_id}...", end="", flush=True)
        prompt = construir_prompt_negrito_in_place(exp_atual)
        nova_exp, erro = chamar_gemini(prompt, api_key)

        if nova_exp:
            cache[q_id] = {
                "gabarito": gab or item_cache.get("gabarito", ""),
                "explicacao": nova_exp
            }
            salvar_json_atomico(CACHE_PATH, cache)
            sucessos += 1
            print(" [✓ OK]")

            # Recompila periodicamente a cada 30 questões atualizadas
            if sucessos > 0 and sucessos % 30 == 0:
                print(f"[*] Recompilação periódica ({sucessos} questões formatadas)...")
                try:
                    recompilar()
                except Exception as e:
                    print(f"[!] Aviso na recompilação: {e}")
        else:
            erros += 1
            print(f" [✗ ERRO: {erro}]")

        if idx < len(questoes_alvo):
            time.sleep(delay)

    print(f"\n[*] Concluído: {sucessos} atualizadas, {puladas} já estavam com negrito, {erros} erros.")
    print("[*] Recompilando simulados HTML...")
    recompilar()
    print("[✓] Simulado atualizado com sucesso!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aplicar negrito inteligente in-place nas justificativas médicas")
    parser.add_argument("--prova", type=str, default="TODAS", help="Nome da prova ou 'TODAS' para o banco completo")
    parser.add_argument("--limite", type=int, default=None, help="Limite de questões a processar")
    parser.add_argument("--delay", type=float, default=1.8, help="Delay entre chamadas em segundos (padrão: 1.8s)")
    parser.add_argument("--forcar", action="store_true", help="Força a re-aplicação mesmo se já tiver negrito")
    args = parser.parse_args()

    processar_negrito_otimizado(prova=args.prova, limite=args.limite, delay=args.delay, forcar=args.forcar)

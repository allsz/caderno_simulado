import json
import time
from pathlib import Path


def carregar_cache_explicacoes(caminho_cache: Path):
    """Carrega o cache de explicações clínicas e gabaritos."""
    if caminho_cache.exists():
        try:
            with open(caminho_cache, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def salvar_cache_explicacoes(caminho_cache: Path, cache: dict):
    """Salva o cache de explicações em disco."""
    try:
        with open(caminho_cache, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"   [!] Erro ao salvar cache de explicações: {e}")


def gerar_explicacao_gemini(questao, gabarito_oficial, api_key):
    """Gera comentário médico e justificativa usando a API gratuita do Gemini (Google AI Studio)."""
    from google import genai
    client = genai.Client(api_key=api_key)
    
    prompt = f"""Você é um médico preceptor de Residência Médica e Revalida.
Analise a questão abaixo e forneça um comentário explicativo objetivo para estudantes de medicina.

PROVA: {questao.get('origem')}
QUESTÃO: {questao.get('numero')}
ENUNCIADO:
{questao.get('enunciado')}

ALTERNATIVAS:
{json.dumps(questao.get('alternativas', {}), ensure_ascii=False)}

GABARITO CONHECIDO: {gabarito_oficial if gabarito_oficial != 'N/A' else 'Determine a alternativa correta.'}

Responda exclusivamente em formato JSON com as seguintes chaves:
"gabarito": "Letra da alternativa correta (A, B, C, D ou E)"
"explicacao": "Comentário médico resumido (máximo 120 palavras), indicando a resposta correta e por que as outras opções estão incorretas."
"""
    modelos_disponiveis = [
        "gemini-3-flash-preview",
        "gemma-4-31b-it",
        "gemma-4-26b-a4b-it",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite"
    ]
    
    for modelo in modelos_disponiveis:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
            )
            texto = response.text.strip()
            if "```json" in texto:
                texto = texto.split("```json")[1].split("```")[0].strip()
            elif "```" in texto:
                texto = texto.split("```")[1].split("```")[0].strip()
            data = json.loads(texto, strict=False)
            exp = data.get("explicacao", "").strip()
            gab = data.get("gabarito", gabarito_oficial).strip()
            time.sleep(3)
            return gab, exp
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                print(f"   [!] Cota do modelo '{modelo}' atingida. Alternando para o próximo modelo...", flush=True)
                time.sleep(2)
                continue
            else:
                print(f"   [!] Erro ao consultar Gemini API ({modelo}): {e}", flush=True)
                break
    return gabarito_oficial, ""

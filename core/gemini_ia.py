import json
import time
import urllib.request
import re
from pathlib import Path

from .utils import salvar_json_atomico, carregar_json_seguro


def carregar_cache_explicacoes(caminho_cache: Path):
    """Carrega o cache de explicações clínicas e gabaritos de forma segura."""
    return carregar_json_seguro(caminho_cache, default={})


def salvar_cache_explicacoes(caminho_cache: Path, cache: dict):
    """Salva o cache de explicações em disco com escrita atômica."""
    return salvar_json_atomico(caminho_cache, cache, indent=2)


def gerar_explicacao_gemini(questao, gabarito_oficial, api_key):
    """
    Gera comentário médico e justificativa usando a API do Gemini via REST (universal, sem dependências externas).
    Garante que a explicação justifique o gabarito oficial.
    """
    if not api_key:
        return gabarito_oficial, ""

    prompt = f"""Você é um médico preceptor especialista em Residência Médica e Revalida.
Analise a questão abaixo e forneça um comentário explicativo oficial, técnico, pedagógico e objetivo para estudantes de medicina.

PROVA: {questao.get('origem')}
QUESTÃO: {questao.get('numero')}
ENUNCIADO:
{questao.get('enunciado')}

ALTERNATIVAS:
{json.dumps(questao.get('alternativas', {}), ensure_ascii=False, indent=2)}

GABARITO CONHECIDO: {gabarito_oficial if gabarito_oficial != 'N/A' else 'Determine a alternativa correta.'}

DIRETRIZ:
Sua explicação deve fundamentar a alternativa correta com base no raciocínio clínico e diretrizes do Ministério da Saúde / Sociedades Médicas, e explicar sucintamente por que as demais opções estão incorretas.

Responda exclusivamente em formato JSON com as chaves:
{{
  "gabarito": "{gabarito_oficial if gabarito_oficial != 'N/A' else 'A/B/C/D/E'}",
  "explicacao": "Comentário médico técnico fundamentando a resposta correta e refutando as demais alternativas."
}}
"""
    modelos_disponiveis = [
        "gemini-3-flash-preview",
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemma-4-31b-it",
        "gemma-4-26b-a4b-it"
    ]

    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    payload = json.dumps(data).encode('utf-8')

    for modelo in modelos_disponiveis:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                res = json.loads(response.read().decode('utf-8'))
                texto = res['candidates'][0]['content']['parts'][0]['text'].strip()
                
                if "```json" in texto:
                    texto = texto.split("```json")[1].split("```")[0].strip()
                elif "```" in texto:
                    texto = texto.split("```")[1].split("```")[0].strip()
                
                try:
                    data_obj = json.loads(texto, strict=False)
                    exp = data_obj.get("explicacao", "").strip()
                    gab = data_obj.get("gabarito", gabarito_oficial).strip().upper()
                    if gabarito_oficial != "N/A" and gab != gabarito_oficial:
                        gab = gabarito_oficial
                    time.sleep(1)
                    return gab, exp
                except Exception:
                    time.sleep(1)
                    return gabarito_oficial, texto
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "503" in err_msg:
                time.sleep(2)
                continue
            else:
                time.sleep(1)
                continue

    return gabarito_oficial, ""


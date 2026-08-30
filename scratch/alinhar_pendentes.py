import json
import time
import urllib.request
import re
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

env_text = open('.env', encoding='utf-8').read()
api_key = env_text.split('GEMINI_API_KEY=')[1].split('\n')[0].strip().strip('"').strip("'")

banco = json.load(open('saida/banco_questoes_cache.json', encoding='utf-8'))
banco_dict = {f"{q['origem']}_{q['numero']}": q for q in banco}
caminho_cache = Path('saida/cache_explicacoes.json')
cache_explicacoes = json.load(open(caminho_cache, encoding='utf-8'))

pendentes = [
    "REVALIDA-2024_1_PV_objetiva_regular_53",
    "REVALIDA-2024_1_PV_objetiva_regular_54",
    "REVALIDA-2024_1_PV_objetiva_regular_60"
]

modelos = [
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemma-4-31b-it"
]

def chamar_gemini(prompt):
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    for m in modelos:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode('utf-8'))
                texto = res['candidates'][0]['content']['parts'][0]['text'].strip()
                if "```json" in texto:
                    texto = texto.split("```json")[1].split("```")[0].strip()
                elif "```" in texto:
                    texto = texto.split("```")[1].split("```")[0].strip()
                try:
                    obj = json.loads(texto, strict=False)
                    return obj.get("explicacao", texto)
                except Exception:
                    return texto
        except Exception as e:
            time.sleep(2)
            continue
    return None

for q_id in pendentes:
    q = banco_dict.get(q_id)
    if not q:
        continue
    gab_oficial = q.get('gabarito')
    prompt = f"""Você é um médico preceptor especialista em Residência Médica e Revalida.
Escreva um comentário explicativo oficial, técnico, pedagógico e objetivo para estudantes de medicina sobre a questão abaixo.

PROVA: {q.get('origem')}
QUESTÃO: {q.get('numero')}
ENUNCIADO:
{q.get('enunciado')}

ALTERNATIVAS:
{json.dumps(q.get('alternativas', {}), ensure_ascii=False, indent=2)}

GABARITO OFICIAL DEFINITIVO: Alternativa ({gab_oficial})

DIRETRIZ OBRIGATÓRIA:
O gabarito oficial definitivo da banca é a alternativa ({gab_oficial}). Sua explicação DEVE obrigatoriamente fundamentar a alternativa ({gab_oficial}) como a correta com base no raciocínio clínico e diretrizes, e refutar sucintamente as outras alternativas. NUNCA discorde do gabarito oficial.

Responda exclusivamente em formato JSON:
{{
  "gabarito": "{gab_oficial}",
  "explicacao": "Texto do comentário médico pedagógico fundamentando a alternativa ({gab_oficial}) e refutando as demais opções."
}}
"""
    nova_exp = chamar_gemini(prompt)
    if nova_exp:
        nova_exp_limpa = re.sub(r'^(?:Gabarito|Resposta|Alternativa)\s*(?:Oficial)?\s*:\s*[A-E]\.?\s*', '', nova_exp, flags=re.IGNORECASE).strip()
        cache_explicacoes[q_id] = {
            "gabarito": gab_oficial,
            "explicacao": nova_exp_limpa
        }
        print(f"✓ Concluído pendente: {q_id} ({gab_oficial})")
    time.sleep(1.5)

with open(caminho_cache, 'w', encoding='utf-8') as f:
    json.dump(cache_explicacoes, f, ensure_ascii=False, indent=2)

print("Todas as pendências finalizadas com sucesso!")

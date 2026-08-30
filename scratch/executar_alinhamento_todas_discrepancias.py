import json
import time
import urllib.request
import re
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Carregar chave de API
env_text = open('.env', encoding='utf-8').read()
api_key = env_text.split('GEMINI_API_KEY=')[1].split('\n')[0].strip().strip('"').strip("'")

# Carregar discrepâncias e caches
discrepancias = json.load(open('scratch/relatorio_discrepancias.json', encoding='utf-8'))
banco = json.load(open('saida/banco_questoes_cache.json', encoding='utf-8'))
banco_dict = {f"{q['origem']}_{q['numero']}": q for q in banco}
caminho_cache = Path('saida/cache_explicacoes.json')
cache_explicacoes = json.load(open(caminho_cache, encoding='utf-8'))

modelos = [
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it"
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
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "503" in err_msg:
                time.sleep(2)
                continue
            else:
                time.sleep(1)
                continue
    return None

total = len(discrepancias)
print(f"[*] Iniciando alinhamento de {total} justificativas...")

sucessos = 0
for idx, item in enumerate(discrepancias, 1):
    q_id = item['id']
    gab_oficial = item['gab_oficial']
    q = banco_dict.get(q_id)
    if not q:
        continue
    
    prompt = f"""Você é um médico preceptor especialista em Residência Médica (ENARE) e Revalida (INEP).
Escreva um comentário explicativo oficial, técnico, pedagógico e objetivo para estudantes de medicina sobre a questão abaixo.

PROVA: {q.get('origem')}
QUESTÃO: {q.get('numero')}
ENUNCIADO:
{q.get('enunciado')}

ALTERNATIVAS:
{json.dumps(q.get('alternativas', {}), ensure_ascii=False, indent=2)}

GABARITO OFICIAL DEFINITIVO: Alternativa ({gab_oficial})

DIRETRIZ OBRIGATÓRIA:
O gabarito oficial definitivo da banca é a alternativa ({gab_oficial}). Sua explicação DEVE obrigatoriamente fundamentar a alternativa ({gab_oficial}) como a correta com base no raciocínio clínico e diretrizes do Ministério da Saúde / Sociedades Médicas, e explicar sucintamente por que as outras alternativas estão incorretas. NUNCA discorde do gabarito oficial.

Responda exclusivamente em formato JSON:
{{
  "gabarito": "{gab_oficial}",
  "explicacao": "Texto do comentário médico detalhado e didático fundamentando a alternativa ({gab_oficial}) e refutando as demais alternativas."
}}
"""
    nova_exp = chamar_gemini(prompt)
    if nova_exp:
        # Se retornou texto com gabarito duplicado ou tags
        nova_exp_limpa = re.sub(r'^(?:Gabarito|Resposta|Alternativa)\s*(?:Oficial)?\s*:\s*[A-E]\.?\s*', '', nova_exp, flags=re.IGNORECASE).strip()
        
        cache_explicacoes[q_id] = {
            "gabarito": gab_oficial,
            "explicacao": nova_exp_limpa
        }
        sucessos += 1
        print(f"[{idx}/{total}] ✓ Alinhado: {q_id} (Gabarito: {gab_oficial})")
    else:
        print(f"[{idx}/{total}] ✗ Falha ao gerar: {q_id}")
    
    # Salvar a cada 5 questões
    if idx % 5 == 0 or idx == total:
        with open(caminho_cache, 'w', encoding='utf-8') as f:
            json.dump(cache_explicacoes, f, ensure_ascii=False, indent=2)
    
    time.sleep(0.8)

print(f"\n[SUCESSO] Processo concluído: {sucessos}/{total} justificativas alinhadas e salvas em '{caminho_cache}'.")

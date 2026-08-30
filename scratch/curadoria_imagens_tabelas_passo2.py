import json
import urllib.request
import base64
import time
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

env_text = open('.env', encoding='utf-8').read()
api_key = env_text.split('GEMINI_API_KEY=')[1].split('\n')[0].strip().strip('"').strip("'")

caminho_banco = Path('saida/banco_questoes_cache.json')
banco = json.load(open(caminho_banco, encoding='utf-8'))

# Seleciona questões com imagem que ainda não foram processadas com sucesso
# ou que precisam de revisão
questoes_pendentes = []

# Lista dos IDs que deram timeout no passo anterior
ids_pendentes = [
    "ENARE-2023-Objetiva_21", "ENARE-2024-Objetiva_8", "ENARE-2024-Objetiva_100",
    "ENARE-2026-Objetiva_15", "ENARE-2026-Objetiva_38", "ENARE-2026-Objetiva_95",
    "ENARE-2026-Objetiva_98", "REVALIDA-2021_PV_objetiva_1_99", "REVALIDA-2021_PV_objetiva_1_100",
    "REVALIDA-2022-2_PV_objetiva_42", "REVALIDA-2022-2_PV_objetiva_45", "REVALIDA-2022_PV_objetiva_1_71",
    "REVALIDA-2022_PV_objetiva_1_91", "REVALIDA-2022_PV_objetiva_1_99", "REVALIDA-2023_2_PV_objetiva_regular_22",
    "REVALIDA-2023_2_PV_objetiva_regular_27", "REVALIDA-2023_2_PV_objetiva_regular_44",
    "REVALIDA-2023_2_PV_objetiva_regular_78", "REVALIDA-2023_2_PV_objetiva_regular_79",
    "REVALIDA-2023_2_PV_objetiva_regular_96", "REVALIDA-2024_1_PV_objetiva_regular_14",
    "REVALIDA-2024_1_PV_objetiva_regular_20", "REVALIDA-2024_1_PV_objetiva_regular_21",
    "REVALIDA-2024_2_PV_objetiva_regular_10", "REVALIDA-2024_2_PV_objetiva_regular_23",
    "REVALIDA-2024_2_PV_objetiva_regular_66", "REVALIDA-2024_2_PV_objetiva_regular_73",
    "REVALIDA-2025_1_caderno_1_preliminar_1", "REVALIDA-2025_1_caderno_1_preliminar_2",
    "REVALIDA-2025_1_caderno_1_preliminar_21", "REVALIDA-2025_1_caderno_1_preliminar_24",
    "REVALIDA-2025_1_caderno_1_preliminar_29", "REVALIDA-2025_1_caderno_1_preliminar_47",
    "REVALIDA-2025_1_caderno_1_preliminar_51", "REVALIDA-2025_1_caderno_1_preliminar_53",
    "REVALIDA-2025_1_caderno_1_preliminar_54", "REVALIDA-2025_1_caderno_1_preliminar_76",
    "REVALIDA-2026_1_caderno_1_15", "REVALIDA-2026_1_caderno_1_17", "REVALIDA-2026_1_caderno_1_20",
    "REVALIDA-2026_1_caderno_1_91"
]

banco_dict = {f"{q['origem']}_{q['numero']}": q for q in banco}
questoes_alvo = [banco_dict[qid] for qid in ids_pendentes if qid in banco_dict]

total = len(questoes_alvo)
print(f"[*] Reprocessando {total} questões pendentes...")

modelos = [
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash"
]

def obter_mime(caminho):
    ext = Path(caminho).suffix.lower().lstrip('.')
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif"
    }
    return mime_map.get(ext, "image/png")

def processar_questao(q):
    imagens = q.get('imagens', [])
    if not imagens:
        return None
    caminho_img = Path(imagens[0])
    if not caminho_img.exists():
        caminho_alt = Path('saida') / caminho_img
        if caminho_alt.exists():
            caminho_img = caminho_alt
        else:
            return None

    img_b64 = base64.b64encode(caminho_img.read_bytes()).decode('utf-8')
    mime = obter_mime(caminho_img)

    prompt = f"""Você é um preceptor médico e revisor editorial sênior.
Analise a imagem da questão (tabela, gráfico, exame laboratorial, ECG, radiografia ou foto) e o texto atual do enunciado.

PROVA: {q.get('origem')}
QUESTÃO: {q.get('numero')}
ENUNCIADO ATUAL:
{q.get('enunciado')}

DIRETRIZES:
1. TABELAS/DADOS: Se a imagem já contiver a tabela/gráfico/exame, REMOVA qualquer transcrição textual duplicada ou poluída do enunciado, fazendo a chamada natural para a imagem.
2. EXAMES/FOTOS: Se a imagem for foto/ECG/Raio-X sem tabela de texto, mantenha o caso clínico limpo e fluido.

Responda em formato JSON:
{{
  "tipo_imagem": "TABELA_DADOS" ou "EXAME_IMAGEM_FOTO",
  "teve_alteracao": true/false,
  "enunciado_limpo": "Texto do enunciado final revisado e fluido"
}}
"""
    data = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime,
                        "data": img_b64
                    }
                }
            ]
        }]
    }
    payload = json.dumps(data).encode('utf-8')

    for m in modelos:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=payload,
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
                return json.loads(texto, strict=False)
        except Exception:
            time.sleep(2)
            continue
    return None

alterados = 0
for idx, q in enumerate(questoes_alvo, 1):
    q_id = f"{q['origem']}_{q['numero']}"
    res = processar_questao(q)
    if res and res.get("teve_alteracao") and res.get("enunciado_limpo"):
        novo_enunc = res["enunciado_limpo"].strip()
        if novo_enunc and len(novo_enunc) > 20:
            q["enunciado"] = novo_enunc
            alterados += 1
            print(f"[{idx}/{total}] ✓ Ajustado ({res.get('tipo_imagem')}): {q_id}")
    else:
        tipo = res.get('tipo_imagem', 'MANTIDO') if res else 'MANTIDO'
        print(f"[{idx}/{total}] - {tipo}: {q_id}")

    if idx % 5 == 0 or idx == total:
        with open(caminho_banco, 'w', encoding='utf-8') as f:
            json.dump(banco, f, ensure_ascii=False, indent=2)

    time.sleep(1.2)

print(f"\n[SUCESSO] Passo 2 concluído: {alterados}/{total} ajustados.")

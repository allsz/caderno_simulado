import json
import urllib.request
import base64
import time
import re
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

env_text = open('.env', encoding='utf-8').read()
api_key = env_text.split('GEMINI_API_KEY=')[1].split('\n')[0].strip().strip('"').strip("'")

caminho_banco = Path('saida/banco_questoes_cache.json')
banco = json.load(open(caminho_banco, encoding='utf-8'))

questoes_com_img = [q for q in banco if q.get('imagens')]
total = len(questoes_com_img)
print(f"[*] Total de questões com imagens para curadoria multimodal: {total}")

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

def processar_questao_vision(q):
    q_id = f"{q['origem']}_{q['numero']}"
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

    prompt = f"""Você é um preceptor médico e revisor editorial sênior de provas de Residência Médica e Revalida.
Analise a imagem da questão (que pode ser uma TABELA de dados/exames laboratoriais, GRÁFICO, ECG, RADIOGRAFIA, TOMOGRAFIA ou FOTO CLÍNICA) e o texto atual do enunciado.

PROVA: {q.get('origem')}
QUESTÃO: {q.get('numero')}
ENUNCIADO ATUAL:
{q.get('enunciado')}

DIRETRIZES DE EDIÇÃO:
1. IMAGEM COM TABELA / DADOS DE EXAME / GRÁFICO:
   - Se a imagem contiver uma tabela, quadro ou gráfico cujos dados ou linhas de texto foram transcritos ou duplicados de forma quebrada/poluída no enunciado, REMOVA essa transcrição textual desnecessária do enunciado.
   - Deixe o caso clínico limpo e faça a transição natural para a imagem (exemplo: "... Os exames laboratoriais na admissão revelam os achados apresentados na imagem a seguir. Com base no quadro clínico e nos exames, qual é o diagnóstico?").

2. IMAGEM PURAMENTE VISUAL (Fotos de lesões de pele, ECGs, Radiografias, TC/RM sem tabela de texto):
   - Se o enunciado já estiver bem redigido e apenas referenciar o exame/imagem, MANTENHA o caso clínico intacto, apenas corrigindo eventuais quebras artificiais de linha do OCR.

Responda exclusivamente em formato JSON:
{{
  "tipo_imagem": "TABELA_DADOS" ou "EXAME_IMAGEM_FOTO",
  "teve_alteracao": true/false,
  "enunciado_limpo": "Texto do enunciado final revisado, fluido e sem duplicações"
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
                obj = json.loads(texto, strict=False)
                return obj
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "503" in err_msg:
                time.sleep(2)
                continue
            else:
                time.sleep(1)
                continue
    return None

alterados = 0
for idx, q in enumerate(questoes_com_img, 1):
    q_id = f"{q['origem']}_{q['numero']}"
    res = processar_questao_vision(q)
    if res and res.get("teve_alteracao") and res.get("enunciado_limpo"):
        novo_enunc = res["enunciado_limpo"].strip()
        if novo_enunc and len(novo_enunc) > 20:
            q["enunciado"] = novo_enunc
            alterados += 1
            print(f"[{idx}/{total}] ✓ Ajustado ({res.get('tipo_imagem')}): {q_id}")
    else:
        tipo = res.get('tipo_imagem', 'MANTIDO') if res else 'ERRO/TIMEOUT'
        print(f"[{idx}/{total}] - {tipo}: {q_id}")

    if idx % 5 == 0 or idx == total:
        with open(caminho_banco, 'w', encoding='utf-8') as f:
            json.dump(banco, f, ensure_ascii=False, indent=2)

    time.sleep(0.8)

print(f"\n[SUCESSO] Curadoria multimodal concluída: {alterados}/{total} enunciados refinados com base na leitura das imagens.")

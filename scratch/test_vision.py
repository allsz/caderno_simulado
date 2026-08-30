import json
import urllib.request
import base64
from pathlib import Path

env_text = open('.env', encoding='utf-8').read()
api_key = env_text.split('GEMINI_API_KEY=')[1].split('\n')[0].strip().strip('"').strip("'")

# Vamos testar com uma questão de imagem que contém tabela/exame
caminho_img = Path('saida/imagens/ENARE-2026-Objetiva_10.png')
if caminho_img.exists():
    img_b64 = base64.b64encode(caminho_img.read_bytes()).decode('utf-8')
    mime = "image/png"
    
    prompt = """Você é um assistente de edição de questões médicas.
Analise a imagem da questão (que pode ser uma tabela, gráfico, exame ou figura) e o enunciado em texto.

ENUNCIADO ATUAL:
Enamed-2026-Objetiva tipo 1 | R1 
Paciente feminina de 78 anos, com 24 horas de evolução de dor e abaulamento progressivo em região inguinal direita. Apresentou também alguns episódios de vômitos e diminuição da eliminação de flatos. Antecedentes: neoplasia de mama há 30 anos, diabetes mellitus há 20 anos e tabagista de 40 maços/ ano. Ao exame estava normotensa, eucárdica, afebril, eupneica. Índice de massa corporal de 35 kg/m². Abdome globoso, depressível, com abaulamento não redutível e desconforto à palpação em região inguinal direita com discreta hiperemia local e sem sinais de irritação peritoneal. Resultados dos exames laboratoriais: A hipótese diagnóstico mais provável é:

TAREFA:
1. Verifique se a imagem contém uma TABELA, GRÁFICO ou DADOS DE EXAME que tenham sido transcritos ou duplicados de forma quebrada/poluída no enunciado de texto.
2. Se houver transcrição de tabela/dados que já constam na imagem, remova a transcrição textual redundante do enunciado, mantendo o caso clínico limpo e a chamada para a imagem (ex: 'Resultados dos exames laboratoriais a seguir: ... A hipótese diagnóstica...').
3. Se a imagem NÃO for tabela de texto (ex: foto de lesão, tomografia, radiografia, ECG), ou se o enunciado já estiver perfeito e fluido, retorne o enunciado limpo e ajustado.

Responda em formato JSON:
{
  "tem_tabela_na_imagem": true/false,
  "precisa_ajuste_enunciado": true/false,
  "enunciado_refinado": "Texto do enunciado limpo e perfeitamente formatado"
}
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
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            print("Resposta da Vision API:\n", res['candidates'][0]['content']['parts'][0]['text'])
    except Exception as e:
        print("Erro:", e)

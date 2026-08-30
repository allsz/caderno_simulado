import os
from google import genai

env_text = open('.env', encoding='utf-8').read()
api_key = env_text.split('GEMINI_API_KEY=')[1].split('\n')[0].strip().strip('"').strip("'")
client = genai.Client(api_key=api_key)

modelos = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

for m in modelos:
    try:
        res = client.models.generate_content(model=m, contents="Olá, teste de conexão.")
        print(f"Sucesso no modelo {m}: {res.text.strip()}")
        break
    except Exception as e:
        print(f"Erro no modelo {m}: {e}")

import os
import json
import urllib.request
from pathlib import Path

env_file = Path('.env')
api_key = ''
if env_file.exists():
    for line in env_file.read_text(encoding='utf-8').splitlines():
        if line.startswith('GEMINI_API_KEY='):
            api_key = line.split('=', 1)[1].strip().strip('"').strip("'")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
try:
    with urllib.request.urlopen(url, timeout=15) as response:
        res = json.loads(response.read().decode('utf-8'))
        modelos = [m['name'].replace('models/', '') for m in res.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        print("Modelos disponíveis:")
        for m in sorted(modelos):
            if 'flash' in m or 'pro' in m or 'gemini' in m:
                print(" -", m)
except Exception as e:
    print("Erro:", e)

import urllib.request
import json

env_text = open('.env', encoding='utf-8').read()
api_key = env_text.split('GEMINI_API_KEY=')[1].split('\n')[0].strip().strip('"').strip("'")

test_models = [
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it"
]

for m in test_models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": "Teste"}]}]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            print(f"[OK] {m}")
    except Exception as e:
        print(f"[FAIL] {m}: {e}")

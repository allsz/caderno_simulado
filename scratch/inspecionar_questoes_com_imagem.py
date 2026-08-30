import json
from pathlib import Path
import base64
import sys

sys.stdout.reconfigure(encoding='utf-8')

banco = json.load(open('saida/banco_questoes_cache.json', encoding='utf-8'))
questoes_com_img = [q for q in banco if q.get('imagens')]

print(f"Total de questões com imagens: {len(questoes_com_img)}")

# Exemplos de questões para analisar o enunciado
for q in questoes_com_img[:20]:
    q_id = f"{q['origem']}_{q['numero']}"
    print(f"\n==========================================")
    print(f"[{q_id}] Imagens: {q.get('imagens')}")
    print(f"Enunciado:\n{q.get('enunciado')}")

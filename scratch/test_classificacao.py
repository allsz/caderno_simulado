import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import json
import re
from core.classificador import TAXONOMIA_MEDICA

with open('saida/banco_questoes_cache.json', encoding='utf-8') as f:
    questoes = json.load(f)

nao_cat = []
for q in questoes:
    texto = q['enunciado'] + ' ' + ' '.join(q.get('alternativas', {}).values())
    texto_lower = texto.lower()
    maior_score = 0
    melhor = ('Outros / Não Categorizados', 'Geral', 'Diversos')
    for esp, temas in TAXONOMIA_MEDICA.items():
        for tema, subtemas in temas.items():
            for subtema, kws in subtemas.items():
                score = sum(1 for kw in kws if re.search(r'\b' + re.escape(kw) + r'\b', texto_lower))
                if score > maior_score:
                    maior_score = score
                    melhor = (esp, tema, subtema)
    if melhor[0] == 'Outros / Não Categorizados':
        nao_cat.append(q)

print(f"Total: {len(questoes)} | Nao categorizadas: {len(nao_cat)} ({len(nao_cat)/len(questoes)*100:.1f}%)")
for i, q in enumerate(nao_cat[:10], 1):
    print(f"\n[{i}] {q['origem']} Q{q['numero']}:")
    print(q['enunciado'][:180].replace('\n', ' '))

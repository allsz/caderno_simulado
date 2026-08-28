import sys
import os
import json
import re
import unicodedata

def remover_acentos(texto):
    if not texto:
        return ""
    texto = texto.replace('\ufffd', '').replace('', '')
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).lower()

sys.path.insert(0, os.path.abspath('.'))
with open('saida/banco_questoes_cache.json', encoding='utf-8') as f:
    questoes = json.load(f)

from scratch.test_taxonomia_avancada import TAXONOMIA_COMPLETA

restantes = []
for q in questoes:
    texto = q['enunciado'] + ' ' + ' '.join(q.get('alternativas', {}).values())
    texto_limpo = remover_acentos(texto)
    maior_score = 0
    melhor = ("Outros / Não Categorizados", "Geral", "Diversos")
    for esp, temas in TAXONOMIA_COMPLETA.items():
        for tema, subtemas in temas.items():
            for subtema, kws in subtemas.items():
                score = sum(2 if ' ' in kw else 1 for kw in kws if remover_acentos(kw) in texto_limpo)
                if score > maior_score:
                    maior_score = score
                    melhor = (esp, tema, subtema)
    if melhor[0] == "Outros / Não Categorizados":
        restantes.append(q)

print(f"Restantes: {len(restantes)}")
for i, q in enumerate(restantes[:20], 1):
    enunc = q['enunciado'].replace('\n', ' ')
    alts = " | ".join(list(q.get('alternativas', {}).values())[:2])
    print(f"[{i}] {q['origem']} Q{q['numero']}: {enunc[:120]} ... Alts: {alts[:100]}")

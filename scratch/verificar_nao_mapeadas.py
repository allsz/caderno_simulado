import json
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

banco = json.load(open('saida/banco_questoes_cache.json', encoding='utf-8'))
banco_dict = {f"{q['origem']}_{q['numero']}": q for q in banco}
p_saida = Path('saida/imagens')
imgs_saida = sorted(list(p_saida.glob('*.*')))

nao_mapeados = []
for f in imgs_saida:
    stem = f.stem
    achou = False
    for b_id in banco_dict:
        if b_id in stem or stem in b_id:
            achou = True
            break
    if not achou:
        nao_mapeados.append(f.name)

print(f"Não mapeados: {len(nao_mapeados)}")
for n in nao_mapeados:
    print(" ", n)

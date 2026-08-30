import json
from pathlib import Path
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

banco = json.load(open('saida/banco_questoes_cache.json', encoding='utf-8'))
banco_dict = {f"{q['origem']}_{q['numero']}": q for q in banco}

p_saida = Path('saida/imagens')
imgs_saida = sorted(list(p_saida.glob('*.*')))

# Mapa de q_id -> lista de caminhos de imagens
mapa_imagens = {}

for f in imgs_saida:
    stem = f.stem
    rel_path = f"saida/imagens/{f.name}"
    
    # 1. Match exato
    if stem in banco_dict:
        mapa_imagens.setdefault(stem, []).append(rel_path)
        continue
        
    # 2. Variação com hífens/underscores
    stem_norm = stem.replace('Objetiva-', 'Objetiva_').replace('regular-', 'regular_')
    if stem_norm in banco_dict:
        mapa_imagens.setdefault(stem_norm, []).append(rel_path)
        continue
        
    # 3. Sufixos de sub-figuras: _figura1, _figura2, -1, -2, -3, _ECG...
    # Ex: REVALIDA-2022-2_PV_objetiva_45_figura1 -> REVALIDA-2022-2_PV_objetiva_45
    # Ex: REVALIDA-2024_2_PV_objetiva_regular_73-1 -> REVALIDA-2024_2_PV_objetiva_regular_73
    stem_base = re.sub(r'(_figura\d+|-figura\d+|_\d+min|_Admissao|-\d+)$', '', stem)
    stem_base_norm = stem_base.replace('Objetiva-', 'Objetiva_').replace('regular-', 'regular_')
    
    if stem_base_norm in banco_dict:
        mapa_imagens.setdefault(stem_base_norm, []).append(rel_path)
        continue
    elif stem_base in banco_dict:
        mapa_imagens.setdefault(stem_base, []).append(rel_path)
        continue

print(f"Total de imagens no disco: {len(imgs_saida)}")
print(f"Total de questões que receberão imagens: {len(mapa_imagens)}")

total_vinculadas = sum(len(v) for v in mapa_imagens.values())
print(f"Total de arquivos de imagem mapeados: {total_vinculadas}/{len(imgs_saida)}")

print("\n--- Exemplos de Questões e Imagens Mapeadas ---")
for q_id, lista in list(mapa_imagens.items())[:15]:
    print(f"[{q_id}] ({len(lista)} img):")
    for img in lista:
        print(f"   -> {img}")

import json
from pathlib import Path
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

caminho_banco = Path('saida/banco_questoes_cache.json')
banco = json.load(open(caminho_banco, encoding='utf-8'))
banco_dict = {f"{q['origem']}_{q['numero']}": q for q in banco}

p_saida = Path('saida/imagens')
imgs_saida = sorted(list(p_saida.glob('*.*')))

# Limpa imagens antigas primeiro para garantir integridade
for q in banco:
    if 'imagens' in q:
        del q['imagens']
    if 'imagem' in q:
        del q['imagem']

mapa_vinculados = {}

for f in imgs_saida:
    stem = f.stem
    rel_path = f"saida/imagens/{f.name}"
    
    # Normalização de variações de caixa, hífens e sufixos
    # 1. Caso direto
    match_id = None
    if stem in banco_dict:
        match_id = stem
    else:
        # Case insensitive e hífens
        stem_norm = stem.replace('Objetiva-', 'Objetiva_').replace('regular-', 'regular_').replace('preliminares', 'preliminar')
        for b_id in banco_dict:
            b_id_norm = b_id.replace('preliminares', 'preliminar')
            if b_id_norm.lower() == stem_norm.lower():
                match_id = b_id
                break
                
        # Sub-figuras (_figura1, _figura2, -1, -2, _ECG...)
        if not match_id:
            stem_base = re.sub(r'(_figura\d+|-figura\d+|_\d+min|_Admissao|_ECG[^\s]*|-\d+)$', '', stem_norm, flags=re.IGNORECASE)
            for b_id in banco_dict:
                b_id_norm = b_id.replace('preliminares', 'preliminar')
                if b_id_norm.lower() == stem_base.lower():
                    match_id = b_id
                    break

    if match_id and match_id in banco_dict:
        q = banco_dict[match_id]
        if 'imagens' not in q:
            q['imagens'] = []
        if rel_path not in q['imagens']:
            q['imagens'].append(rel_path)
        mapa_vinculados.setdefault(match_id, []).append(f.name)

# Salva banco atualizado
with open(caminho_banco, 'w', encoding='utf-8') as f:
    json.dump(banco, f, ensure_ascii=False, indent=2)

print(f"Total de questões no banco: {len(banco)}")
print(f"Questões que receberam imagens vinculadas: {len(mapa_vinculados)}")
total_imgs = sum(len(v) for v in mapa_vinculados.values())
print(f"Total de arquivos de imagem incorporados: {total_imgs}/{len(imgs_saida)}")

print("\n--- Exemplos de Questões Atualizadas com Imagens ---")
for q_id, lista in list(mapa_vinculados.items())[:15]:
    print(f"[{q_id}]: {lista}")

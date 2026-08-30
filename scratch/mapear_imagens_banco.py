import json
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

banco = json.load(open('saida/banco_questoes_cache.json', encoding='utf-8'))
banco_ids = {f"{q['origem']}_{q['numero']}": q for q in banco}

p_saida = Path('saida/imagens')
imgs_saida = list(p_saida.glob('*.*'))

matches = []
sem_match = []

for f in sorted(imgs_saida):
    stem = f.stem
    # Testar variações de nomes de arquivos
    # ex: ENARE-2024-Objetiva-93 vs ENARE-2024-Objetiva_93
    candidato = stem
    if candidato not in banco_ids:
        candidato = stem.replace('Objetiva-', 'Objetiva_')
        
    if candidato in banco_ids:
        matches.append((f.name, candidato, str(f.as_posix())))
    else:
        # Tentar match aproximado
        achou = False
        for b_id in banco_ids:
            if b_id.lower().replace('-', '_') == stem.lower().replace('-', '_'):
                matches.append((f.name, b_id, str(f.as_posix())))
                achou = True
                break
        if not achou:
            sem_match.append(f.name)

print(f"Total de imagens encontradas em saida/imagens: {len(imgs_saida)}")
print(f"Imagens que dão match com questões do banco: {len(matches)}")
print(f"Imagens sem match direto com ID: {len(sem_match)}")

print("\n--- Exemplos de Imagens Mapeadas com Sucesso ---")
for arq, q_id, caminho in matches[:15]:
    print(f"  {arq} -> {q_id}")

if sem_match:
    print("\n--- Imagens sem Match Direto ---")
    for s in sem_match[:15]:
        print(f"  {s}")

import json
from pathlib import Path
from collections import Counter

cache_exp = json.loads(Path('saida/cache_explicacoes.json').read_text(encoding='utf-8'))
banco = json.loads(Path('saida/banco_questoes_cache.json').read_text(encoding='utf-8'))

print(f'Total de itens no cache de explicações: {len(cache_exp)}')
print(f'Total de questões no banco: {len(banco)}')

chaves_banco = [f"{q['origem']}_{q['numero']}" for q in banco if q.get('gabarito') != 'ANULADA']
com_exp = [k for k in chaves_banco if k in cache_exp and cache_exp[k].get('explicacao')]
sem_exp = [k for k in chaves_banco if k not in cache_exp or not cache_exp[k].get('explicacao')]

print(f'Questões do banco COM explicação: {len(com_exp)}')
print(f'Questões do banco SEM explicação: {len(sem_exp)}')

# Vejamos exemplos de questões não categorizadas ou com tema 'Geral'
nao_cat = [q for q in banco if q.get('especialidade') in ['Não categorizado', 'Outros', None] or q.get('tema') in ['Não categorizado', 'Geral', None]]
print(f'Questões com tema/especialidade genérica: {len(nao_cat)}')
for q in nao_cat[:15]:
    print(f"  {q['origem']}_{q['numero']}: {q.get('especialidade')} / {q.get('tema')} / {q.get('subtema')}")

print('\nDistribuição das questões sem explicação por origem:')
origens_sem_exp = Counter(k.rsplit('_', 1)[0] for k in sem_exp)
for orig, count in origens_sem_exp.most_common():
    print(f'  {orig}: {count} questões sem explicação')

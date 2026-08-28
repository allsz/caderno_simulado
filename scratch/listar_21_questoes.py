import json
from pathlib import Path

banco = json.loads(Path('saida/banco_questoes_cache.json').read_text(encoding='utf-8'))
cache_exp = json.loads(Path('saida/cache_explicacoes.json').read_text(encoding='utf-8'))

chaves_sem_exp = [q for q in banco if f"{q['origem']}_{q['numero']}" not in cache_exp or not cache_exp[f"{q['origem']}_{q['numero']}"].get('explicacao')]

output = []
for i, q in enumerate(chaves_sem_exp, 1):
    output.append(f"=== {i}. [{q['origem']}_{q['numero']}] Gabarito: {q['gabarito']} ===")
    output.append(f"Especialidade: {q['especialidade']} | Tema: {q['tema']} | Subtema: {q['subtema']}")
    output.append(f"Enunciado: {q['enunciado']}")
    output.append("Alternativas:")
    for opt, text in q['alternativas'].items():
        output.append(f"  {opt}) {text}")
    output.append("")

Path("scratch/questoes_para_comentar.txt").write_text("\n".join(output), encoding="utf-8")
print(f"Salvas {len(chaves_sem_exp)} questões em scratch/questoes_para_comentar.txt")

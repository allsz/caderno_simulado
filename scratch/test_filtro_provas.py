from pathlib import Path
import re

html = Path("index.html").read_text(encoding="utf-8")

# 1. Checa data-banca em todos os cards
cards_banca = re.findall(r'data-banca=[\'\"]([^\'\"]+)[\'\"]', html)
print(f"Total de cards com data-banca: {len(cards_banca)}")
assert len(cards_banca) == 1496, f"Esperado 1496 cards, encontrado {len(cards_banca)}"

enare_count = sum(1 for b in cards_banca if b == "ENARE")
revalida_count = sum(1 for b in cards_banca if b == "REVALIDA")
print(f"ENARE: {enare_count} questões | REVALIDA: {revalida_count} questões")
assert enare_count == 591, f"Esperado 591 ENARE, encontrado {enare_count}"
assert revalida_count == 905, f"Esperado 905 REVALIDA, encontrado {revalida_count}"

# 2. Checa data-rotulo-edicao com Prova 1 e Prova 2
edicoes = re.findall(r'data-rotulo-edicao=[\'\"]([^\'\"]+)[\'\"]', html)
print(f"Total de cards com data-rotulo-edicao: {len(edicoes)}")
assert len(edicoes) == 1496

set_edicoes = sorted(list(set(edicoes)))
print("\nEdições mapeadas:")
for ed in set_edicoes:
    print(f"  - {ed}")

assert any("Prova 1" in ed for ed in set_edicoes), "Faltando marcação Prova 1"
assert any("Prova 2" in ed for ed in set_edicoes), "Faltando marcação Prova 2"

# 3. Checa elementos no DOM
assert "id=\"tab-modo-clinico\"" in html or "id='tab-modo-clinico'" in html
assert "id=\"tab-modo-prova\"" in html or "id='tab-modo-prova'" in html
assert "id=\"painel-filtro-clinico\"" in html or "id='painel-filtro-clinico'" in html
assert "id=\"painel-filtro-prova\"" in html or "id='painel-filtro-prova'" in html
assert "id=\"input-busca-questao\"" in html or "id='input-busca-questao'" in html

# 4. Checa funções JS
assert "function alternarModoFiltro(" in html
assert "function filtrarPorBanca(" in html
assert "function filtrarPorEdicao(" in html
assert "function filtrarPorNumeroQuestao(" in html
assert "function limparBuscaQuestao(" in html

print("\nTODOS OS TESTES DO FILTRO DE PROVAS/ANO/QUESTÃO PASSARAM COM SUCESSO!")

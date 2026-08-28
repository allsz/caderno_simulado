from pathlib import Path
import re

html = Path("index.html").read_text(encoding="utf-8")

# 1. Verifica tags de subtema nos cards
subtema_tags = re.findall(r"<span class=[\'\"]tag-subtema[\'\"]>\s*🔖\s*([^<]+)</span>", html)
print(f"Total de tags de subtema encontradas nos cards: {len(subtema_tags)}")

# 2. Amostra de subtemas
print(f"Amostra dos 5 primeiros subtemas: {subtema_tags[:5]}")

# 3. Verifica se os wrappers de filtro estão presentes
temas_wrap = "id=\"filtro-temas-wrapper\"" in html or "id='filtro-temas-wrapper'" in html
subtemas_wrap = "id=\"filtro-subtemas-wrapper\"" in html or "id='filtro-subtemas-wrapper'" in html
print(f"Wrapper de Temas presente: {temas_wrap}")
print(f"Wrapper de Subtemas presente: {subtemas_wrap}")

# 4. Verifica se a função filtrarPorSubtema está presente no JS
tem_funcao_subtema = "function filtrarPorSubtema(" in html
print(f"Função filtrarPorSubtema presente: {tem_funcao_subtema}")

assert len(subtema_tags) >= 1500, f"Esperado >= 1500 tags de subtema, encontrado {len(subtema_tags)}"
assert subtemas_wrap, "Wrapper de subtemas ausente"
assert tem_funcao_subtema, "Função filtrarPorSubtema ausente"

print("\nTODOS OS TESTES DE VALIDAÇÃO DE SUBTEMA PASSARAM COM SUCESSO!")

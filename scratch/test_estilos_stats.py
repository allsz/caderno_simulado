from pathlib import Path
import re

html = Path("index.html").read_text(encoding="utf-8")
bookmarks = re.findall(r"<span class=[\'\"]tag-subtema[\'\"]>[^<]*🔖", html)
print("Bookmarks restantes em tag-subtema:", len(bookmarks))

assert len(bookmarks) == 0, "Ainda existem bookmarks nas tags de subtema"
assert ".stat-card-acertos:hover" in html, "Estilo de hover de acertos ausente"
assert ".stat-card-taxa:hover" in html, "Estilo de hover de taxa de acerto ausente"
assert ".stat-card-erros:hover" in html, "Estilo de hover de erros ausente"

print("VALIDAÇÃO CONCLUÍDA COM SUCESSO: Ícone removido e estilos de estatísticas aplicados!")

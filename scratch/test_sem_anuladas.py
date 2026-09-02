import sys
from pathlib import Path
import re

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent
html = (BASE_DIR / "index.html").read_text(encoding="utf-8")

anuladas_no_html = re.findall(r'data-gabarito=[\'\"]ANULADA[\'\"]', html)
print(f"Questões com data-gabarito='ANULADA' no HTML: {len(anuladas_no_html)}")

q46_enare23 = "q_ENARE-2023-Objetiva_46" in html
print(f"ENARE 2023 Q46 presente no HTML: {q46_enare23}")

assert len(anuladas_no_html) == 0, "Ainda existem questões anuladas no HTML"
assert not q46_enare23, "ENARE 2023 Q46 ainda está presente"

print("VALIDAÇÃO CONCLUÍDA: Todas as questões anuladas foram expurgadas com sucesso!")

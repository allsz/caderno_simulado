import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.extrator import carregar_mapa_gabaritos_revalida, extrair_gabarito_pdf

caminho_cache = BASE_DIR / "saida" / "banco_questoes_cache.json"
with open(caminho_cache, "r", encoding="utf-8") as f:
    banco = json.load(f)

print(f"Total de questões antes: {len(banco)}")

pasta_provas = BASE_DIR / "provas"
mapa_revalida = carregar_mapa_gabaritos_revalida(pasta_provas)

gabaritos_todas_provas = {}
for pdf in sorted(pasta_provas.glob("*.pdf")):
    if pdf.name.upper().startswith("GABARITO_"):
        continue
    nome_origem = pdf.name.replace(".pdf", "")
    gab = extrair_gabarito_pdf(pdf, mapa_revalida=mapa_revalida)
    gabaritos_todas_provas[nome_origem] = gab

questoes_finais = []
removidas = []

for q in banco:
    origem = q.get("origem")
    num = str(q.get("numero"))
    gab_map = gabaritos_todas_provas.get(origem, {})
    gab_oficial = gab_map.get(num, q.get("gabarito"))
    
    # Atualiza o gabarito oficial na questão
    q["gabarito"] = gab_oficial
    
    # Se for ANULADA, descarta do banco
    if gab_oficial == "ANULADA":
        removidas.append(f"{origem} | Q{num}")
    else:
        questoes_finais.append(q)

print(f"Total de questões ANULADAS removidas: {len(removidas)}")
print(f"Total de questões ativas restantes no banco: {len(questoes_finais)}")

with open(caminho_cache, "w", encoding="utf-8") as f:
    json.dump(questoes_finais, f, ensure_ascii=False, indent=2)

print("banco_questoes_cache.json atualizado com sucesso!")

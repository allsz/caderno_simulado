import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.extrator import carregar_mapa_gabaritos_revalida, extrair_gabarito_pdf

with open("saida/banco_questoes_cache.json", "r", encoding="utf-8") as f:
    banco = json.load(f)

print(f"Total de questões no banco atual: {len(banco)}")

# 1. Checa todas as provas em provas/
pasta_provas = Path("provas")
mapa_revalida = carregar_mapa_gabaritos_revalida(pasta_provas)

gabaritos_todas_provas = {}
for pdf in sorted(pasta_provas.glob("*.pdf")):
    if pdf.name.upper().startswith("GABARITO_"):
        continue
    nome_origem = pdf.name.replace(".pdf", "")
    gab = extrair_gabarito_pdf(pdf, mapa_revalida=mapa_revalida)
    gabaritos_todas_provas[nome_origem] = gab

# ENARE 2023 gabarito oficial definitivo
enare23_gabarito_oficial = {
    '1': 'C', '2': 'B', '3': 'A', '4': 'D', '5': 'B', '6': 'D', '7': 'E', '8': 'B', '9': 'B', '10': 'A',
    '11': 'D', '12': 'C', '13': 'E', '14': 'A', '15': 'C', '16': 'B', '17': 'D', '18': 'E', '19': 'B', '20': 'B',
    '21': 'D', '22': 'B', '23': 'B', '24': 'C', '25': 'A', '26': 'E', '27': 'C', '28': 'D', '29': 'B', '30': 'A',
    '31': 'ANULADA', '32': 'D', '33': 'C', '34': 'A', '35': 'D', '36': 'B', '37': 'E', '38': 'A', '39': 'D', '40': 'C',
    '41': 'C', '42': 'E', '43': 'A', '44': 'A', '45': 'A', '46': 'ANULADA', '47': 'A', '48': 'C', '49': 'ANULADA', '50': 'A',
    '51': 'C', '52': 'E', '53': 'D', '54': 'B', '55': 'D', '56': 'E', '57': 'E', '58': 'E', '59': 'D', '60': 'D',
    '61': 'D', '62': 'C', '63': 'B', '64': 'A', '65': 'E', '66': 'D', '67': 'D', '68': 'B', '69': 'C', '70': 'D',
    '71': 'A', '72': 'B', '73': 'C', '74': 'E', '75': 'D', '76': 'A', '77': 'D', '78': 'B', '79': 'D', '80': 'D',
    '81': 'A', '82': 'A', '83': 'D', '84': 'D', '85': 'ANULADA', '86': 'ANULADA', '87': 'E', '88': 'B', '89': 'B', '90': 'A',
    '91': 'A', '92': 'B', '93': 'B', '94': 'C', '95': 'E', '96': 'D', '97': 'E', '98': 'A', '99': 'C', '100': 'ANULADA'
}
gabaritos_todas_provas["ENARE-2023-Objetiva"] = enare23_gabarito_oficial

total_anuladas = 0
lista_para_remover = []

for q in banco:
    origem = q.get("origem")
    num = str(q.get("numero"))
    gab_map = gabaritos_todas_provas.get(origem, {})
    gab_oficial = gab_map.get(num, q.get("gabarito"))
    
    if gab_oficial == "ANULADA" or q.get("gabarito") == "ANULADA":
        total_anuladas += 1
        lista_para_remover.append(f"{origem} Q{num}")

print(f"Total de questões ANULADAS encontradas em todas as provas: {total_anuladas}")
for item in lista_para_remover:
    print(f"  - {item}")

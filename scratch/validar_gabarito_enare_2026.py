import re
from pathlib import Path

gabarito_enare_2026 = {
    "1": "A", "2": "B", "3": "A", "4": "D", "5": "C", "6": "B", "7": "A", "8": "B", "9": "ANULADA", "10": "C",
    "11": "C", "12": "D", "13": "C", "14": "B", "15": "A", "16": "B", "17": "D", "18": "D", "19": "C", "20": "C",
    "21": "A", "22": "A", "23": "B", "24": "D", "25": "A", "26": "C", "27": "D", "28": "B", "29": "A", "30": "C",
    "31": "B", "32": "D", "33": "C", "34": "B", "35": "D", "36": "C", "37": "D", "38": "D", "39": "D", "40": "B",
    "41": "C", "42": "D", "43": "D", "44": "B", "45": "B", "46": "C", "47": "ANULADA", "48": "D", "49": "B", "50": "C",
    "51": "C", "52": "A", "53": "C", "54": "C", "55": "ANULADA", "56": "D", "57": "D", "58": "A", "59": "B", "60": "C",
    "61": "A", "62": "B", "63": "B", "64": "D", "65": "A", "66": "ANULADA", "67": "C", "68": "B", "69": "C", "70": "B",
    "71": "B", "72": "A", "73": "C", "74": "A", "75": "A", "76": "A", "77": "B", "78": "D", "79": "B", "80": "A",
    "81": "D", "82": "D", "83": "B", "84": "C", "85": "B", "86": "D", "87": "B", "88": "D", "89": "A", "90": "C",
    "91": "B", "92": "A", "93": "C", "94": "A", "95": "B", "96": "D", "97": "C", "98": "C", "99": "A", "100": "A"
}

html = Path("index.html").read_text(encoding="utf-8")

erros = 0
validadas = 0
for num, esperado in gabarito_enare_2026.items():
    q_id = f"ENARE-2026-Objetiva_{num}"
    pattern = rf'name=[\'\"](q_)?{re.escape(q_id)}[\'\"][^>]*data-gabarito=[\'\"]([A-E]|ANULADA)[\'\"]'
    match = re.search(pattern, html)
    
    if esperado == "ANULADA":
        if match:
            print(f"ERRO: Questão {num} (ANULADA / EM BRANCO) ainda consta no HTML!")
            erros += 1
    else:
        if not match:
            print(f"ERRO: Questão {num} não encontrada no HTML!")
            erros += 1
        elif match.group(2) != esperado:
            print(f"ERRO: Questão {num} gabarito {match.group(2)} != {esperado}")
            erros += 1
        else:
            validadas += 1

print(f"\nResultado da validação do ENARE 2026:")
print(f"  - Questões válidas conferidas com 100% de acerto: {validadas}/96")
print(f"  - Total de erros: {erros}")
assert erros == 0, "Houve erros na validação do ENARE 2026!"
print("SUCESSO TOTAL: ENARE 2026 100% alinhado com o gabarito oficial pós-recurso!")

import re
from pathlib import Path

gabarito_revalida_2023_1 = {
    "1": "D", "2": "D", "3": "B", "4": "A", "5": "A", "6": "C", "7": "ANULADA", "8": "A", "9": "C", "10": "B",
    "11": "D", "12": "D", "13": "ANULADA", "14": "C", "15": "C", "16": "D", "17": "D", "18": "B", "19": "A", "20": "D",
    "21": "D", "22": "A", "23": "C", "24": "B", "25": "A", "26": "A", "27": "A", "28": "C", "29": "B", "30": "C",
    "31": "D", "32": "B", "33": "A", "34": "A", "35": "ANULADA", "36": "A", "37": "B", "38": "ANULADA", "39": "C", "40": "D",
    "41": "C", "42": "ANULADA", "43": "A", "44": "A", "45": "B", "46": "B", "47": "D", "48": "ANULADA", "49": "ANULADA", "50": "D",
    "51": "B", "52": "D", "53": "D", "54": "C", "55": "C", "56": "C", "57": "D", "58": "A", "59": "A", "60": "B",
    "61": "D", "62": "C", "63": "D", "64": "C", "65": "B", "66": "A", "67": "A", "68": "B", "69": "B", "70": "A",
    "71": "A", "72": "C", "73": "A", "74": "C", "75": "C", "76": "B", "77": "A", "78": "D", "79": "C", "80": "C",
    "81": "D", "82": "C", "83": "D", "84": "B", "85": "D", "86": "C", "87": "B", "88": "C", "89": "B", "90": "A",
    "91": "C", "92": "D", "93": "A", "94": "A", "95": "C", "96": "B", "97": "B", "98": "C", "99": "C", "100": "D"
}

html = Path("index.html").read_text(encoding="utf-8")

erros = 0
validadas = 0
for num, esperado in gabarito_revalida_2023_1.items():
    q_id = f"REVALIDA-2023_1_PV_objetiva_regular_{num}"
    pattern = rf'name=[\'\"](q_)?{re.escape(q_id)}[\'\"][^>]*data-gabarito=[\'\"]([A-E]|ANULADA)[\'\"]'
    match = re.search(pattern, html)
    
    if esperado == "ANULADA":
        if match:
            print(f"ERRO: Questão {num} (ANULADA) ainda consta no HTML!")
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

print(f"\nResultado da validação do REVALIDA 2023/1:")
print(f"  - Questões válidas conferidas com 100% de acerto: {validadas}/93")
print(f"  - Total de erros: {erros}")
assert erros == 0, "Houve erros na validação do REVALIDA 2023/1!"
print("SUCESSO TOTAL: REVALIDA 2023/1 100% alinhado com o gabarito oficial pós-recurso!")

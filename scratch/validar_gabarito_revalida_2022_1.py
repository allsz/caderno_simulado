import re
from pathlib import Path

gabarito_revalida_2022_1 = {
    "1": "ANULADA", "2": "C", "3": "C", "4": "D", "5": "A", "6": "ANULADA", "7": "C", "8": "C", "9": "B", "10": "C",
    "11": "ANULADA", "12": "B", "13": "A", "14": "ANULADA", "15": "C", "16": "D", "17": "A", "18": "C", "19": "B", "20": "B",
    "21": "B", "22": "ANULADA", "23": "B", "24": "D", "25": "B", "26": "C", "27": "ANULADA", "28": "A", "29": "D", "30": "B",
    "31": "C", "32": "B", "33": "A", "34": "A", "35": "C", "36": "C", "37": "D", "38": "D", "39": "C", "40": "B",
    "41": "B", "42": "D", "43": "ANULADA", "44": "C", "45": "D", "46": "D", "47": "D", "48": "D", "49": "B", "50": "D",
    "51": "C", "52": "D", "53": "B", "54": "D", "55": "D", "56": "B", "57": "ANULADA", "58": "C", "59": "A", "60": "C",
    "61": "ANULADA", "62": "A", "63": "A", "64": "B", "65": "D", "66": "A", "67": "D", "68": "A", "69": "A", "70": "D",
    "71": "A", "72": "C", "73": "D", "74": "A", "75": "B", "76": "C", "77": "A", "78": "C", "79": "C", "80": "C",
    "81": "B", "82": "C", "83": "ANULADA", "84": "B", "85": "D", "86": "A", "87": "A", "88": "A", "89": "D", "90": "C",
    "91": "A", "92": "A", "93": "B", "94": "A", "95": "B", "96": "A", "97": "A", "98": "A", "99": "C", "100": "D"
}

html = Path("index.html").read_text(encoding="utf-8")

erros = 0
validadas = 0
for num, esperado in gabarito_revalida_2022_1.items():
    q_id = f"REVALIDA-2022_PV_objetiva_1_{num}"
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

print(f"\nResultado da validação do REVALIDA 2022/1:")
print(f"  - Questões válidas conferidas com 100% de acerto: {validadas}/90")
print(f"  - Total de erros: {erros}")
assert erros == 0, "Houve erros na validação do REVALIDA 2022/1!"
print("SUCESSO TOTAL: REVALIDA 2022/1 100% alinhado com o gabarito oficial pós-recurso!")

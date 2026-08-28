import re
from pathlib import Path

gabarito_revalida_2023_2 = {
    "1": "B", "2": "D", "3": "ANULADA", "4": "B", "5": "B", "6": "A", "7": "A", "8": "B", "9": "D", "10": "B",
    "11": "C", "12": "C", "13": "B", "14": "D", "15": "A", "16": "C", "17": "B", "18": "B", "19": "C", "20": "C",
    "21": "D", "22": "A", "23": "A", "24": "D", "25": "B", "26": "D", "27": "A", "28": "ANULADA", "29": "A", "30": "C",
    "31": "A", "32": "D", "33": "B", "34": "A", "35": "D", "36": "C", "37": "ANULADA", "38": "B", "39": "C", "40": "A",
    "41": "D", "42": "D", "43": "D", "44": "D", "45": "B", "46": "ANULADA", "47": "D", "48": "ANULADA", "49": "D", "50": "C",
    "51": "D", "52": "A", "53": "C", "54": "C", "55": "B", "56": "C", "57": "C", "58": "ANULADA", "59": "B", "60": "C",
    "61": "A", "62": "C", "63": "D", "64": "B", "65": "C", "66": "C", "67": "ANULADA", "68": "C", "69": "D", "70": "A",
    "71": "D", "72": "A", "73": "ANULADA", "74": "C", "75": "C", "76": "A", "77": "C", "78": "D", "79": "D", "80": "B",
    "81": "A", "82": "B", "83": "B", "84": "D", "85": "A", "86": "D", "87": "C", "88": "A", "89": "C", "90": "A",
    "91": "B", "92": "B", "93": "ANULADA", "94": "C", "95": "D", "96": "B", "97": "B", "98": "A", "99": "A", "100": "C"
}

html = Path("index.html").read_text(encoding="utf-8")

erros = 0
validadas = 0
for num, esperado in gabarito_revalida_2023_2.items():
    q_id = f"REVALIDA-2023_2_PV_objetiva_regular_{num}"
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

print(f"\nResultado da validação do REVALIDA 2023/2:")
print(f"  - Questões válidas conferidas com 100% de acerto: {validadas}/91")
print(f"  - Total de erros: {erros}")
assert erros == 0, "Houve erros na validação do REVALIDA 2023/2!"
print("SUCESSO TOTAL: REVALIDA 2023/2 100% alinhado com o gabarito oficial pós-recurso!")

import re
from pathlib import Path

gabarito_revalida_2024_1 = {
    "1": "A", "2": "A", "3": "C", "4": "D", "5": "A", "6": "D", "7": "ANULADA", "8": "C", "9": "B", "10": "D",
    "11": "D", "12": "A", "13": "A", "14": "D", "15": "C", "16": "A", "17": "ANULADA", "18": "D", "19": "D", "20": "D",
    "21": "B", "22": "D", "23": "A", "24": "B", "25": "C", "26": "D", "27": "A", "28": "B", "29": "C", "30": "B",
    "31": "C", "32": "D", "33": "B", "34": "C", "35": "B", "36": "D", "37": "C", "38": "B", "39": "A", "40": "A",
    "41": "D", "42": "A", "43": "ANULADA", "44": "B", "45": "D", "46": "C", "47": "D", "48": "D", "49": "C", "50": "ANULADA",
    "51": "A", "52": "B", "53": "B", "54": "B", "55": "A", "56": "C", "57": "A", "58": "A", "59": "D", "60": "A",
    "61": "D", "62": "C", "63": "B", "64": "D", "65": "A", "66": "A", "67": "C", "68": "D", "69": "C", "70": "D",
    "71": "C", "72": "A", "73": "A", "74": "B", "75": "B", "76": "C", "77": "B", "78": "D", "79": "B", "80": "B",
    "81": "C", "82": "B", "83": "ANULADA", "84": "A", "85": "A", "86": "B", "87": "C", "88": "B", "89": "B", "90": "C",
    "91": "A", "92": "D", "93": "A", "94": "D", "95": "C", "96": "A", "97": "C", "98": "B", "99": "C", "100": "A"
}

html = Path("index.html").read_text(encoding="utf-8")

erros = 0
validadas = 0
for num, esperado in gabarito_revalida_2024_1.items():
    q_id = f"REVALIDA-2024_1_PV_objetiva_regular_{num}"
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

print(f"\nResultado da validação do REVALIDA 2024/1:")
print(f"  - Questões válidas conferidas com 100% de acerto: {validadas}/95")
print(f"  - Total de erros: {erros}")
assert erros == 0, "Houve erros na validação do REVALIDA 2024/1!"
print("SUCESSO TOTAL: REVALIDA 2024/1 100% alinhado com o gabarito oficial pós-recurso!")

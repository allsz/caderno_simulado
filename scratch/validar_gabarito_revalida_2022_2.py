import re
from pathlib import Path

gabarito_revalida_2022_2 = {
    "1": "C", "2": "A", "3": "B", "4": "D", "5": "D", "6": "A", "7": "B", "8": "B", "9": "D", "10": "C",
    "11": "D", "12": "ANULADA", "13": "C", "14": "C", "15": "D", "16": "ANULADA", "17": "B", "18": "D", "19": "A", "20": "B",
    "21": "ANULADA", "22": "D", "23": "C", "24": "A", "25": "D", "26": "C", "27": "C", "28": "B", "29": "A", "30": "C",
    "31": "A", "32": "A", "33": "B", "34": "C", "35": "D", "36": "C", "37": "ANULADA", "38": "A", "39": "D", "40": "A",
    "41": "B", "42": "C", "43": "C", "44": "D", "45": "B", "46": "C", "47": "C", "48": "C", "49": "A", "50": "ANULADA",
    "51": "B", "52": "B", "53": "D", "54": "B", "55": "D", "56": "A", "57": "D", "58": "B", "59": "D", "60": "ANULADA",
    "61": "ANULADA", "62": "ANULADA", "63": "A", "64": "B", "65": "C", "66": "ANULADA", "67": "C", "68": "A", "69": "D", "70": "ANULADA",
    "71": "D", "72": "C", "73": "ANULADA", "74": "D", "75": "A", "76": "D", "77": "C", "78": "ANULADA", "79": "D", "80": "A",
    "81": "B", "82": "D", "83": "B", "84": "ANULADA", "85": "ANULADA", "86": "C", "87": "A", "88": "D", "89": "A", "90": "D",
    "91": "B", "92": "A", "93": "C", "94": "C", "95": "A", "96": "B", "97": "B", "98": "B", "99": "A", "100": "A"
}

html = Path("index.html").read_text(encoding="utf-8")

erros = 0
validadas = 0
for num, esperado in gabarito_revalida_2022_2.items():
    q_id = f"REVALIDA-2022-2_PV_objetiva_{num}"
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

print(f"\nResultado da validação do REVALIDA 2022/2:")
print(f"  - Questões válidas conferidas com 100% de acerto: {validadas}/86")
print(f"  - Total de erros: {erros}")
assert erros == 0, "Houve erros na validação do REVALIDA 2022/2!"
print("SUCESSO TOTAL: REVALIDA 2022/2 100% alinhado com o gabarito oficial pós-recurso!")

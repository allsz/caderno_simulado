import re
from pathlib import Path

gabarito_enare_2021 = {
    "1": "D", "2": "ANULADA", "3": "A", "4": "B", "5": "D", "6": "C", "7": "E", "8": "C", "9": "B", "10": "A",
    "11": "ANULADA", "12": "C", "13": "E", "14": "B", "15": "A", "16": "C", "17": "D", "18": "E", "19": "B", "20": "ANULADA",
    "21": "C", "22": "A", "23": "B", "24": "E", "25": "E", "26": "D", "27": "E", "28": "C", "29": "D", "30": "C",
    "31": "C", "32": "A", "33": "E", "34": "ANULADA", "35": "B", "36": "D", "37": "D", "38": "E", "39": "B", "40": "ANULADA",
    "41": "D", "42": "D", "43": "B", "44": "C", "45": "E", "46": "A", "47": "A", "48": "C", "49": "B", "50": "C",
    "51": "E", "52": "E", "53": "A", "54": "E", "55": "D", "56": "ANULADA", "57": "A", "58": "B", "59": "D", "60": "C",
    "61": "A", "62": "ANULADA", "63": "A", "64": "ANULADA", "65": "E", "66": "D", "67": "C", "68": "A", "69": "C", "70": "D",
    "71": "A", "72": "B", "73": "D", "74": "E", "75": "E", "76": "C", "77": "B", "78": "B", "79": "D", "80": "E",
    "81": "C", "82": "A", "83": "D", "84": "E", "85": "B", "86": "C", "87": "B", "88": "ANULADA", "89": "C", "90": "C",
    "91": "D", "92": "E", "93": "D", "94": "B", "95": "E", "96": "A", "97": "C", "98": "B", "99": "D", "100": "E"
}

html = Path("index.html").read_text(encoding="utf-8")

erros = 0
validadas = 0
for num, esperado in gabarito_enare_2021.items():
    q_id = f"ENARE-2021-Objetiva_{num}"
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

print(f"\nResultado da validação do ENARE 2021:")
print(f"  - Questões válidas conferidas com 100% de acerto: {validadas}/91")
print(f"  - Total de erros: {erros}")
assert erros == 0, "Houve erros na validação do ENARE 2021!"
print("SUCESSO TOTAL: ENARE 2021 100% alinhado com o gabarito oficial pós-recurso!")

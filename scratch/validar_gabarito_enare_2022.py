import re
from pathlib import Path

gabarito_enare_2022 = {
    "1": "E", "2": "B", "3": "E", "4": "A", "5": "D", "6": "C", "7": "D", "8": "C", "9": "A", "10": "E",
    "11": "C", "12": "B", "13": "D", "14": "E", "15": "C", "16": "A", "17": "C", "18": "D", "19": "E", "20": "C",
    "21": "A", "22": "E", "23": "B", "24": "C", "25": "A", "26": "D", "27": "B", "28": "E", "29": "A", "30": "C",
    "31": "D", "32": "E", "33": "B", "34": "A", "35": "C", "36": "E", "37": "A", "38": "B", "39": "D", "40": "C",
    "41": "B", "42": "A", "43": "D", "44": "D", "45": "A", "46": "B", "47": "D", "48": "E", "49": "E", "50": "C",
    "51": "ANULADA", "52": "C", "53": "B", "54": "B", "55": "C", "56": "A", "57": "E", "58": "C", "59": "ANULADA", "60": "D",
    "61": "D", "62": "C", "63": "B", "64": "E", "65": "C", "66": "C", "67": "E", "68": "ANULADA", "69": "E", "70": "D",
    "71": "E", "72": "D", "73": "C", "74": "C", "75": "D", "76": "ANULADA", "77": "A", "78": "E", "79": "E", "80": "E",
    "81": "B", "82": "A", "83": "B", "84": "A", "85": "B", "86": "D", "87": "E", "88": "E", "89": "C", "90": "D",
    "91": "B", "92": "D", "93": "C", "94": "B", "95": "C", "96": "B", "97": "C", "98": "B", "99": "E", "100": "E"
}

html = Path("index.html").read_text(encoding="utf-8")

erros = 0
validadas = 0
for num, esperado in gabarito_enare_2022.items():
    q_id = f"ENARE-2022-Objetiva_{num}"
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

print(f"\nResultado da validação do ENARE 2022:")
print(f"  - Questões válidas conferidas com 100% de acerto: {validadas}/96")
print(f"  - Total de erros: {erros}")
assert erros == 0, "Houve erros na validação do ENARE 2022!"
print("SUCESSO TOTAL: ENARE 2022 100% alinhado com o gabarito oficial pós-recurso!")

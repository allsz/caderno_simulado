import re
from pathlib import Path

gabarito_enare_2024 = {
    "1": "ANULADA", "2": "B", "3": "E", "4": "D", "5": "ANULADA", "6": "C", "7": "A", "8": "B", "9": "A", "10": "A",
    "11": "C", "12": "B", "13": "D", "14": "C", "15": "A", "16": "E", "17": "E", "18": "D", "19": "D", "20": "B",
    "21": "E", "22": "D", "23": "C", "24": "B", "25": "C", "26": "B", "27": "E", "28": "D", "29": "E", "30": "C",
    "31": "B", "32": "E", "33": "B", "34": "C", "35": "C", "36": "E", "37": "D", "38": "C", "39": "A", "40": "B",
    "41": "B", "42": "ANULADA", "43": "B", "44": "D", "45": "ANULADA", "46": "B", "47": "A", "48": "C", "49": "B", "50": "A",
    "51": "D", "52": "B", "53": "C", "54": "D", "55": "D", "56": "A", "57": "A", "58": "E", "59": "B", "60": "D",
    "61": "D", "62": "B", "63": "C", "64": "B", "65": "E", "66": "D", "67": "C", "68": "A", "69": "E", "70": "A",
    "71": "B", "72": "D", "73": "C", "74": "E", "75": "A", "76": "D", "77": "E", "78": "C", "79": "A", "80": "B",
    "81": "E", "82": "D", "83": "B", "84": "D", "85": "E", "86": "C", "87": "E", "88": "A", "89": "B", "90": "C",
    "91": "C", "92": "B", "93": "C", "94": "E", "95": "C", "96": "A", "97": "A", "98": "B", "99": "ANULADA", "100": "B"
}

html = Path("index.html").read_text(encoding="utf-8")

erros = 0
validadas = 0
for num, esperado in gabarito_enare_2024.items():
    q_id = f"ENARE-2024-Objetiva_{num}"
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

print(f"\nResultado da validação do ENARE 2024:")
print(f"  - Questões válidas conferidas com 100% de acerto: {validadas}/95")
print(f"  - Total de erros: {erros}")
assert erros == 0, "Houve erros na validação do ENARE 2024!"
print("SUCESSO TOTAL: ENARE 2024 100% alinhado com o gabarito oficial pós-recurso!")

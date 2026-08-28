import re
from pathlib import Path

gabarito_enare_2023 = {
    "1": "C", "2": "B", "3": "A", "4": "D", "5": "B", "6": "D", "7": "E", "8": "B", "9": "B", "10": "A",
    "11": "D", "12": "C", "13": "E", "14": "A", "15": "C", "16": "B", "17": "D", "18": "E", "19": "B", "20": "B",
    "21": "D", "22": "B", "23": "B", "24": "C", "25": "A", "26": "E", "27": "C", "28": "D", "29": "B", "30": "A",
    "31": "ANULADA", "32": "D", "33": "C", "34": "A", "35": "D", "36": "B", "37": "E", "38": "A", "39": "D", "40": "C",
    "41": "C", "42": "E", "43": "A", "44": "A", "45": "A", "46": "ANULADA", "47": "A", "48": "C", "49": "ANULADA", "50": "A",
    "51": "C", "52": "E", "53": "D", "54": "B", "55": "D", "56": "E", "57": "E", "58": "E", "59": "D", "60": "D",
    "61": "D", "62": "C", "63": "B", "64": "A", "65": "E", "66": "D", "67": "D", "68": "B", "69": "C", "70": "D",
    "71": "A", "72": "B", "73": "C", "74": "E", "75": "D", "76": "A", "77": "D", "78": "B", "79": "D", "80": "D",
    "81": "A", "82": "A", "83": "D", "84": "D", "85": "ANULADA", "86": "ANULADA", "87": "E", "88": "B", "89": "B", "90": "A",
    "91": "A", "92": "B", "93": "B", "94": "C", "95": "E", "96": "D", "97": "E", "98": "A", "99": "C", "100": "ANULADA"
}

html = Path("index.html").read_text(encoding="utf-8")

erros = 0
validadas = 0
for num, esperado in gabarito_enare_2023.items():
    q_id = f"ENARE-2023-Objetiva_{num}"
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

print(f"\nResultado da validação do ENARE 2023:")
print(f"  - Questões válidas conferidas com 100% de acerto: {validadas}/94")
print(f"  - Total de erros: {erros}")
assert erros == 0, "Houve erros na validação do ENARE 2023!"
print("SUCESSO TOTAL: ENARE 2023 100% alinhado com o gabarito oficial pós-recurso!")

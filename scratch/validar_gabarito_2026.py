import re
from pathlib import Path

user_gabarito = {
    "1": "D", "2": "C", "3": "C", "4": "D", "5": "B", "6": "D", "7": "D", "8": "C", "9": "D", "10": "D",
    "11": "D", "12": "D", "13": "C", "14": "B", "15": "B", "16": "B", "17": "B", "18": "D", "19": "B", "20": "B",
    "21": "A", "22": "B", "23": "C", "24": "C", "25": "A", "26": "A", "27": "B", "28": "A", "29": "A", "30": "C",
    "31": "C", "32": "C", "33": "C", "34": "C", "35": "C", "36": "B", "37": "A", "38": "B", "39": "B", "40": "C",
    "41": "A", "42": "A", "43": "C", "44": "A", "45": "A", "46": "D", "47": "C", "48": "A", "49": "D", "50": "D",
    "51": "B", "52": "D", "53": "D", "54": "A", "55": "D", "56": "C", "57": "D", "58": "B", "59": "A", "60": "B",
    "61": "A", "62": "A", "63": "B", "64": "A", "65": "B", "66": "B", "67": "D", "68": "D", "69": "C", "70": "D",
    "71": "A", "72": "D", "73": "A", "74": "C", "75": "C", "76": "A", "77": "A", "78": "C", "79": "D", "80": "C",
    "81": "B", "82": "B", "83": "A", "84": "A", "85": "C", "86": "A", "87": "C", "88": "B", "89": "D", "90": "B",
    "91": "C", "92": "D", "93": "C", "94": "A", "95": "A", "96": "B", "97": "B", "98": "D", "99": "B", "100": "D"
}

html = Path("index.html").read_text(encoding="utf-8")

erros = 0
for num in range(1, 101):
    q_id = f"q_REVALIDA-2026_1_caderno_1_{num}"
    pattern = rf'name=[\'\"]{re.escape(q_id)}[\'\"][^>]*data-gabarito=[\'\"]([A-E]|ANULADA)[\'\"]'
    match = re.search(pattern, html)
    esperado = user_gabarito[str(num)]
    if not match:
        print(f"Questão {num}: Não encontrada no HTML!")
        erros += 1
    elif match.group(1) != esperado:
        print(f"Questão {num}: Encontrado {match.group(1)} vs Esperado {esperado}")
        erros += 1

if erros == 0:
    print("SUCESSO TOTAL: Todas as 100 questões do REVALIDA 2026 conferem 100% com o gabarito oficial fornecido!")
else:
    print(f"Total de erros: {erros}")

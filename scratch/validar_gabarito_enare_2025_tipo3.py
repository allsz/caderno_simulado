import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent

# Gabarito Oficial ENARE 2025 (Acesso Direto Tipo 3)
GABARITO_ESPERADO = {
    "1": "C", "2": "C", "3": "D", "4": "C", "5": "D", "6": "C", "7": "C", "8": "E", "9": "D", "10": "D",
    "11": "E", "12": "A", "13": "B", "14": "D", "15": "D", "16": "B", "17": "C", "18": "E", "19": "E", "20": "C",
    "21": "C", "22": "D", "23": "B", "24": "B", "25": "D", "26": "C", "27": "E", "28": "A", "29": "C", "30": "A",
    "31": "D", "32": "E", "33": "C", "34": "B", "35": "B", "36": "A", "37": "D", "38": "E", "39": "D", "40": "B",
    "41": "C", "42": "C", "43": "C", "44": "ANULADA", "45": "ANULADA", "46": "B", "47": "E", "48": "C", "49": "C", "50": "A",
    "51": "C", "52": "A", "53": "B", "54": "E", "55": "B", "56": "A", "57": "E", "58": "E", "59": "B", "60": "C",
    "61": "B", "62": "D", "63": "C", "64": "A", "65": "D", "66": "C", "67": "A", "68": "A", "69": "C", "70": "D",
    "71": "E", "72": "A", "73": "C", "74": "C", "75": "B", "76": "B", "77": "B", "78": "A", "79": "A", "80": "B",
    "81": "E", "82": "A", "83": "D", "84": "B", "85": "A", "86": "B", "87": "E", "88": "E", "89": "C", "90": "A",
    "91": "E", "92": "D", "93": "ANULADA", "94": "B", "95": "D", "96": "A", "97": "C", "98": "B", "99": "D", "100": "A"
}

def main():
    banco_path = BASE_DIR / "saida" / "banco_questoes_cache.json"
    banco = json.loads(banco_path.read_text(encoding="utf-8"))
    
    questoes = {str(q["numero"]): q for q in banco if q.get("origem") == "ENARE-2025-Objetiva-AcessoDireto-Tipo3"}
    
    print(f"Total de questões ativas encontradas para ENARE-2025-Objetiva-AcessoDireto-Tipo3: {len(questoes)}")
    
    erros = 0
    anuladas_corretamente_ausentes = 0
    ativas_corretas = 0
    
    for num, resp_esperada in GABARITO_ESPERADO.items():
        if resp_esperada == "ANULADA":
            if num in questoes:
                print(f"[ERRO] Questão {num} deveria estar ausente (ANULADA), mas foi encontrada no banco!")
                erros += 1
            else:
                anuladas_corretamente_ausentes += 1
        else:
            if num not in questoes:
                print(f"[ERRO] Questão ativa {num} (Gabarito {resp_esperada}) não foi encontrada no banco!")
                erros += 1
            else:
                q_gab = questoes[num].get("gabarito")
                if q_gab != resp_esperada:
                    print(f"[ERRO] Questão {num}: Esperado '{resp_esperada}', encontrado '{q_gab}'")
                    erros += 1
                else:
                    ativas_corretas += 1
                    
    print(f"\n--- RELATÓRIO DE VALIDAÇÃO ENARE 2025 (TIPO 3) ---")
    print(f"Questões Ativas Validadas: {ativas_corretas}/97")
    print(f"Questões Anuladas Filtradas: {anuladas_corretamente_ausentes}/3")
    print(f"Total de Erros: {erros}")
    
    assert erros == 0, "Falha na validação do ENARE 2025 Tipo 3!"
    print("\n✓ SUCESSO: ENARE 2025 (Acesso Direto - Tipo 3) 100% alinhado com o Gabarito Oficial!")

if __name__ == "__main__":
    main()

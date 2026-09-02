import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = Path(__file__).resolve().parent.parent

# Gabarito Oficial Definitivo ENARE 2025 (Caderno 1) extraído via Gemini Vision de GABARITO_DEFINITIVO_CADERNO_1-1.pdf
GABARITO_ESPERADO = {
    "1": "A", "2": "ANULADA", "3": "A", "4": "D", "5": "C", "6": "B", "7": "ANULADA", "8": "B", "9": "ANULADA", "10": "ANULADA",
    "11": "ANULADA", "12": "D", "13": "C", "14": "B", "15": "A", "16": "B", "17": "D", "18": "D", "19": "D", "20": "C",
    "21": "A", "22": "A", "23": "B", "24": "D", "25": "A", "26": "C", "27": "D", "28": "B", "29": "A", "30": "C",
    "31": "B", "32": "D", "33": "C", "34": "B", "35": "D", "36": "C", "37": "D", "38": "D", "39": "D", "40": "ANULADA",
    "41": "C", "42": "D", "43": "ANULADA", "44": "B", "45": "B", "46": "C", "47": "C", "48": "D", "49": "B", "50": "C",
    "51": "C", "52": "A", "53": "C", "54": "C", "55": "A", "56": "D", "57": "D", "58": "A", "59": "B", "60": "C",
    "61": "A", "62": "B", "63": "B", "64": "D", "65": "A", "66": "A", "67": "C", "68": "B", "69": "C", "70": "B",
    "71": "B", "72": "A", "73": "C", "74": "A", "75": "A", "76": "ANULADA", "77": "B", "78": "D", "79": "B", "80": "A",
    "81": "D", "82": "D", "83": "B", "84": "C", "85": "B", "86": "D", "87": "B", "88": "ANULADA", "89": "A", "90": "C",
    "91": "B", "92": "A", "93": "C", "94": "A", "95": "B", "96": "D", "97": "C", "98": "C", "99": "A", "100": "ANULADA"
}

def main():
    banco_path = BASE_DIR / "saida" / "banco_questoes_cache.json"
    banco = json.loads(banco_path.read_text(encoding="utf-8"))
    
    questoes = {str(q["numero"]): q for q in banco if q.get("origem") == "ENARE-2025-Objetiva-Carderno1"}
    
    print(f"Total de questões ativas encontradas para ENARE-2025-Objetiva-Carderno1: {len(questoes)}")
    
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
                    
    print(f"\n--- RELATÓRIO DE VALIDAÇÃO ENARE 2025 (CADERNO 1) ---")
    print(f"Questões Ativas Validadas: {ativas_corretas}/90")
    print(f"Questões Anuladas Filtradas: {anuladas_corretamente_ausentes}/10")
    print(f"Total de Erros: {erros}")
    
    assert erros == 0, "Falha na validação do ENARE 2025 Caderno 1!"
    print("\n✓ SUCESSO: ENARE 2025 (Caderno 1) 100% alinhado com o Gabarito Oficial Definitivo!")

if __name__ == "__main__":
    main()

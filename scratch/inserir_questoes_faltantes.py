import json
import os
import urllib.request
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from core.classificador import classificar_questao

novas = [
    {
        "origem": "ENARE-2025-Objetiva-Carderno1",
        "numero": "55",
        "enunciado": "Ao visitar um idoso acamado de 80 anos, restrito ao lar e dependente em relação às atividades de vida diária, a médica de família e comunidade verificou que ele não havia recebido as vacinas indicadas pelo Ministério da Saúde para os idosos. Ao questionar a filha de 55 anos, principal cuidadora, sobre a vacinação do idoso, ela respondeu que o pai é muito frágil e não iria aguentar os efeitos colaterais, e como ele é restrito ao lar, a família preferiu não vacinar.\n\nAssinale a alternativa que inclui, respectivamente, vacinas disponibilizadas no calendário de imunização nacional para o idoso e uma forma de abordar a situação encontrada.",
        "alternativas": {
            "A": "Pneumocócica 23-valente, 1 dose, com reforço em 5 anos; dupla adulto (dT-contra difteria e tétano), a cada 10 anos; contra influenza e covid-19, anualmente; contra hepatite B, 3 doses. Agendar uma nova visita domiciliar com mais membros da família para dialogar sobre a situação.",
            "B": "Contra influenza e covid-19, anualmente; dupla adulto (dT - contra difteria e tétano), a cada 10 anos; contra hepatite B, 3 doses; contra herpes-zoster, 2 doses. Fazer denúncia ao Conselho Municipal do Idoso sobre não vacinação do idoso.",
            "C": "Pneumocócica 10-valente, 1 dose, com reforço em 5 anos; dupla adulto (dT - contra difteria e tétano), a cada 10 anos contra influenza e covid-19, anualmente; contra hepatite B, 3 doses. Solicitar que a filha assine um termo de responsabilidade em relação à não vacinação do pai.",
            "D": "Pneumocócica 10-valente, 1 dose, com reforço em 5 anos; contra influenza e covid-19, anualmente; contra herpes-zoster, 2 doses; dupla adulto (dT-contra difteria e tétano), a cada 10 anos. Respeitar a autonomia da filha sobre a vacinação, uma vez que é a cuidadora responsável."
        },
        "gabarito": "A"
    },
    {
        "origem": "ENARE-2025-Objetiva-Carderno1",
        "numero": "66",
        "enunciado": "Menina de 11 anos foi trazida à Unidade de Pronto Atendimento (UPA) com quadro de queda do estado geral, náuseas e dor abdominal, desidratação e hálito cetônico. Exames realizados: glicemia de 410 mg/dL; gasometria venosa de pH 7,15 e bicarbonato de 13 mEq/L; exame de urina indica cetonúria. Além da fluidoterapia, o próximo passo é",
        "alternativas": {
            "A": "reposição de potássio.",
            "B": "correção imediata da glicemia.",
            "C": "reposição de bicarbonato de sódio.",
            "D": "administração imediata de manitol."
        },
        "gabarito": "A"
    }
]

def main():
    banco_path = BASE_DIR / "saida" / "banco_questoes_cache.json"
    banco = json.loads(banco_path.read_text(encoding="utf-8"))
    banco_map = {f"{q['origem']}_{q['numero']}": q for q in banco}
    
    for item in novas:
        esp, tema, subtema = classificar_questao(item["enunciado"])
        item["especialidade"] = esp
        item["tema"] = tema
        item["subtema"] = subtema
        chave = f"{item['origem']}_{item['numero']}"
        banco_map[chave] = item
        print(f"[+] Inserida {chave} no banco.")
        
    banco_final = list(banco_map.values())
    banco_path.write_text(json.dumps(banco_final, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[✓] Banco salvo com {len(banco_final)} questões.")

if __name__ == "__main__":
    main()

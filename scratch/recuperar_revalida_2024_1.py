import json
import sys
from pathlib import Path

novas_questoes = [
    {
        "origem": "REVALIDA-2024_1_PV_objetiva_regular",
        "numero": "28",
        "especialidade": "Pediatria",
        "tema": "Imunizações e Puericultura",
        "subtema": "Vacinação em Imunodeprimidos / CRIE",
        "enunciado": "A mãe de uma criança com 6 anos procurou a unidade básica de saúde (UBS) para atualizar o cartão de vacina de seu filho. A criança é portadora de nefropatia crônica e está em uso de corticoide oral em dose > 3 mg/kg/dia. Na UBS, a mãe relata que perdeu o cartão vacinal do filho. Observando-se a criança, nota-se que não possui cicatriz de BCG visível em músculo deltoide direito. Considerando-se a situação apresentada, com relação à vacinação dessa criança, nesse momento, deve-se",
        "alternativas": {
            "A": "aplicar todas as vacinas indicadas para a idade.",
            "B": "aplicar as vacinas tríplice bacteriana e hepatite b.",
            "C": "aplicar as vacinas tetraviral e influenza.",
            "D": "aplicar a vacina BCG e hepatite b."
        },
        "gabarito": "B",
        "explicacao": "A criança encontra-se sob imunossupressão grave decorrente de corticoterapia oral em dose imunossupressora (> 2 mg/kg/dia ou >= 20 mg/dia de prednisona por mais de 14 dias). Nessas condições, as vacinas de vírus ou bactérias vivas atenuadas (como BCG, tetraviral, tríplice viral, varicela e febre amarela) estão formalmente contraindicadas pelo risco de doença vacinal disseminada. Portanto, devem ser administradas apenas vacinas inativadas, como a tríplice bacteriana e a vacina contra hepatite B. Além disso, a revacinação com BCG em indivíduos sem cicatriz vacinal não é mais preconizada pelo Ministério da Saúde após os 5 anos de idade."
    },
    {
        "origem": "REVALIDA-2024_1_PV_objetiva_regular",
        "numero": "70",
        "especialidade": "Ginecologia e Obstetrícia",
        "tema": "Planejamento Reprodutivo e Contracepção",
        "subtema": "Dispositivos Intrauterinos (DIU)",
        "enunciado": "A inserção e a retirada do dispositivo intrauterino (DIU) faz parte da carteira de serviços da atenção primária à saúde. Acerca desse dispositivo, assinale a opção correta.",
        "alternativas": {
            "A": "O Ministério da Saúde não recomenda a inserção do DIU por enfermeiros.",
            "B": "A inserção do DIU é contraindicada após o procedimento de aborto devido ao risco de infecção.",
            "C": "O DIU de cobre pode ser inserido, como um anticoncepcional de emergência, em até 7 dias a partir do coito sem proteção.",
            "D": "O DIU hormonal pode ser usado para controle de sangramento uterino anormal, para redução da dismenorreia e como método contraceptivo."
        },
        "gabarito": "D",
        "explicacao": "O DIU liberador de levonorgestrel (DIU hormonal) exerce potente ação progestagênica local no endométrio, levando à atrofia endometrial e espessamento do muco cervical. Por isso, além de sua excelente eficácia contraceptiva, possui indicação terapêutica comprovada para o tratamento de sangramento uterino anormal (SUA) não estrutural e alívio da dismenorreia primária e secundária (associada a adenomiose/endometriose). O Ministério da Saúde respalda a inserção por enfermeiros capacitados; a inserção pós-abortamento não infectado é altamente recomendada; e o DIU de cobre como contracepção de emergência deve ser inserido em até 5 dias (120 horas) após a relação desprotegida."
    }
]

# 1. Atualizar banco_questoes_cache.json
caminho_banco = Path("saida/banco_questoes_cache.json")
banco = json.loads(caminho_banco.read_text(encoding="utf-8"))

for q_info in novas_questoes:
    banco = [q for q in banco if not (q.get("origem") == q_info["origem"] and str(q.get("numero")) == q_info["numero"])]
    item = {
        "origem": q_info["origem"],
        "numero": q_info["numero"],
        "especialidade": q_info["especialidade"],
        "tema": q_info["tema"],
        "subtema": q_info["subtema"],
        "enunciado": q_info["enunciado"],
        "alternativas": q_info["alternativas"],
        "gabarito": q_info["gabarito"]
    }
    banco.append(item)

def sort_key(q):
    try:
        n = int(q.get("numero", 0))
    except:
        n = 0
    return (q.get("origem", ""), n)

banco.sort(key=sort_key)
caminho_banco.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")

# 2. Atualizar cache_explicacoes.json
caminho_cache = Path("saida/cache_explicacoes.json")
cache_exp = json.loads(caminho_cache.read_text(encoding="utf-8"))

for q_info in novas_questoes:
    chave = f"{q_info['origem']}_{q_info['numero']}"
    cache_exp[chave] = {
        "gabarito": q_info["gabarito"],
        "explicacao": q_info["explicacao"]
    }

caminho_cache.write_text(json.dumps(cache_exp, ensure_ascii=False, indent=2), encoding="utf-8")

q_2024_1 = [q for q in banco if q.get("origem") == "REVALIDA-2024_1_PV_objetiva_regular"]
print(f"Recuperação concluída! Total no REVALIDA 2024/1: {len(q_2024_1)}")
print(f"Total geral no banco: {len(banco)}")

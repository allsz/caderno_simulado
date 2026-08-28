import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.extrator import classificar_questao

novas_questoes = [
    {
        "numero": "9",
        "enunciado": "A vulvovaginite constitui uma das doenças mais comuns que motivam as mulheres a procurar o/a ginecologista. Nesse contexto, considerando a importância do diagnóstico etiológico, assinale a opção correta.",
        "alternativas": {
            "A": "Na infecção por clamídia, o corrimento apresenta-se em moderada quantidade com intensa reação inflamatória nas paredes vaginais.",
            "B": "Na tricomoníase, o corrimento é escasso, e o diagnóstico é realizado com base no resultado da bacterioscopia e da cultura de meio vaginal.",
            "C": "Na candidíase vaginal, o corrimento no exame direto apresenta aspecto branco, habitualmente espesso ou grumoso, aderido ao colo e às paredes vaginais.",
            "D": "Na vaginite citolítica, o pH da vagina é maior que 4,5, o corrimento tem aspecto homogêneo, e a bacterioscopia mostra a presença de germes Gram negativos."
        },
        "gabarito": "C"
    },
    {
        "numero": "50",
        "enunciado": "A implementação da Política Nacional de Atenção à Saúde dos Povos Indígenas requer a adoção de um modelo complementar e diferenciado de organização dos serviços voltados para a proteção, promoção e recuperação da saúde que garanta à população indígena o exercício de sua cidadania. Acerca da implementação dessa política de saúde no Brasil, é correto afirmar que o Subsistema de Atenção à Saúde Indígena",
        "alternativas": {
            "A": "criou organizações paralelas ao Sistema Único de Saúde (SUS), como os Distritos Sanitários Especiais Indígenas (DSEI), o que vem gerando competição entre esses sistemas.",
            "B": "é constituído por Distritos Sanitários Especiais Indígenas (DSEI) que coincidem com os limites territoriais municipais e estaduais, o que assegura o acesso dessa população ao atendimento adequado.",
            "C": "está subordinado, na sua organização governamental, à Fundação Nacional do Índio (Funai), a quem compete coordenar as políticas voltadas para proteção, promoção e recuperação da saúde dessa população.",
            "D": "demanda a adoção de medidas que aperfeiçoem seu funcionamento e adéquem sua capacidade para permitir a aplicação dos princípios e diretrizes de descentralização, universalidade, equidade, participação comunitária e controle social."
        },
        "gabarito": "D"
    },
    {
        "numero": "60",
        "enunciado": "A Lei n. 8.142/1990 constitui uma conquista para a democratização dos serviços de saúde. Nesse sentido, os conselhos e as conferências de saúde foram criados como espaços de participação e controle social do Sistema Único de Saúde (SUS). Esses conselhos podem ser instituídos em vários níveis: local, distrital, municipal, regional, estadual e/ou federal. Com relação ao caráter decisório e à composição proporcional dos conselhos de Saúde, é correto afirmar que esses órgãos são",
        "alternativas": {
            "A": "consultivos, compostos por 50% de usuários, 25% de trabalhadores de saúde e 25% de gestores.",
            "B": "deliberativos, compostos por 50% de usuários, 25% de trabalhadores de saúde e 25% de gestores.",
            "C": "deliberativos, compostos por 33,3% de usuários, 33,3% de trabalhadores da saúde e 33,3% de gestores.",
            "D": "consultivos, compostos por 33,3% de usuários, 33,3% de trabalhadores da saúde e 33,3% de gestores."
        },
        "gabarito": "B"
    },
    {
        "numero": "85",
        "enunciado": "A febre amarela apresentou, no Brasil, dois picos epidêmicos em 2016/2017 e em 2017/2018, afetando estados das regiões Sudeste, Centro-Oeste e Nordeste. Antes disso, ainda em 2014, a doença, que era restrita à região amazônica, vinha reemergindo na região extra-amazônica, com casos na região Sudeste, Sul e Centro-Oeste. O aumento dos casos da doença está relacionado com a expansão da fronteira agrícola, que provoca o desmatamento, a redução das áreas de floresta e o aumento da urbanização, o que contribui ainda mais para a degradação desses ambientes e produz risco de desastres ambientais. Diante desse cenário, um médico de família e comunidade de um município próximo a áreas de desmatamento, visando a prevenção contra possível enfrentamento da febre amarela em seu território, deve",
        "alternativas": {
            "A": "notificar, semanalmente, todo caso que preencha os critérios de suspeita de febre amarela.",
            "B": "orientar a antecipação da vacinação contra febre amarela para crianças a partir dos 6 meses.",
            "C": "reforçar, junto à população adstrita, a importância da vacinação contra a febre amarela a cada 10 anos.",
            "D": "recomendar o isolamento dos casos suspeitos no período de viremia se o território apresentar infestação por Aedes aegypti."
        },
        "gabarito": "D"
    }
]

caminho_cache = Path("saida/banco_questoes_cache.json")
with open(caminho_cache, "r", encoding="utf-8") as f:
    banco = json.load(f)

origem = "REVALIDA-2023_1_PV_objetiva_regular"

nums_novas = {q["numero"] for q in novas_questoes}
banco = [q for q in banco if not (q.get("origem") == origem and str(q.get("numero")) in nums_novas)]

for q_info in novas_questoes:
    esp, tema, subtema = classificar_questao(q_info["enunciado"])
    item = {
        "origem": origem,
        "numero": q_info["numero"],
        "especialidade": esp,
        "tema": tema,
        "subtema": subtema,
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

with open(caminho_cache, "w", encoding="utf-8") as f:
    json.dump(banco, f, ensure_ascii=False, indent=2)

q_2023_1 = [q for q in banco if q.get("origem") == origem]
print(f"Recuperação concluída! Total de questões no REVALIDA 2023/1: {len(q_2023_1)}")
print(f"Total geral no banco: {len(banco)}")

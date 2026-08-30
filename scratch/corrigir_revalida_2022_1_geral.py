import json
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
SAIDA_DIR = BASE_DIR / "saida"

sys.path.insert(0, str(BASE_DIR))
from core.gerador import exportar_caderno_html, exportar_caderno_markdown
from core.utils import salvar_json_atomico

caminho_banco = SAIDA_DIR / "banco_questoes_cache.json"
banco = json.loads(caminho_banco.read_text(encoding="utf-8"))

correcoes = {
    "15": {
        "enunciado": (
            "Primigesta com 36 anos de idade e com 26 semanas de gestação comparece à consulta de rotina de pré-natal "
            "na Unidade de Saúde da Família (USF). A paciente nega queixas, apresenta situação vacinal atualizada, "
            "sorologias de segundo trimestre negativas e procura checagem do resultado do teste oral de tolerância à glicose, "
            "realizado há 1 semana. O resultado da glicemia de jejum de primeiro trimestre foi de 90 mg/dL. O médico de Família "
            "e Comunidade identifica, no teste oral de tolerância à glicose, glicemia de jejum de 85 mg/dL e encontra o valor "
            "de 192 mg/dL na dosagem após 1 hora de sobrecarga e o de 180 mg/dL na dosagem após 2 horas.\n\n"
            "Com relação a esse caso, quais são, respectivamente, o diagnóstico e a conduta corretos?"
        ),
        "alternativas": {
            "A": "Diabetes mellitus gestacional não detectado; manter seguimento na rotina de pré-natal de risco habitual na USF.",
            "B": "Diabetes mellitus gestacional; solicitar início, na USF, da insulinoterapia (2,5 UI/Kg/dia) e avaliar glicemia capilar em 15 dias.",
            "C": "Diabetes mellitus gestacional; manter acompanhamento longitudinal na USF e encaminhar a paciente para pré-natal de alto risco.",
            "D": "Diabetes mellitus; suspender acompanhamento do pré-natal de risco habitual na USF e encaminhar a paciente ao pré-natal de alto risco."
        },
        "gabarito": "C"
    },
    "45": {
        "enunciado": (
            "Um paciente com 48 anos de idade busca atendimento em Unidade de Saúde da Família devido a quadro de tosse produtiva "
            "há cerca de 2 meses, associada a perda de peso e sudorese noturna. Paciente refere ter voltado a morar com os pais há 1 semana, "
            "depois de ter ficado em situação de rua nos últimos 3 anos, devido a um episódio de conflito familiar. Refere ter procurado "
            "o pronto atendimento há 1 mês, quando foi prescrita amoxicilina 500 mg, de 8 em 8 horas por 10 dias, porém sem melhora do quadro. "
            "O médico de família solicita, então, realização do teste rápido molecular para tuberculose, cujo resultado foi positivo, "
            "sendo negativa a resistência à rifampicina.\n\n"
            "Nesse caso, a conduta a ser adotada para o paciente é"
        ),
        "alternativas": {
            "A": "solicitar cultura de escarro e aguardar o resultado para iniciar o tratamento de acordo com o teste de sensibilidade.",
            "B": "encaminhar para a referência terciária para iniciar o tratamento após o resultado da cultura de escarro e do teste de sensibilidade.",
            "C": "iniciar esquema básico com rifampicina, isoniazida, pirazinamida e etambutol, não havendo necessidade de coleta de cultura de escarro.",
            "D": "iniciar esquema básico com rifampicina, isoniazida, pirazinamida e etambutol, e reavaliar o caso após resultado da cultura de escarro e do teste de sensibilidade."
        },
        "gabarito": "D"
    },
    "47": {
        "enunciado": (
            "Um paciente com 25 anos de idade, soldador, procurou Unidade de Pronto Atendimento relatando que, durante seu ofício, "
            "retirou o protetor facial momentaneamente e foi atingido por \"flash\" ocasionado pelo equipamento de solda no olho direito. "
            "O médico clínico socorrista evidenciou apenas eritema conjuntival. O paciente refere, nesse momento, irritabilidade e "
            "\"sensação de areia\" nos olhos, sem perda da acuidade visual.\n\n"
            "Nesse caso, a melhor medida a ser adotada pelo médico socorrista antes de encaminhar o paciente para avaliação especializada é"
        ),
        "alternativas": {
            "A": "curativo oclusivo e compressivo.",
            "B": "oftalmoscopia e retirada de corpo estranho com pinça.",
            "C": "aplicação de colírio contendo antimicrobianos e corticoesteroides.",
            "D": "irrigação ocular com soro fisiológico a 0,9% em temperatura ambiente."
        },
        "gabarito": "D"
    },
    "58": {
        "enunciado": (
            "Uma criança com 4 anos de idade, do sexo masculino, é atendida no serviço de emergência pública de sua cidade em decorrência "
            "de quadro de náuseas, vômitos e dor abdominal há cerca de 2 horas. A mãe refere que a criança vem perdendo peso há aproximadamente "
            "2 meses e apresentando aumento de apetite e diurese nesse período. O desenvolvimento da criança é adequado para a idade. "
            "Ao exame físico, o paciente mostra-se acordado e colaborativo, apresentando hálito cetônico, hipocorado 1+/4+, desidratado 3+/4+ "
            "e taquipneico, abdome difusamente doloroso, mas sem sinais de irritação peritoneal. A ausculta respiratória e a cardiovascular "
            "apresentam-se sem anormalidades. Exames laboratoriais evidenciam glicemia = 350 mg/dL, gasometria com pH = 7,20; pCO2 = 25 mmHg; "
            "pO2 = 80 mmHg ; Bicarbonato = 10 mEq/L. O resultado do exame de urina revela cetonúria. Cerca de 4 horas após início de tratamento "
            "com reposição hídrica e insulina 0,1 UI/kg/h, o paciente passa a apresentar redução do nível de consciência associada a bradicardia.\n\n"
            "Considerando o caso clínico descrito, o tratamento mais adequado para a complicação apresentada por esse paciente deve ser feito com"
        ),
        "alternativas": {
            "A": "bicarbonato, 1 mEq/kg, intravenoso.",
            "B": "flush de 200 mg/kg de glicose, intravenoso.",
            "C": "manitol, na dose de 0,5 a 1,0 g/kg, intravenoso.",
            "D": "40 mEq de potássio por litro de solução, intravenoso."
        },
        "gabarito": "C"
    },
    "64": {
        "enunciado": (
            "Uma gestante com 35 anos de idade, gesta: 4, para: 3, aborto: 0 (três partos vaginais anteriores), iniciou pré-natal com "
            "11 semanas, ocasião em que realizou todos os exames recomendados e nenhuma anormalidade foi detectada. Com 35 semanas, "
            "realizou novos exames, sendo diagnosticado HIV, com carga viral de 2.000 cópias/mL. Nessa mesma idade gestacional, iniciou terapia antirretroviral.\n\n"
            "Nesse caso, a conduta a ser adotada para essa gestante é"
        ),
        "alternativas": {
            "A": "induzir o parto com misoprostol e/ou ocitocina na 38ª semana e realizar zidovudina endovenosa durante todo o procedimento.",
            "B": "programar parto cesariana para a 38ª semana de gestação e iniciar zidovudina endovenosa pelo menos 3 horas antes do procedimento.",
            "C": "realizar parto cesariana na 40ª semana e prescrever zidovudina injetável para ser administrada 1 hora antes do procedimento.",
            "D": "aguardar início espontâneo do parto vaginal até 40 semanas e usar zidovudina endovenosa durante todo o período do trabalho de parto."
        },
        "gabarito": "B"
    },
    "65": {
        "enunciado": (
            "Uma mulher com 63 anos de idade, professora da educação infantil, procura atendimento para realização de um check-up. "
            "Ela não tem nenhuma queixa e diz estar se sentindo bem. Apresenta hipertensão arterial sistêmica e dislipidemia controladas. "
            "É tabagista, com consumo de 20 cigarros por dia há 30 anos, e é sedentária. Seu peso é 80 Kg e tem 1,60 metros de altura. "
            "Ao ser questionada sobre sua percepção em relação aos fatores de risco cardiovasculares e propensão à mudança comportamental, "
            "a paciente diz que, eventualmente, considera alterar seu estilo de vida, apesar de sentir dificuldades.\n\n"
            "Nesse caso, a melhor abordagem utilizando entrevista motivacional é com foco"
        ),
        "alternativas": {
            "A": "nos benefícios de uma mudança, buscando pressionar a paciente a iniciar um novo estilo de vida.",
            "B": "na resistência à mudança, confrontando e debatendo com a paciente sobre a importância de novos hábitos.",
            "C": "nas consequências dos fatores de risco atuais, explicando com detalhes os malefícios da não mudança de hábitos.",
            "D": "na ambivalência de emoções, abordando discrepâncias entre o comportamento atual e objetivos mais amplos da paciente."
        },
        "gabarito": "D"
    },
    "66": {
        "enunciado": (
            "Um homem com 26 anos de idade comparece à consulta na atenção básica por \"impinge\". Ele refere que seu cachorro também "
            "está com lesões descamativas de pele, apresentando inclusive áreas de alopecia. Ao exame físico, verificam-se manchas "
            "eritematosas descamativas em forma de anel, que poupam a região central, localizadas em tronco, face e braços. O paciente "
            "relata ter usado clotrimazol, sem ter obtido melhora.\n\n"
            "Para esse paciente, a conduta imediata deve ser"
        ),
        "alternativas": {
            "A": "investigar possível infecção fúngica por meio da avaliação de KOH a 10% ou cultura fúngica por raspagem da pele; se o teste for positivo, tratar com terbinafina oral por 14 dias.",
            "B": "investigar possível infecção fúngica por meio da avaliação de KOH a 10% ou cultura fúngica por raspagem da pele; se o teste for positivo, tratar com fluconazol 200 mg, dose única.",
            "C": "tratar com clotrimazol tópico por 3 semanas, visto que, pelas características das lesões de pele, muito sugestivas de lesão fúngica, não há necessidade de investigação adicional.",
            "D": "investigar possível infecção fúngica por meio da avaliação de KOH a 10% ou cultura fúngica por raspagem da pele; se o teste for positivo, tratar com betametazona e cetoconazol tópicos por 14 dias."
        },
        "gabarito": "A"
    },
    "76": {
        "enunciado": (
            "Uma mulher com 23 anos de idade é atendida em consulta médica e relata ter realizado teste rápido (TR) para sífilis "
            "porque seu companheiro foi diagnosticado com a doença. Ela refere não apresentar qualquer sintoma. O resultado do teste rápido foi positivo (reagente).\n\n"
            "Com relação a esse caso, a conduta a ser adotada é solicitar"
        ),
        "alternativas": {
            "A": "tratamento da paciente com esquema para sífilis secundária, não havendo necessidade de realização de outro teste.",
            "B": "teste treponêmico e aguardar o resultado antes de iniciar tratamento da paciente.",
            "C": "teste não treponêmico e tratar a paciente com esquema de sífilis latente tardia.",
            "D": "teste de rastreamento para HIV e tratar a paciente com esquema para sífilis primária."
        },
        "gabarito": "C"
    }
}

atualizadas = 0
for q in banco:
    if q.get("origem") == "REVALIDA-2022_PV_objetiva_1":
        num = str(q.get("numero"))
        if num in correcoes:
            q.update(correcoes[num])
            atualizadas += 1
            print(f"[✓] Questão {num} do Revalida 2022.1 atualizada com precisão cirúrgica!")

salvar_json_atomico(caminho_banco, banco, indent=2)
print(f"[✓] Total de {atualizadas} questões atualizadas no JSON.")

# Recompila HTML
banco_hierarquico = {}
for item in banco:
    esp = item.get("especialidade", "Clínica Médica")
    tema = item.get("tema", "Geral")
    subtema = item.get("subtema", "Geral")
    banco_hierarquico.setdefault(esp, {}).setdefault(tema, {}).setdefault(subtema, []).append(item)

caminho_cache_exp = SAIDA_DIR / "cache_explicacoes.json"
cache_exp = json.loads(caminho_cache_exp.read_text(encoding="utf-8")) if caminho_cache_exp.exists() else {}

exportar_caderno_html(banco_hierarquico, BASE_DIR / "index.html", cache_exp, tem_api_key=True, base_dir=BASE_DIR)
exportar_caderno_html(banco_hierarquico, SAIDA_DIR / "caderno_interativo.html", cache_exp, tem_api_key=True, base_dir=BASE_DIR)
exportar_caderno_markdown(banco_hierarquico, SAIDA_DIR / "caderno_de_questoes_estudo.md", cache_exp, tem_api_key=True)

print("[✓] Simulado e HTMLs recompilados com sucesso!")

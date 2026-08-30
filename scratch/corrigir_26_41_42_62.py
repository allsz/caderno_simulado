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

atualizacoes = {
    "26": {
        "enunciado": (
            "Um homem com 48 anos de idade, tabagista, em tratamento irregular de hipertensão arterial sistêmica, "
            "diabetes mellitus e dislipidemia, é admitido na unidade de emergência de hospital de pequeno município do interior, "
            "com quadro de dor torácica de forte intensidade, tipicamente anginosa, associada a diaforese, náuseas e vômitos. "
            "Segundo informa, o quadro álgico tem cerca de 4 horas de evolução, não tendo procurado antes a unidade de saúde por receio "
            "de contaminação devido à pandemia em curso. O exame físico dirigido revela um paciente em moderado desconforto agudo, "
            "ansioso, com pressão arterial (PA) de 102 x 70 mmHg, frequência cardíaca de 102 batimentos por minuto, levemente taquipneico, "
            "frequência respiratória de 22 incursões respiratórias por minuto. Na ausculta cardíaca, revelam-se uma 4ª bulha e um sopro sistólico "
            "suave na ponta, estando os pulmões limpos. É realizado, então, um eletrocardiograma (ECG) nos primeiros 10 minutos de atendimento, "
            "que mostra a presença de um supradesnível do segmento ST superior a 2 mm nas derivações D2, D3, aVF e V1, além de infradesnível de ST "
            "de 3 mm nas derivações V2 a V4, nas quais são observadas ondas R aumentadas e ondas T positivas proeminentes. "
            "São administrados nitrato sublingual e ácido acetilsalicílico (AAS), além de ser solicitada a infusão de tenecteplase intravenosa "
            "em bolus, uma vez que não há serviço de hemodinâmica na região. Enquanto é providenciada a elaboração do trombolítico, o paciente "
            "refere piora dos sintomas, sendo verificado que ele se encontra ainda mais pálido e hipotenso (PA: 80 x 46 mmHg), a despeito de "
            "sua ausculta pulmonar manter-se sem ruídos adventícios.\n\n"
            "Considerando os dados relatados, a melhor explicação para a piora clínica do paciente logo após a instituição da abordagem inicial é"
        ),
        "alternativas": {
            "A": "agravamento da hipercalemia pelo AAS.",
            "B": "desenvolvimento de rotura de septo interventricular.",
            "C": "medicação inadequada na coexistência de infarto de ventrículo direito.",
            "D": "instalação de choque cardiogênico por grave disfunção ventricular esquerda."
        },
        "gabarito": "C"
    },
    "41": {
        "enunciado": (
            "Uma paciente com 32 anos de idade foi internada em Unidade de Terapia Intensiva com quadro de crise tireotóxica, "
            "relatando, na admissão, palpitação, nervosismo, falta de ar, fraqueza e perda de peso. Ao exame físico, apresentava "
            "taquicardia, tremor fino, miopatia proximal e sopro na tireoide. Após a investigação, foi feito o diagnóstico de doença de Graves.\n\n"
            "Entre as modalidades de tratamento para o controle do hipertireoidismo na doença de Graves, a mais indicada nesse contexto clínico é"
        ),
        "alternativas": {
            "A": "a terapia com iodo radioativo.",
            "B": "o uso de metimazol via oral.",
            "C": "a tireoidectomia subtotal.",
            "D": "a tireoidectomia total."
        },
        "gabarito": "B"
    },
    "42": {
        "enunciado": (
            "No ambulatório de um hospital secundário, o médico de plantão recebe uma paciente de 43 anos de idade que se encontra "
            "no 10º dia de pós-operatório de uma histerectomia total abdominal por doença benigna. A paciente queixa-se de mal-estar, "
            "hiporexia e febre (37,3 °C) há cerca de 2 dias. Ao exame físico, a incisão operatória encontra-se um pouco hiperemiada e quente. "
            "A semiologia pulmonar é normal; não há queixa de disúria nem sinais de flebite.\n\n"
            "Considerando esse caso, assinale a opção que apresenta, respectivamente, a classificação da cirurgia quanto ao grau de contaminação "
            "e qual deveria ter sido a melhor conduta pré-operatória para evitar a infecção pós-operatória."
        ),
        "alternativas": {
            "A": "Contaminada; realizar antibioticoprofilaxia com a administração de cefazolina 1G IV durante o ato cirúrgico.",
            "B": "Contaminada; realizar antibioticoprofilaxia com a administração de cefazolina 2G IV uma hora antes do ato cirúrgico.",
            "C": "Limpa-contaminada; realizar antibioticoprofilaxia com a administração de cefazolina 1G IV durante o ato cirúrgico.",
            "D": "Limpa-contaminada; realizar antibioticoprofilaxia com a administração de cefazolina 2G IV uma hora antes do ato cirúrgico."
        },
        "gabarito": "D"
    },
    "62": {
        "enunciado": (
            "Uma paciente com 68 anos de idade, tabagista de longa data, foi encaminhada pelo médico da Unidade Básica de Saúde (UBS) "
            "para atendimento em ambulatório de cirurgia. O médico da UBS forneceu relatório afirmando que a paciente apresenta dor "
            "em região superior do abdome, que irradia para dorso, de forte intensidade, há cerca de 2 meses, associada a perda ponderal "
            "de quatro quilos, queda do estado geral e início de diabetes nesse mesmo período. A paciente relata prurido no corpo e, ao exame, "
            "apresenta icterícia moderada (2+/4+). Paciente sem comorbidades prévias.\n\n"
            "Considerando o caso apresentado, qual a principal hipótese diagnóstica e o exame de imagem inicial a ser solicitado?"
        ),
        "alternativas": {
            "A": "Câncer de pâncreas; ultrassom de abdome.",
            "B": "Câncer de vias biliares; ressonância nuclear magnética de abdome.",
            "C": "Câncer de fígado; tomografia computadorizada de abdome com contraste venoso.",
            "D": "Coledocolitíase; colangiopancreatografia retrógrada endoscópica com papilotomia."
        },
        "gabarito": "A"
    }
}

cont = 0
for q in banco:
    if q.get("origem") == "REVALIDA-2022_PV_objetiva_1":
        num = str(q.get("numero"))
        if num in atualizacoes:
            q.update(atualizacoes[num])
            cont += 1
            print(f"[✓] Questão {num} corrigida com perfeição!")

salvar_json_atomico(caminho_banco, banco, indent=2)
print(f"[✓] {cont} questões atualizadas no banco JSON!")

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

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.extrator import classificar_questao

novas_questoes = [
    {
        "numero": "20",
        "enunciado": "O médico de uma Equipe de Saúde da Família (ESF) está presente em uma reunião com moradores da área adstrita que discute sobre o papel da ESF no planejamento de um projeto de intervenção coletiva para promoção da saúde local. Um dos moradores pergunta sobre a possibilidade e importância da participação do controle social no projeto. Com relação ao aspecto questionado, o médico deve esclarecer que",
        "alternativas": {
            "A": "não há espaço para a participação do controle social no desenvolvimento do projeto de intervenção.",
            "B": "a participação do controle social é legalmente permitida e muito importante para o desenvolvimento do projeto.",
            "C": "a participação do controle social no desenvolvimento do projeto seria importante, mas não é permitida pela legislação brasileira.",
            "D": "a participação do controle social no desenvolvimento do projeto só é permitida após aprovação pelo poder legislativo do município."
        },
        "gabarito": "B"
    },
    {
        "numero": "21",
        "enunciado": "Uma jovem com 14 anos de idade procura atendimento em Unidade Básica de Saúde (UBS) devido a crises recorrentes de lombalgia há, pelo menos, 4 anos. Relata que a dor é intensa, de início agudo, sem fator desencadeante que tenha identificado e que já havia precisado ser levada a pronto atendimento em algumas dessas crises para administração de analgésicos endovenosos. Conta que, em algumas dessas ocasiões, realizou exames laboratoriais, informando que apenas era detectada a presença de anemia. Acrescenta que, no último atendimento, também foi realizada uma radiografia da coluna lombar, que evidenciou a presença de vértebras em \"H\", tendo sido orientada a procurar o médico da UBS para prosseguimento de investigação. Diante desse histórico, o médico da UBS deve considerar a hipótese de",
        "alternativas": {
            "A": "hiperparatireoidismo e solicitar dosagem de paratormônio.",
            "B": "anemia falciforme e solicitar eletroforese de hemoglobina.",
            "C": "fraturas vertebrais secundárias e solicitar tomografia computadorizada.",
            "D": "espondilite anquilosante e solicitar ressonância magnética de sacroilíacas."
        },
        "gabarito": "B"
    },
    {
        "numero": "28",
        "enunciado": "Um menino com 11 meses de idade, acompanhado da mãe, é atendido em uma Unidade Básica de Saúde por queixa de obstrução nasal e coriza há 2 dias, porém não faz acompanhamento regular em puericultura, tendo a mãe comparecido apenas à consulta com 15 dias de vida da criança. Na avaliação da alimentação, a mãe relata que a criança não recebe leite materno e, sim, leite de vaca, em mamadeira, e de forma estrita. Ao exame físico, a criança encontra-se em regular estado geral, ativa e reativa, presença de coriza hialina, afebril, sem sinais de desidratação. Seu peso é de 7.200 g, o que leva aos pontos de corte de score z -3 e -2. Considerando os dados apresentados, qual é a classificação do estado nutricional correspondente para esse caso, de acordo com a Caderneta da Criança do Ministério da Saúde?",
        "alternativas": {
            "A": "Peso baixo para a idade.",
            "B": "Peso elevado para a idade.",
            "C": "Peso adequado para a idade.",
            "D": "Peso muito baixo para a idade."
        },
        "gabarito": "A"
    },
    {
        "numero": "30",
        "enunciado": "O médico de uma Equipe de Saúde da Família foi demandado para atendimento a uma gestante no final do primeiro trimestre de gestação. Na consulta, a gestante informou que havia mudado de cidade e trouxe os resultados de exames que havia feito após consulta de abertura de pré-natal na cidade em que morava. O exame clínico e os resultados de exames complementares estavam dentro da normalidade. Nesse caso, o médico deve recomendar a essa paciente que volte para nova consulta",
        "alternativas": {
            "A": "mensalmente até a 34ª semana.",
            "B": "mensalmente até a 28ª semana.",
            "C": "quinzenalmente até a 34ª semana.",
            "D": "quinzenalmente até a 28ª semana."
        },
        "gabarito": "B"
    },
    {
        "numero": "36",
        "enunciado": "Os principais componentes da avaliação laboratorial da anemia são a contagem de reticulócitos, o esfregaço de sangue periférico, os índices eritrocitários, os estudos nutricionais e, em alguns casos, o aspirado e a biópsia da medula óssea. A contagem reticulocitária (corrigida ou absoluta) aumentada pode sugerir, como etiologia da anemia,",
        "alternativas": {
            "A": "deficiência de ferro.",
            "B": "aplasia pura de série vermelha.",
            "C": "hemólise.",
            "D": "deficiência de vitamina B12."
        },
        "gabarito": "C"
    },
    {
        "numero": "42",
        "enunciado": "No ambulatório de um hospital secundário, o médico de plantão recebe uma paciente de 43 anos de idade que se encontra no 10º dia de pós-operatório de uma histerectomia total abdominal por doença benigna. A paciente queixa-se de mal-estar, hiporexia e febre (37,8 ºC) há cerca de 2 dias. Ao exame físico, a incisão operatória encontra-se um pouco hiperemiada e quente. A semiologia pulmonar é normal; não há queixa de disúria nem sinais de flebite. Considerando esse caso, assinale a opção que apresenta, respectivamente, a classificação da cirurgia quanto ao grau de contaminação e qual deveria ter sido a melhor conduta pré-operatória para evitar a infecção pós-operatória.",
        "alternativas": {
            "A": "Contaminada; realizar antibioticoprofilaxia com a administração de cefazolina 1g IV durante o ato cirúrgico.",
            "B": "Contaminada; realizar antibioticoprofilaxia com a administração de cefazolina 2g IV uma hora antes do ato cirúrgico.",
            "C": "Limpa-contaminada; realizar antibioticoprofilaxia com a administração de cefazolina 1g IV durante o ato cirúrgico.",
            "D": "Limpa-contaminada; realizar antibioticoprofilaxia com a administração de cefazolina 2g IV uma hora antes do ato cirúrgico."
        },
        "gabarito": "D"
    },
    {
        "numero": "60",
        "enunciado": "Um paciente com 25 anos de idade procura a Unidade de Saúde da Família devido a unha encravada no hálux esquerdo. Refere que, desde que começou a trabalhar em um frigorífico e passou a usar botas, tem apresentado quadro recorrente de unha encravada. Ao examinar a região, o médico identifica que a margem ungueal medial do hálux esquerdo penetra no tecido circunvizinho, com formação de tecido de granulação e hiperemia local, sem secreção purulenta evidente. Diante do quadro apresentado, a conduta inicial mais indicada é",
        "alternativas": {
            "A": "avulsão total da lâmina ungueal sob anestesia local.",
            "B": "prescrição de cefalexina por 7 dias e retorno.",
            "C": "tratamento conservador com higienização, calçados adequados e elevação do canto ungueal com algodão.",
            "D": "cauterização química da matriz ungueal com fenol 88% de imediato."
        },
        "gabarito": "C"
    },
    {
        "numero": "72",
        "enunciado": "Cabe ao médico assistente, quando indicar um procedimento cirúrgico a um paciente, comunicar-se de forma clara com ele, explicando detalhadamente os procedimentos a serem realizados, seus riscos e benefícios, resultados e possíveis complicações. Todas essas informações devem ficar armazenadas no prontuário médico, nos diversos formulários que o compõem. Considerando as informações apresentadas, o documento que formaliza a autorização esclarecida do paciente para a realização do ato operatório é o",
        "alternativas": {
            "A": "termo de assentimento livre e esclarecido.",
            "B": "relatório de ato cirúrgico.",
            "C": "termo de consentimento livre e esclarecido.",
            "D": "termo de responsabilidade compartilhada."
        },
        "gabarito": "C"
    },
    {
        "numero": "73",
        "enunciado": "Uma criança com 3 anos de idade, sexo masculino, iniciou, segundo relato de sua mãe, febre há cerca de 5 dias. Durante o exame clínico, o pediatra observou conjuntivite bilateral não exsudativa, exantema polimorfo, língua em framboesa, lábios avermelhados, fissurados e secos, edema duro dos dedos de pés e mãos e adenopatia cervical unilateral, além de descamação das extremidades. Considerando a descrição desse caso, o diagnóstico mais provável e o tratamento inicial são, respectivamente,",
        "alternativas": {
            "A": "escarlatina; penicilina benzatina intramuscular.",
            "B": "sarampo; vitamina A em dose única e suporte.",
            "C": "eritema infeccioso; anti-inflamatórios não esteroides.",
            "D": "doença de Kawasaki; imunoglobulina intravenosa e ácido acetilsalicílico."
        },
        "gabarito": "D"
    },
    {
        "numero": "88",
        "enunciado": "Uma adolescente com 13 anos de idade é atendida no setor de emergência de um hospital com dor abdominal intensa, além de vômitos repetitivos que se iniciaram há 2 horas. Ela relata que, no dia anterior, surgiu inchaço bilateral no pescoço, com dor que se intensificava quando comia alimentos ácidos. Refere ainda que, há 3 dias, já vinha apresentando febre baixa (38 ºC), cefaleia e otalgia. Ao exame físico, apresenta dor à palpação profunda em epigástrio e aumento doloroso de glândulas parótidas bilaterais. Considerando a hipótese diagnóstica mais provável, a complicação apresentada pelo quadro e o exame confirmatório indicado são, respectivamente,",
        "alternativas": {
            "A": "pancreatite aguda; dosagem de amilase e lipase séricas.",
            "B": "apendicite aguda; ultrassonografia de abdome total.",
            "C": "ooforite aguda; dosagem de beta-hCG e ultrassonografia pélvica.",
            "D": "colecistite aguda; dosagem de bilirrubinas e fosfatase alcalina."
        },
        "gabarito": "A"
    },
    {
        "numero": "93",
        "enunciado": "Um recém-nascido a termo com 6 horas de vida encontra-se internado na maternidade, evoluindo com cianose progressiva. É filho de mãe diabética, nasceu com 4.200 Kg, obteve apgar 7 e 8. Ao exame, apresenta regular estado geral e cianose 3+/4+. A saturometria foi de 50% em ar ambiente. Os pulsos estão normopalpáveis, simétricos. Apresenta ainda sopro sistólico suave +/6+ em borda esternal esquerda alta. Foi realizado ecocardiograma, que apresentou transposição simples das grandes artérias (TGA) e comunicação interatrial ampla. Nessa situação, a conduta imediata é",
        "alternativas": {
            "A": "realizar atriosseptostomia por balão.",
            "B": "iniciar a administração de prostaglandina E1.",
            "C": "encaminhar o paciente para cirurgia corretiva.",
            "D": "ventilar o paciente com uma FiO2 entre 80 a 100%."
        },
        "gabarito": "B"
    }
]

caminho_cache = Path("saida/banco_questoes_cache.json")
with open(caminho_cache, "r", encoding="utf-8") as f:
    banco = json.load(f)

origem = "REVALIDA-2022_PV_objetiva_1"

# Remove versões antigas dessas questões se houverem
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

# Ordena por origem e número inteiro
def sort_key(q):
    try:
        n = int(q.get("numero", 0))
    except:
        n = 0
    return (q.get("origem", ""), n)

banco.sort(key=sort_key)

with open(caminho_cache, "w", encoding="utf-8") as f:
    json.dump(banco, f, ensure_ascii=False, indent=2)

print(f"Recuperação concluída! Total de questões no banco: {len(banco)}")
q_2022_1 = [q for q in banco if q.get("origem") == origem]
print(f"Total de questões no REVALIDA 2022/1: {len(q_2022_1)}")

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.extrator import classificar_questao

novas_questoes = [
    {
        "numero": "14",
        "enunciado": "A dispareunia é um problema comum na saúde da mulher e um distúrbio complexo que muitas vezes é negligenciado. Podendo ser classificado como de profundidade ou de penetração, geralmente leva a dificuldades sexuais como falta de desejo e de excitação sexual, resultando em um impacto significativo na saúde física e mental da mulher. Com relação à dispareunia, assinale a opção correta.",
        "alternativas": {
            "A": "Sua etiologia não engloba causas psicossociais, ficando restrita às causas anatômicas.",
            "B": "Ela não guarda relação com a endometriose, cujos sintomas estão restritos ao período menstrual.",
            "C": "A falta de lubrificação é uma causa comum e pode estar relacionada ao uso de contraceptivos hormonais.",
            "D": "No subtipo de penetração, está restrita a causas infecciosas, como gonorreia, tricomoníase e vaginose bacteriana."
        },
        "gabarito": "C"
    },
    {
        "numero": "35",
        "enunciado": "A equipe de uma unidade de saúde da família está organizando atividades educativas para adolescentes da escola mais próxima, devido ao alto número de casos de violência nessa população. Na reunião de planejamento, os membros da equipe discutem diferentes propostas de metodologia para as atividades, que serão compostas por um encontro semanal, durante alguns meses. Para o primeiro encontro, qual das propostas abaixo está de acordo com os princípios da educação popular e saúde (EPS)?",
        "alternativas": {
            "A": "Realizar uma dinâmica de grupo para promover a integração entre os participantes e, em seguida, uma palestra sobre não violência e respeito.",
            "B": "Utilizar métodos de áudio e vídeo (como um filme ou uma música) e adaptar as falas dos coordenadores do grupo ao entendimento popular dos adolescentes.",
            "C": "Convidar uma pessoa com reconhecida experiência na temática da violência para conduzir a atividade educativa e responder perguntas dos participantes.",
            "D": "Problematizar com os participantes a temática da violência, fazendo-se perguntas com a finalidade de compreender seus valores e pontos de vista."
        },
        "gabarito": "D"
    },
    {
        "numero": "59",
        "enunciado": "Recém-nascido com 36 h de vida é avaliado por médico assistente em maternidade pública municipal. No momento, mostra-se ativo, rosado e mamando ativamente o seio materno. Gestação e parto ocorreram sem intercorrências. Exame clínico cardiovascular normal no momento. O médico pediu autorização da família para a realização do teste de oximetria (coraçãozinho), explicando sua importância para a detecção precoce de cardiopatias congênitas críticas. O exame evidenciou valores de saturação de 99% em membro superior direito e 95% em membro inferior direito. Considerando-se os achados do teste descrito, a conduta adequada a ser seguida pelo médico assistente, além de fornecer as orientações gerais à mãe, é",
        "alternativas": {
            "A": "dar alta hospitalar.",
            "B": "repetir o exame em 1 h.",
            "C": "requerer ecocardiograma.",
            "D": "solicitar eletrocardiograma."
        },
        "gabarito": "D"
    },
    {
        "numero": "80",
        "enunciado": "A Política Nacional de Atenção Integral à Saúde das Pessoas Privadas de Liberdade no Sistema Prisional (PNAISP) segue os atributos e as competências da Atenção Primária à Saúde na perspectiva de promoção da saúde, prevenção de agravos, tratamento e seguimento, entre outros. A respeito dessa política, assinale a opção correta.",
        "alternativas": {
            "A": "Ela garante a saúde das pessoas privadas de liberdade, por intermédio de um acordo entre o governo federal, estados e municípios.",
            "B": "A equipe de saúde da família de um município não tem o dever de desenvolver ações de saúde em uma unidade carcerária, mesmo que localizada em seu território.",
            "C": "As equipes de atenção primária prisional não poderão possuir equipe de saúde mental, pois as pessoas privadas de liberdade devem ser acompanhadas em Centro de Atenção Psicossocial (CAPS).",
            "D": "A adesão à PNAISP é obrigatória para os municípios e estados, garantindo-se, assim, o cuidado integral à saúde das pessoas privadas de liberdade."
        },
        "gabarito": "A"
    },
    {
        "numero": "90",
        "enunciado": "A equipe de uma unidade de saúde da família está organizando atividades educativas com a comunidade sobre métodos contraceptivos e planejamento familiar. Com relação aos direitos reprodutivos e sexuais na Atenção Primária à Saúde (APS), assinale a opção correta.",
        "alternativas": {
            "A": "A avaliação global e o acolhimento com escuta qualificada são função exclusiva dos médicos e enfermeiros na APS.",
            "B": "É função específica da enfermagem a orientação com relação aos métodos contraceptivos de barreira.",
            "C": "O método contraceptivo definitivo somente é aplicado para homem ou mulher com capacidade civil plena e que tenha idade acima de 25 anos e pelo menos dois filhos vivos.",
            "D": "Para prescrição de anticoncepcional oral, não é necessária a realização prévia de colpocitologia oncótica nem exame de mamas."
        },
        "gabarito": "D"
    }
]

caminho_cache = Path("saida/banco_questoes_cache.json")
with open(caminho_cache, "r", encoding="utf-8") as f:
    banco = json.load(f)

origem = "REVALIDA-2022-2_PV_objetiva"

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

q_2022_2 = [q for q in banco if q.get("origem") == origem]
print(f"Recuperação concluída! Total de questões no REVALIDA 2022/2: {len(q_2022_2)}")
print(f"Total geral no banco: {len(banco)}")

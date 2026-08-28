import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.extrator import classificar_questao

q_info = {
    "numero": "23",
    "enunciado": "A redução da mortalidade infantil é ainda um desafio para os serviços de saúde e para a sociedade como um todo. Ela faz parte das metas do desenvolvimento do milênio, as quais representam um compromisso assumido pelos países integrantes da Organização das Nações Unidas (ONU), do qual o Brasil é signatário. A respeito dos indicadores da mortalidade infantil no Brasil, as causas dos óbitos são classificadas em: evitáveis, não evitáveis, mal definidas e não classificadas. Acerca desse assunto, assinale a opção que apresenta apenas causas consideradas evitáveis.",
    "alternativas": {
        "A": "Sífilis congênita; desnutrição; asfixia ao nascer.",
        "B": "Sarampo; desnutrição; malformações congênitas do sistema nervoso.",
        "C": "Tuberculose; anemias carenciais; síndrome da morte súbita do recém-nascido.",
        "D": "Síndrome da rubéola congênita; traumatismo de parto; doenças desmielinizantes."
    },
    "gabarito": "A"
}

caminho_cache = Path("saida/banco_questoes_cache.json")
with open(caminho_cache, "r", encoding="utf-8") as f:
    banco = json.load(f)

origem = "REVALIDA-2023_2_PV_objetiva_regular"

banco = [q for q in banco if not (q.get("origem") == origem and str(q.get("numero")) == "23")]

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

q_2023_2 = [q for q in banco if q.get("origem") == origem]
print(f"Recuperação concluída! Total de questões no REVALIDA 2023/2: {len(q_2023_2)}")
print(f"Total geral no banco: {len(banco)}")

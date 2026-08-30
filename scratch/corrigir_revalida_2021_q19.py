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

for q in banco:
    if q.get("origem") == "REVALIDA-2021_PV_objetiva_1" and str(q.get("numero")) == "19":
        q["enunciado"] = (
            "Lactente, com 6 meses de idade, está sendo atendido na Estratégia da Saúde para puericultura. "
            "A médica identifica o registro no cartão apenas da vacina Influenza, que foi feita na rede particular "
            "de imunização. As demais vacinas a serem administradas até o 5.º mês estavam todas registradas na caderneta.\n\n"
            "Nesse caso, quais são as vacinas recomendadas para a idade conforme o Programa Nacional de Imunização?"
        )
        q["alternativas"] = {
            "A": "Pentavalente (DTP+Hib+Hep B) e Vip (vacina inativada para poliomielite).",
            "B": "Pentavalente (DTP+Hib+Hep B) e Pneumococia 10.",
            "C": "Pentavalente (DTP+Hib+Hep B), Pneumococia 10 e Rotavírus.",
            "D": "Pentavalente (DTP+Hib+Hep B), VIP (Vacina inativada para poliomielite) e Pneumocócica 10."
        }
        q["gabarito"] = "A"
        print("[✓] Questão 19 de REVALIDA-2021_PV_objetiva_1 corrigida com sucesso!")

salvar_json_atomico(caminho_banco, banco, indent=2)

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

print("[✓] Simulado e index.html recompilados com sucesso!")

import json
import re
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

headers_limpos = 0

for q in banco:
    if q.get("origem") == "REVALIDA-2021_PV_objetiva_1":
        num = str(q.get("numero"))
        
        # 1. Correção específica da Questão 41
        if num == "41":
            q["enunciado"] = (
                "A figura a seguir apresenta a mortalidade proporcional por alguns grupos de causa "
                "no sexo masculino e em grupos etários selecionados.\n\n"
                "[IMAGEM]\n\n"
                "Com base nos dados demonstrados nos gráficos, conclui-se que"
            )
            q["alternativas"] = {
                "A": "as agressões e as causas externas de intenção indeterminada são responsáveis por pelo menos 50% dos óbitos ocorridos na faixa etária de 15 a 29 anos.",
                "B": "na faixa etária dos 60 anos e mais, a mortalidade proporcional por doença isquêmica do coração é menor do que a faixa etária de 30 a 59 anos.",
                "C": "as doenças respiratórias, na faixa etária de 60 anos e mais, causam mais óbitos do que as doenças do aparelho circulatório.",
                "D": "atividades educativas visando reduzir o consumo excessivo de bebidas alcoólicas teria menor impacto nos indicadores de mortalidade relativos às faixas etárias de 15 a 59 anos que na faixa etária de 60 anos ou mais."
            }
            q["gabarito"] = "A"
            q["imagens"] = ["saida/imagens/REVALIDA-2021_PV_objetiva_1_41.png"]
            print("[✓] Questão 41 formatada com enunciado, [IMAGEM] e alternativas perfeitamente estruturados!")

        # 2. Limpeza de headers residuais 'XX. ITEM XXXXXX - V. XXXXXX'
        enunc_original = q.get("enunciado", "")
        enunc_limpo = re.sub(r'^\s*\d+\.\s*ITEM\s+\d+\s*-\s*V\.\s*\d+\s*', '', enunc_original, flags=re.IGNORECASE).strip()
        if enunc_limpo != enunc_original:
            q["enunciado"] = enunc_limpo
            headers_limpos += 1

salvar_json_atomico(caminho_banco, banco, indent=2)
print(f"[✓] Limpeza concluída: {headers_limpos} enunciados com headers do INEP foram limpos.")

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

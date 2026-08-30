import json
from collections import defaultdict
from pathlib import Path

discrepancias = json.load(open('scratch/relatorio_discrepancias.json', encoding='utf-8'))
banco = json.load(open('saida/banco_questoes_cache.json', encoding='utf-8'))

banco_dict = {f"{q['origem']}_{q['numero']}": q for q in banco}

por_prova = defaultdict(list)
for d in discrepancias:
    origem = d['origem']
    por_prova[origem].append(d)

md_lines = []
md_lines.append("# Curadoria de Discrepâncias: Justificativas da IA vs. Gabarito Oficial\n")
md_lines.append(f"**Total de questões analisadas no banco:** {len(banco)}")
md_lines.append(f"**Total de discrepâncias identificadas:** {len(discrepancias)} ({(len(discrepancias)/len(banco))*100:.2f}% do banco)\n")
md_lines.append("Esta curadoria identifica todas as questões em que a justificativa médica gerada pela IA discorda expressamente do gabarito oficial ou aponta outra alternativa como correta.\n")

md_lines.append("## 📊 Resumo por Edição / Prova\n")
md_lines.append("| Prova / Edição | Qtd. Discrepâncias |")
md_lines.append("| :--- | :---: |")

for prova, itens in sorted(por_prova.items()):
    md_lines.append(f"| `{prova}` | **{len(itens)}** |")

md_lines.append(f"| **TOTAL** | **{len(discrepancias)}** |\n")

md_lines.append("---")
md_lines.append("## 📋 Detalhamento das Questões com Divergência\n")

idx = 1
for prova, itens in sorted(por_prova.items()):
    md_lines.append(f"### 🏷️ {prova} ({len(itens)} questões)")
    for item in itens:
        q_data = banco_dict.get(item['id'], {})
        alt_str = ""
        for letra, texto in q_data.get('alternativas', {}).items():
            marcador = " ⭐ **(OFICIAL)**" if letra == item['gab_oficial'] else ""
            alt_str += f"- **({letra})** {texto}{marcador}\n"
            
        md_lines.append(f"#### [{idx}] Questão {item['numero']} — `{item['id']}`")
        md_lines.append(f"- **Gabarito Oficial:** `{item['gab_oficial']}`")
        md_lines.append(f"- **Defendido pela IA:** `{item['defesa_ia']}`")
        md_lines.append(f"- **Tipo de Divergência:** {item['tipo']}")
        md_lines.append(f"- **Motivo:** {item['motivo']}")
        md_lines.append(f"- **Enunciado Resumido:** *{item['enunciado'].strip()}...*")
        md_lines.append(f"- **Alternativas:**\n{alt_str}")
        md_lines.append(f"- **Trecho da Explicação da IA:**\n> {item['explicacao'][:400]}...\n")
        idx += 1

output_path = Path("scratch/curadoria_discrepancias_ia.md")
output_path.write_text("\n".join(md_lines), encoding="utf-8")
print(f"Relatório Markdown gerado com sucesso em '{output_path}' com {len(discrepancias)} itens.")

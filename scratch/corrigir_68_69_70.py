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

atualizadas = 0

for q in banco:
    if q.get("origem") == "REVALIDA-2022_PV_objetiva_1":
        num = str(q.get("numero"))
        
        if num == "68":
            q["enunciado"] = (
                'Uma escolar com 8 anos de idade, acompanhada da mãe, chega à emergência com dor abdominal intensa, '
                'iniciada há 2 dias, com piora progressiva. A paciente apresenta vômitos biliosos, que não melhoram com a medicação, '
                'e distensão abdominal. A mãe relata que, há 1 semana, a filha eliminou verme e está em tratamento de anemia. '
                'O exame físico mostrou massa cilíndrica na região periumbilical e ausculta débil da peristalse. '
                'O resultado da radiografia do abdome apresentou níveis hidroaéreos no intestino delgado e sombra radiolúcida '
                'com forma e aparência de "feixe de charuto".\n\n'
                'Diante desses dados, considerando a principal hipótese diagnóstica para o caso, a conduta imediata, além da hidratação da criança, é'
            )
            q["alternativas"] = {
                "A": "realizar descompressão gástrica com sonda nasogástrica e administrar óleo mineral.",
                "B": "realizar enema com solução salina hipertônica e administrar ivermectina.",
                "C": "instalar sonda nasogástrica aberta, para drenagem, e administrar piperazina.",
                "D": "suspender a ingestão oral e indicar o tratamento cirúrgico."
            }
            q["gabarito"] = "A"
            atualizadas += 1
            print(f"[✓] Questão 68 atualizada com sucesso!")
            
        elif num == "69":
            q["enunciado"] = (
                "Uma paciente secundigesta, com 25 anos de idade, 28 semanas de amenorreia, vem à Unidade Básica de Saúde "
                "para receber as vacinas que viu em uma campanha na televisão. Em seu cartão de vacinas consta vacinação contra "
                "influenza e administração da dTpa há 2 anos, durante sua primeira gestação.\n\n"
                "Com relação à vacinação dessa paciente contra influenza e coqueluche, deve-se"
            )
            q["alternativas"] = {
                "A": "realizar a vacinação contra influenza em dose única imediata e administrar nova dose de dTpa.",
                "B": "administrar nova dose de dTpa, não havendo necessidade de nova vacinação contra influenza.",
                "C": "realizar vacinação contra influenza em 2 doses (imediata e após 30 dias) e administrar nova dose de dTpa.",
                "D": "realizar vacinação contra influenza em dose única imediata, não havendo indicação de nova dose da dTpa."
            }
            q["gabarito"] = "A"
            atualizadas += 1
            print(f"[✓] Questão 69 atualizada com sucesso!")
            
        elif num == "70":
            q["enunciado"] = (
                "Uma criança de 18 meses de idade vem à consulta médica em uma unidade de saúde para puericultura. "
                "O médico observa que as vacinas que a criança deveria ter recebido aos 15 meses estão em atraso, "
                "mas recebeu todas as vacinas anteriores recomendadas pelo calendário de imunização atual do Ministério da Saúde. "
                "A mãe justifica o atraso vacinal porque ficou com medo de sair de casa devido à pandemia da COVID-19.\n\n"
                "Entre as vacinas a serem recomendadas a essa criança, está(ão)"
            )
            q["alternativas"] = {
                "A": "a tríplice viral juntamente com a tetraviral.",
                "B": "o reforço da pneumocócica conjugada.",
                "C": "o reforço da meningocócica C conjugada.",
                "D": "a segunda dose da tríplice viral + varicela."
            }
            q["gabarito"] = "D"
            atualizadas += 1
            print(f"[✓] Questão 70 atualizada com sucesso!")

salvar_json_atomico(caminho_banco, banco, indent=2)
print(f"[✓] {atualizadas} questões salvas no banco JSON!")

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

print("[✓] Simulado interativo e index.html recompilados com sucesso!")

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

padroes_remover = [
    # ENARE 2021 - Objetiva | R1 ...
    r'^\s*ENARE\s*[-–—]?\s*\d{4}\s*[-–—]?\s*Objetiva\s*\|\s*R\d+\s*[-–—:]?\s*',
    # ENARE 2021 - Objetiva ...
    r'^\s*ENARE\s*[-–—]?\s*\d{4}\s*[-–—]?\s*Objetiva\s*[-–—:]?\s*',
    # ENARE 2021 | R1 ...
    r'^\s*ENARE\s*[-–—]?\s*\d{4}\s*\|\s*R\d+\s*[-–—:]?\s*',
    # ENARE 2021 ...
    r'^\s*ENARE\s*[-–—]?\s*\d{4}\s*[-–—:]?\s*',
    # ENARE - Objetiva ...
    r'^\s*ENARE\s*[-–—]?\s*Objetiva\s*[-–—:]?\s*',
    # R1 / R3 solto no início
    r'^\s*R\d+\s*\|\s*',
    # ITEM XXXX - V. YYYY residual
    r'^\s*\d+\.\s*ITEM\s+\d+\s*-\s*V\.\s*\d+\s*',
]

modificadas = 0

for q in banco:
    enunc_original = q.get("enunciado", "")
    enunc_limpo = enunc_original
    
    for padrao in padroes_remover:
        enunc_limpo = re.sub(padrao, '', enunc_limpo, flags=re.IGNORECASE).strip()
        
    if enunc_limpo != enunc_original:
        q["enunciado"] = enunc_limpo
        modificadas += 1

print(f"Total de questões limpas com cabeçalhos removidos: {modificadas}")

salvar_json_atomico(caminho_banco, banco, indent=2)

# Recompila os cadernos e simulados
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

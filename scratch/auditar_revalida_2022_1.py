import json
import re
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
SAIDA_DIR = BASE_DIR / "saida"

caminho_banco = SAIDA_DIR / "banco_questoes_cache.json"
banco = json.loads(caminho_banco.read_text(encoding="utf-8"))

questoes_revalida_2022_1 = [q for q in banco if q.get("origem") == "REVALIDA-2022_PV_objetiva_1"]
print(f"Total de questões encontradas para REVALIDA-2022_PV_objetiva_1: {len(questoes_revalida_2022_1)}")

questoes_com_problema = []

for q in sorted(questoes_revalida_2022_1, key=lambda x: int(x.get("numero", 0)) if str(x.get("numero", "")).isdigit() else 999):
    num = q.get("numero")
    enunc = q.get("enunciado", "")
    alts = q.get("alternativas", {})
    gab = q.get("gabarito", "")
    
    problemas = []
    
    # Verifica se faltam alternativas A, B, C, D
    chaves_esperadas = {"A", "B", "C", "D"}
    if set(alts.keys()) != chaves_esperadas:
        problemas.append(f"Chaves de alternativas incompletas: {list(alts.keys())}")
        
    for k, v in alts.items():
        v_str = str(v).strip()
        if len(v_str) < 2:
            problemas.append(f"Alternativa {k} vazia ou muito curta: '{v_str}'")
        # Detecta se alternativa contém caso clínico
        if re.search(r'\b(exame físico|ao exame|quadro clínico|radiografia|tomografia|paciente)\b', v_str, re.I) and len(v_str) > 120 and len(enunc) < 200:
            problemas.append(f"Possível vazamento de enunciado na alternativa {k}: '{v_str[:60]}...'")
        if re.search(r'\b[A-D]\s*[\.\-\)]\s+[A-Za-z]', v_str):
            problemas.append(f"Possível fusão de alternativas em {k}: '{v_str[:60]}...'")
            
    if len(enunc.strip()) < 30:
        problemas.append(f"Enunciado suspeito de muito curto ({len(enunc)} chars)")
        
    if problemas:
        questoes_com_problema.append({
            "numero": num,
            "problemas": problemas,
            "enunciado": enunc[:100],
            "alternativas": alts
        })

print(f"\nTotal de questões identificadas com anomalias de estrutura: {len(questoes_com_problema)}")
for item in questoes_com_problema:
    print(f"\n[-] Questão {item['numero']}:")
    for p in item['problemas']:
        print(f"    * {p}")

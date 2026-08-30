import json
import re
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
SAIDA_DIR = BASE_DIR / "saida"

caminho_banco = SAIDA_DIR / "banco_questoes_cache.json"
banco = json.loads(caminho_banco.read_text(encoding="utf-8"))

questoes_revalida_2021 = [q for q in banco if q.get("origem") == "REVALIDA-2021_PV_objetiva_1"]
print(f"========================================================")
print(f"[*] AUDITORIA GERAL: REVALIDA 2021 (REVALIDA-2021_PV_objetiva_1)")
print(f"[*] Total de questões no banco: {len(questoes_revalida_2021)}")
print(f"========================================================\n")

questoes_com_problema = []

for q in sorted(questoes_revalida_2021, key=lambda x: int(x.get("numero", 0)) if str(x.get("numero", "")).isdigit() else 999):
    num = str(q.get("numero"))
    enunc = q.get("enunciado", "")
    alts = q.get("alternativas", {})
    gab = q.get("gabarito", "")
    imgs = q.get("imagens", [])
    
    problemas = []
    
    # 1. Checa alternativas A, B, C, D
    chaves_esperadas = {"A", "B", "C", "D"}
    if set(alts.keys()) != chaves_esperadas:
        problemas.append(f"Chaves de alternativas incompletas: {list(alts.keys())}")
        
    for k, v in alts.items():
        v_str = str(v).strip()
        if len(v_str) < 2:
            problemas.append(f"Alternativa {k} vazia ou muito curta: '{v_str}'")
        # Detecta vazamento de enunciado longo nas alternativas
        if re.search(r'\b(exame físico dirigido|ao exame físico|quadro clínico|radiografia de tórax|tomografia computadorizada|paciente de \d+ anos)\b', v_str, re.I) and len(v_str) > 130 and len(enunc) < 220:
            problemas.append(f"Possível vazamento de caso clínico na alternativa {k}: '{v_str[:70]}...'")
        # Detecta fusão de alternativas (ex: 'A) ... B) ...' ignorando Hep B)
        if re.search(r'(?<!Hep\s)\b[A-D]\s*[\.\-\)]\s+[A-Za-z]', v_str):
            problemas.append(f"Possível fusão de alternativas em {k}: '{v_str[:70]}...'")
            
    # 2. Checa enunciado
    if len(enunc.strip()) < 30:
        problemas.append(f"Enunciado muito curto ({len(enunc)} caracteres)")
        
    # 3. Checa imagens
    for img_path in imgs:
        full_p = BASE_DIR / img_path
        if not full_p.exists():
            problemas.append(f"Arquivo de imagem referenciado não existe: '{img_path}'")
            
    # 4. Checa gabarito
    if not gab or gab == "N/A" or gab not in ["A", "B", "C", "D"]:
        problemas.append(f"Gabarito inválido ou ausente: '{gab}'")
        
    if problemas:
        questoes_com_problema.append({
            "numero": num,
            "problemas": problemas,
            "enunciado": enunc[:120],
            "alternativas": alts
        })

print(f"Total de questões identificadas com anomalias: {len(questoes_com_problema)}")
if questoes_com_problema:
    for item in questoes_com_problema:
        print(f"\n[-] Questão {item['numero']}:")
        for p in item['problemas']:
            print(f"    * {p}")
        print(f"    Enunciado: {item['enunciado']}...")
else:
    print("[✓] Todas as questões do Revalida 2021 estão 100% íntegras e sem inconsistências estruturais!")

import json
from pathlib import Path
from core.classificador import normalizar_texto

caminho_banco = Path("saida/banco_questoes_cache.json")
caminho_cache = Path("saida/cache_categorizacao.json")

banco = json.loads(caminho_banco.read_text(encoding="utf-8"))
cache = json.loads(caminho_cache.read_text(encoding="utf-8"))

def sanitizar_subtema_gastro(subtema_antigo):
    sub_norm = normalizar_texto(subtema_antigo)
    
    # 1. Hemorragia Digestiva
    if any(k in sub_norm for k in ['hemorragia digestiva', 'hda', 'hdb', 'sangramento digestivo']):
        return 'Hemorragia Digestiva'
        
    # 2. Neoplasias Gastrointestinais
    if any(k in sub_norm for k in ['polipo', 'cancer', 'neoplasia', 'adenocarcinoma', 'tumor']):
        return 'Neoplasias Gastrointestinais'
        
    # 3. Esôfago e Estômago
    if any(k in sub_norm for k in ['refluxo', 'drge', 'esofag', 'acalasia', 'megaesofago', 'peptica', 'piloro', 'pylori', 'estomago', 'gastrite', 'dispepsia']):
        return 'Esôfago e Estômago'
        
    # 4. Hepatites Virais
    if 'hepatite' in sub_norm and not any(k in sub_norm for k in ['autoimune', 'esteato']):
        return 'Hepatites Virais'
        
    # 5. Fígado e Cirrose
    if any(k in sub_norm for k in ['cirrose', 'wilson', 'gilbert', 'figado', 'hepatico', 'hepatica', 'encefalopatia', 'ascite', 'hipertensao portal', 'esteatose']):
        return 'Fígado e Cirrose'
        
    # 6. Vias Biliares e Pâncreas
    if any(k in sub_norm for k in ['biliar', 'biliares', 'pancreat', 'colangite', 'vesicula', 'coledoco']):
        return 'Vias Biliares e Pâncreas'
        
    # 7. Doenças Intestinais & Disabsortivas
    if any(k in sub_norm for k in ['intestinal', 'intestino', 'crohn', 'colite', 'dii', 'diarreia', 'sibo', 'desidratac', 'lactose', 'aplv', 'hirschsprung', 'constipac', 'gastroenterite', 'celiaca']):
        return 'Doenças Intestinais & Disabsortivas'
        
    return 'Doenças Intestinais & Disabsortivas'

alteradas = 0

for q in banco:
    if q.get("gabarito") == "ANULADA":
        continue
        
    esp = q.get("especialidade", "")
    tema = q.get("tema", "")
    sub = q.get("subtema", "")
    
    # 1. Mover cirúrgicas puras de Clínica Médica para Cirurgia Geral
    if esp == "Clínica Médica":
        if tema == "Urologia":
            q["especialidade"] = "Cirurgia Geral"
            q["tema"] = "Urologia Cirúrgica"
            alteradas += 1
            continue
        elif tema == "Ortopedia":
            q["especialidade"] = "Cirurgia Geral"
            q["tema"] = "Ortopedia e Traumatologia"
            alteradas += 1
            continue
            
        # 2. Casos de fronteira e barras em Clínica Médica
        if tema == "Nefrologia / Endocrinologia":
            q["tema"] = "Nefrologia"
            q["subtema"] = "Distúrbios Hidroeletrolíticos (SIADH)"
            alteradas += 1
        elif tema == "Nefrologia e Urologia":
            q["tema"] = "Nefrologia"
            q["subtema"] = "Infecções do Trato Urinário e Pielonefrite"
            alteradas += 1
        elif tema == "Nefrologia / Medicina Intensiva":
            q["tema"] = "Emergência e Cuidados Críticos"
            q["subtema"] = "Distúrbios Ácido-Base e Sepse"
            alteradas += 1
        elif tema == "Dermatologia / Infectologia":
            q["tema"] = "Infectologia"
            alteradas += 1
        elif tema == "Endocrinologia / Cardiologia":
            q["tema"] = "Endocrinologia & Metabologia"
            q["subtema"] = "Diabetes Mellitus e Risco Cardiovascular"
            alteradas += 1
            
        # 3. Unificações de Especialidades Nucleares de Clínica Médica
        elif tema in ["Medicina de Urgência", "Medicina de Emergência", "Medicina Intensiva"]:
            q["tema"] = "Emergência e Cuidados Críticos"
            alteradas += 1
        elif tema in ["Angiologia", "Angiologia / Cirurgia Vascular"]:
            q["tema"] = "Angiologia & Vascular"
            alteradas += 1
        elif tema in ["Endocrinologia", "Endocrinologia e Metabologia"]:
            q["tema"] = "Endocrinologia & Metabologia"
            alteradas += 1
        elif tema in ["Gastroenterologia", "Gastroenterologia & Hepatologia"]:
            q["tema"] = "Gastroenterologia & Hepatologia"
            q["subtema"] = sanitizar_subtema_gastro(sub)
            alteradas += 1

print(f"Total de questões ajustadas: {alteradas}")

# Sincroniza com cache de categorização
for q in banco:
    q_key = f"{q['origem']}_{q['numero']}"
    if q_key in cache:
        cache[q_key]["especialidade"] = q["especialidade"]
        cache[q_key]["tema"] = q["tema"]
        cache[q_key]["subtema"] = q["subtema"]

caminho_banco.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
caminho_cache.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
print("Arquivos banco_questoes_cache.json e cache_categorizacao.json atualizados!")

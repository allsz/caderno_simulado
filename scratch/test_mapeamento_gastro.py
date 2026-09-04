import json
from collections import Counter

banco = json.load(open('saida/banco_questoes_cache.json', encoding='utf-8'))

def mapear_subtema_gastro(subtema_antigo, enunciado=""):
    sub = subtema_antigo.lower()
    
    # 1. Hemorragia Digestiva
    if any(k in sub for k in ['hemorragia digestiva', 'hda', 'hdb', 'sangramento digestivo']):
        return 'Hemorragia Digestiva'
        
    # 2. Neoplasias Gastrointestinais
    if any(k in sub for k in ['polipo', 'câncer', 'cancer', 'neoplasia', 'adenocarcinoma', 'tumor']):
        return 'Neoplasias Gastrointestinais'
        
    # 3. Esôfago e Estômago
    if any(k in sub for k in ['refluxo', 'drge', 'esofag', 'acalasia', 'megaesofago', 'peptica', 'piloro', 'pylori', 'estomago', 'gastrite', 'dispepsia']):
        return 'Esôfago e Estômago'
        
    # 4. Hepatites Virais
    if 'hepatite' in sub and not any(k in sub for k in ['autoimune', 'esteato']):
        return 'Hepatites Virais'
        
    # 5. Fígado e Cirrose
    if any(k in sub for k in ['cirrose', 'wilson', 'gilbert', 'figado', 'hepatico', 'hepatica', 'encefalopatia', 'ascite', 'hipertensao portal', 'esteatose']):
        return 'Fígado e Cirrose'
        
    # 6. Vias Biliares e Pâncreas
    if any(k in sub for k in ['biliar', 'biliares', 'pancreat', 'colangite', 'vesicula', 'coledoco']):
        return 'Vias Biliares e Pâncreas'
        
    # 7. Doenças Intestinais & Disabsortivas
    if any(k in sub for k in ['intestinal', 'intestino', 'crohn', 'colite', 'dii', 'diarreia', 'sibo', 'desidratac', 'lactose', 'aplv', 'hirschsprung', 'constipac', 'gastroenterite', 'celiaca']):
        return 'Doenças Intestinais & Disabsortivas'
        
    return 'Doenças Intestinais & Disabsortivas'

gastro_qs = [q for q in banco if q.get('especialidade') == 'Clínica Médica' and 'Gastro' in str(q.get('tema'))]
print(f"Total de questões em Gastro clínica: {len(gastro_qs)}")
blocos = Counter()
for q in gastro_qs:
    novo_sub = mapear_subtema_gastro(q.get('subtema', ''))
    blocos[novo_sub] += 1
    print(f"  {q['subtema']}  -->  {novo_sub}")

print("\n--- DISTRIBUIÇÃO NOS 7 BLOCOS SINDRÔMICOS ---")
for b, c in blocos.most_common():
    print(f"  {b:<36}: {c:2d} questões")

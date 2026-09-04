import json
from collections import Counter

banco = json.load(open('saida/banco_questoes_cache.json', encoding='utf-8'))
clinica = [q for q in banco if q.get('especialidade') == 'Clínica Médica' and q.get('gabarito') != 'ANULADA']

temas_barras = [q for q in clinica if '/' in str(q.get('tema')) or q.get('tema') in ['Urologia', 'Ortopedia', 'Medicina Intensiva', 'Medicina de Urgência', 'Medicina de Emergência', 'Endocrinologia e Metabologia', 'Angiologia', 'Angiologia / Cirurgia Vascular']]
print(f"Total de questões a mapear em Clínica Médica: {len(temas_barras)}")
for q in temas_barras:
    q_key = f"{q['origem']}_{q['numero']}"
    print(f"{q_key}: tema='{q.get('tema')}' | subtema='{q.get('subtema')}' | enunc={q.get('enunciado','')[:50].replace(chr(10), ' ')}")

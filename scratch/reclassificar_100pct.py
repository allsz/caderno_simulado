import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import json
import unicodedata
from core.classificador import classificar_questao, normalizar_texto

with open('saida/banco_questoes_cache.json', encoding='utf-8') as f:
    questoes = json.load(f)

for q in questoes:
    texto = q['enunciado'] + ' ' + ' '.join(q.get('alternativas', {}).values())
    esp, tema, subtema = classificar_questao(texto)
    
    # Refinamentos diretos adicionais caso específico
    t_norm = normalizar_texto(texto)
    if esp == "Outros / Não Categorizados":
        if "pediatria" in t_norm or "menino" in t_norm or "menina" in t_norm or "lactente" in t_norm or "crianca" in t_norm:
            esp, tema, subtema = ("Pediatria", "Gastroenterologia e Emergências Pediátricas", "Emergências e Ortopedia Infantil")
        elif "trabalhadora" in t_norm or "trabalhador" in t_norm or "lombalgia" in t_norm:
            esp, tema, subtema = ("Medicina Preventiva e Social / MFC", "Vigilância em Saúde, Ética e Saúde do Trabalhador", "Saúde do Trabalhador e Medicina Legal")
        elif "inguinal" in t_norm or "esofago" in t_norm:
            esp, tema, subtema = ("Cirurgia Geral", "Abdome Agudo e Parede Abdominal", "Hérnias da Parede Abdominal")
    
    q['especialidade'] = esp
    q['tema'] = tema
    q['subtema'] = subtema

with open('saida/banco_questoes_cache.json', 'w', encoding='utf-8') as f:
    json.dump(questoes, f, ensure_ascii=False, indent=2)

contagem = {}
for q in questoes:
    esp = q['especialidade']
    contagem[esp] = contagem.get(esp, 0) + 1

print("\n--- DISTRIBUIÇÃO FINAL 100% RECLASSIFICADA ---")
for esp, count in sorted(contagem.items(), key=lambda x: -x[1]):
    print(f"  {esp:38}: {count:4} questões ({(count/len(questoes))*100:.1f}%)")

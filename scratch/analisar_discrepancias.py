import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

banco = json.load(open('saida/banco_questoes_cache.json', encoding='utf-8'))
explicacoes = json.load(open('saida/cache_explicacoes.json', encoding='utf-8'))

discrepancias = []

for q in banco:
    q_key = f"{q['origem']}_{q['numero']}"
    gab_oficial = q.get('gabarito', '').strip().upper()
    exp_item = explicacoes.get(q_key, {})
    
    exp_raw = exp_item.get('explicacao', '') if isinstance(exp_item, dict) else str(exp_item)
    if isinstance(exp_raw, list):
        exp_texto = "\n".join(str(x) for x in exp_raw)
    else:
        exp_texto = str(exp_raw)
        
    exp_gab = exp_item.get('gabarito', '').strip().upper() if isinstance(exp_item, dict) else ''
    
    if not exp_texto.strip():
        continue

    # 1. Se o campo "gabarito" no cache de explicações discorda do banco de questões
    if exp_gab and gab_oficial and exp_gab != gab_oficial and exp_gab != 'N/A':
        discrepancias.append({
            'id': q_key,
            'origem': q.get('origem'),
            'numero': q.get('numero'),
            'gab_oficial': gab_oficial,
            'defesa_ia': exp_gab,
            'tipo': 'Divergência de Gabarito no Cache JSON',
            'motivo': f"Gabarito no cache é '{exp_gab}', mas o oficial é '{gab_oficial}'",
            'explicacao': exp_texto,
            'enunciado': q.get('enunciado', '')[:160],
            'alternativas': q.get('alternativas', {})
        })
        continue

    # 2. Busca padrões no início ou conclusões do texto que cravam outra alternativa como correta
    # Exemplos:
    # "A alternativa A é a correta" ou "Gabarito: C" ou "A resposta correta é a letra D"
    # Cuidado para não pegar "A alternativa A está incorreta"
    
    # Procura explicitamente afirmações de gabarito/resposta correta:
    m_correta = re.findall(r'(?:gabarito(?:\s+oficial|\s+correto)?(?:\s*:\s*|\s+é\s+)(?:a\s+)?(?:alternativa\s+|letra\s+|opção\s+)?\(?([A-E])\)?|'
                           r'(?:a\s+)?alternativa\s+\(?([A-E])\)?\s+(?:é\s+a\s+correta|está\s+correta)|'
                           r'resposta\s+correta(?:\s*:\s*|\s+é\s+(?:a\s+)?(?:alternativa\s+|letra\s+|opção\s+)?)\(?([A-E])\)?|'
                           r'opção\s+correta(?:\s*:\s*|\s+é\s+(?:a\s+)?(?:alternativa\s+|letra\s+|opção\s+)?)\(?([A-E])\)?|'
                           r'correta\s*:\s*(?:alternativa\s+|letra\s+|opção\s+)?\(?([A-E])\)?|'
                           r'portanto,?\s+(?:a\s+)?(?:alternativa|letra|opção)\s+\(?([A-E])\)?\s+é\s+(?:a\s+)?correta)',
                           exp_texto, re.IGNORECASE)
    
    letras_defendidas = set()
    for match in m_correta:
        for g in match:
            if g:
                letras_defendidas.add(g.upper())

    # Se a IA defendeu explicitamente uma ou mais letras, e NENHUMA delas é o gabarito oficial:
    if letras_defendidas and (gab_oficial not in letras_defendidas):
        discrepancias.append({
            'id': q_key,
            'origem': q.get('origem'),
            'numero': q.get('numero'),
            'gab_oficial': gab_oficial,
            'defesa_ia': list(letras_defendidas),
            'tipo': 'Texto crava outra alternativa como correta',
            'motivo': f"O texto afirma que a correta é {list(letras_defendidas)}, mas o gabarito oficial é {gab_oficial}",
            'explicacao': exp_texto,
            'enunciado': q.get('enunciado', '')[:160],
            'alternativas': q.get('alternativas', {})
        })
        continue

    # 3. Verifica se o texto afirma expressamente que a alternativa oficial ESTÁ INCORRETA/ERRADA
    # ex: "A alternativa B está incorreta", "A alternativa B é incorreta"
    m_inc = re.findall(rf'(?:a\s+)?(?:alternativa|letra|opção)\s+\(?({gab_oficial})\)?\s+(?:está|é)\s+incorreta', exp_texto, re.IGNORECASE)
    if m_inc:
        # Mas vamos verificar se ele não estava apenas citando "embora a alternativa X esteja correta..."
        # Se ele diz que a oficial é incorreta, é uma forte discrepância
        discrepancias.append({
            'id': q_key,
            'origem': q.get('origem'),
            'numero': q.get('numero'),
            'gab_oficial': gab_oficial,
            'defesa_ia': f"Afirma que a oficial ({gab_oficial}) está incorreta",
            'tipo': 'Texto afirma que a alternativa oficial está incorreta',
            'motivo': f"O texto afirma expressamente que a alternativa do gabarito oficial ({gab_oficial}) está incorreta",
            'explicacao': exp_texto,
            'enunciado': q.get('enunciado', '')[:160],
            'alternativas': q.get('alternativas', {})
        })

print(f"Total de questões analisadas: {len(banco)}")
print(f"Total de discrepâncias confirmadas: {len(discrepancias)}\n")

# Salvar relatório completo em JSON no scratch
with open('scratch/relatorio_discrepancias.json', 'w', encoding='utf-8') as f:
    json.dump(discrepancias, f, ensure_ascii=False, indent=2)

for i, d in enumerate(discrepancias, 1):
    print(f"[{i}] {d['id']} | Gabarito Oficial: {d['gab_oficial']} | Defesa IA: {d['defesa_ia']}")
    print(f"    Tipo: {d['tipo']}")
    print(f"    Motivo: {d['motivo']}")
    print(f"    Enunciado: {d['enunciado']}...")
    print(f"    Explicacao: {d['explicacao'][:300]}...")
    print("-" * 70)

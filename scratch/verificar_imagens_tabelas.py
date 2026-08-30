import json
from pathlib import Path
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

banco = json.load(open('saida/banco_questoes_cache.json', encoding='utf-8'))

com_imagens = []
sem_imagem_com_mencao = []

# Imagens que existem fisicamente no disco
pasta_imagens_saida = Path('saida/imagens')
pasta_imagens_raiz = Path('imagens')

arquivos_disco = set()
if pasta_imagens_saida.exists():
    for f in pasta_imagens_saida.glob('*.*'):
        arquivos_disco.add(f.name.lower())
if pasta_imagens_raiz.exists():
    for f in pasta_imagens_raiz.glob('*.*'):
        arquivos_disco.add(f.name.lower())

print(f"Total de arquivos de imagem no disco: {len(arquivos_disco)}")

termos_imagem = [
    r'tabela\s+(?:a\s+seguir|abaixo|mostrada|apresentada)',
    r'quadro\s+(?:a\s+seguir|abaixo|mostrado|apresentado)',
    r'figura\s+(?:a\s+seguir|abaixo|mostrada|apresentada)',
    r'imagem\s+(?:a\s+seguir|abaixo|mostrada|apresentada)',
    r'gráfico\s+(?:a\s+seguir|abaixo|mostrado|apresentado)',
    r'radiografia\s+(?:a\s+seguir|abaixo|mostrada|apresentada)',
    r'eletrocardiograma\s+(?:a\s+seguir|abaixo|mostrado|apresentado)',
    r'conforme\s+(?:a\s+tabela|a\s+figura|o\s+quadro|o\s+gráfico|a\s+imagem)',
    r'de\s+acordo\s+com\s+(?:a\s+tabela|a\s+figura|o\s+quadro|o\s+gráfico|a\s+imagem)',
    r'a\s+seguir\s+apresenta\s+os\s+dados',
    r'os\s+dados\s+estão\s+dispostos\s+na\s+tabela'
]

imagens_resolvidas_ok = []
imagens_com_caminho_quebrado = []

for q in banco:
    q_id = f"{q.get('origem')}_{q.get('numero')}"
    enunc = q.get('enunciado', '')
    imgs = q.get('imagens') or ([q.get('imagem')] if q.get('imagem') else [])
    
    if imgs:
        com_imagens.append((q_id, imgs))
        for img_path in imgs:
            img_nome = Path(img_path).name.lower()
            if img_nome in arquivos_disco or str(img_path).startswith('data:'):
                imagens_resolvidas_ok.append((q_id, img_path))
            else:
                imagens_com_caminho_quebrado.append((q_id, img_path))
    else:
        for p in termos_imagem:
            m = re.search(p, enunc, re.IGNORECASE)
            if m:
                sem_imagem_com_mencao.append({
                    'id': q_id,
                    'origem': q.get('origem'),
                    'numero': q.get('numero'),
                    'termo': m.group(0),
                    'enunciado': enunc[:250],
                    'alternativas': q.get('alternativas', {})
                })
                break

print(f"\n==============================================")
print(f"DIAGNÓSTICO GERAL DE IMAGENS E TABELAS")
print(f"==============================================")
print(f"Total de questões no banco: {len(banco)}")
print(f"Questões com imagens vinculadas no JSON: {len(com_imagens)}")
print(f" - Imagens com arquivo existente no disco: {len(imagens_resolvidas_ok)}")
print(f" - Imagens com caminho inexistente/quebrado: {len(imagens_com_caminho_quebrado)}")
print(f"Questões que citam tabela/gráfico/figura mas NÃO possuem imagem no JSON: {len(sem_imagem_com_mencao)}")

print("\n--- Primeiros 10 casos com imagem vinculada ---")
for q_id, imgs in com_imagens[:10]:
    print(f"[{q_id}]: {imgs}")

print("\n--- Primeiros 10 casos que citam Tabela/Figura sem imagem ---")
for item in sem_imagem_com_mencao[:10]:
    print(f"[{item['id']}] (Termo: '{item['termo']}')")
    print(f"  Enunciado: {item['enunciado'].strip()}...")
    print("-" * 50)

# Salvar relatório no scratch
with open('scratch/relatorio_imagens_tabelas.json', 'w', encoding='utf-8') as f:
    json.dump({
        "com_imagens": com_imagens,
        "sem_imagem_com_mencao": sem_imagem_com_mencao,
        "imagens_com_caminho_quebrado": imagens_com_caminho_quebrado
    }, f, ensure_ascii=False, indent=2)

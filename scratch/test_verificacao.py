html = open('index.html', encoding='utf-8').read()

for num in ['84', '85', '86']:
    pos = html.find(f"id='card_REVALIDA-2022_PV_objetiva_1_{num}'")
    if pos != -1:
        print(f"Card {num} encontrado com sucesso!")
    else:
        print(f"Card {num} NÃO encontrado!")

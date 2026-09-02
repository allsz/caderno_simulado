import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding='utf-8')

from core.extrator import extrair_gabarito_pdf, carregar_mapa_gabaritos_revalida

def main():
    banco_path = BASE_DIR / 'saida' / 'banco_questoes_cache.json'
    banco = json.loads(banco_path.read_text(encoding='utf-8'))
    gabs_map = carregar_mapa_gabaritos_revalida(BASE_DIR / 'provas')

    novo_banco = []
    removidas = 0

    for q in banco:
        origem = q.get('origem', '')
        num = str(q.get('numero', ''))
        gab_map = extrair_gabarito_pdf(BASE_DIR / 'provas' / f"{origem}.pdf", mapa_revalida=gabs_map)
        gab = gab_map.get(num, q.get('gabarito'))
        if str(gab).upper() in ['ANULADA', 'X', '*', '-']:
            removidas += 1
            print(f"Removendo questão anulada remanescente: {origem}_{num}")
            continue
        q['gabarito'] = gab
        novo_banco.append(q)

    print(f"Total de questões mantidas: {len(novo_banco)} (Removidas: {removidas})")
    banco_path.write_text(json.dumps(novo_banco, indent=2, ensure_ascii=False), encoding='utf-8')

if __name__ == "__main__":
    main()

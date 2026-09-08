import json
import sys
from pathlib import Path
from core.gerador import exportar_caderno_html

def recompilar():
    base_dir = Path(__file__).resolve().parent
    sys.stdout.reconfigure(encoding='utf-8')

    banco_cache_path = base_dir / 'saida' / 'banco_questoes_cache.json'
    if not banco_cache_path.exists():
        print(f"[ERRO] Banco de questões não encontrado em '{banco_cache_path}'.")
        return

    banco_lista = json.loads(banco_cache_path.read_text(encoding='utf-8'))
    cache_exp_path = base_dir / 'saida' / 'cache_explicacoes.json'
    cache_exp = json.loads(cache_exp_path.read_text(encoding='utf-8')) if cache_exp_path.exists() else {}

    banco_hierarquico = {}
    for q in banco_lista:
        esp = q.get('especialidade', 'Outros')
        tema = q.get('tema', 'Geral')
        subtema = q.get('subtema', 'Diversos')
        banco_hierarquico.setdefault(esp, {}).setdefault(tema, {}).setdefault(subtema, []).append(q)

    print("[*] Recompilando index.html...")
    exportar_caderno_html(banco_hierarquico, base_dir / 'index.html', cache_exp, tem_api_key=True, base_dir=base_dir)

    print("[*] Recompilando saida/caderno_interativo.html...")
    exportar_caderno_html(banco_hierarquico, base_dir / 'saida' / 'caderno_interativo.html', cache_exp, tem_api_key=True, base_dir=base_dir)

    print("[✓] Recompilação concluída com sucesso!")

if __name__ == '__main__':
    recompilar()

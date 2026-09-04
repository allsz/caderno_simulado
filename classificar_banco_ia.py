#!/usr/bin/env python3
"""
Script de Classificação Inteligente do Banco de Questões via Gemini com Fallback em Camadas.

Uso:
  python classificar_banco_ia.py                 # Classifica todo o banco (apenas questões ainda não em cache)
  python classificar_banco_ia.py --limite 10     # Testa com 10 questões para conferir resultado
  python classificar_banco_ia.py --forcar        # Reclassifica mesmo as que já estão em cache
  python classificar_banco_ia.py --somente-prova REVALIDA-2025_1_caderno_1_preliminar
"""

import argparse
import json
import sys
import time
from pathlib import Path

from core.categorizador_ia import (
    carregar_chaves_api,
    carregar_cache_categorizacao,
    salvar_cache_categorizacao,
    classificar_com_fallback
)
from core.gerador import exportar_caderno_html, exportar_caderno_markdown
from core.gemini_ia import carregar_cache_explicacoes


def main():
    parser = argparse.ArgumentParser(description="Classificador Inteligente via IA com Fallback e Economia de Tokens")
    parser.add_argument("--limite", type=int, default=0, help="Limita o número de questões a processar (0 = todas)")
    parser.add_argument("--forcar", action="store_true", help="Força reclassificação mesmo se já estiver em cache")
    parser.add_argument("--somente-prova", type=str, default="", help="Filtra por substring do nome da prova/origem")
    parser.add_argument("--sem-compilar", action="store_true", help="Pula a recompilação do index.html ao final")
    args = parser.parse_args()

    caminho_banco = Path("saida/banco_questoes_cache.json")
    if not caminho_banco.exists():
        print(f"[ERRO] Banco de questões não encontrado em '{caminho_banco}'")
        sys.exit(1)

    banco = json.loads(caminho_banco.read_text(encoding="utf-8"))
    chave_primaria, chave_gratis = carregar_chaves_api()
    cache = carregar_cache_categorizacao()

    print("=" * 65)
    print("      CLASSIFICADOR INTELIGENTE DE MEDICINA (GEMINI FLASH-LITE)     ")
    print("=" * 65)
    print(f"[*] Total de questões no banco: {len(banco)}")
    print(f"[*] Chave Primária (GEMINI_API_KEY): {'Configurada' if chave_primaria else 'NÃO ENCONTRADA'}")
    print(f"[*] Chave Gratuita (GEMINI_API_KEY_FREE): {'Configurada' if chave_gratis else 'Não informada (usará heurística como fallback)'}")
    print(f"[*] Questões já em cache de categorização: {len(cache)}")

    # Filtra questões a processar
    candidatas = []
    for q in banco:
        if q.get("gabarito") == "ANULADA":
            continue
        if args.somente_prova and args.somente_prova.lower() not in q.get("origem", "").lower():
            continue
        q_key = f"{q.get('origem')}_{q.get('numero')}"
        if not args.forcar and q_key in cache:
            continue
        candidatas.append(q)

    if args.limite > 0:
        candidatas = candidatas[:args.limite]

    total_processar = len(candidatas)
    print(f"[*] Questões a processar nesta rodada: {total_processar}")
    
    if total_processar == 0:
        print("[i] Todas as questões elegíveis já estão categorizadas no cache!")
    else:
        print("\n[>] Iniciando processamento em lote...\n")

    contadores_fonte = {}
    modificadas = 0

    for idx, q in enumerate(candidatas, 1):
        q_key = f"{q.get('origem')}_{q.get('numero')}"
        enunc_curto = q.get("enunciado", "").replace("\n", " ")[:55]
        
        esp, tema, subtema, fonte = classificar_com_fallback(
            q,
            cache,
            api_key_primaria=chave_primaria,
            api_key_gratis=chave_gratis,
            delay_entre_chamadas=0.4
        )
        
        contadores_fonte[fonte] = contadores_fonte.get(fonte, 0) + 1
        
        # Salva o cache incrementalmente a cada 5 questões ou na última
        if idx % 5 == 0 or idx == total_processar:
            salvar_cache_categorizacao(cache)

        # Atualiza a questão no banco em memória
        if q.get("especialidade") != esp or q.get("tema") != tema or q.get("subtema") != subtema:
            q["especialidade"] = esp
            q["tema"] = tema
            q["subtema"] = subtema
            modificadas += 1

        print(f"[{idx:4d}/{total_processar:4d}] {q_key:<40} -> {esp} | {tema} ({fonte})", flush=True)

    # Salva o cache final
    salvar_cache_categorizacao(cache)

    # Aplica categorizações do cache a TODO o banco
    print("\n[*] Sincronizando metadados com 'banco_questoes_cache.json'...")
    banco_modificado = False
    for q in banco:
        q_key = f"{q.get('origem')}_{q.get('numero')}"
        if q_key in cache:
            c = cache[q_key]
            if (q.get("especialidade") != c["especialidade"] or 
                q.get("tema") != c["tema"] or 
                q.get("subtema") != c["subtema"]):
                q["especialidade"] = c["especialidade"]
                q["tema"] = c["tema"]
                q["subtema"] = c["subtema"]
                banco_modificado = True

    if banco_modificado or modificadas > 0:
        caminho_banco.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[OK] 'banco_questoes_cache.json' atualizado com sucesso!")

    print("\n" + "=" * 65)
    print("                 ESTATÍSTICAS DA CLASSIFICAÇÃO                   ")
    print("=" * 65)
    for f, count in sorted(contadores_fonte.items(), key=lambda x: -x[1]):
        print(f"  - {f:<25}: {count:4d} questões")
    print(f"  - Total alteradas no banco : {modificadas:4d}")

    # Recompila os cadernos se solicitado
    if not args.sem_compilar:
        print("\n[*] Recompilando index.html e caderno_interativo.html...")
        base_dir = Path(".")
        pasta_saida = Path("saida")
        cache_explicacoes = carregar_cache_explicacoes(pasta_saida / "cache_explicacoes.json")
        
        banco_hierarquico = {}
        for q in banco:
            if q.get("gabarito") == "ANULADA":
                continue
            esp = q.get("especialidade", "Outros")
            tema = q.get("tema", "Geral")
            subtema = q.get("subtema", "Diversos")
            banco_hierarquico.setdefault(esp, {}).setdefault(tema, {}).setdefault(subtema, []).append(q)

        exportar_caderno_html(banco_hierarquico, pasta_saida / "caderno_interativo.html", cache_explicacoes, tem_api_key=bool(chave_primaria), base_dir=base_dir)
        exportar_caderno_html(banco_hierarquico, base_dir / "index.html", cache_explicacoes, tem_api_key=bool(chave_primaria), base_dir=base_dir)
        exportar_caderno_markdown(banco_hierarquico, pasta_saida / "caderno_de_questoes_estudo.md", cache_explicacoes, tem_api_key=bool(chave_primaria))
        print("[OK] Cadernos e index.html recompilados com sucesso!")

    print("\n[SUCESSO] Operação concluída com êxito.")


if __name__ == "__main__":
    main()

"""
Ponto de Entrada Principal para Processamento e Geração do Simulado Médico Interativo.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Garante saída com codificação UTF-8
sys.stdout.reconfigure(encoding='utf-8')

from core import (
    carregar_cache_explicacoes,
    carregar_mapa_gabaritos_revalida,
    exportar_caderno_html,
    exportar_caderno_markdown,
    extrair_gabarito_pdf,
    extrair_questoes_do_texto,
    extrair_texto_pdf,
    gerar_explicacao_gemini,
    salvar_cache_explicacoes,
    salvar_json_atomico,
    carregar_json_seguro,
    auditar_banco_questoes,
)



def main():
    parser = argparse.ArgumentParser(description="Processador e Gerador do Simulado Interativo de Medicina")
    parser.add_argument("--extrair-pdfs", action="store_true", help="Força a re-extração dos PDFs na pasta provas/")
    parser.add_argument("--sem-ia", action="store_true", help="Pula consultas online da API Gemini")
    args = parser.parse_args()

    BASE_DIR = Path(__file__).resolve().parent
    pasta_provas = BASE_DIR / "provas"
    pasta_saida = BASE_DIR / "saida"
    pasta_saida.mkdir(parents=True, exist_ok=True)
    pasta_provas.mkdir(parents=True, exist_ok=True)
    
    caminho_cache = pasta_saida / "cache_explicacoes.json"
    cache_explicacoes = carregar_cache_explicacoes(caminho_cache)
    
    api_key = None if args.sem_ia else os.environ.get("GEMINI_API_KEY")
    if not api_key and not args.sem_ia:
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass

    cache_questoes = pasta_saida / "banco_questoes_cache.json"
    cache_questoes = pasta_saida / "banco_questoes_cache.json"
    banco_hierarquico = {}
    total_questoes = 0

    usar_cache = cache_questoes.exists() and not args.extrair_pdfs

    if usar_cache:
        print(f"[*] Modo Rápido: Carregando banco de questões a partir de '{cache_questoes.name}'...")
        questoes_lista = carregar_json_seguro(cache_questoes, default=[])
        
        # Executa auditoria automática de integridade
        valido, relatorio = auditar_banco_questoes(questoes_lista)
        if not valido:
            print(f"   [!] Alerta de Schema: {len(relatorio['erros_schema'])} inconsistências detectadas.")
        if relatorio["alertas_categorizacao"]:
            print(f"   [i] {len(relatorio['alertas_categorizacao'])} avisos de heurística clínica revisados.")
            
        # Filtra e descarta questões anuladas
        questoes_lista = [q for q in questoes_lista if q.get("gabarito") != "ANULADA"]
        total_questoes = len(questoes_lista)
        for q in questoes_lista:
            esp = q["especialidade"]
            tema = q["tema"]
            subtema = q["subtema"]
            banco_hierarquico.setdefault(esp, {}).setdefault(tema, {}).setdefault(subtema, []).append(q)
    else:
        arquivos_pdf = [f for f in pasta_provas.iterdir() if f.suffix.lower() == ".pdf"]
        if not arquivos_pdf:
            print(f"[!] Nenhum arquivo PDF encontrado na pasta '{pasta_provas.resolve()}'.")
            return

        mapa_revalida = carregar_mapa_gabaritos_revalida(pasta_provas)
        if mapa_revalida:
            print(f"[*] Gabaritos oficiais consolidados do Revalida carregados com sucesso ({len(mapa_revalida)} edições).")

        print(f"[*] Encontrados {len(arquivos_pdf)} arquivos PDF. Iniciando extração, gabaritos e categorização...\n")
        todas_questoes = []

        for caminho_pdf in arquivos_pdf:
            nome_arq = caminho_pdf.name
            if nome_arq.upper().startswith("GABARITO_"):
                continue

            nome_origem = nome_arq.replace(".pdf", "")
            print(f"-> Processando: {nome_arq}...")
            
            gabarito_map = extrair_gabarito_pdf(caminho_pdf, mapa_revalida=mapa_revalida)
            if gabarito_map:
                print(f"   ✓ Gabarito oficial vinculado ({len(gabarito_map)} respostas).")
                
            texto = extrair_texto_pdf(caminho_pdf)
            questoes = extrair_questoes_do_texto(texto, nome_arq)
            
            for q in questoes:
                q["gabarito"] = gabarito_map.get(q["numero"], "N/A")
                q_key = f"{nome_origem}_{q['numero']}"
                
                exp_existente = cache_explicacoes.get(q_key, {}).get("explicacao")
                if api_key and not exp_existente:
                    print(f"   [IA] Gerando explicação via Gemini para {q_key}...")
                    gab_gemini, exp_gemini = gerar_explicacao_gemini(q, q["gabarito"], api_key)
                    if exp_gemini:
                        cache_explicacoes[q_key] = {
                            "gabarito": gab_gemini if q["gabarito"] == "N/A" else q["gabarito"],
                            "explicacao": exp_gemini
                        }
                        salvar_cache_explicacoes(caminho_cache, cache_explicacoes)

            # Filtra apenas questões válidas (descarta anuladas)
            questoes_validas = [q for q in questoes if q.get("gabarito") != "ANULADA"]
            anuladas_count = len(questoes) - len(questoes_validas)
            print(f"   ✓ {len(questoes_validas)} questões ativas processadas ({anuladas_count} anuladas descartadas).")
            total_questoes += len(questoes_validas)
            todas_questoes.extend(questoes_validas)
            
            for q in questoes_validas:
                esp = q["especialidade"]
                tema = q["tema"]
                subtema = q["subtema"]
                banco_hierarquico.setdefault(esp, {}).setdefault(tema, {}).setdefault(subtema, []).append(q)

        # Salva o banco completo de questões usando gravação atômica segura
        salvar_json_atomico(cache_questoes, todas_questoes, indent=2)


    # Caminhos finais de saída
    caminho_md = pasta_saida / "caderno_de_questoes_estudo.md"
    caminho_html = pasta_saida / "caderno_interativo.html"
    caminho_root_index = BASE_DIR / "index.html"
    
    print("\n[*] Compilando arquivos finais a partir dos templates modulares (web/)...")
    exportar_caderno_markdown(banco_hierarquico, caminho_md, cache_explicacoes, tem_api_key=bool(api_key))
    exportar_caderno_html(banco_hierarquico, caminho_html, cache_explicacoes, tem_api_key=bool(api_key), base_dir=BASE_DIR)
    exportar_caderno_html(banco_hierarquico, caminho_root_index, cache_explicacoes, tem_api_key=bool(api_key), base_dir=BASE_DIR)

    print("\n========================================================")
    print(f"[SUCESSO] Processamento modular concluído com êxito!")
    print(f"Total de questões organizadas: {total_questoes}")
    print(f"1. Caderno em Markdown: '{caminho_md.resolve()}'")
    print(f"2. Simulado Interativo (HTML): '{caminho_html.resolve()}'")
    print(f"3. Site GitHub Pages (Root): '{caminho_root_index.resolve()}'")
    print("========================================================")


if __name__ == "__main__":
    main()
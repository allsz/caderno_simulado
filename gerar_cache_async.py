import os
import json
import time
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
CACHE_PATH = BASE_DIR / "saida" / "cache_explicacoes.json"

# Importa funções do script principal
import processar_questoes

def carregar_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    env_file = BASE_DIR / ".env"
    if not api_key and env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return api_key

def main():
    api_key = carregar_api_key()
    if not api_key:
        print("[!] GEMINI_API_KEY não encontrada em .env")
        return

    banco_cache_file = BASE_DIR / "saida" / "banco_questoes_cache.json"
    if banco_cache_file.exists():
        print("[*] Carregando 1.579 questões instantaneamente do cache JSON...", flush=True)
        todas_questoes = json.loads(banco_cache_file.read_text(encoding="utf-8"))
    else:
        print("[*] Lendo PDFs para identificar questões...", flush=True)
        pasta_provas = BASE_DIR / "provas"
        arquivos_pdf = [f for f in pasta_provas.iterdir() if f.suffix.lower() == ".pdf"]
        todas_questoes = []
        for caminho_pdf in arquivos_pdf:
            nome_arq = caminho_pdf.name
            nome_origem = nome_arq.replace(".pdf", "")
            gabarito_map = processar_questoes.extrair_gabarito_pdf(caminho_pdf)
            texto = processar_questoes.extrair_texto_pdf(caminho_pdf)
            questoes = processar_questoes.extrair_questoes_do_texto(texto, nome_arq)
            for q in questoes:
                q["gabarito"] = gabarito_map.get(q["numero"], "N/A")
                q["q_key"] = f"{nome_origem}_{q['numero']}"
                todas_questoes.append(q)

    banco_hierarquico = {}
    for q in todas_questoes:
        esp = q["especialidade"]
        tema = q["tema"]
        subtema = q["subtema"]
        if esp not in banco_hierarquico: banco_hierarquico[esp] = {}
        if tema not in banco_hierarquico[esp]: banco_hierarquico[esp][tema] = {}
        if subtema not in banco_hierarquico[esp][tema]: banco_hierarquico[esp][tema][subtema] = []
        banco_hierarquico[esp][tema][subtema].append(q)

    total = len(todas_questoes)
    cache = processar_questoes.carregar_cache_explicacoes(CACHE_PATH)

    print(f"[*] Total de questões: {total}")
    comentadas_iniciais = len([k for k, v in cache.items() if v.get("explicacao")])
    print(f"[*] Já no cache: {comentadas_iniciais}/{total} ({comentadas_iniciais/total*100:.1f}%)")

    contador_novas = 0

    for idx, q in enumerate(todas_questoes, 1):
        q_key = q["q_key"]
        exp_existente = cache.get(q_key, {}).get("explicacao")
        
        if not exp_existente:
            print(f"[{idx}/{total}] ({idx/total*100:.1f}%) IA Gerando -> {q_key}...", flush=True)
            gab_gemini, exp_gemini = processar_questoes.gerar_explicacao_gemini(q, q["gabarito"], api_key)
            
            if exp_gemini:
                cache[q_key] = {
                    "gabarito": gab_gemini if q["gabarito"] == "N/A" else q["gabarito"],
                    "explicacao": exp_gemini
                }
                processar_questoes.salvar_cache_explicacoes(CACHE_PATH, cache)
                contador_novas += 1
                
                # Regenera HTML a cada 20 questões para manter o usuário atualizado
                if contador_novas % 20 == 0:
                    print(f"   [+] Atualizando caderno_interativo.html ({len(cache)} questões comentadas)...", flush=True)
                    processar_questoes.exportar_caderno_html(banco_hierarquico, BASE_DIR / "saida" / "caderno_interativo.html", cache, tem_api_key=True)

    # Exportação final
    print("\n[✓] Concluído! Gerando arquivos finais atualizados...", flush=True)
    processar_questoes.exportar_caderno_markdown(banco_hierarquico, BASE_DIR / "saida" / "caderno_de_questoes_estudo.md", cache, tem_api_key=True)
    processar_questoes.exportar_caderno_html(banco_hierarquico, BASE_DIR / "saida" / "caderno_interativo.html", cache, tem_api_key=True)
    print("[✓] Processo finalizado com sucesso!", flush=True)

if __name__ == "__main__":
    main()

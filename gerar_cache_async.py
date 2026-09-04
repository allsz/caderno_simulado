"""
Gerador Concorrente de Justificativas e Comentários Médicos via API Gemini.
Processa questões do banco de forma concorrente e atômica, garantindo explicações
técnicas de alta qualidade com base no gabarito oficial definitivo.
"""

import argparse
import concurrent.futures
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

# Configuração de saída UTF-8 para Windows
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
PASTA_SAIDA = BASE_DIR / "saida"
CACHE_PATH = PASTA_SAIDA / "cache_explicacoes.json"
BANCO_PATH = PASTA_SAIDA / "banco_questoes_cache.json"

from core.gerador import exportar_caderno_html, exportar_caderno_markdown
from core.utils import salvar_json_atomico, carregar_json_seguro


def carregar_api_key():
    """Carrega a chave de API do Gemini a partir do ambiente ou do arquivo .env."""
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


def construir_prompt_preceptor(questao, gabarito_oficial):
    """Constrói prompt didático de preceptor médico sênior com diretrizes oficiais."""
    origem = questao.get("origem", "")
    numero = questao.get("numero", "")
    enunciado = questao.get("enunciado", "")
    alternativas = json.dumps(questao.get("alternativas", {}), ensure_ascii=False, indent=2)

    return f"""Você é um médico preceptor especialista de excelência em Residência Médica e Revalida.
Analise detalhadamente a questão clínica abaixo e forneça uma justificativa médica oficial, didática, aprofundada e pedagógica para médicos e estudantes.

PROVA: {origem}
QUESTÃO: {numero}
ENUNCIADO:
{enunciado}

ALTERNATIVAS:
{alternativas}

GABARITO OFICIAL DEFINITIVO: Alternativa ({gabarito_oficial})

DIRETRIZES DE RESPOSTA:
1. Comece fundamentando com clareza clínica e raciocínio fisiopatológico o porquê de a alternativa ({gabarito_oficial}) ser a resposta correta/conduta padrão segundo as diretrizes médicas oficiais vigentes (Ministério da Saúde, SBC, CFM, SBP, FEBRASGO, etc.).
2. Em seguida, analise sucintamente cada uma das demais alternativas, explicando o erro específico de cada distrator.
3. Mantenha tom formal, técnico, objetivo e altamente instrutivo.

Responda exclusivamente em formato JSON com a seguinte estrutura:
{{
  "gabarito": "{gabarito_oficial}",
  "explicacao": "Sua justificativa técnica completa, estruturada e fundamentada."
}}"""


def chamar_gemini_com_retry(prompt, api_key, modelos, max_tentativas=4):
    """Executa requisição à API Gemini com suporte a múltiplos modelos e exponential backoff."""
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
    }).encode("utf-8")

    ultimo_erro = None
    for modelo in modelos:
        for tentativa in range(1, max_tentativas + 1):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=35) as resp:
                    raw_data = resp.read().decode("utf-8")
                    data = json.loads(raw_data)
                    texto = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
                    # Remove markdown se presente
                    if "```json" in texto:
                        texto = texto.split("```json")[1].split("```")[0].strip()
                    elif "```" in texto:
                        texto = texto.split("```")[1].split("```")[0].strip()

                    res_json = json.loads(texto)
                    if "explicacao" in res_json and len(res_json["explicacao"]) > 40:
                        return res_json.get("gabarito"), res_json.get("explicacao"), modelo
            except urllib.error.HTTPError as e:
                ultimo_erro = f"HTTP {e.code}"
                if e.code == 429:
                    # Rate limit: espera exponencial
                    wait_time = 2 ** tentativa + 1
                    time.sleep(wait_time)
                elif e.code == 404:
                    # Modelo não suportado nesta versão/chave, tenta o próximo modelo
                    break
                else:
                    time.sleep(1.5 * tentativa)
            except Exception as e:
                ultimo_erro = str(e)
                time.sleep(1.5 * tentativa)

    return None, None, ultimo_erro


def main():
    parser = argparse.ArgumentParser(description="Gerador Concorrente de Explicações Clínicas com Gemini")
    parser.add_argument("--workers", type=int, default=8, help="Número de workers simultâneos (default: 8)")
    parser.add_argument("--modelo", type=str, default="gemini-flash-latest", help="Modelo principal (default: gemini-flash-latest)")
    parser.add_argument("--forcar", action="store_true", help="Regera todas as explicações mesmo se já presentes no cache")
    parser.add_argument("--prova", type=str, default=None, help="Filtra por origem de prova específica (ex: REVALIDA-2025_1)")
    parser.add_argument("--limite", type=int, default=None, help="Limite máximo de questões para processar")
    args = parser.parse_args()

    api_key = carregar_api_key()
    if not api_key:
        print("[!] Erro: GEMINI_API_KEY não encontrada em .env ou variável de ambiente.", flush=True)
        sys.exit(1)

    if not BANCO_PATH.exists():
        print(f"[!] Erro: Banco de questões não encontrado em {BANCO_PATH}.", flush=True)
        sys.exit(1)

    print(f"[*] Carregando questões de '{BANCO_PATH.name}'...", flush=True)
    questoes = carregar_json_seguro(BANCO_PATH, default=[])
    
    # Filtra por prova se solicitado
    if args.prova:
        questoes = [q for q in questoes if args.prova.lower() in q.get("origem", "").lower()]
        print(f"[*] Filtrado para prova contendo '{args.prova}': {len(questoes)} questões.")

    if args.limite:
        questoes = questoes[:args.limite]
        print(f"[*] Limitado a {len(questoes)} questões.")

    cache_explicacoes = carregar_json_seguro(CACHE_PATH, default={})
    print(f"[*] Cache atual: {len(cache_explicacoes)} explicações armazenadas.", flush=True)

    # Identifica questões que precisam de geração
    fila_processamento = []
    for q in questoes:
        q_key = f"{q['origem']}_{q['numero']}"
        ja_tem = q_key in cache_explicacoes and cache_explicacoes[q_key].get("explicacao")
        if args.forcar or not ja_tem:
            fila_processamento.append(q)

    total_fila = len(fila_processamento)
    print(f"[*] Questões a processar: {total_fila}/{len(questoes)}")
    if total_fila == 0:
        print("[✓] Todas as questões selecionadas já possuem justificativas completas no cache!")
        print("    (Use a flag --forcar se desejar regerar as explicações para aprimorar a qualidade).")
        return

    # Modelos com fallback
    modelos = [args.modelo, "gemini-flash-latest", "gemini-pro-latest"]
    modelos = list(dict.fromkeys(modelos))  # remove duplicatas preservando ordem
    print(f"[*] Modelo preferencial: '{args.modelo}' | Workers simultâneos: {args.workers}")

    lock = threading.Lock()
    sucessos = 0
    falhas = 0
    concluidas = 0
    t_inicio = time.time()

    def processar_item(q):
        nonlocal sucessos, falhas, concluidas
        q_key = f"{q['origem']}_{q['numero']}"
        gab = q.get("gabarito", "N/A")
        
        prompt = construir_prompt_preceptor(q, gab)
        gab_ia, exp_ia, status = chamar_gemini_com_retry(prompt, api_key, modelos)

        with lock:
            concluidas += 1
            if exp_ia:
                sucessos += 1
                cache_explicacoes[q_key] = {
                    "gabarito": gab if gab != "N/A" else (gab_ia or "N/A"),
                    "explicacao": exp_ia
                }
            else:
                falhas += 1

            # Estatísticas de progresso
            elapsed = time.time() - t_inicio
            taxa_q_min = (concluidas / elapsed) * 60 if elapsed > 0 else 0
            restantes = total_fila - concluidas
            eta_segundos = (restantes / (concluidas / elapsed)) if concluidas > 0 else 0
            eta_min = eta_segundos / 60

            status_icon = "✓" if exp_ia else "✗"
            print(
                f"[{concluidas:4d}/{total_fila}] {status_icon} {q_key:45s} | "
                f"Progresso: {concluidas/total_fila*100:5.1f}% | "
                f"Velocidade: {taxa_q_min:4.1f} q/min | "
                f"ETA: {eta_min:4.1f} min",
                flush=True
            )

            # Salva no disco periodicamente a cada 15 questões geradas
            if sucessos % 15 == 0 and exp_ia:
                salvar_json_atomico(CACHE_PATH, cache_explicacoes, indent=2)

    print(f"\n[*] Iniciando pool de threads concorrentes ({args.workers} workers)...")
    print("=" * 90)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(processar_item, q) for q in fila_processamento]
        concurrent.futures.wait(futures)

    # Salva o cache consolidado final
    salvar_json_atomico(CACHE_PATH, cache_explicacoes, indent=2)
    tempo_total = time.time() - t_inicio
    print("=" * 90)
    print(f"[✓] Geração de justificativas concluída em {tempo_total/60:.2f} minutos!")
    print(f"    - Total processado: {concluidas}")
    print(f"    - Sucessos: {sucessos}")
    print(f"    - Falhas: {falhas}")
    print(f"    - Total no cache: {len(cache_explicacoes)} explicações")

    # Recompila os cadernos Markdown e HTML com as novas justificativas
    print("\n[*] Recompilando arquivos interativos com as novas explicações médicas...")
    todas_do_banco = carregar_json_seguro(BANCO_PATH, default=[])
    banco_hierarquico = {}
    for q in todas_do_banco:
        esp = q.get("especialidade", "Geral")
        tema = q.get("tema", "Geral")
        subtema = q.get("subtema", "Geral")
        banco_hierarquico.setdefault(esp, {}).setdefault(tema, {}).setdefault(subtema, []).append(q)

    caminho_md = PASTA_SAIDA / "caderno_de_questoes_estudo.md"
    caminho_html = PASTA_SAIDA / "caderno_interativo.html"
    caminho_root_index = BASE_DIR / "index.html"

    exportar_caderno_markdown(banco_hierarquico, caminho_md, cache_explicacoes, tem_api_key=True)
    exportar_caderno_html(banco_hierarquico, caminho_html, cache_explicacoes, tem_api_key=True, base_dir=BASE_DIR)
    exportar_caderno_html(banco_hierarquico, caminho_root_index, cache_explicacoes, tem_api_key=True, base_dir=BASE_DIR)

    print(f"[✓] 'caderno_interativo.html' e 'index.html' atualizados com 100% de sucesso!")


if __name__ == "__main__":
    main()

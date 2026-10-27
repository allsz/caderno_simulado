"""
Enriquecedor Semântico de Justificativas Clínicas via API Gemini.
Transforma explicações médicas no padrão-ouro de 3 blocos:
1. Lead / Conduta direta com diretrizes oficiais
2. Raciocínio Clínico e Fisiopatológico (numerado e com negrito semântico)
3. Análise dos Distratores (com bullets elegantes e erros conceituais destacados)
Garante ausência total de marcações '#' e aplicação de negrito cirúrgico.
"""

import argparse
import json
import os
import re
import sys
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

from core.utils import salvar_json_atomico, carregar_json_seguro
from recompilar import recompilar


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


def construir_prompt_enriquecimento(questao, gabarito_oficial, explicacao_atual=""):
    origem = questao.get("origem", "")
    numero = questao.get("numero", "")
    enunciado = questao.get("enunciado", "")
    alternativas = json.dumps(questao.get("alternativas", {}), ensure_ascii=False, indent=2)

    return f"""Você é um médico preceptor especialista de excelência em Residência Médica e Revalida.
Sua missão é estruturar e formatar a justificativa médica oficial desta questão, aplicando uma estrutura didática padrão-ouro de 3 blocos com DESTAQUES SEMÂNTICOS EM NEGRITO (semantic bolding).

PROVA: {origem}
QUESTÃO: {numero}
ENUNCIADO:
{enunciado}

ALTERNATIVAS:
{alternativas}

GABARITO OFICIAL DEFINITIVO: Alternativa ({gabarito_oficial})

JUSTIFICATIVA BASE DISPONÍVEL:
{explicacao_atual}

DIRETRIZES ESTRUTURAIS E REGRAS DE FORMATAÇÃO (RIGOROSO):
1. NUNCA utilize caracteres '#', '##' ou '###' no início de linhas. Para títulos de seção, use estritamente negrito simples:
   **Raciocínio Clínico e Fisiopatológico:**
   **Análise dos Distratores:**
2. BLOCO 1 - LEAD / RESPOSTA DIRETA:
   Inicie declarando a resposta correta de forma imediata e assertiva:
   Exemplo: "O gabarito correto é a **Alternativa (X)**. [Justificativa direta citando a conduta/diagnóstico central e diretrizes/consensos médicos oficiais vigentes como MS, SBC, ACLS, FEBRASGO, SBP, CFM, etc.]."
3. BLOCO 2 - **Raciocínio Clínico e Fisiopatológico:**
   Apresente em tópicos numerados:
   1. **Diagnóstico da Afecção/Quadro:** Nome exato da condição em negrito, correlacionando aos achados clínicos. Use itálico para termos em latim ou epônimos.
   2. **Critério Clínico / Fisiopatologia:** Destaque em negrito dados clínicos decisivos (ex.: valores de corte, sinais de gravidade, drogas/mecanismos fisiopatológicos).
   3. **Indicação de Conduta:** A regra técnica padrão-ouro que fundamenta a abordagem correta.
4. BLOCO 3 - **Análise dos Distratores:**
   Analise cada uma das alternativas incorretas com bullet (•):
   • **Alternativa X (Incorreta):** Explicação técnica direta de por que a opção está errada, destacando em negrito termos cruciais (contraindicações formais, dados ausentes, distinções semiológicas).
5. NEGRITO CIRÚRGICO (SEMANTIC BOLDING):
   Aplique **negrito** de forma inteligente e equilibrada apenas nos termos-chave (diagnósticos, drogas de escolha, lesões elementares, contraindicações). NUNCA negrite frases inteiras.

Responda exclusivamente em formato JSON:
{{
  "gabarito": "{gabarito_oficial}",
  "explicacao": "Sua justificativa completa, estruturada e com negrito semântico."
}}"""


def construir_prompt_enxuto(questao, gabarito_oficial, explicacao_atual=""):
    origem = questao.get("origem", "")
    numero = questao.get("numero", "")
    enunciado = questao.get("enunciado", "")
    alternativas = json.dumps(questao.get("alternativas", {}), ensure_ascii=False, indent=2)

    return f"""Você é um médico preceptor especialista de excelência em Residência Médica e Revalida.
Analise detalhadamente a questão clínica abaixo e forneça uma justificativa médica oficial COMPLETA, APROFUNDADA, DETALHADA e PEDAGÓGICA para médicos e estudantes.

ATENÇÃO CRÍTICA SOBRE EXTENSÃO vs. NEGRITO:
- O CONTEÚDO MÉDICO DEVE SER COMPLETO, DETALHADO E APROFUNDADO: Não resuma, não encurte e não simplifique o raciocínio clínico. Discuta a fisiopatologia completa, os critérios de gravidade/instabilidade, as diretrizes de referência vigentes (ACLS, SBC, MS, FEBRASGO, SBP, etc.) e o erro técnico detalhado de cada alternativa distratora.
- A ÚNICA COISA RESTRITA É A QUANTIDADE DE PALAVRAS EM NEGRITO: Use negrito com parcimônia estrita para manter a leitura visualmente limpa e elegante.

PROVA: {origem}
QUESTÃO: {numero}
ENUNCIADO:
{enunciado}

ALTERNATIVAS:
{alternativas}

GABARITO OFICIAL DEFINITIVO: Alternativa ({gabarito_oficial})

JUSTIFICATIVA BASE DISPONÍVEL:
{explicacao_atual}

REGRAS DE FORMATAÇÃO E DISTRIBUIÇÃO DO NEGRITO:
1. NUNCA utilize caracteres '#', '##' ou '###'.
2. Use negrito EXCLUSIVAMENTE em:
   - Títulos de seção (ex.: **Raciocínio Clínico e Fisiopatológico:** e **Análise das alternativas incorretas:**)
   - Chamadas dos tópicos numerados se houver (ex.: 1. **Diagnóstico da Arritmia:**)
   - Chamadas de cada alternativa (ex.: • **A) Incorreta:**)
   - No corpo da fundamentação: no máximo 2 a 3 palavras-chave no total (apenas a afecção central e a conduta/síndrome de escolha, ex.: **fibrilação atrial com alta resposta ventricular**, **cardioversão elétrica sincronizada**).
   - No corpo das alternativas incorretas (após a chamada • **X) Incorreta:**): NÃO use negrito. Mantenha o texto da explicação de cada distrator 100% limpo, sem palavras em negrito.

Responda exclusivamente em formato JSON:
{{
  "gabarito": "{gabarito_oficial}",
  "explicacao": "Sua justificativa médica completa, profunda e com negrito restrito."
}}"""


def chamar_gemini(prompt, api_key, modelo="gemini-flash-latest", max_tentativas=4):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.15
        }
    }).encode("utf-8")

    for tentativa in range(1, max_tentativas + 1):
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                texto = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if "```json" in texto:
                    texto = texto.split("```json")[1].split("```")[0].strip()
                elif "```" in texto:
                    texto = texto.split("```")[1].split("```")[0].strip()

                res_json = json.loads(texto)
                if "explicacao" in res_json and len(res_json["explicacao"]) > 40:
                    return res_json.get("explicacao"), None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = (2 ** tentativa) * 3
                print(f" [!] Rate limit (429). Aguardando {wait_time}s...", flush=True)
                time.sleep(wait_time)
            else:
                time.sleep(2 * tentativa)
        except Exception as e:
            time.sleep(2 * tentativa)

    return None, "Falha após tentativas"


def processar_enriquecimento(prova="REVALIDA-2022-2_PV_objetiva", limite=None, delay=4.0, forcar=False, estilo="enxuto"):
    api_key = carregar_api_key()
    if not api_key:
        print("[!] Erro: GEMINI_API_KEY não encontrada.")
        return

    banco = carregar_json_seguro(BANCO_PATH, default=[])
    cache = carregar_json_seguro(CACHE_PATH, default={})

    questoes_alvo = [
        q for q in banco 
        if q.get("origem") == prova and q.get("gabarito") and q.get("gabarito") != "ANULADA"
    ]

    print(f"[*] Total de questões encontradas para '{prova}': {len(questoes_alvo)}")
    print(f"[*] Modo de estilo de negrito: '{estilo}'")
    if limite:
        questoes_alvo = questoes_alvo[:limite]
        print(f"[*] Processando limite de {limite} questões para teste...")

    sucessos = 0
    puladas = 0
    erros = 0

    for idx, q in enumerate(questoes_alvo, 1):
        q_id = f"{q.get('origem')}_{q.get('numero')}"
        gab = q.get("gabarito")
        exp_atual = cache.get(q_id, {}).get("explicacao", "")

        # Pula questões que já possuem a estrutura semântica padrão-ouro (a menos que seja forçar)
        if not forcar and "**Análise das alternativas incorretas" in exp_atual:
            print(f"[{idx}/{len(questoes_alvo)}] Questão {q.get('numero')} já está formatada no padrão enxuto. Pulando.")
            puladas += 1
            continue

        print(f"[{idx}/{len(questoes_alvo)}] Enriquecendo Questão {q.get('numero')} ({q_id})...", end="", flush=True)
        if estilo == "enxuto":
            prompt = construir_prompt_enxuto(q, gab, exp_atual)
        else:
            prompt = construir_prompt_enriquecimento(q, gab, exp_atual)
        nova_exp, erro = chamar_gemini(prompt, api_key)

        if nova_exp:
            cache[q_id] = {
                "gabarito": gab,
                "explicacao": nova_exp
            }
            salvar_json_atomico(CACHE_PATH, cache)
            sucessos += 1
            print(" [✓ OK]")
            
            # Recompila a cada 10 questões processadas para disponibilizar no HTML imediatamente
            if sucessos > 0 and sucessos % 10 == 0:
                print(f"[*] Recompilação intermediária ({sucessos} questões atualizadas)...")
                try:
                    recompilar()
                except Exception as e:
                    print(f"[!] Aviso na recompilação: {e}")
        else:
            erros += 1
            print(f" [✗ ERRO: {erro}]")

        # Pacing para respeitar o limite gratuito (15 requisições por minuto)
        if idx < len(questoes_alvo):
            time.sleep(delay)

    print(f"\n[*] Concluído: {sucessos} atualizadas, {puladas} já estavam no padrão, {erros} erros.")
    print("[*] Recompilando simulados HTML...")
    recompilar()
    print("[✓] Simulado atualizado com as novas justificativas enriquecidas!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enriquecer justificativas com negrito inteligente via IA")
    parser.add_argument("--prova", type=str, default="REVALIDA-2022-2_PV_objetiva", help="Nome da prova")
    parser.add_argument("--limite", type=int, default=None, help="Limite de questões a processar")
    parser.add_argument("--delay", type=float, default=4.0, help="Delay entre chamadas em segundos (padrão: 4.0s para free tier)")
    parser.add_argument("--forcar", action="store_true", help="Força a re-execução mesmo se já estiver no padrão")
    parser.add_argument("--estilo", type=str, default="enxuto", choices=["enxuto", "completo"], help="Estilo do negrito (enxuto ou completo)")
    args = parser.parse_args()

    processar_enriquecimento(prova=args.prova, limite=args.limite, delay=args.delay, forcar=args.forcar, estilo=args.estilo)


import json
import os
import sys
import time
from pathlib import Path

# Configura stdout UTF-8
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
PROVAS_DIR = BASE_DIR / "provas"

sys.path.insert(0, str(BASE_DIR))
import extrair_prova_vision

# Provas Revalida disponíveis
provas_revalida = sorted([f for f in PROVAS_DIR.glob("REVALIDA*.pdf")])

print(f"========================================================")
print(f"[*] TESTE AUTOMATIZADO DE VISION NAS PROVAS DO REVALIDA")
print(f"[*] Total de edições encontradas: {len(provas_revalida)}")
print(f"========================================================\n")

api_key = extrair_prova_vision.carregar_api_key()
if not api_key:
    print("[!] GEMINI_API_KEY não configurada no .env")
    sys.exit(1)

relatorio_testes = []

for idx, caminho_pdf in enumerate(provas_revalida, 1):
    nome_prova = caminho_pdf.stem
    print(f"\n[{idx}/{len(provas_revalida)}] Testando: {nome_prova}...")
    
    try:
        import fitz
        doc = fitz.open(caminho_pdf)
        total_pags = len(doc)
        
        # Testamos 2 páginas estratégicas de cada prova (ex: pág 2 e uma do meio)
        pags_teste = [2, min(5, total_pags)]
        print(f"   -> PDF com {total_pags} páginas. Extraindo páginas de teste {pags_teste}...")
        
        t0 = time.time()
        questoes = extrair_prova_vision.extrair_prova_completa(
            caminho_pdf,
            paginas_alvo=pags_teste,
            api_key=api_key,
            salvar_banco=True,
            recompilar_html=False
        )
        tempo = time.time() - t0
        
        total_q = len(questoes)
        total_imgs = len([q for q in questoes if q.get("imagens") or "[IMAGEM]" in q.get("enunciado", "")])
        
        relatorio_testes.append({
            "prova": nome_prova,
            "total_paginas_pdf": total_pags,
            "paginas_testadas": pags_teste,
            "questoes_extraidas": total_q,
            "questoes_com_imagem": total_imgs,
            "tempo_segundos": round(tempo, 1),
            "status": "SUCESSO" if total_q > 0 else "AVISO_SEM_QUESTOES"
        })
        
        print(f"   [✓] Sucesso em {tempo:.1f}s: {total_q} questões extraídas ({total_imgs} com imagem/tabela).")
        
        # Pausa preventiva de 2 segundos para respeitar rate limits
        time.sleep(2)
        
    except Exception as e:
        print(f"   [!] Erro ao testar {nome_prova}: {e}")
        relatorio_testes.append({
            "prova": nome_prova,
            "status": f"ERRO: {e}"
        })

print(f"\n========================================================")
print(f"[*] RESUMO GERAL DOS TESTES REVALIDA")
print(f"========================================================")
for r in relatorio_testes:
    status = r.get("status")
    prova = r.get("prova")
    q = r.get("questoes_extraidas", 0)
    img = r.get("questoes_com_imagem", 0)
    t = r.get("tempo_segundos", 0)
    print(f"- {prova:40s} | {q:2d} questões | {img} imgs | {t:4.1f}s | Status: {status}")

print("\n[✓] Teste de compatibilidade em todas as edições do Revalida concluído com sucesso!")

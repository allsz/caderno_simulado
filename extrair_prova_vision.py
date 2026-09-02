
import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# Configuração de saída UTF-8 para Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent
SAIDA_DIR = BASE_DIR / "saida"
IMAGENS_DIR = SAIDA_DIR / "imagens"
SCRATCH_DIR = BASE_DIR / "scratch" / "vision_temp"

# Importa módulos internos
from core.classificador import classificar_questao
from core.extrator import extrair_gabarito_pdf, carregar_mapa_gabaritos_revalida
from core.gerador import exportar_caderno_html, exportar_caderno_markdown
from core.utils import salvar_json_atomico

MODELOS_GEMINI = [
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-3.7-flash"
]

def carregar_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def chamar_gemini_vision(img_bytes, prompt, api_key, max_tentativas=4, mime_type="image/jpeg"):
    """Envia a imagem de uma página para a API Multimodal do Gemini com modelos estáveis e timeout robusto."""
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": img_b64
                    }
                }
            ]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }
    
    for tentativa in range(max_tentativas):
        modelo = MODELOS_GEMINI[tentativa % len(MODELOS_GEMINI)]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            # Timeout ampliado para 60s para páginas densas com múltiplas questões
            with urllib.request.urlopen(req, timeout=60) as response:
                res = json.loads(response.read().decode('utf-8'))
                texto_resp = res['candidates'][0]['content']['parts'][0]['text']
                return json.loads(texto_resp)
        except urllib.error.HTTPError as he:
            if he.code == 429:
                tempo_espera = 8 + (tentativa * 4)
                print(f"   [i] Limite de cota (429) no {modelo}. Aguardando ({tempo_espera}s)...", flush=True)
                time.sleep(tempo_espera)
            else:
                print(f"   [!] Erro HTTP {he.code} ({modelo}): {he.reason}")
                time.sleep(2)
        except Exception as e:
            print(f"   [!] Aviso na requisição ({modelo}): {e}. Tentando próximo modelo...")
            time.sleep(2)
            
    return None

PROMPT_EXTRAIR_PAGINA = """Você é um especialista em extração e curadoria de provas médicas (INEP Revalida e ENARE).
Analise com extrema precisão a imagem desta página da prova médica.

TAREFA:
Extraia todas as questões contidas nesta página. Preste atenção ao layout de colunas (geralmente 2 colunas), lendo cada coluna do início ao fim sem misturar o texto entre elas.

Para CADA questão identificada:
1. 'numero': número da questão (número inteiro).
2. 'enunciado': texto completo do caso clínico e do gancho/pergunta final. 
   - Se a questão contiver uma TABELA, GRÁFICO, ECG, FOTO CLÍNICA ou FIGURA, insira a tag exata '[IMAGEM]' no ponto do enunciado onde a imagem deve aparecer (por exemplo, após a vinheta clínica e antes do comando/pergunta final).
   - Não transcreva tabelas ou gráficos como texto se eles forem imagens/quadros.
3. 'tem_imagem': true se houver imagem, tabela formatada, gráfico, ECG ou foto na questão; false se for apenas texto contínuo.
4. 'box_imagem': se 'tem_imagem' for true, forneça a caixa delimitadora normalizada da imagem/tabela na página no formato [ymin, xmin, ymax, xmax] em escala de 0 a 1000 (onde 0,0 é topo-esquerdo e 1000,1000 é base-direita). Se não houver, use null.
5. 'alternativas': dicionário com as alternativas da questão (ex: {"A": "texto da alternativa A", "B": "texto...", "C": "...", "D": "..."}).

Responda ESTRITAMENTE em formato JSON com o seguinte schema:
{
  "questoes": [
    {
      "numero": 1,
      "enunciado": "Texto do enunciado...",
      "tem_imagem": false,
      "box_imagem": null,
      "alternativas": {
        "A": "texto",
        "B": "texto",
        "C": "texto",
        "D": "texto"
      }
    }
  ]
}
"""

def extrair_prova_completa(caminho_pdf: Path, paginas_alvo=None, api_key=None, salvar_banco=True, recompilar_html=True):
    """Processa um PDF página por página usando Gemini Vision."""
    if not fitz:
        print("[!] PyMuPDF não encontrado. Instale com: pip install pymupdf")
        return []

    if not api_key:
        api_key = carregar_api_key()
        if not api_key:
            print("[!] GEMINI_API_KEY não encontrada no .env")
            return []

    origem = caminho_pdf.stem
    print(f"\n========================================================")
    print(f"[*] INICIANDO EXTRAÇÃO AUTOMÁTICA VISION")
    print(f"[*] Prova: {origem} ({caminho_pdf.name})")
    print(f"========================================================")

    doc = fitz.open(caminho_pdf)
    total_pags = len(doc)
    print(f"[*] Total de páginas no PDF: {total_pags}")

    IMAGENS_DIR.mkdir(parents=True, exist_ok=True)
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

    # Página 1 no Revalida é a capa/regras. Começa por padrão a partir da página 2.
    pags_a_processar = paginas_alvo if paginas_alvo else list(range(2, total_pags + 1))
    
    questoes_extraidas = {}

    gabs_map = carregar_mapa_gabaritos_revalida(BASE_DIR / "provas")
    gabarito_oficial = extrair_gabarito_pdf(caminho_pdf, mapa_revalida=gabs_map)
    print(f"[*] Gabaritos oficiais carregados: {len(gabarito_oficial)} respostas mapeadas.")

    for num_pag in pags_a_processar:
        if num_pag < 1 or num_pag > total_pags:
            continue
        
        idx_pag = num_pag - 1
        page = doc[idx_pag]
        # Otimizado para DPI 140 em JPEG 85% para reduzir uso de tokens em 60% com máxima legibilidade
        pix = page.get_pixmap(dpi=140)
        img_bytes = pix.tobytes("jpeg", jpg_quality=85)
        
        print(f"\n[Pag. {num_pag}/{total_pags}] Analisando layout e questões com Gemini Vision...", flush=True)
        resultado_json = chamar_gemini_vision(img_bytes, PROMPT_EXTRAIR_PAGINA, api_key, mime_type="image/jpeg")
        
        if not resultado_json or "questoes" not in resultado_json:
            print(f"   [!] Nenhuma questão estruturada retornada na página {num_pag}.")
            continue
        
        lista_q = resultado_json["questoes"]
        print(f"   [✓] {len(lista_q)} questões identificadas na página {num_pag}.")
        
        # Abre a imagem da página com PIL para eventuais crops
        img_pil = None
        
        for q_dados in lista_q:
            num_q = q_dados.get("numero")
            if not num_q:
                continue
            
            gab = gabarito_oficial.get(str(num_q), "N/A")
            if str(gab).upper() in ["ANULADA", "*", "X"]:
                print(f"      [-] Questão {num_q} anulada oficialmente no Revalida.")
                continue

            enunciado = q_dados.get("enunciado", "").strip()
            alts = q_dados.get("alternativas", {})
            tem_img = q_dados.get("tem_imagem", False)
            box = q_dados.get("box_imagem")
            
            # Crop automático da imagem se houver box e imagem
            imagens_list = []
            if tem_img and box and len(box) == 4:
                try:
                    if img_pil is None:
                        import io
                        img_pil = Image.open(io.BytesIO(img_bytes))
                    
                    w, h = img_pil.size
                    ymin, xmin, ymax, xmax = box
                    crop_box = (
                        int((xmin / 1000) * w),
                        int((ymin / 1000) * h),
                        int((xmax / 1000) * w),
                        int((ymax / 1000) * h)
                    )
                    
                    # Salva o recorte
                    nome_img = f"{origem}_{num_q}.png"
                    caminho_salvar_img = IMAGENS_DIR / nome_img
                    cropped = img_pil.crop(crop_box)
                    cropped.save(caminho_salvar_img, optimize=True)
                    rel_img_path = f"saida/imagens/{nome_img}"
                    imagens_list.append(rel_img_path)
                    print(f"      [+] Imagem/tabela recortada e salva: '{rel_img_path}'")
                except Exception as ex_crop:
                    print(f"      [!] Falha no crop da questão {num_q}: {ex_crop}")

            # Se já existir arquivo de imagem vinculado anteriormente
            if not imagens_list:
                img_padrao = IMAGENS_DIR / f"{origem}_{num_q}.png"
                if img_padrao.exists():
                    imagens_list.append(f"saida/imagens/{img_padrao.name}")

            # Classificação clínica automática
            esp, tema, subtema = classificar_questao(enunciado)
            
            questao_obj = {
                "origem": origem,
                "numero": str(num_q),
                "especialidade": esp,
                "tema": tema,
                "subtema": subtema,
                "enunciado": enunciado,
                "alternativas": alts,
                "gabarito": gab
            }
            if imagens_list:
                questao_obj["imagens"] = imagens_list
            
            questoes_extraidas[str(num_q)] = questao_obj
            print(f"      - Questão {num_q} (Gab: {gab}): {len(alts)} alternativas | Tema: {tema} -> {subtema}")
            
        # Intervalo rápido e suave para modo pago (alta velocidade)
        time.sleep(0.5)

    print(f"\n[✓] Extração concluída! Total de questões processadas: {len(questoes_extraidas)}")
    
    if salvar_banco and questoes_extraidas:
        mesclar_com_banco_questoes(questoes_extraidas, origem, recompilar_html=recompilar_html)
        
    return list(questoes_extraidas.values())

def mesclar_com_banco_questoes(novas_questoes_dict, origem, recompilar_html=True):
    """Mescla as questões extraídas no banco de questões cache JSON e opcionalmente recompila o simulado."""
    caminho_banco = SAIDA_DIR / "banco_questoes_cache.json"
    banco = []
    if caminho_banco.exists():
        try:
            banco = json.loads(caminho_banco.read_text(encoding="utf-8"))
        except Exception:
            banco = []

    # Cria índice por origem + numero
    banco_map = {f"{q.get('origem')}_{q.get('numero')}": q for q in banco}
    
    atualizadas = 0
    inseridas = 0
    
    for num_q, nova_q in novas_questoes_dict.items():
        chave = f"{origem}_{num_q}"
        if chave in banco_map:
            # Preserva gabarito se já existia
            if banco_map[chave].get("gabarito") and banco_map[chave].get("gabarito") != "N/A":
                nova_q["gabarito"] = banco_map[chave]["gabarito"]
            banco_map[chave].update(nova_q)
            atualizadas += 1
        else:
            banco_map[chave] = nova_q
            inseridas += 1

    banco_final = list(banco_map.values())
    salvar_json_atomico(caminho_banco, banco_final, indent=2)
    print(f"[✓] Banco atualizado: {atualizadas} questões atualizadas, {inseridas} inseridas.")
    
    if not recompilar_html:
        return

    # Recompilação automática do simulado
    print("[*] Recompilando simulado interativo (index.html)...")
    try:
        import processar_questoes
        # Recria banco hierárquico
        banco_hierarquico = {}
        for q in banco_final:
            esp = q.get("especialidade", "Clínica Médica")
            tema = q.get("tema", "Geral")
            subtema = q.get("subtema", "Geral")
            banco_hierarquico.setdefault(esp, {}).setdefault(tema, {}).setdefault(subtema, []).append(q)
        
        caminho_cache_exp = SAIDA_DIR / "cache_explicacoes.json"
        cache_exp = json.loads(caminho_cache_exp.read_text(encoding="utf-8")) if caminho_cache_exp.exists() else {}
        
        exportar_caderno_html(banco_hierarquico, BASE_DIR / "index.html", cache_exp, tem_api_key=True, base_dir=BASE_DIR)
        exportar_caderno_html(banco_hierarquico, SAIDA_DIR / "caderno_interativo.html", cache_exp, tem_api_key=True, base_dir=BASE_DIR)
        exportar_caderno_markdown(banco_hierarquico, SAIDA_DIR / "caderno_de_questoes_estudo.md", cache_exp, tem_api_key=True)
        print("[✓] Simulado e HTMLs recompilados com sucesso!")
    except Exception as e:
        print(f"[!] Erro ao recompilar HTML: {e}")

def parse_paginas(pag_str):
    """Converte '1-5,8,10-12' em lista de inteiros [1,2,3,4,5,8,10,11,12]."""
    if not pag_str:
        return None
    resultado = set()
    for parte in pag_str.split(','):
        parte = parte.strip()
        if '-' in parte:
            inicio, fim = parte.split('-', 1)
            resultado.update(range(int(inicio), int(fim) + 1))
        elif parte.isdigit():
            resultado.add(int(parte))
    return sorted(list(resultado))

def main():
    parser = argparse.ArgumentParser(description="Extrator Automático de Provas Médicas com Gemini Vision")
    parser.add_argument("--pdf", type=str, default=None, help="Caminho do arquivo PDF da prova (ex: provas/REVALIDA-2022_PV_objetiva_1.pdf)")
    parser.add_argument("--todas-revalida", action="store_true", help="Processa todas as edições pendentes do Revalida automaticamente.")
    parser.add_argument("--forcar", action="store_true", help="Força a re-extração com Gemini Vision mesmo para provas que já possuem questões no banco.")
    parser.add_argument("--paginas", type=str, default=None, help="Páginas a processar (ex: '1-5', '3,7,9-12'). Se omitido, processa a prova inteira.")
    parser.add_argument("--nao-salvar", action="store_true", help="Apenas exibe a extração sem salvar no banco.")
    
    args = parser.parse_args()

    if args.todas_revalida:
        provas_dir = BASE_DIR / "provas"
        lista_pdfs = sorted([p for p in provas_dir.glob("REVALIDA*.pdf")])
        
        # Lê banco existente para saber quais provas já foram 100% extraídas
        banco_existente = []
        caminho_banco = SAIDA_DIR / "banco_questoes_cache.json"
        if caminho_banco.exists():
            try:
                banco_existente = json.loads(caminho_banco.read_text(encoding="utf-8"))
            except Exception:
                banco_existente = []
        
        contagem_origem = {}
        for q in banco_existente:
            orig = q.get("origem")
            contagem_origem[orig] = contagem_origem.get(orig, 0) + 1

        print(f"[*] Processando edições do Revalida com Gemini Vision...")
        for p in lista_pdfs:
            origem = p.stem
            # Pula as que já foram 100% curadas manualmente
            if not args.forcar and ("2021_PV" in p.name or "2022_PV_objetiva_1" in p.name or "2022-2_PV" in p.name):
                print(f"[*] Pulando {p.name} (já 100% validada e curada).")
                continue
            extrair_prova_completa(p, paginas_alvo=parse_paginas(args.paginas), salvar_banco=not args.nao_salvar, recompilar_html=False)
        
        # Recompilação final no final do lote
        if not args.nao_salvar:
            print("\n[*] Recompilando simulado interativo final...")
            mesclar_com_banco_questoes({}, "LOTE_FINAL", recompilar_html=True)
        return

    if not args.pdf:
        print("[!] Especifique um arquivo PDF com --pdf ou use --todas-revalida.")
        return

    caminho_pdf = Path(args.pdf)
    if not caminho_pdf.exists():
        caminho_pdf = BASE_DIR / args.pdf
        if not caminho_pdf.exists():
            print(f"[!] Arquivo PDF não encontrado: {args.pdf}")
            return

    pags = parse_paginas(args.paginas)
    extrair_prova_completa(caminho_pdf, paginas_alvo=pags, salvar_banco=not args.nao_salvar)

if __name__ == "__main__":
    main()

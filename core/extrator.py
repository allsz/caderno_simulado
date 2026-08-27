import asyncio
import io
import re
from pathlib import Path
from PIL import Image
import pymupdf
import winocr

from .classificador import classificar_questao


def extrair_gabarito_pdf(caminho_pdf):
    """Extrai gabarito oficial das últimas páginas da prova PDF (se disponível)."""
    try:
        doc = pymupdf.open(str(caminho_pdf))
        gabarito = {}
        for num_pag in range(max(0, len(doc) - 3), len(doc)):
            texto = doc[num_pag].get_text("text")
            matches = re.findall(r'(?:^|\n)\s*(\d{1,3})\s*[\.\)-]?\s*\n?\s*([A-E]|ANULADA)', texto, re.IGNORECASE)
            for num, resp in matches:
                gabarito[str(int(num))] = resp.upper()
        doc.close()
        return gabarito
    except Exception:
        return {}


async def _ocr_pixmap(pix):
    """Executa OCR nativo do Windows em um buffer de imagem."""
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    res = await winocr.recognize_pil(img, lang="pt-BR")
    return res.text


def extrair_texto_pdf(caminho_pdf):
    """Extrai texto e aplica OCR nativo em 2 colunas se o PDF contiver fontes corrompidas."""
    doc = pymupdf.open(str(caminho_pdf))
    texto_acumulado = []
    
    for num_pag in range(len(doc)):
        pagina = doc[num_pag]
        texto = pagina.get_text("text")
        
        if re.search(r'(?:GABARITO|RESPOSTAS|QUESTIONÁRIO DE PERCEPÇÃO|NOSSOS CURSOS)', texto, re.IGNORECASE) and num_pag > len(doc) - 6:
            break
            
        texto_acumulado.append(texto)
        
    doc.close()
    texto_total = "\n".join(texto_acumulado)

    # Detecta se o PDF possui caracteres corrompidos/não mapeados (glifos sem tabela Unicode)
    ctrl_chars = len(re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', texto_total))
    if ctrl_chars > 50:
        nome_arq = Path(caminho_pdf).name
        print(f"   [OCR Automático] PDF com fontes não mapeadas detectado ('{nome_arq}'). Recuperando texto via OCR nativo...")
        doc = pymupdf.open(str(caminho_pdf))
        texto_ocr = []
        for num_pag in range(len(doc)):
            p = doc[num_pag]
            w, h = p.rect.width, p.rect.height
            
            # Divide a página em 2 colunas para respeitar a ordem de leitura das questões
            rect_left = pymupdf.Rect(15, 30, w/2 + 5, h - 25)
            rect_right = pymupdf.Rect(w/2 - 5, 30, w - 15, h - 25)
            
            pix_left = p.get_pixmap(dpi=200, clip=rect_left)
            pix_right = p.get_pixmap(dpi=200, clip=rect_right)
            
            txt_left = asyncio.run(_ocr_pixmap(pix_left))
            txt_right = asyncio.run(_ocr_pixmap(pix_right))
            
            texto_ocr.append(txt_left)
            texto_ocr.append(txt_right)
            
            if re.search(r'(?:GABARITO|RESPOSTAS|QUESTIONÁRIO DE PERCEPÇÃO)', txt_left + txt_right, re.IGNORECASE) and num_pag > len(doc) - 6:
                break
        doc.close()
        texto_total = "\n\n".join(texto_ocr)
        
        # Normalização do OCR para quebra de linhas nas questões
        texto_total = re.sub(r'([^\n])\s*(QUEST[ÃA]O\s+\d+)', r'\1\n\n\2\n', texto_total, flags=re.IGNORECASE)

    return texto_total


def extrair_alternativas(bloco_limpo):
    """Extrai alternativas com e sem pontuação (A., A), (A), A -, ou apenas A com espaço, e OCR Revalida)."""
    # 1. Tenta padrão com pontuação: A., A), (A), A -
    padrao_com_pontuacao = re.compile(r'(?:^|\n)\s*(?:\(([A-E])\)|([A-E])[\.\)-])\s+', re.MULTILINE)
    matches = list(padrao_com_pontuacao.finditer(bloco_limpo))
    
    # 2. Se não achou pelo menos 2 alternativas com pontuação, tenta padrão sem pontuação (ex: Revalida)
    if len(matches) < 2:
        padrao_sem_pontuacao = re.compile(r'(?:^|\n)\s*([A-E])\s+(?=[A-Za-z0-9"\'\(\u00C0-\u00FF])', re.MULTILINE)
        matches_cand = list(padrao_sem_pontuacao.finditer(bloco_limpo))
        
        # Validação de sequência lógica (A -> B -> C -> D ...) para evitar falsos positivos
        seq = []
        for m in matches_cand:
            letra = m.group(1).upper()
            if not seq and letra == 'A':
                seq.append(m)
            elif seq:
                esperado = chr(ord((seq[-1].group(1) or "").upper()) + 1)
                if letra == esperado:
                    seq.append(m)
        if len(seq) >= 2:
            matches = seq

    if matches:
        idx_primeira_alt = matches[0].start()
        enunciado = bloco_limpo[:idx_primeira_alt].strip()
        enunciado = re.sub(r'^QUESTÃO\s+\d+[\.\s-]*', '', enunciado, flags=re.IGNORECASE).strip()

        alternativas = {}
        for j in range(len(matches)):
            letra = (matches[j].group(1) or matches[j].group(2) or matches[j].group(0).strip()[0]).upper()
            inicio_alt = matches[j].end()
            fim_alt = matches[j+1].start() if j + 1 < len(matches) else len(bloco_limpo)
            texto_alt = bloco_limpo[inicio_alt:fim_alt].strip()
            texto_alt = re.sub(r'\s+', ' ', texto_alt)
            alternativas[letra] = texto_alt

        return enunciado, alternativas

    # 3. Fallback especial para Revalida OCR (onde botões de opção viraram O, 0 ou @)
    if "@" in bloco_limpo or re.search(r'\s+[O0]\s+', bloco_limpo):
        m = re.search(r'\s+[O0@]\s+([a-zA-Z\u00C0-\u00FF0-9].*)', bloco_limpo, re.DOTALL)
        if m:
            idx = m.start()
            enunciado_cand = bloco_limpo[:idx].strip()
            enunciado_cand = re.sub(r'^(?:QUEST[ÃAÁO0-9\?]+|QUEST[ÃA]O)\s*\d+[\.\s-]*', '', enunciado_cand, flags=re.IGNORECASE).strip()
            enunciado_cand = re.sub(r'^A\s+(?=[A-Z\u00C0-\u00FF])', '', enunciado_cand)

            resto = m.group(1).strip()
            if "@" in resto:
                partes = [p.strip().rstrip('.') for p in re.split(r'\s*@\s*', resto) if p.strip()]
            else:
                partes = [p.strip().rstrip('.') for p in re.split(r'\.\s+(?=[a-zA-Z\u00C0-\u00FF0-9])', resto) if p.strip()]
                
            if partes:
                partes[-1] = re.sub(r'\s*(?:Espaço livre|Revalid|Na2022).*', '', partes[-1], flags=re.IGNORECASE).strip()
                
            if len(partes) >= 4:
                return enunciado_cand, {
                    "A": partes[0],
                    "B": partes[1],
                    "C": partes[2],
                    "D": " ".join(partes[3:])
                }
            elif len(partes) == 3:
                return enunciado_cand, {
                    "A": partes[0],
                    "B": partes[1],
                    "C": partes[2]
                }

    return bloco_limpo, {}


def extrair_questoes_do_texto(texto_bruto, nome_arquivo):
    """Identifica blocos de questões e separa enunciado de alternativas."""
    padrao_questao = re.compile(r'(?:^|\n|\b)(?:QUEST[ÃAÁO0-9\?]+|QUEST[ÃA]O)\s*(\d+)[\.\s-]*', re.IGNORECASE)
    matches = list(padrao_questao.finditer(texto_bruto))
    
    if not matches:
        return []

    questoes_processadas = []
    
    for i in range(len(matches)):
        inicio = matches[i].start()
        fim = matches[i+1].start() if i + 1 < len(matches) else len(texto_bruto)
        bloco = texto_bruto[inicio:fim].strip()
        
        num_q = matches[i].group(1)
        
        # Limpeza de cabeçalhos repetitivos
        bloco_limpo = re.sub(r'Medway\s*-\s*[A-Z0-9\s-]+\n+Páginas\s+\d+/\d+', '', bloco)
        bloco_limpo = re.sub(r'Revalida\s*\d{4}', '', bloco_limpo)
        bloco_limpo = re.sub(r'PRIMEIRA EDIÇÃO|EDIÇÃO\s*\d+/\d+|SEGUNDA EDIÇÃO', '', bloco_limpo)
        bloco_limpo = re.sub(r'ENARE\s*-\s*\d{4}\s*-\s*Objetiva\s*\|\s*R1', '', bloco_limpo)
        
        # Separação robusta de Enunciado e Alternativas
        enunciado, alternativas = extrair_alternativas(bloco_limpo)

        if len(enunciado) > 20:
            especialidade, tema, subtema = classificar_questao(bloco_limpo)
            questoes_processadas.append({
                "origem": nome_arquivo.replace(".pdf", ""),
                "numero": num_q,
                "especialidade": especialidade,
                "tema": tema,
                "subtema": subtema,
                "enunciado": enunciado,
                "alternativas": alternativas
            })

    return questoes_processadas

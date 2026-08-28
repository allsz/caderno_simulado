import asyncio
import io
import re
from pathlib import Path
from PIL import Image
import pymupdf
import winocr

from .classificador import classificar_questao


def parse_gabarito_text_block(text):
    """Analisa blocos textuais e tabelas de gabarito para extrair pares questão-resposta."""
    gabarito = {}
    blocks = re.split(r'Quest[aã]o', text, flags=re.IGNORECASE)
    for block in blocks:
        if 'Gabarito' in block or 'GAB' in block:
            parts = re.split(r'Gabarito|GAB', block, flags=re.IGNORECASE)
            nums = [n.strip() for n in parts[0].split() if n.strip().isdigit()]
            raw_resps = [r.strip() for r in parts[1].split() if r.strip()]
            resps = []
            for r in raw_resps:
                if re.match(r'^[A-E]$', r, re.IGNORECASE):
                    resps.append(r.upper())
                elif r in ['-', '—', 'X', 'x', '̶'] or 'anulad' in r.lower() or '̶' in r:
                    resps.append('ANULADA')
            for n, r in zip(nums, resps):
                gabarito[n] = r
    
    if len(gabarito) < 20:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for i in range(len(lines) - 1):
            if lines[i].isdigit() and (re.match(r'^[A-E]$', lines[i+1]) or 'anulad' in lines[i+1].lower() or lines[i+1] in ['X', 'x', '-', '—']):
                resp = 'ANULADA' if 'anulad' in lines[i+1].lower() or lines[i+1] in ['X', 'x', '-', '—'] else lines[i+1].upper()
                gabarito[lines[i]] = resp

    return gabarito


def decode_gabarito_custom_glyphs(txt):
    """Decodifica páginas com fontes customizadas (letras gregas e bytes especiais) como no Revalida 2026/1."""
    greek_to_digit = {'ϭ': '1', 'Ϯ': '2', 'ϯ': '3', 'ϰ': '4', 'ϱ': '5', 'ϲ': '6', 'ϳ': '7', 'ϴ': '8', 'ϵ': '9', 'Ϭ': '0'}
    byte_to_resp = {'\x11': 'A', '\x12': 'B', '\x04': 'C', '\x18': 'D'}
    g = {}
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    i = 0
    while i < len(lines) - 1:
        line = lines[i]
        num_str = ''.join([greek_to_digit.get(c, c) for c in line])
        if num_str.isdigit():
            resp_raw = lines[i+1]
            resp = None
            if '\x03' in resp_raw:
                resp = 'ANULADA'
            else:
                for b, r in byte_to_resp.items():
                    if b in resp_raw:
                        resp = r
                        break
            if resp:
                g[num_str] = resp
                i += 2
                continue
        i += 1
    return g


def carregar_mapa_gabaritos_revalida(pasta_provas: Path):
    """Carrega todos os gabaritos oficiais consolidados do documento GABARITO_REVALIDA_2021_a_2026.pdf."""
    caminho_gabarito = pasta_provas / "GABARITO_REVALIDA_2021_a_2026.pdf"
    if not caminho_gabarito.exists():
        return {}
    
    try:
        doc = pymupdf.open(str(caminho_gabarito))
        paginas_map = {
            "REVALIDA-2021": [0],
            "REVALIDA-2022_PV": [1],
            "REVALIDA-2022-2": [2],
            "REVALIDA-2023_1": [3],
            "REVALIDA-2023_2": [4],
            "REVALIDA-2024_1": [5],
            "REVALIDA-2024_2": [6],
            "REVALIDA-2025_1": [7],
            "REVALIDA-2025_2": [8, 9, 10, 11],
            "REVALIDA-2026_1": [12, 13],
        }
        
        mapa_por_prova = {}
        for chave_prova, lista_pags in paginas_map.items():
            gab_completo = {}
            for p_idx in lista_pags:
                if p_idx < len(doc):
                    txt = doc[p_idx].get_text()
                    gab_parcial = parse_gabarito_text_block(txt)
                    if len(gab_parcial) < 10:
                        gab_parcial = decode_gabarito_custom_glyphs(txt)
                    gab_completo.update(gab_parcial)
            mapa_por_prova[chave_prova] = gab_completo
            
        doc.close()
        return mapa_por_prova
    except Exception:
        return {}


def extrair_gabarito_pdf(caminho_pdf, mapa_revalida=None):
    """Extrai gabarito oficial da prova PDF ou do mapa consolidado Revalida."""
    caminho = Path(caminho_pdf)
    nome_arq = caminho.name

    # Se for REVALIDA-2026, o gabarito oficial consolidado é o definitivo de 100 questões
    if "REVALIDA-2026" in nome_arq.upper() or "REVALIDA_2026" in nome_arq.upper():
        return {
            "1": "D", "2": "C", "3": "C", "4": "D", "5": "B", "6": "D", "7": "D", "8": "C", "9": "D", "10": "D",
            "11": "D", "12": "D", "13": "C", "14": "B", "15": "B", "16": "B", "17": "B", "18": "D", "19": "B", "20": "B",
            "21": "A", "22": "B", "23": "C", "24": "C", "25": "A", "26": "A", "27": "B", "28": "A", "29": "A", "30": "C",
            "31": "C", "32": "C", "33": "C", "34": "C", "35": "C", "36": "B", "37": "A", "38": "B", "39": "B", "40": "C",
            "41": "A", "42": "A", "43": "C", "44": "A", "45": "A", "46": "D", "47": "C", "48": "A", "49": "D", "50": "D",
            "51": "B", "52": "D", "53": "D", "54": "A", "55": "D", "56": "C", "57": "D", "58": "B", "59": "A", "60": "B",
            "61": "A", "62": "A", "63": "B", "64": "A", "65": "B", "66": "B", "67": "D", "68": "D", "69": "C", "70": "D",
            "71": "A", "72": "D", "73": "A", "74": "C", "75": "C", "76": "A", "77": "A", "78": "C", "79": "D", "80": "C",
            "81": "B", "82": "B", "83": "A", "84": "A", "85": "C", "86": "A", "87": "C", "88": "B", "89": "D", "90": "B",
            "91": "C", "92": "D", "93": "C", "94": "A", "95": "A", "96": "B", "97": "B", "98": "D", "99": "B", "100": "D"
        }

    # Se for ENARE-2021, gabarito oficial consolidado pós-recurso (com as 9 anuladas: 2, 11, 20, 34, 40, 56, 62, 64, 88)
    if "ENARE-2021" in nome_arq.upper() or "ENARE_2021" in nome_arq.upper():
        return {
            "1": "D", "2": "ANULADA", "3": "A", "4": "B", "5": "D", "6": "C", "7": "E", "8": "C", "9": "B", "10": "A",
            "11": "ANULADA", "12": "C", "13": "E", "14": "B", "15": "A", "16": "C", "17": "D", "18": "E", "19": "B", "20": "ANULADA",
            "21": "C", "22": "A", "23": "B", "24": "E", "25": "E", "26": "D", "27": "E", "28": "C", "29": "D", "30": "C",
            "31": "C", "32": "A", "33": "E", "34": "ANULADA", "35": "B", "36": "D", "37": "D", "38": "E", "39": "B", "40": "ANULADA",
            "41": "D", "42": "D", "43": "B", "44": "C", "45": "E", "46": "A", "47": "A", "48": "C", "49": "B", "50": "C",
            "51": "E", "52": "E", "53": "A", "54": "E", "55": "D", "56": "ANULADA", "57": "A", "58": "B", "59": "D", "60": "C",
            "61": "A", "62": "ANULADA", "63": "A", "64": "ANULADA", "65": "E", "66": "D", "67": "C", "68": "A", "69": "C", "70": "D",
            "71": "A", "72": "B", "73": "D", "74": "E", "75": "E", "76": "C", "77": "B", "78": "B", "79": "D", "80": "E",
            "81": "C", "82": "A", "83": "D", "84": "E", "85": "B", "86": "C", "87": "B", "88": "ANULADA", "89": "C", "90": "C",
            "91": "D", "92": "E", "93": "D", "94": "B", "95": "E", "96": "A", "97": "C", "98": "B", "99": "D", "100": "E"
        }

    # Se for ENARE-2022, gabarito oficial consolidado pós-recurso (com as 4 anuladas: 51, 59, 68, 76)
    if "ENARE-2022" in nome_arq.upper() or "ENARE_2022" in nome_arq.upper():
        return {
            "1": "E", "2": "B", "3": "E", "4": "A", "5": "D", "6": "C", "7": "D", "8": "C", "9": "A", "10": "E",
            "11": "C", "12": "B", "13": "D", "14": "E", "15": "C", "16": "A", "17": "C", "18": "D", "19": "E", "20": "C",
            "21": "A", "22": "E", "23": "B", "24": "C", "25": "A", "26": "D", "27": "B", "28": "E", "29": "A", "30": "C",
            "31": "D", "32": "E", "33": "B", "34": "A", "35": "C", "36": "E", "37": "A", "38": "B", "39": "D", "40": "C",
            "41": "B", "42": "A", "43": "D", "44": "D", "45": "A", "46": "B", "47": "D", "48": "E", "49": "E", "50": "C",
            "51": "ANULADA", "52": "C", "53": "B", "54": "B", "55": "C", "56": "A", "57": "E", "58": "C", "59": "ANULADA", "60": "D",
            "61": "D", "62": "C", "63": "B", "64": "E", "65": "C", "66": "C", "67": "E", "68": "ANULADA", "69": "E", "70": "D",
            "71": "E", "72": "D", "73": "C", "74": "C", "75": "D", "76": "ANULADA", "77": "A", "78": "E", "79": "E", "80": "E",
            "81": "B", "82": "A", "83": "B", "84": "A", "85": "B", "86": "D", "87": "E", "88": "E", "89": "C", "90": "D",
            "91": "B", "92": "D", "93": "C", "94": "B", "95": "C", "96": "B", "97": "C", "98": "B", "99": "E", "100": "E"
        }

    # Se for ENARE-2023, gabarito oficial consolidado com as 6 questões anuladas pós-recurso
    if "ENARE-2023" in nome_arq.upper() or "ENARE_2023" in nome_arq.upper():
        return {
            "1": "C", "2": "B", "3": "A", "4": "D", "5": "B", "6": "D", "7": "E", "8": "B", "9": "B", "10": "A",
            "11": "D", "12": "C", "13": "E", "14": "A", "15": "C", "16": "B", "17": "D", "18": "E", "19": "B", "20": "B",
            "21": "D", "22": "B", "23": "B", "24": "C", "25": "A", "26": "E", "27": "C", "28": "D", "29": "B", "30": "A",
            "31": "ANULADA", "32": "D", "33": "C", "34": "A", "35": "D", "36": "B", "37": "E", "38": "A", "39": "D", "40": "C",
            "41": "C", "42": "E", "43": "A", "44": "A", "45": "A", "46": "ANULADA", "47": "A", "48": "C", "49": "ANULADA", "50": "A",
            "51": "C", "52": "E", "53": "D", "54": "B", "55": "D", "56": "E", "57": "E", "58": "E", "59": "D", "60": "D",
            "61": "D", "62": "C", "63": "B", "64": "A", "65": "E", "66": "D", "67": "D", "68": "B", "69": "C", "70": "D",
            "71": "A", "72": "B", "73": "C", "74": "E", "75": "D", "76": "A", "77": "D", "78": "B", "79": "D", "80": "D",
            "81": "A", "82": "A", "83": "D", "84": "D", "85": "ANULADA", "86": "ANULADA", "87": "E", "88": "B", "89": "B", "90": "A",
            "91": "A", "92": "B", "93": "B", "94": "C", "95": "E", "96": "D", "97": "E", "98": "A", "99": "C", "100": "ANULADA"
        }

    # Se for ENARE-2024, gabarito oficial consolidado pós-recurso (com as 5 anuladas: 1, 5, 42, 45, 99)
    if "ENARE-2024" in nome_arq.upper() or "ENARE_2024" in nome_arq.upper():
        return {
            "1": "ANULADA", "2": "B", "3": "E", "4": "D", "5": "ANULADA", "6": "C", "7": "A", "8": "B", "9": "A", "10": "A",
            "11": "C", "12": "B", "13": "D", "14": "C", "15": "A", "16": "E", "17": "E", "18": "D", "19": "D", "20": "B",
            "21": "E", "22": "D", "23": "C", "24": "B", "25": "C", "26": "B", "27": "E", "28": "D", "29": "E", "30": "C",
            "31": "B", "32": "E", "33": "B", "34": "C", "35": "C", "36": "E", "37": "D", "38": "C", "39": "A", "40": "B",
            "41": "B", "42": "ANULADA", "43": "B", "44": "D", "45": "ANULADA", "46": "B", "47": "A", "48": "C", "49": "B", "50": "A",
            "51": "D", "52": "B", "53": "C", "54": "D", "55": "D", "56": "A", "57": "A", "58": "E", "59": "B", "60": "D",
            "61": "D", "62": "B", "63": "C", "64": "B", "65": "E", "66": "D", "67": "C", "68": "A", "69": "E", "70": "A",
            "71": "B", "72": "D", "73": "C", "74": "E", "75": "A", "76": "D", "77": "E", "78": "C", "79": "A", "80": "B",
            "81": "E", "82": "D", "83": "B", "84": "D", "85": "E", "86": "C", "87": "E", "88": "A", "89": "B", "90": "C",
            "91": "C", "92": "B", "93": "C", "94": "E", "95": "C", "96": "A", "97": "A", "98": "B", "99": "ANULADA", "100": "B"
        }

    # Se for ENARE-2025, o PDF possui gabarito incompleto na última página.
    # O gabarito oficial consolidado é obtido da imagem Gabarito_ENARE_2025.png (Acesso Direto - Tipo 3).
    if "ENARE-2025" in nome_arq.upper() or "ENARE_2025" in nome_arq.upper():
        return {
            "1": "C", "2": "C", "3": "D", "4": "C", "5": "D", "6": "C", "7": "C", "8": "E", "9": "D", "10": "D",
            "11": "E", "12": "A", "13": "B", "14": "D", "15": "D", "16": "B", "17": "C", "18": "E", "19": "E", "20": "C",
            "21": "C", "22": "D", "23": "B", "24": "B", "25": "D", "26": "C", "27": "E", "28": "A", "29": "C", "30": "A",
            "31": "D", "32": "E", "33": "C", "34": "B", "35": "B", "36": "A", "37": "D", "38": "E", "39": "D", "40": "B",
            "41": "C", "42": "C", "43": "C", "44": "ANULADA", "45": "ANULADA", "46": "B", "47": "E", "48": "C", "49": "C", "50": "A",
            "51": "C", "52": "A", "53": "B", "54": "E", "55": "B", "56": "A", "57": "E", "58": "E", "59": "B", "60": "C",
            "61": "B", "62": "D", "63": "C", "64": "A", "65": "D", "66": "C", "67": "A", "68": "A", "69": "C", "70": "D",
            "71": "E", "72": "A", "73": "C", "74": "C", "75": "B", "76": "B", "77": "B", "78": "A", "79": "A", "80": "B",
            "81": "E", "82": "A", "83": "D", "84": "B", "85": "A", "86": "B", "87": "E", "88": "E", "89": "C", "90": "A",
            "91": "E", "92": "D", "93": "ANULADA", "94": "B", "95": "D", "96": "A", "97": "C", "98": "B", "99": "D", "100": "A"
        }

    # Se for ENARE-2026, gabarito oficial consolidado pós-recurso (com as 4 anuladas: 9, 47, 55, 66)
    if "ENARE-2026" in nome_arq.upper() or "ENARE_2026" in nome_arq.upper():
        return {
            "1": "A", "2": "B", "3": "A", "4": "D", "5": "C", "6": "B", "7": "A", "8": "B", "9": "ANULADA", "10": "C",
            "11": "C", "12": "D", "13": "C", "14": "B", "15": "A", "16": "B", "17": "D", "18": "D", "19": "C", "20": "C",
            "21": "A", "22": "A", "23": "B", "24": "D", "25": "A", "26": "C", "27": "D", "28": "B", "29": "A", "30": "C",
            "31": "B", "32": "D", "33": "C", "34": "B", "35": "D", "36": "C", "37": "D", "38": "D", "39": "D", "40": "B",
            "41": "C", "42": "D", "43": "D", "44": "B", "45": "B", "46": "C", "47": "ANULADA", "48": "D", "49": "B", "50": "C",
            "51": "C", "52": "A", "53": "C", "54": "C", "55": "ANULADA", "56": "D", "57": "D", "58": "A", "59": "B", "60": "C",
            "61": "A", "62": "B", "63": "B", "64": "D", "65": "A", "66": "ANULADA", "67": "C", "68": "B", "69": "C", "70": "B",
            "71": "B", "72": "A", "73": "C", "74": "A", "75": "A", "76": "A", "77": "B", "78": "D", "79": "B", "80": "A",
            "81": "D", "82": "D", "83": "B", "84": "C", "85": "B", "86": "D", "87": "B", "88": "D", "89": "A", "90": "C",
            "91": "B", "92": "A", "93": "C", "94": "A", "95": "B", "96": "D", "97": "C", "98": "C", "99": "A", "100": "A"
        }

    # Se for REVALIDA-2022/1 (Prova 1), gabarito oficial consolidado pós-recurso (com 10 anuladas: 1, 6, 11, 14, 22, 27, 43, 57, 61, 83)
    if "REVALIDA-2022_PV_OBJETIVA_1" in nome_arq.upper() or "REVALIDA_2022_1" in nome_arq.upper() or "REVALIDA-2022-1" in nome_arq.upper():
        return {
            "1": "ANULADA", "2": "C", "3": "C", "4": "D", "5": "A", "6": "ANULADA", "7": "C", "8": "C", "9": "B", "10": "C",
            "11": "ANULADA", "12": "B", "13": "A", "14": "ANULADA", "15": "C", "16": "D", "17": "A", "18": "C", "19": "B", "20": "B",
            "21": "B", "22": "ANULADA", "23": "B", "24": "D", "25": "B", "26": "C", "27": "ANULADA", "28": "A", "29": "D", "30": "B",
            "31": "C", "32": "B", "33": "A", "34": "A", "35": "C", "36": "C", "37": "D", "38": "D", "39": "C", "40": "B",
            "41": "B", "42": "D", "43": "ANULADA", "44": "C", "45": "D", "46": "D", "47": "D", "48": "D", "49": "B", "50": "D",
            "51": "C", "52": "D", "53": "B", "54": "D", "55": "D", "56": "B", "57": "ANULADA", "58": "C", "59": "A", "60": "C",
            "61": "ANULADA", "62": "A", "63": "A", "64": "B", "65": "D", "66": "A", "67": "D", "68": "A", "69": "A", "70": "D",
            "71": "A", "72": "C", "73": "D", "74": "A", "75": "B", "76": "C", "77": "A", "78": "C", "79": "C", "80": "C",
            "81": "B", "82": "C", "83": "ANULADA", "84": "B", "85": "D", "86": "A", "87": "A", "88": "A", "89": "D", "90": "C",
            "91": "A", "92": "A", "93": "B", "94": "A", "95": "B", "96": "A", "97": "A", "98": "A", "99": "C", "100": "D"
        }

    # Se for REVALIDA-2022/2 (Prova 2), gabarito oficial consolidado pós-recurso (com 14 anuladas: 12, 16, 21, 37, 50, 60, 61, 62, 66, 70, 73, 78, 84, 85)
    if "REVALIDA-2022-2" in nome_arq.upper() or "REVALIDA_2022_2" in nome_arq.upper() or "REVALIDA-2022_2" in nome_arq.upper():
        return {
            "1": "C", "2": "A", "3": "B", "4": "D", "5": "D", "6": "A", "7": "B", "8": "B", "9": "D", "10": "C",
            "11": "D", "12": "ANULADA", "13": "C", "14": "C", "15": "D", "16": "ANULADA", "17": "B", "18": "D", "19": "A", "20": "B",
            "21": "ANULADA", "22": "D", "23": "C", "24": "A", "25": "D", "26": "C", "27": "C", "28": "B", "29": "A", "30": "C",
            "31": "A", "32": "A", "33": "B", "34": "C", "35": "D", "36": "C", "37": "ANULADA", "38": "A", "39": "D", "40": "A",
            "41": "B", "42": "C", "43": "C", "44": "D", "45": "B", "46": "C", "47": "C", "48": "C", "49": "A", "50": "ANULADA",
            "51": "B", "52": "B", "53": "D", "54": "B", "55": "D", "56": "A", "57": "D", "58": "B", "59": "D", "60": "ANULADA",
            "61": "ANULADA", "62": "ANULADA", "63": "A", "64": "B", "65": "C", "66": "ANULADA", "67": "C", "68": "A", "69": "D", "70": "ANULADA",
            "71": "D", "72": "C", "73": "ANULADA", "74": "D", "75": "A", "76": "D", "77": "C", "78": "ANULADA", "79": "D", "80": "A",
            "81": "B", "82": "D", "83": "B", "84": "ANULADA", "85": "ANULADA", "86": "C", "87": "A", "88": "D", "89": "A", "90": "D",
            "91": "B", "92": "A", "93": "C", "94": "C", "95": "A", "96": "B", "97": "B", "98": "B", "99": "A", "100": "A"
        }

    # Se for REVALIDA-2023/1 (Prova 1), gabarito oficial consolidado pós-recurso (com 7 anuladas: 7, 13, 35, 38, 42, 48, 49)
    if "REVALIDA-2023_1" in nome_arq.upper() or "REVALIDA_2023_1" in nome_arq.upper() or "REVALIDA-2023-1" in nome_arq.upper():
        return {
            "1": "D", "2": "D", "3": "B", "4": "A", "5": "A", "6": "C", "7": "ANULADA", "8": "A", "9": "C", "10": "B",
            "11": "D", "12": "D", "13": "ANULADA", "14": "C", "15": "C", "16": "D", "17": "D", "18": "B", "19": "A", "20": "D",
            "21": "D", "22": "A", "23": "C", "24": "B", "25": "A", "26": "A", "27": "A", "28": "C", "29": "B", "30": "C",
            "31": "D", "32": "B", "33": "A", "34": "A", "35": "ANULADA", "36": "A", "37": "B", "38": "ANULADA", "39": "C", "40": "D",
            "41": "C", "42": "ANULADA", "43": "A", "44": "A", "45": "B", "46": "B", "47": "D", "48": "ANULADA", "49": "ANULADA", "50": "D",
            "51": "B", "52": "D", "53": "D", "54": "C", "55": "C", "56": "C", "57": "D", "58": "A", "59": "A", "60": "B",
            "61": "D", "62": "C", "63": "D", "64": "C", "65": "B", "66": "A", "67": "A", "68": "B", "69": "B", "70": "A",
            "71": "A", "72": "C", "73": "A", "74": "C", "75": "C", "76": "B", "77": "A", "78": "D", "79": "C", "80": "C",
            "81": "D", "82": "C", "83": "D", "84": "B", "85": "D", "86": "C", "87": "B", "88": "C", "89": "B", "90": "A",
            "91": "C", "92": "D", "93": "A", "94": "A", "95": "C", "96": "B", "97": "B", "98": "C", "99": "C", "100": "D"
        }

    # Se for REVALIDA-2023/2 (Prova 2), gabarito oficial consolidado pós-recurso (com 9 anuladas: 3, 28, 37, 46, 48, 58, 67, 73, 93)
    if "REVALIDA-2023_2" in nome_arq.upper() or "REVALIDA_2023_2" in nome_arq.upper() or "REVALIDA-2023-2" in nome_arq.upper():
        return {
            "1": "B", "2": "D", "3": "ANULADA", "4": "B", "5": "B", "6": "A", "7": "A", "8": "B", "9": "D", "10": "B",
            "11": "C", "12": "C", "13": "B", "14": "D", "15": "A", "16": "C", "17": "B", "18": "B", "19": "C", "20": "C",
            "21": "D", "22": "A", "23": "A", "24": "D", "25": "B", "26": "D", "27": "A", "28": "ANULADA", "29": "A", "30": "C",
            "31": "A", "32": "D", "33": "B", "34": "A", "35": "D", "36": "C", "37": "ANULADA", "38": "B", "39": "C", "40": "A",
            "41": "D", "42": "D", "43": "D", "44": "D", "45": "B", "46": "ANULADA", "47": "D", "48": "ANULADA", "49": "D", "50": "C",
            "51": "D", "52": "A", "53": "C", "54": "C", "55": "B", "56": "C", "57": "C", "58": "ANULADA", "59": "B", "60": "C",
            "61": "A", "62": "C", "63": "D", "64": "B", "65": "C", "66": "C", "67": "ANULADA", "68": "C", "69": "D", "70": "A",
            "71": "D", "72": "A", "73": "ANULADA", "74": "C", "75": "C", "76": "A", "77": "C", "78": "D", "79": "D", "80": "B",
            "81": "A", "82": "B", "83": "B", "84": "D", "85": "A", "86": "D", "87": "C", "88": "A", "89": "C", "90": "A",
            "91": "B", "92": "B", "93": "ANULADA", "94": "C", "95": "D", "96": "B", "97": "B", "98": "A", "99": "A", "100": "C"
        }

    # Se for REVALIDA-2024/1 (Prova 1), gabarito oficial consolidado pós-recurso (com 5 anuladas: 7, 17, 43, 50, 83)
    if "REVALIDA-2024_1" in nome_arq.upper() or "REVALIDA_2024_1" in nome_arq.upper() or "REVALIDA-2024-1" in nome_arq.upper():
        return {
            "1": "A", "2": "A", "3": "C", "4": "D", "5": "A", "6": "D", "7": "ANULADA", "8": "C", "9": "B", "10": "D",
            "11": "D", "12": "A", "13": "A", "14": "D", "15": "C", "16": "A", "17": "ANULADA", "18": "D", "19": "D", "20": "D",
            "21": "B", "22": "D", "23": "A", "24": "B", "25": "C", "26": "D", "27": "A", "28": "B", "29": "C", "30": "B",
            "31": "C", "32": "D", "33": "B", "34": "C", "35": "B", "36": "D", "37": "C", "38": "B", "39": "A", "40": "A",
            "41": "D", "42": "A", "43": "ANULADA", "44": "B", "45": "D", "46": "C", "47": "D", "48": "D", "49": "C", "50": "ANULADA",
            "51": "A", "52": "B", "53": "B", "54": "B", "55": "A", "56": "C", "57": "A", "58": "A", "59": "D", "60": "A",
            "61": "D", "62": "C", "63": "B", "64": "D", "65": "A", "66": "A", "67": "C", "68": "D", "69": "C", "70": "D",
            "71": "C", "72": "A", "73": "A", "74": "B", "75": "B", "76": "C", "77": "B", "78": "D", "79": "B", "80": "B",
            "81": "C", "82": "B", "83": "ANULADA", "84": "A", "85": "A", "86": "B", "87": "C", "88": "B", "89": "B", "90": "C",
            "91": "A", "92": "D", "93": "A", "94": "D", "95": "C", "96": "A", "97": "C", "98": "B", "99": "C", "100": "A"
        }

    # Se for REVALIDA-2024/2 (Prova 2), gabarito oficial consolidado pós-recurso (com 6 anuladas: 3, 22, 30, 37, 46, 60)
    if "REVALIDA-2024_2" in nome_arq.upper() or "REVALIDA_2024_2" in nome_arq.upper() or "REVALIDA-2024-2" in nome_arq.upper():
        return {
            "1": "C", "2": "B", "3": "ANULADA", "4": "D", "5": "D", "6": "A", "7": "D", "8": "A", "9": "B", "10": "B",
            "11": "A", "12": "B", "13": "D", "14": "C", "15": "D", "16": "C", "17": "C", "18": "A", "19": "A", "20": "B",
            "21": "D", "22": "ANULADA", "23": "B", "24": "D", "25": "C", "26": "C", "27": "A", "28": "C", "29": "B", "30": "ANULADA",
            "31": "C", "32": "B", "33": "A", "34": "A", "35": "C", "36": "B", "37": "ANULADA", "38": "A", "39": "C", "40": "A",
            "41": "B", "42": "C", "43": "D", "44": "A", "45": "C", "46": "ANULADA", "47": "C", "48": "D", "49": "D", "50": "D",
            "51": "B", "52": "B", "53": "C", "54": "D", "55": "C", "56": "B", "57": "B", "58": "C", "59": "A", "60": "ANULADA",
            "61": "A", "62": "A", "63": "B", "64": "D", "65": "B", "66": "D", "67": "A", "68": "D", "69": "A", "70": "A",
            "71": "D", "72": "C", "73": "C", "74": "D", "75": "D", "76": "B", "77": "C", "78": "A", "79": "C", "80": "D",
            "81": "D", "82": "D", "83": "B", "84": "B", "85": "A", "86": "C", "87": "C", "88": "A", "89": "A", "90": "B",
            "91": "B", "92": "C", "93": "B", "94": "B", "95": "C", "96": "A", "97": "C", "98": "A", "99": "D", "100": "D"
        }

    # Se for REVALIDA-2025/1 (Prova 1), gabarito oficial consolidado pós-recurso (com 3 anuladas: 7, 23, 34)
    if "REVALIDA-2025_1" in nome_arq.upper() or "REVALIDA_2025_1" in nome_arq.upper() or "REVALIDA-2025-1" in nome_arq.upper():
        return {
            "1": "B", "2": "A", "3": "A", "4": "B", "5": "D", "6": "C", "7": "ANULADA", "8": "B", "9": "A", "10": "C",
            "11": "B", "12": "A", "13": "A", "14": "D", "15": "A", "16": "B", "17": "B", "18": "D", "19": "D", "20": "B",
            "21": "C", "22": "B", "23": "ANULADA", "24": "A", "25": "B", "26": "D", "27": "D", "28": "B", "29": "A", "30": "A",
            "31": "C", "32": "C", "33": "C", "34": "ANULADA", "35": "C", "36": "A", "37": "B", "38": "D", "39": "D", "40": "D",
            "41": "A", "42": "B", "43": "A", "44": "D", "45": "A", "46": "B", "47": "D", "48": "C", "49": "D", "50": "C",
            "51": "C", "52": "D", "53": "B", "54": "A", "55": "C", "56": "C", "57": "C", "58": "B", "59": "D", "60": "B",
            "61": "A", "62": "B", "63": "D", "64": "A", "65": "C", "66": "C", "67": "D", "68": "C", "69": "D", "70": "B",
            "71": "B", "72": "D", "73": "C", "74": "D", "75": "C", "76": "A", "77": "C", "78": "D", "79": "A", "80": "D",
            "81": "A", "82": "B", "83": "D", "84": "B", "85": "C", "86": "B", "87": "B", "88": "B", "89": "C", "90": "B",
            "91": "A", "92": "D", "93": "A", "94": "B", "95": "A", "96": "B", "97": "D", "98": "A", "99": "C", "100": "D"
        }

    # Se for REVALIDA-2025/2 (Prova 2), gabarito oficial consolidado pós-recurso (com 7 anuladas: 7, 9, 11, 43, 55, 85, 87)
    if "REVALIDA-2025_2" in nome_arq.upper() or "REVALIDA_2025_2" in nome_arq.upper() or "REVALIDA-2025-2" in nome_arq.upper():
        return {
            "1": "A", "2": "B", "3": "A", "4": "D", "5": "C", "6": "B", "7": "ANULADA", "8": "B", "9": "ANULADA", "10": "C",
            "11": "ANULADA", "12": "D", "13": "C", "14": "B", "15": "A", "16": "B", "17": "D", "18": "D", "19": "D", "20": "C",
            "21": "A", "22": "A", "23": "B", "24": "D", "25": "A", "26": "C", "27": "D", "28": "B", "29": "A", "30": "C",
            "31": "B", "32": "D", "33": "C", "34": "B", "35": "D", "36": "C", "37": "D", "38": "D", "39": "D", "40": "B",
            "41": "C", "42": "D", "43": "ANULADA", "44": "B", "45": "B", "46": "C", "47": "C", "48": "D", "49": "B", "50": "C",
            "51": "B", "52": "C", "53": "C", "54": "B", "55": "ANULADA", "56": "B", "57": "C", "58": "A", "59": "C", "60": "D",
            "61": "C", "62": "A", "63": "C", "64": "B", "65": "B", "66": "B", "67": "B", "68": "B", "69": "D", "70": "B",
            "71": "A", "72": "C", "73": "D", "74": "D", "75": "C", "76": "B", "77": "A", "78": "D", "79": "D", "80": "A",
            "81": "D", "82": "D", "83": "A", "84": "A", "85": "ANULADA", "86": "A", "87": "ANULADA", "88": "A", "89": "B", "90": "D",
            "91": "D", "92": "A", "93": "A", "94": "B", "95": "C", "96": "C", "97": "A", "98": "A", "99": "A", "100": "B"
        }

    # Se for REVALIDA-2026/1 (Prova 1), gabarito oficial consolidado
    if "REVALIDA-2026_1" in nome_arq.upper() or "REVALIDA_2026_1" in nome_arq.upper() or "REVALIDA-2026-1" in nome_arq.upper():
        return {
            "1": "D", "2": "C", "3": "C", "4": "D", "5": "B", "6": "D", "7": "D", "8": "C", "9": "D", "10": "D",
            "11": "D", "12": "D", "13": "C", "14": "B", "15": "B", "16": "B", "17": "B", "18": "D", "19": "B", "20": "B",
            "21": "A", "22": "B", "23": "C", "24": "C", "25": "A", "26": "A", "27": "B", "28": "A", "29": "A", "30": "C",
            "31": "C", "32": "C", "33": "C", "34": "C", "35": "C", "36": "B", "37": "A", "38": "B", "39": "B", "40": "C",
            "41": "A", "42": "A", "43": "C", "44": "A", "45": "A", "46": "D", "47": "C", "48": "A", "49": "D", "50": "D",
            "51": "B", "52": "D", "53": "D", "54": "A", "55": "D", "56": "C", "57": "D", "58": "B", "59": "A", "60": "B",
            "61": "A", "62": "A", "63": "B", "64": "A", "65": "B", "66": "B", "67": "D", "68": "D", "69": "C", "70": "D",
            "71": "A", "72": "D", "73": "A", "74": "C", "75": "C", "76": "A", "77": "A", "78": "C", "79": "D", "80": "C",
            "81": "B", "82": "B", "83": "A", "84": "A", "85": "C", "86": "A", "87": "C", "88": "B", "89": "D", "90": "B",
            "91": "C", "92": "D", "93": "C", "94": "A", "95": "A", "96": "B", "97": "B", "98": "D", "99": "B", "100": "D"
        }

    # Se for uma prova do Revalida e tivermos o mapa carregado
    if mapa_revalida:
        for chave, gab_map in mapa_revalida.items():
            if chave.lower() in nome_arq.lower():
                if gab_map:
                    return gab_map

    # Se não, tenta extrair das últimas páginas do próprio PDF (padrão ENARE)
    try:
        doc = pymupdf.open(str(caminho_pdf))
        gabarito = {}
        for num_pag in range(max(0, len(doc) - 4), len(doc)):
            texto = doc[num_pag].get_text("text")
            # Tenta via parser de blocos e tabelas
            gab_bloco = parse_gabarito_text_block(texto)
            if gab_bloco:
                gabarito.update(gab_bloco)
            else:
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


CORRECOES_MANUAIS_QUESTOES = {
    "REVALIDA-2022_PV_objetiva_1_100": {
        "enunciado": "Uma mulher com 32 anos de idade comparece à consulta médica agendada na Unidade Básica de Saúde levando o resultado de exame citopatológico do colo uterino coletado há 1 mês. A paciente, muito nervosa, confessa que havia lido o resultado do exame e que pesquisou na internet sobre o tema. Ressaltou que segue corretamente às orientações do seu médico e que, aos 29 anos de idade, realizou o mesmo exame, com resultado normal. O resultado do exame citopatológico do colo uterino realizado no último mês apresentou amostra satisfatória, representatividade da junção escamo colunar, presença de células escamosas e glandulares e presença de ASCUS – (células escamosas atípicas de significado indeterminado).\n\nConsiderando o caso apresentado, após explicar à paciente que há presença de um exame com alteração, o médico de família deve",
        "alternativas": {
            "A": "repetir o exame citopatológico do colo uterino no momento da consulta.",
            "B": "solicitar novo exame citopatológico do colo uterino em 12 meses e, caso a alteração permaneça, avaliar indicação de cirurgia.",
            "C": "encaminhar a paciente para o serviço especializado de Ginecologia para realização de um novo exame mais detalhado, a colposcopia.",
            "D": "solicitar novo exame citopatológico do colo uterino em 6 meses e, caso a alteração permaneça, solicitar a realização de um exame mais detalhado, a colposcopia."
        }
    },
    "REVALIDA-2025_1_caderno_1_preliminar_5": {
        "enunciado": "A médica de uma penitenciária avalia homem de 26 anos, com 98 kg, que relata compartilhar a cela com 12 pessoas (a qual comportaria no máximo 5). O paciente queixa-se de prurido cutâneo há 2 dias com piora no período noturno. Ao exame físico, a médica identifica pápulas eritematosas com escoriações em região de prega em braços e em região posterior de joelhos.\n\nCom relação a essa situação, assinale a alternativa que apresenta, respectivamente, a orientação médica e a prescrição medicamentosa adequadas.",
        "alternativas": {
            "A": "Restrição de visitas aos detentos e isolamento dos casos nas celas, sem permissão de saída; uso de ivermectina 6 mg, 01 comprimido via oral, repetindo em 15 dias, para todos da cela.",
            "B": "Isolamento dos casos na enfermaria da unidade e lavagem frequente das roupas de cama, de banho e de vestuário com água quente (pelo menos a 30 °C); uso de sprays inseticidas e fumigantes.",
            "C": "Realização de palestras educativas para os detentos sobre medidas preventivas e aumento do tempo de banho de sol; uso de fluconazol 150 mg por semana durante 1 mês, para todos da cela.",
            "D": "Incremento da frequência de limpeza geral da unidade e higienização adequada das roupas de uso pessoal, de cama e de banho; uso de ivermectina 6 mg, dose conforme o peso, repetindo em 15 dias, para todos da cela."
        }
    }
}


def extrair_questoes_do_texto(texto_bruto, nome_arquivo):
    """Identifica blocos de questões e separa enunciado de alternativas."""
    padrao_questao = re.compile(r'(?:^|\n|\b)(?:QUEST[ÃAÁO0-9\?]+|QUEST[ÃA]O)\s*(\d+)[\.\s-]*', re.IGNORECASE)
    matches = list(padrao_questao.finditer(texto_bruto))
    
    if not matches:
        return []

    questoes_processadas = []
    nome_origem = nome_arquivo.replace(".pdf", "")
    
    for i in range(len(matches)):
        inicio = matches[i].start()
        fim = matches[i+1].start() if i + 1 < len(matches) else len(texto_bruto)
        bloco = texto_bruto[inicio:fim].strip()
        
        num_q = matches[i].group(1)
        chave_q = f"{nome_origem}_{num_q}"
        
        if chave_q in CORRECOES_MANUAIS_QUESTOES:
            corr = CORRECOES_MANUAIS_QUESTOES[chave_q]
            especialidade, tema, subtema = classificar_questao(corr["enunciado"])
            questoes_processadas.append({
                "origem": nome_origem,
                "numero": num_q,
                "especialidade": especialidade,
                "tema": tema,
                "subtema": subtema,
                "enunciado": corr["enunciado"],
                "alternativas": corr["alternativas"]
            })
            continue

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
                "origem": nome_origem,
                "numero": num_q,
                "especialidade": especialidade,
                "tema": tema,
                "subtema": subtema,
                "enunciado": enunciado,
                "alternativas": alternativas
            })

    return questoes_processadas

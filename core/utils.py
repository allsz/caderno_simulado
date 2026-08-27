import base64
import re
from html import escape as html_escape
from pathlib import Path

_IMAGE_CACHE = {}


def obter_base64_imagem(caminho_relativo, base_dir=None):
    """Converte qualquer imagem local em data URI Base64 autônoma para abrir perfeitamente em qualquer dispositivo."""
    if not caminho_relativo or caminho_relativo.startswith("data:"):
        return caminho_relativo
    if caminho_relativo in _IMAGE_CACHE:
        return _IMAGE_CACHE[caminho_relativo]

    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
    caminho_p = Path(caminho_relativo)
    
    possibilidades = [
        caminho_p,
        base_dir / caminho_p,
        base_dir / "saida" / caminho_p,
        base_dir / "src" / caminho_p.name,
        base_dir / "saida" / "src" / caminho_p.name,
        base_dir / "imagens" / caminho_p.name,
        base_dir / "saida" / "imagens" / caminho_p.name,
    ]
    
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "svg": "image/svg+xml",
        "webp": "image/webp"
    }
    
    for p in possibilidades:
        if p.is_file():
            try:
                ext = p.suffix.lower().lstrip('.')
                mime = mime_map.get(ext, "image/png")
                encoded = base64.b64encode(p.read_bytes()).decode('utf-8')
                res = f"data:{mime};base64,{encoded}"
                _IMAGE_CACHE[caminho_relativo] = res
                return res
            except Exception as e:
                print(f"   [!] Erro ao converter {p} para Base64: {e}")
                
    p_name_clean = caminho_p.name.lower().replace("ã", "a").replace("ç", "c")
    cand_dirs = [
        base_dir / "src",
        base_dir / "saida" / "src",
        base_dir / "imagens",
        base_dir / "saida" / "imagens",
    ]
    for d in cand_dirs:
        if d.is_dir():
            for item in d.iterdir():
                if item.is_file():
                    item_clean = item.name.lower().replace("ã", "a").replace("ç", "c")
                    if item_clean == p_name_clean:
                        try:
                            ext = item.suffix.lower().lstrip('.')
                            mime = mime_map.get(ext, "image/png")
                            encoded = base64.b64encode(item.read_bytes()).decode('utf-8')
                            res = f"data:{mime};base64,{encoded}"
                            _IMAGE_CACHE[caminho_relativo] = res
                            return res
                        except Exception as e:
                            print(f"   [!] Erro ao converter {item} para Base64: {e}")

    _IMAGE_CACHE[caminho_relativo] = caminho_relativo
    return caminho_relativo


def formatar_texto_fluido(texto, modo_html=True):
    """
    Remove quebras de linha artificiais provocadas pelas colunas estreitas dos PDFs A4 do INEP/ENARE.
    Une frases contínuas e preserva parágrafos reais.
    """
    if not texto:
        return ""
    if modo_html:
        texto = html_escape(texto)
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    paragrafos = re.split(r'\n\s*\n', texto)
    paragrafos_limpos = []
    for par in paragrafos:
        par_limpo = re.sub(r'\s*\n\s*', ' ', par)
        par_limpo = re.sub(r'\s+', ' ', par_limpo).strip()
        if par_limpo:
            paragrafos_limpos.append(par_limpo)
    
    sep = "<br><br>" if modo_html else "\n\n"
    return sep.join(paragrafos_limpos)

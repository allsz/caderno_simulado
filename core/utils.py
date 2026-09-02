import base64
import json
import os
import re
import tempfile
from html import escape as html_escape
from pathlib import Path

_IMAGE_CACHE = {}


def salvar_json_atomico(caminho: Path, dados: any, indent: int = 2) -> bool:
    """
    Salva dados em formato JSON usando escrita atômica (tempfile + os.replace).
    Garante que falhas de energia ou interrupções não corrompam os arquivos de cache.
    """
    caminho = Path(caminho).resolve()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    
    dir_destino = caminho.parent
    prefixo = f".{caminho.name}.tmp_"
    
    try:
        with tempfile.NamedTemporaryFile("w", dir=dir_destino, prefix=prefixo, delete=False, encoding="utf-8") as f_tmp:
            nome_tmp = f_tmp.name
            json.dump(dados, f_tmp, ensure_ascii=False, indent=indent)
            f_tmp.flush()
            os.fsync(f_tmp.fileno())
            
        os.replace(nome_tmp, caminho)
        return True
    except Exception as e:
        print(f"   [!] Erro na gravação atômica de {caminho.name}: {e}")
        if 'nome_tmp' in locals() and os.path.exists(nome_tmp):
            try:
                os.remove(nome_tmp)
            except Exception:
                pass
        return False


def carregar_json_seguro(caminho: Path, default=None):
    """Carrega arquivo JSON com tratamento de exceções e fallback seguro."""
    caminho = Path(caminho)
    if not caminho.exists():
        return default if default is not None else {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"   [!] Erro ao carregar JSON '{caminho.name}': {e}")
        return default if default is not None else {}


def validar_schema_questao(q: dict) -> list:
    """Valida se um objeto de questão médica está em conformidade com o schema esperado."""
    erros = []
    if not isinstance(q, dict):
        return ["Questão não é um objeto válido"]
        
    for campo in ["origem", "numero", "especialidade", "tema", "subtema", "enunciado", "alternativas", "gabarito"]:
        if campo not in q:
            erros.append(f"Campo obrigatório '{campo}' ausente")
            
    if not str(q.get("enunciado", "")).strip():
        erros.append("Enunciado vazio")
        
    alts = q.get("alternativas", {})
    if not isinstance(alts, dict) or len(alts) < 2:
        erros.append("Alternativas insuficientes ou em formato inválido")
        
    gab = str(q.get("gabarito", "")).strip().upper()
    if not gab:
        erros.append("Gabarito não especificado")
        
    return erros


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
    Une frases contínuas e preserva parágrafos reais com escape HTML seguro.
    """
    if not texto:
        return ""
    if modo_html:
        texto = html_escape(str(texto))
    texto = str(texto).replace("\r\n", "\n").replace("\r", "\n")
    paragrafos = re.split(r'\n\s*\n', texto)
    paragrafos_limpos = []
    for par in paragrafos:
        par_limpo = re.sub(r'\s*\n\s*', ' ', par)
        par_limpo = re.sub(r'\s+', ' ', par_limpo).strip()
        if par_limpo:
            paragrafos_limpos.append(par_limpo)
    
    sep = "<br><br>" if modo_html else "\n\n"
    return sep.join(paragrafos_limpos)


def formatar_explicacao_html(exp):
    """
    Formata texto de justificativa médica para exibição limpa em HTML:
    - Normaliza quebras de linha e trata literais \\n ou \\r\\n
    - Converte **negrito** markdown para <strong>negrito</strong>
    - Converte marcadores de lista (- item) para bullets elegantes (• item)
    - Preserva quebras de parágrafo sem poluição visual
    """
    if not exp:
        return ""
    texto = str(exp).replace("\r\n", "\n").replace("\\r\\n", "\n").replace("\\n", "\n").replace("\r", "")
    texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', texto)
    texto = re.sub(r'(?m)^-\s+', '• ', texto)
    paragrafos = [p.strip().replace('\n', '<br>') for p in re.split(r'\n\s*\n', texto) if p.strip()]
    return "<br><br>".join(paragrafos)


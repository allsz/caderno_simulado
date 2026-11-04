import json
import re
import sys
from pathlib import Path

# Força UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
SAIDA_DIR = BASE_DIR / "saida"
CACHE_EXP_PATH = SAIDA_DIR / "cache_explicacoes.json"
BANCO_PATH = SAIDA_DIR / "banco_questoes_cache.json"

def carregar_mapa_gabaritos():
    """Carrega o gabarito oficial de cada questão a partir do banco de questões."""
    mapa = {}
    if BANCO_PATH.exists():
        with open(BANCO_PATH, "r", encoding="utf-8") as f:
            banco = json.load(f)
        for q in banco:
            origem = q.get("origem", "").strip()
            numero = str(q.get("numero", "")).strip()
            gab = q.get("gabarito", "").strip().upper()
            if origem and numero:
                mapa[f"{origem}_{numero}"] = gab
    return mapa

def eh_titulo_de_secao(linha: str) -> bool:
    """Verifica se a linha é um título de seção estrutural."""
    l = linha.strip()
    if re.search(r'Justificativa\s+d[ao]\s+alternativa\s+correta', l, re.IGNORECASE):
        return True
    if re.search(r'An[aá]lise\s+d[eao]s?\s+(?:demais\s+)?(?:alternativas|distratores)', l, re.IGNORECASE):
        return True
    if re.search(r'Racioc[ií]nio\s+Cl[ií]nico', l, re.IGNORECASE):
        return True
    if re.search(r'Justificativa\s+M[eé]dica', l, re.IGNORECASE):
        return True
    return False

def padronizar_header(linha: str) -> str:
    """Padroniza cabeçalhos estruturais principais."""
    l = linha.strip()
    if re.search(r'An[aá]lise\s+d[eao]s?\s+(?:demais\s+)?(?:alternativas|distratores)', l, re.IGNORECASE):
        return '**Análise das alternativas:**'
    if re.search(r'Justificativa\s+d[ao]\s+alternativa\s+correta', l, re.IGNORECASE):
        return '**Raciocínio Clínico e Fisiopatológico:**'
    if re.search(r'Racioc[ií]nio\s+Cl[ií]nico', l, re.IGNORECASE):
        return '**Raciocínio Clínico e Fisiopatológico:**'
    if re.search(r'Justificativa\s+M[eé]dica', l, re.IGNORECASE):
        return '**Justificativa Médica:**'
    return linha

def formatar_linha_alternativa(letra: str, status_raw: str, resto: str, gabarito_oficial: str = None) -> str:
    """Padroniza a linha para o formato Clean: • **Alternativa X: [Correta/Incorreta].** texto normal"""
    eh_incorr = any(x in status_raw for x in ['incorr', 'errad', 'falsa', 'distrator']) or re.match(r'^(?:É\s+)?i?ncorreta\b', resto, re.IGNORECASE)
    eh_corr = any(x in status_raw for x in ['corret', 'certa', 'verdadeir']) or re.match(r'^(?:É\s+a\s+)?correta\b', resto, re.IGNORECASE)

    if eh_incorr:
        status = 'Incorreta.'
    elif eh_corr:
        status = 'Correta.'
    elif gabarito_oficial and gabarito_oficial in ['A', 'B', 'C', 'D', 'E']:
        status = 'Correta.' if letra == gabarito_oficial else 'Incorreta.'
    else:
        status = 'Incorreta.'

    resto_limpo = resto.replace('**', '').replace('*', '').strip()
    resto_limpo = re.sub(r'^(?:É\s+a\s+)?o?rreta\s*(?:\([A-E]\))?[\.\:\-\s]*', '', resto_limpo, flags=re.IGNORECASE).strip()
    resto_limpo = re.sub(r'^(?:É\s+)?i?ncorreta[\.\:\-\s]*', '', resto_limpo, flags=re.IGNORECASE).strip()
    resto_limpo = re.sub(r'^[\:\.\-\–\s]+', '', resto_limpo).strip()

    return f"• **Alternativa {letra}: {status}** {resto_limpo}"

def detectar_alternativa(linha: str, gabarito_oficial: str = None):
    """Detecta itens de alternativas."""
    l = linha.strip()
    if not l:
        return None

    if eh_titulo_de_secao(l):
        return None

    # Variação 1: 'Alternativa X ...'
    m1 = re.match(
        r'^[•\-\*]?\s*(?:\d+[\.\)]\s*)?\*{0,3}(?:Justificativa\s+d[ao]\s+)?Alternativa\s*\(?([A-E])\)?\s*(?:\(([^\)]+)\)|:\s*([^\*]+?)|(?:está|é|–|-)\s*(?:a\s+)?([^\*\:\.\–]+?))?\*{0,3}\s*[\:\.\-\–]*\s*(.*)$',
        l,
        re.IGNORECASE
    )
    if m1:
        letra = m1.group(1).upper()
        status_raw = (m1.group(2) or m1.group(3) or m1.group(4) or '').strip().lower()
        resto = (m1.group(5) or '').strip()
        if not resto and not status_raw:
            return None
        return formatar_linha_alternativa(letra, status_raw, resto, gabarito_oficial)

    # Variação 2: Letra direta 'B está incorreta: ...', '• A) Incorreta: ...'
    m2 = re.match(
        r'^[•\-\*]?\s*(?:\d+[\.\)]\s*)?\*{0,3}([A-E])\s*(?:\)|\.|\:|\-|\–)?\s*(?:(?:está|é|–|-|:)\s*(?:a\s+)?)?(?:\(([^\)]+)\)|(i?ncorreta|correta|distrator|certo|errado))?\*{0,3}\s*[\:\.\-\–]*\s*(.*)$',
        l,
        re.IGNORECASE
    )
    if m2:
        letra = m2.group(1).upper()
        status_raw = (m2.group(2) or m2.group(3) or '').strip().lower()
        resto = (m2.group(4) or '').strip()
        if any(x in status_raw for x in ['corr', 'cert', 'incorr', 'errad', 'distrator']) or re.match(r'^(?:i?ncorreta|correta)\b', resto, re.IGNORECASE):
            return formatar_linha_alternativa(letra, status_raw, resto, gabarito_oficial)

    return None

def formatar_lead_in_ou_subtitulo(linha: str) -> str:
    """
    Formata títulos e 'lead-in headings' do corpo com negrito:
    - Linhas de introdução terminadas em ':' (ex: 'Conforme as diretrizes...:') -> '**Conforme as diretrizes...:**'
    - Tópicos com bullet (ex: '- Fisiopatologia e Clínica: texto') -> '- **Fisiopatologia e Clínica:** texto'
    - Tópicos numerados (ex: '1. Classificação do ferimento: texto') -> '1. **Classificação do ferimento:** texto'
    """
    # Remove qualquer sequência de 3 ou mais asteriscos que cause bug visual
    l = re.sub(r'^\*{3,}', '**', linha.strip())
    l = re.sub(r'\*{3,}$', '**', l)

    # 1. Tópico com bullet ou traço: '- Fisiopatologia e Clínica: texto' ou '• Tratamento de Escolha: texto'
    m_bullet = re.match(r'^([•\-\*]\s*)\*{0,3}([A-ZÀ-Ú][^:\n]{2,70}:)\*{0,3}\s*(.*)$', l)
    if m_bullet:
        prefixo = m_bullet.group(1)
        titulo = m_bullet.group(2).replace('*', '').strip()
        resto = m_bullet.group(3)
        return f"{prefixo}**{titulo}** {resto}".strip()

    # 2. Tópico numerado: '1. Classificação do ferimento: texto' ou '1. Classificação da Queimadura:'
    m_num = re.match(r'^(\d+[\.\)]\s*)\*{0,3}([A-ZÀ-Ú][^:\n]+:)\*{0,3}\s*(.*)$', l)
    if m_num:
        num = m_num.group(1)
        titulo = m_num.group(2).replace('*', '').strip()
        resto = m_num.group(3)
        return f"{num}**{titulo}** {resto}".strip()

    # 3. Linha de chamada terminando em dois pontos (ex: 'Conforme as diretrizes...:', 'De acordo com...:', 'Fundamentação clínica:')
    m_chamada = re.match(r'^\*{0,3}([A-ZÀ-Ú][^:\n]{3,160}:)\*{0,3}$', l)
    if m_chamada and not l.startswith('•') and not l.startswith('-'):
        titulo = m_chamada.group(1).replace('*', '').strip()
        return f"**{titulo}**"

    return l

def aplicar_negrito_ultra_clean(texto: str, gabarito_oficial: str = None) -> str:
    """Aplica o padrão Clean Elegante em todo o texto."""
    if not texto:
        return texto

    # Normaliza previamente qualquer asterisco triplo solto no início de linhas
    texto = re.sub(r'(?m)^\*{3,}', '**', texto)

    linhas = texto.splitlines()
    novas_linhas = []
    em_analise = False
    termos_corpo_destacados = 0

    for linha in linhas:
        l = linha.strip()
        if not l:
            novas_linhas.append('')
            continue

        # 1. Cabeçalhos estruturais principais
        if eh_titulo_de_secao(l):
            header_limpo = padronizar_header(l)
            if 'Análise das alternativas' in header_limpo:
                em_analise = True
            novas_linhas.append(header_limpo)
            continue

        # 2. Alternativas
        alt_formatada = detectar_alternativa(l, gabarito_oficial)
        if alt_formatada:
            em_analise = True
            novas_linhas.append(alt_formatada)
            continue

        # 3. Continuação de parágrafo dentro de alternativas (sem negrito adicional)
        if em_analise:
            novas_linhas.append(l.replace('**', '').replace('*', ''))
        else:
            # 4. No corpo clínico:
            linha_lead = formatar_lead_in_ou_subtitulo(l)

            # Separa o título já negritado do restante do texto
            m_prefixo = re.match(r'^((?:[•\-\*]|\d+[\.\)])?\s*\*\*[^*]+:\*\*\s*)(.*)$', linha_lead)
            if m_prefixo:
                prefixo_titulo = m_prefixo.group(1)
                corpo_texto = m_prefixo.group(2)
            elif linha_lead.startswith('**') and linha_lead.endswith(':**'):
                prefixo_titulo = linha_lead
                corpo_texto = ""
            else:
                prefixo_titulo = ""
                corpo_texto = linha_lead

            # Remove menções soltas de gabarito em negrito
            corpo_texto = re.sub(r'\*\*(?:Alternativa\s*\([A-E]\)|Alternativa\s+[A-E])\*\*', lambda m: m.group(0).replace('**', ''), corpo_texto)

            # Filtra os termos médicos do corpo para permitir no MÁXIMO 2 termos destacados
            partes = corpo_texto.split('**')
            if len(partes) > 1:
                corpo_novo = []
                for i, pedaco in enumerate(partes):
                    if i % 2 == 1:
                        palavras = pedaco.strip().split()
                        termos_proibidos = ['sociedade', 'diretriz', 'linha', 'estritamente', 'apresenta', 'quadro', 'conduta', 'critério']
                        eh_proibido = any(p in pedaco.lower() for p in termos_proibidos)

                        if termos_corpo_destacados < 2 and len(palavras) <= 4 and not eh_proibido:
                            corpo_novo.append(f'**{pedaco}**')
                            termos_corpo_destacados += 1
                        else:
                            corpo_novo.append(pedaco)
                    else:
                        corpo_novo.append(pedaco)
                corpo_final = ''.join(corpo_novo)
            else:
                corpo_final = corpo_texto

            novas_linhas.append(f"{prefixo_titulo}{corpo_final}".strip())

    resultado = '\n'.join(novas_linhas)
    # Garante que nenhum asterisco triplo escape no resultado
    resultado = re.sub(r'\*{3,}', '**', resultado)
    resultado = re.sub(r'\n{3,}', '\n\n', resultado).strip()
    return resultado

def processar_cache():
    if not CACHE_EXP_PATH.exists():
        print(f"[ERRO] {CACHE_EXP_PATH} não encontrado.")
        return

    mapa_gabaritos = carregar_mapa_gabaritos()
    print(f"[*] {len(mapa_gabaritos)} gabaritos carregados.")

    with open(CACHE_EXP_PATH, "r", encoding="utf-8") as f:
        cache = json.load(f)

    total = len(cache)
    modificadas = 0

    print(f"[*] Aplicando Padrão Elegante com Lead-in Headings em {total} questões...")
    for q_id, valor in cache.items():
        gab_oficial = mapa_gabaritos.get(q_id)
        if isinstance(valor, dict):
            exp_orig = valor.get("explicacao", "")
            exp_clean = aplicar_negrito_ultra_clean(exp_orig, gab_oficial)
            if exp_clean != exp_orig:
                valor["explicacao"] = exp_clean
                modificadas += 1
        elif isinstance(valor, str):
            exp_clean = aplicar_negrito_ultra_clean(valor, gab_oficial)
            if exp_clean != valor:
                cache[q_id] = exp_clean
                modificadas += 1

    print(f"[✓] {modificadas} explicações atualizadas com sucesso!")

    temp_path = CACHE_EXP_PATH.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    temp_path.replace(CACHE_EXP_PATH)
    print(f"[✓] Cache salvo atomicamente!")

if __name__ == "__main__":
    processar_cache()

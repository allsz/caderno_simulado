import os
import re
import asyncio
import io
import json
import time
from pathlib import Path
import pymupdf
import winocr
from PIL import Image
import sys
sys.stdout.reconfigure(encoding='utf-8')


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


def carregar_cache_explicacoes(caminho_cache: Path):
    if caminho_cache.exists():
        try:
            with open(caminho_cache, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def salvar_cache_explicacoes(caminho_cache: Path, cache: dict):
    try:
        with open(caminho_cache, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"   [!] Erro ao salvar cache de explicações: {e}")


def gerar_explicacao_gemini(questao, gabarito_oficial, api_key):
    """Gera comentário médico e justificativa usando a API gratuita do Gemini (Google AI Studio)."""
    from google import genai
    client = genai.Client(api_key=api_key)
    
    prompt = f"""Você é um médico preceptor de Residência Médica e Revalida.
Analise a questão abaixo e forneça um comentário explicativo objetivo para estudantes de medicina.

PROVA: {questao.get('origem')}
QUESTÃO: {questao.get('numero')}
ENUNCIADO:
{questao.get('enunciado')}

ALTERNATIVAS:
{json.dumps(questao.get('alternativas', {}), ensure_ascii=False)}

GABARITO CONHECIDO: {gabarito_oficial if gabarito_oficial != 'N/A' else 'Determine a alternativa correta.'}

Responda exclusivamente em formato JSON com as seguintes chaves:
"gabarito": "Letra da alternativa correta (A, B, C, D ou E)"
"explicacao": "Comentário médico resumido (máximo 120 palavras), indicando a resposta correta e por que as outras opções estão incorretas."
"""
    modelos_disponiveis = [
        "gemini-3-flash-preview",
        "gemma-4-31b-it",
        "gemma-4-26b-a4b-it",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite"
    ]
    
    for modelo in modelos_disponiveis:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
            )
            texto = response.text.strip()
            if "```json" in texto:
                texto = texto.split("```json")[1].split("```")[0].strip()
            elif "```" in texto:
                texto = texto.split("```")[1].split("```")[0].strip()
            data = json.loads(texto, strict=False)
            exp = data.get("explicacao", "").strip()
            gab = data.get("gabarito", gabarito_oficial).strip()
            time.sleep(3)
            return gab, exp
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                print(f"   [!] Cota do modelo '{modelo}' atingida. Alternando para o próximo modelo...", flush=True)
                time.sleep(2)
                continue
            else:
                print(f"   [!] Erro ao consultar Gemini API ({modelo}): {e}", flush=True)
                break
    return gabarito_oficial, ""


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

# ==============================================================================
# TAXONOMIA MÉDICA DE CLASSIFICAÇÃO (ESPECIALIDADE > TEMA > SUBTEMA)
# ==============================================================================
TAXONOMIA_MEDICA = {
    "Cirurgia Geral": {
        "Trauma e Emergências Cirúrgicas": {
            "Neurotrauma e TCE": ["hematoma extradural", "hematoma subdural", "escala de glasgow", "tce", "herniação", "pupila midriática", "intervalo lúcido", "fratura de crânio"],
            "Trauma Torácico": ["pneumotórax", "hemotórax", "tamponamento cardíaco", "tríade de beck", "drenagem pleural", "toracocentese", "selo d'água", "flail chest", "drenagem de tórax"],
            "Trauma Abdominal e Pélvico": ["fast", "lesão esplênica", "esplenectomia", "trauma hepático", "hematoma subcapsular", "anel pélvico", "trauma renal", "choque hemorrágico"],
            "Queimaduras e Resposta Metabólica": ["parkland", "regra dos nove", "queimadura elétrica", "mioglobinúria", "scq", "queimadura de segundo grau", "área queimada", "enxerto", "retalho"]
        },
        "Abdome Agudo e Parede Abdominal": {
            "Apendicite Aguda": ["apendicite", "sinal de rovsing", "sinal de blumberg", "ponto de mcburney", "apêndice retrocecal", "bacteroides fragilis"],
            "Obstrução Intestinal": ["obstrução intestinal", "bridas", "aderências", "níveis hidroaéreos", "íleo paralítico", "síndrome de ogilvie", "volvo de sigmoide"],
            "Doença Diverticular e Perfurativa": ["diverticulite", "procedimento de hartmann", "abscesso pericolônico", "pneumoperitônio", "linite plástica", "úlcera perfurada"],
            "Hérnias da Parede Abdominal": ["hérnia inguinal", "lichtenstein", "canal inguinal", "hérnia femoral", "hérnia hiatal", "anel inguinal", "tapp", "shouldice"]
        },
        "Vias Biliares, Fígado e Pâncreas": {
            "Doenças da Vesícula e Vias Biliares": ["colelitíase", "colecistite", "sinal de murphy", "colangite", "tríade de charcot", "cpre", "coledocolitíase", "dreno de kehr"],
            "Pancreatite e Neoplasias Digestivas": ["pancreatite aguda", "escore bisap", "critérios de ranson", "pseudocisto", "adenocarcinoma de cabeça de pâncreas", "courvoisier", "hiperplasia nodular focal", "câncer gástrico"]
        },
        "Proctologia, Urologia e Técnica Cirúrgica": {
            "Doenças Orificiais e Anorretais": ["hemorroidas", "trombose hemorroidária", "fístula anorretal", "abscesso perianal", "linha denteada"],
            "Urologia Cirúrgica": ["câncer de bexiga", "uretrocistoscopia", "cálculo ureteral", "litotripsia", "tumor de testículo", "jup", "hiperplasia prostática"],
            "Fios, Cicatrização e Profilaxia": ["fases da cicatrização", "fio de monocryl", "fio de vicryl", "fio de prolene", "cefazolina", "potencialmente contaminada", "cantoplastia"]
        }
    },
    "Clínica Médica": {
        "Cardiologia": {
            "Arritmias e Eletrocardiografia": ["fibrilação atrial", "flutter atrial", "taquicardia ventricular", "cardioversão elétrica", "bloqueio atrioventricular", "bavt", "marcapasso", "onda f"],
            "Síndromes Coronarianas e Valvopatias": ["infarto agudo do miocárdio", "iam com supra", "trombólise", "alteplase", "estenose mitral", "dissecção de aorta", "angina"],
            "Hipertensão e Insuficiência Cardíaca": ["crise hipertensiva", "emergência hipertensiva", "edema de papila", "nitroprussiato", "insuficiência cardíaca", "sacubitril", "fração de ejeção"]
        },
        "Pneumologia": {
            "Doenças Obstrutivas e Asma": ["asma", "salbutamol", "beclometasona", "dpoc", "espirometria", "vef1", "relação vef1/cvf", "broncodilatador"],
            "Doenças Intersticiais e Pleura": ["derrame pleural", "critérios de light", "exsudato", "pneumonia em organização", "boop", "poc", "empiema pleural"]
        },
        "Nefrologia e Distúrbios Ácido-Base": {
            "Injúria Renal e Distúrbios Hidroeletrolíticos": ["doença renal crônica", "clearance de creatinina", "cockcroft-gault", "diálise", "capd", "acidose metabólica", "hipercalemia", "rabdomiólise", "gasometria"],
            "Glomerulopatias": ["síndrome nefrótica", "síndrome nefrítica", "hematúria", "proteinúria", "nefropatia membranosa", "gnpe"]
        },
        "Reumatologia e Doenças Autoimunes": {
            "Colagenoses e Artrites": ["lúpus eritematoso", "nefrite lúpica", "fan", "anti-dna", "artrite reumatoide", "fator reumatoide", "metotrexato", "espondilite anquilosante", "esclerose sistêmica", "fibromialgia", "gota", "ácido úrico"]
        },
        "Infectologia e Toxicologia": {
            "Doenças Infecciosas Sistêmicas": ["tuberculose", "trm-tb", "leptospirose", "síndrome de weil", "hepatite b", "hepatite c", "hiv", "tarv", "leishmaniose", "esporotricose", "actinomicose", "febre maculosa"],
            "Toxíndromes e Emergências": ["botulismo", "síndrome neuroléptica maligna", "delirium tremens", "síndrome de wernicke", "tiamina", "dantrolene", "intoxicação", "dress"]
        }
    },
    "Pediatria": {
        "Neonatologia": {
            "Sala de Parto e Reanimação": ["sala de parto", "clampeamento", "reanimação neonatal", "pressão positiva", "vpp", "apgar", "teste do coraçãozinho", "oximetria de pulso", "eritema tóxico"],
            "Icterícia e Infecções Congênitas": ["icterícia neonatal", "zona de kramer", "fototerapia", "exsanguineotransfusão", "toxoplasmose congênita", "citomegalovirose", "sífilis congênita"]
        },
        "Puericultura e Crescimento": {
            "Alimentação e Desenvolvimento": ["aleitamento materno", "alimentação complementar", "escore-z", "baixo peso para a idade", "marcos motores", "desenvolvimento neuropsicomotor", "m-chat", "autismo"],
            "Imunização (PNI)": ["vacina", "calendário vacinal", "tríplice viral", "tetraviral", "rotavírus", "bcg", "pentavalente", "vip", "vop", "hpv"]
        },
        "Doenças Respiratórias e Infecciosas": {
            "Vias Aéreas e Pulmão": ["bronquiolite", "bva", "vírus sincicial", "crupe", "laringotraqueobronquite", "estridor", "coqueluche", "bordetella", "pneumonia comunitária"],
            "Doenças Exantemáticas e Vasculites": ["exantema súbito", "roséola", "doença de kawasaki", "aneurisma coronariano", "mão-pé-boca", "púrpura de henoch-schönlein", "sim-p"]
        },
        "Gastroenterologia e Emergências Pediátricas": {
            "Trato Gastrointestinal": ["estenose hipertrófica de piloro", "oliva pilórica", "invaginação intestinal", "intussuscepção", "doença de hirschsprung", "megacólon", "diarreia aguda", "desidratação", "sro", "ascaridíase"],
            "Emergências e Ortopedia Infantil": ["síndrome hemolítico-urêmica", "shu", "síndrome do bebê sacudido", "shaken baby", "convulsão febril", "mal epiléptico", "osgood-schlatter", "epifisiólise", "artrite séptica do quadril"]
        }
    },
    "Ginecologia e Obstetrícia": {
        "Obstetrícia": {
            "Assistência Pré-Natal e Fisiologia": ["pré-natal", "regra de naegele", "altura uterina", "manobras de leopold", "apresentação cefálica", "vitalidade fetal", "cardiotocografia", "dopplervelocimetria", "ciur", "polidrâmnio"],
            "Síndromes Hipertensivas e Diabetes": ["pré-eclâmpsia", "eclâmpsia", "sulfato de magnésio", "gluconato de cálcio", "síndrome hellp", "diabetes gestacional", "totg", "overt diabetes"],
            "Sangramentos Gestacionais e Parto": ["descolamento prematuro de placenta", "dpp", "placenta prévia", "abortamento", "gravidez ectópica", "metotrexato", "distócia de espáduas", "manobra de mcroberts", "partograma", "atonia uterina", "endometrite", "síndrome de sheehan", "aloimunização"]
        },
        "Ginecologia Geral e Climatério": {
            "Endocrinologia Ginecológica": ["síndrome dos ovários policísticos", "sop", "amenorreia", "síndrome de rokitansky", "insuficiência ovariana prematura", "galactorreia", "prolactina", "anticoncepcional"],
            "Climatério e Patologia Benigna": ["climatério", "fogachos", "terapia de reposição hormonal", "atrofia vulvovaginal", "miomatose", "pólipo endometrial", "endometriose", "torção ovariana", "cisto de ovário"]
        },
        "Infectologia Ginecológica e Oncologia": {
            "Vulvovaginites e ISTs": ["vaginose bacteriana", "clue-cells", "tricomoníase", "candidíase", "herpes genital", "doença inflamatória pélvica", "dip", "hidradenite"],
            "Oncologia Ginecológica e Mastologia": ["câncer de colo de útero", "papanicolau", "citopatológico", "hsil", "lsil", "ascus", "colposcopia", "ezt", "biópsia de colo", "câncer de mama", "bi-rads", "linfonodo sentinela", "câncer de vulva"]
        }
    },
    "Medicina Preventiva e Social / MFC": {
        "Epidemiologia e Bioestatística": {
            "Indicadores e Medidas de Saúde": ["incidência", "prevalência", "mortalidade infantil", "mortalidade proporcional", "transição demográfica", "transição epidemiológica", "diagrama de controle"],
            "Desenhos de Estudo e Diagnóstico": ["estudo de coorte", "caso-controle", "ensaio clínico", "estudo transversal", "sensibilidade", "especificidade", "valor preditivo positivo", "vpp", "razão de verossimilhança", "risco relativo", "odds ratio"]
        },
        "Atenção Primária e Sistemas de Saúde": {
            "Políticas de Saúde e SUS": ["pnab", "estratégia saúde da família", "esf", "territorialização", "adstrição", "resolubilidade", "atributos da aps", "beveridge", "bismarck", "lei 8080", "lei 8142", "controle social", "conselhos de saúde", "dsei", "saúde indígena", "pnaisp"],
            "Abordagem Comunitária e Familiar": ["método clínico centrado na pessoa", "mccp", "genograma", "projeto terapêutico singular", "pts", "rcop", "soap", "prevenção quaternária", "educação popular em saúde", "entrevista motivacional", "cuidados paliativos", "escala de zarit", "ivcf-20"]
        },
        "Vigilância em Saúde e Saúde do Trabalhador": {
            "Vigilância Epidemiológica e Ambiental": ["notificação compulsória", "sinan", "vigilância epidemiológica", "srag", "surto", "esquistossomose", "febre amarela", "monkeypox", "mpox"],
            "Saúde do Trabalhador e Ética": ["acidente de trabalho", "cat", "doença profissional", "silicose", "saturnismo", "intoxicação por mercúrio", "prontuário médico", "código de ética médica", "sigilo médico", "autonomia", "beneficência"]
        }
    }
}


def classificar_questao(texto_completo):
    """Classifica o enunciado/alternativas por frequência de termos-chave."""
    texto_lower = texto_completo.lower()
    melhor_match = ("Outros / Não Categorizados", "Geral", "Diversos")
    maior_score = 0

    for especialidade, temas in TAXONOMIA_MEDICA.items():
        for tema, subtemas in temas.items():
            for subtema, keywords in subtemas.items():
                score = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', texto_lower))
                if score > maior_score:
                    maior_score = score
                    melhor_match = (especialidade, tema, subtema)

    return melhor_match



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


def formatar_texto_fluido(texto, modo_html=True):
    """
    Remove quebras de linha artificiais provocadas pelas colunas estreitas dos PDFs A4 do INEP/ENARE.
    Une frases contínuas e preserva parágrafos reais.
    """
    if not texto:
        return ""
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


def exportar_caderno_markdown(banco_questoes, caminho_saida: Path, cache_explicacoes: dict = None, tem_api_key: bool = False):
    """Gera um arquivo Markdown organizado hierarquicamente para estudo com respostas colapsáveis."""
    if cache_explicacoes is None:
        cache_explicacoes = {}
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("# CADERNO DE QUESTÕES CATEGORIZADAS PARA ESTUDO\n")
        f.write("> **Material de Simulado e Prática de Residência Médica / Revalidação com Gabarito e Comentários**\n\n")
        f.write("---\n\n")
        
        for esp in sorted(banco_questoes.keys()):
            f.write(f"# 📂 {esp.upper()}\n\n")
            for tema in sorted(banco_questoes[esp].keys()):
                f.write(f"## 📌 Tema: {tema}\n\n")
                for subtema in sorted(banco_questoes[esp][tema].keys()):
                    lista_q = banco_questoes[esp][tema][subtema]
                    f.write(f"### 🔖 Subtema: {subtema} ({len(lista_q)} questões)\n\n")
                    
                    for q in lista_q:
                        q_key = f"{q['origem']}_{q['numero']}"
                        dados_cache = cache_explicacoes.get(q_key, {})
                        gab = q.get("gabarito", "N/A")
                        if gab == "N/A" and dados_cache.get("gabarito"):
                            gab = dados_cache.get("gabarito")
                            
                        exp = dados_cache.get("explicacao")
                        if not exp:
                            if tem_api_key:
                                if gab != "N/A":
                                    exp = f"Gabarito oficial extraído do PDF da prova: **{gab}**. (O comentário detalhado por IA para esta questão está sendo processado)."
                                else:
                                    exp = "Gabarito não fornecido no PDF. (O comentário por IA para esta questão está sendo processado)."
                            else:
                                if gab != "N/A":
                                    exp = f"Gabarito oficial extraído do PDF da prova: **{gab}**. (Configure sua GEMINI_API_KEY no arquivo .env para gerar justificativas clínicas por IA)."
                                else:
                                    exp = "Gabarito não fornecido no PDF. (Configure sua GEMINI_API_KEY no arquivo .env para gerar justificativas clínicas por IA)."
                        
                        f.write(f"#### **[{q['origem']} | Questão {q['numero']}]**\n\n")
                        enunc_md = formatar_texto_fluido(q['enunciado'], modo_html=False)
                        f.write(f"{enunc_md}\n\n")
                        
                        imgs = q.get("imagens") or ([q.get("imagem")] if q.get("imagem") else [])
                        if imgs:
                            for img_path in imgs:
                                f.write(f"![Figura da Questão]({img_path})\n\n")
                        
                        if q['alternativas']:
                            for letra, alt in sorted(q['alternativas'].items()):
                                f.write(f"- [ ] **({letra})** {alt}\n")
                            f.write("\n")
                            
                        f.write("<details>\n")
                        f.write(f"<summary><b>👁️ Ver Resposta e Comentário (Gabarito: {gab})</b></summary>\n\n")
                        f.write(f"> **Gabarito Oficial:** Alternativa **({gab})**\n>\n")
                        f.write(f"> **Comentário Médica:** {exp}\n")
                        f.write("</details>\n\n")
                        f.write("---\n\n")


def exportar_caderno_html(banco_questoes, caminho_saida: Path, cache_explicacoes: dict = None, tem_api_key: bool = False):
    """Gera um simulado interativo em HTML com gabarito oficial, comentários por IA e botão 'Ver Resposta'."""
    if cache_explicacoes is None:
        cache_explicacoes = {}
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    
    total_questoes_com_alt = 0
    for esp in banco_questoes:
        for tema in banco_questoes[esp]:
            for subtema in banco_questoes[esp][tema]:
                for q in banco_questoes[esp][tema][subtema]:
                    if q['alternativas']:
                        total_questoes_com_alt += 1

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Caderno de Questões - Simulado de Estudos Interativo</title>
<style>
    :root {{
        --primary: #1e40af;
        --primary-light: #3b82f6;
        --bg-main: #f8fafc;
        --card-bg: #ffffff;
        --alt-bg: #f8fafc;
        --alt-hover-bg: #f1f5f9;
        --alt-hover-border: #cbd5e1;
        --text-main: #0f172a;
        --text-enunciado: #1e293b;
        --text-muted: #64748b;
        --border-color: #e2e8f0;
        --accent: #10b981;
        --topbar-bg: rgba(255, 255, 255, 0.95);
        --tag-bg: #f1f5f9;
        --tag-text: #475569;
        --hero-bg: #ffffff;
        --hero-h1: #1e3a8a;
        --badge-persistence-bg: #ecfdf5;
        --badge-persistence-text: #065f46;
        --badge-persistence-border: #a7f3d0;
        --tema-bg: #e0f2fe;
        --tema-text: #0369a1;
        --subtema-text: #475569;
        --img-container-bg: #f8fafc;
        --box-bg: #f0f9ff;
        --box-border: #bae6fd;
        --box-text: #0c4a6e;
        --btn-resp-bg: #eff6ff;
        --btn-resp-text: #1d4ed8;
        --btn-resp-border: #bfdbfe;
        --btn-reset-bg: #f1f5f9;
        --btn-reset-border: #cbd5e1;
    }}
    [data-theme="dark"] {{
        --primary: #60a5fa;
        --primary-light: #93c5fd;
        --bg-main: #0b0f19; /* Fundo geral cinza ultra escuro */
        --card-bg: #1e293b; /* Container da questão: Cinza escuro elegante */
        --alt-bg: #0f172a;  /* Alternativas: Tom de cinza diferente para contraste perfeito! */
        --alt-hover-bg: #1e293b;
        --alt-hover-border: #475569;
        --text-main: #ffffff; /* Letras 100% brancas! */
        --text-enunciado: #ffffff; /* Enunciado branco limpo! */
        --text-muted: #94a3b8;
        --border-color: #334155;
        --accent: #34d399;
        --topbar-bg: rgba(15, 23, 42, 0.95);
        --tag-bg: #334155;
        --tag-text: #cbd5e1;
        --hero-bg: #1e293b;
        --hero-h1: #93c5fd;
        --badge-persistence-bg: #064e3b;
        --badge-persistence-text: #a7f3d0;
        --badge-persistence-border: #047857;
        --tema-bg: #0369a1;
        --tema-text: #e0f2fe;
        --subtema-text: #94a3b8;
        --img-container-bg: #0f172a;
        --box-bg: #0f172a;
        --box-border: #0284c7;
        --box-text: #e0f2fe;
        --btn-resp-bg: #1e3a8a;
        --btn-resp-text: #93c5fd;
        --btn-resp-border: #2563eb;
        --btn-reset-bg: #334155;
        --btn-reset-border: #475569;
    }}
    * {{ box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background: var(--bg-main);
        color: var(--text-main);
        margin: 0;
        padding: 0 0 60px 0;
        line-height: 1.6;
        transition: background-color 0.3s ease, color 0.3s ease;
    }}
    .top-bar {{
        position: sticky;
        top: 0;
        background: var(--topbar-bg);
        backdrop-filter: blur(8px);
        border-bottom: 1px solid var(--border-color);
        padding: 12px 24px;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        transition: background-color 0.3s ease, border-color 0.3s ease;
    }}
    .btn-theme-toggle {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        width: 38px;
        height: 38px;
        padding: 0;
        border-radius: 50%;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }}
    .btn-theme-toggle:hover {{
        border-color: var(--primary-light);
        transform: translateY(-2px) scale(1.08);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }}
    .theme-icon-img {{
        width: 22px;
        height: 22px;
        object-fit: contain;
        transition: transform 0.3s ease;
    }}
    .btn-theme-toggle:hover .theme-icon-img {{
        transform: rotate(15deg);
    }}
    .progress-container {{
        flex: 1;
        max-width: 450px;
    }}
    .progress-labels {{
        display: flex;
        justify-content: space-between;
        font-size: 13px;
        font-weight: 600;
        color: var(--text-muted);
        margin-bottom: 4px;
    }}
    .progress-bar-bg {{
        background: var(--border-color);
        border-radius: 999px;
        height: 10px;
        overflow: hidden;
    }}
    .progress-bar-fill {{
        background: linear-gradient(90deg, var(--primary-light), var(--accent));
        height: 100%;
        width: 0%;
        transition: width 0.3s ease;
    }}
    .btn-reset {{
        background: var(--btn-reset-bg);
        color: #ef4444;
        border: 1px solid var(--btn-reset-border);
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 600;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
    }}
    .btn-reset:hover {{
        background: #fee2e2;
        border-color: #fca5a5;
        color: #dc2626;
    }}
    .container {{
        max-width: 920px;
        margin: 24px auto;
        padding: 0 16px;
    }}
    .header-hero {{
        text-align: center;
        background: var(--hero-bg);
        padding: 30px 20px;
        border-radius: 12px;
        border: 1px solid var(--border-color);
        margin-bottom: 24px;
        transition: background-color 0.3s ease;
    }}
    h1 {{
        color: var(--hero-h1);
        margin: 0 0 8px 0;
        font-size: 26px;
    }}
    .header-hero p {{
        margin: 0;
        color: var(--text-muted);
        font-size: 15px;
    }}
    .badge-persistence {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: var(--badge-persistence-bg);
        color: var(--badge-persistence-text);
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 999px;
        margin-top: 10px;
        border: 1px solid var(--badge-persistence-border);
    }}
    .especialidade {{
        background: linear-gradient(135deg, #1e3a8a, #2563eb);
        color: white;
        padding: 14px 20px;
        border-radius: 10px;
        margin-top: 36px;
        font-size: 20px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .tema {{
        background: var(--tema-bg);
        color: var(--tema-text);
        padding: 10px 16px;
        border-left: 5px solid var(--primary-light);
        margin-top: 24px;
        border-radius: 4px;
        font-size: 17px;
        font-weight: 700;
    }}
    .subtema {{
        color: var(--subtema-text);
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 18px;
        margin-bottom: 12px;
        font-weight: 700;
    }}
    .card-questao {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 18px;
        transition: background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.2s;
    }}
    .card-questao.answered {{
        border-left: 5px solid var(--accent);
    }}
    .card-questao:hover {{
        box-shadow: 0 4px 14px rgba(0,0,0,0.12);
    }}
    .tag-origem {{
        background: var(--tag-bg);
        color: var(--tag-text);
        font-size: 12px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        display: inline-block;
        margin-bottom: 12px;
    }}
    .enunciado {{
        font-size: 15px;
        margin-bottom: 16px;
        color: var(--text-enunciado);
        text-align: justify;
        line-height: 1.65;
    }}
    .alternativas-container {{
        display: flex;
        flex-direction: column;
        gap: 8px;
    }}
    .alternativa {{
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 10px 14px;
        border-radius: 8px;
        background: var(--alt-bg);
        border: 1px solid var(--border-color);
        color: var(--text-main);
        cursor: pointer;
        transition: all 0.15s ease;
        font-size: 14.5px;
    }}
    .alternativa:hover {{
        background: var(--alt-hover-bg);
        border-color: var(--alt-hover-border);
    }}
    .alternativa input {{
        margin-top: 4px;
        cursor: pointer;
        width: 17px;
        height: 17px;
    }}
    .alternativa.selected {{
        background: #eff6ff !important;
        border-color: #3b82f6 !important;
        color: #1e40af !important;
        font-weight: 500;
    }}
    [data-theme="dark"] .alternativa.selected {{
        background: #1e3a8a !important;
        border-color: #3b82f6 !important;
        color: #ffffff !important;
    }}
    .alternativa.correct {{
        background: #dcfce7 !important;
        border-color: #16a34a !important;
        color: #14532d !important;
        font-weight: 600;
    }}
    [data-theme="dark"] .alternativa.correct {{
        background: #064e3b !important;
        border-color: #10b981 !important;
        color: #d1fae5 !important;
    }}
    .alternativa.incorrect {{
        background: #fee2e2 !important;
        border-color: #dc2626 !important;
        color: #7f1d1d !important;
    }}
    [data-theme="dark"] .alternativa.incorrect {{
        background: #7f1d1d !important;
        border-color: #ef4444 !important;
        color: #fee2e2 !important;
    }}
    .questao-imagem-container {{
        text-align: center;
        margin: 16px 0;
        background: var(--img-container-bg);
        padding: 10px;
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }}
    .img-questao {{
        max-width: 100%;
        max-height: 480px;
        border-radius: 6px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.12);
        display: inline-block;
    }}
    .btn-resposta {{
        margin-top: 14px;
        background: var(--btn-resp-bg);
        color: var(--btn-resp-text);
        border: 1px solid var(--btn-resp-border);
        padding: 8px 16px;
        font-size: 13.5px;
        font-weight: 600;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}
    .btn-resposta:hover {{
        background: var(--primary-light);
        color: #ffffff;
    }}
    .gabarito-box {{
        margin-top: 14px;
        background: var(--box-bg);
        border: 1px solid var(--box-border);
        border-radius: 8px;
        padding: 16px;
        color: var(--box-text);
        animation: fadeIn 0.2s ease-in-out;
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(-4px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .badge-gabarito {{
        display: inline-block;
        background: #0284c7;
        color: #ffffff;
        font-weight: 700;
        font-size: 13px;
        padding: 4px 12px;
        border-radius: 6px;
        margin-bottom: 10px;
    }}
    .explicacao-texto {{
        font-size: 14px;
        color: var(--box-text);
        line-height: 1.65;
    }}
    [data-theme="dark"] .gabarito-box {{
        background: #0f172a !important;
        border-color: #0284c7 !important;
        color: #f8fafc !important;
    }}
    [data-theme="dark"] .explicacao-texto {{
        color: #f8fafc !important;
    }}
    [data-theme="dark"] .theme-icon-img {{
        filter: brightness(0) invert(0.9);
    }}
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(-4px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .badge-gabarito {{
        display: inline-block;
        background: #0284c7;
        color: #ffffff;
        font-weight: 700;
        font-size: 13px;
        padding: 4px 12px;
        border-radius: 6px;
        margin-bottom: 10px;
    }}
    .explicacao-texto {{
        font-size: 14px;
        color: #0c4a6e;
        line-height: 1.65;
    }}
    /* Banner Ko-fi de Doações */
    .kofi-banner {{
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 70%, #ff5e5b 100%);
        border-radius: 16px;
        padding: 22px 28px;
        margin-bottom: 28px;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.25), 0 12px 30px -5px rgba(255, 94, 91, 0.35), 0 6px 15px -5px rgba(30, 27, 75, 0.4);
        border: none;
        position: relative;
        overflow: hidden;
        transform: translateZ(0);
        -webkit-mask-image: -webkit-radial-gradient(white, black);
        isolation: isolate;
    }}
    .kofi-banner::before {{
        content: '';
        position: absolute;
        top: -60%;
        left: -60%;
        width: 220%;
        height: 220%;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.12) 0%, transparent 60%);
        animation: rotateGlow 14s linear infinite;
        pointer-events: none;
    }}
    .kofi-banner::after {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border-radius: 16px;
        background: linear-gradient(115deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.04) 35%, transparent 65%);
        pointer-events: none;
    }}
    @keyframes rotateGlow {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}
    .kofi-content {{
        position: relative;
        z-index: 2;
        max-width: 680px;
    }}
    .kofi-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 19px;
        font-weight: 800;
        margin-bottom: 6px;
        letter-spacing: -0.3px;
        color: #ffffff;
    }}
    .kofi-badge-img {{
        width: 34px;
        height: 34px;
        object-fit: contain;
        display: inline-block;
        vertical-align: middle;
        filter: drop-shadow(0 2px 5px rgba(0,0,0,0.3));
    }}
    .kofi-desc {{
        font-size: 13.5px;
        color: rgba(255, 255, 255, 0.92);
        line-height: 1.5;
    }}
    .kofi-btn-container {{
        position: relative;
        z-index: 2;
        flex-shrink: 0;
    }}
    .kofi-btn {{
        display: inline-flex;
        align-items: center;
        gap: 10px;
        background: #ff5e5b;
        color: #ffffff !important;
        font-size: 15px;
        font-weight: 800;
        padding: 13px 24px;
        border-radius: 12px;
        text-decoration: none;
        box-shadow: 0 4px 15px rgba(255, 94, 91, 0.5);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border: 2px solid rgba(255, 255, 255, 0.35);
        cursor: pointer;
    }}
    .kofi-btn:hover {{
        background: #ff4743;
        transform: translateY(-3px) scale(1.03);
        box-shadow: 0 8px 25px rgba(255, 94, 91, 0.75);
        color: #ffffff !important;
    }}
    .kofi-btn:active {{
        transform: translateY(-1px) scale(0.99);
    }}
    .kofi-icon-img {{
        width: 26px;
        height: 26px;
        object-fit: contain;
        display: inline-block;
        vertical-align: middle;
        animation: kofiJump 1.6s cubic-bezier(0.28, 0.84, 0.42, 1) infinite;
    }}
    @keyframes kofiJump {{
        0%, 100% {{
            transform: translateY(0) scale(1, 1);
        }}
        20% {{
            transform: translateY(0) scale(1.15, 0.85);
        }}
        45% {{
            transform: translateY(-9px) scale(0.92, 1.08);
        }}
        60% {{
            transform: translateY(0) scale(1.05, 0.95);
        }}
        75% {{
            transform: translateY(-3px) scale(0.98, 1.02);
        }}
    }}
    @media (max-width: 768px) {{
        .kofi-banner {{
            flex-direction: column;
            text-align: center;
            padding: 18px 20px;
        }}
        .kofi-header {{
            justify-content: center;
        }}
        .kofi-btn {{
            width: 100%;
            justify-content: center;
        }}
    }}
</style>
</head>
<body>

<div class="top-bar">
    <div style="font-weight: 700; font-size: 15px; color: #1e3a8a;">
        🩺 Simulado Residência Médica
    </div>
    <div class="progress-container">
        <div class="progress-labels">
            <span>Progresso:</span>
            <span id="progress-text">0 de {total_questoes_com_alt} respondidas (0%)</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" id="progress-bar"></div>
        </div>
    </div>
    <div style="display: flex; gap: 8px; align-items: center;">
        <button class="btn-theme-toggle" id="theme-toggle-btn" onclick="toggleTheme()" title="Alternar Modo Escuro / Modo Claro">
            <img src="src/dark-mode.png" alt="Alternar Tema" id="theme-icon-img" class="theme-icon-img">
        </button>
        <button class="btn-reset" onclick="limparRespostas()">✖ Limpar Respostas</button>
    </div>
</div>

<div class="container">
    <div class="header-hero">
        <h1>Caderno de Questões - Simulado Interativo</h1>
        <p>Questões oficiais de bancas categorizadas com Gabarito Oficial e Explicações Médicas.</p>
        <div class="badge-persistence">
            <span>💾</span> Respostas salvas automaticamente no navegador
        </div>
    </div>

    <!-- Container Ko-fi de Doações -->
    <div class="kofi-banner">
        <div class="kofi-content">
            <div class="kofi-header">
                <img src="src/ffbe___cloud_strife_gif_3_by_zerolympiustrife_dbuxzfm.gif" alt="FFBE Icon" class="kofi-badge-img">
                <span>Gostou do Simulado? Me apoie!</span>
            </div>
            <div class="kofi-desc">
                Este caderno com 1.500+ questões oficiais, imagens médicas curadas e justificativas clínicas por IA é mantido de forma 100% gratuita. Se este material está te ajudando nos estudos, considere me pagar um café no Ko-fi!
            </div>
        </div>
        <div class="kofi-btn-container">
            <a href="https://ko-fi.com" target="_blank" rel="noopener noreferrer" class="kofi-btn">
                <img src="src/logomarkLogo.png" alt="Ko-fi Logo" class="kofi-icon-img">
                <span>Pagar um Café no Ko-fi</span>
            </a>
        </div>
    </div>
"""

    for esp in sorted(banco_questoes.keys()):
        html += f"<div class='especialidade'>📂 {esp.upper()}</div>\n"
        for tema in sorted(banco_questoes[esp].keys()):
            html += f"<div class='tema'>📌 {tema}</div>\n"
            for subtema in sorted(banco_questoes[esp][tema].keys()):
                lista_q = banco_questoes[esp][tema][subtema]
                html += f"<div class='subtema'>🔖 {subtema} ({len(lista_q)} questões)</div>\n"
                
                for q in lista_q:
                    q_id = f"q_{q['origem']}_{q['numero']}".replace(" ", "_").replace("-", "_").replace(".", "_").replace("(", "_").replace(")", "_")
                    q_key = f"{q['origem']}_{q['numero']}"
                    dados_cache = cache_explicacoes.get(q_key, {})
                    gab = q.get("gabarito", "N/A")
                    if gab == "N/A" and dados_cache.get("gabarito"):
                        gab = dados_cache.get("gabarito")
                        
                    exp = dados_cache.get("explicacao")
                    if not exp:
                        if tem_api_key:
                            if gab != "N/A":
                                exp = f"Gabarito oficial extraído do PDF da prova: <strong>{gab}</strong>. (O comentário detalhado por IA para esta questão está sendo processado)."
                            else:
                                exp = "Gabarito não fornecido no PDF da prova. (O comentário por IA para esta questão está sendo processado)."
                        else:
                            if gab != "N/A":
                                exp = f"Gabarito oficial extraído do PDF da prova: <strong>{gab}</strong>. (Configure sua GEMINI_API_KEY no arquivo .env para gerar comentários detalhados por IA)."
                            else:
                                exp = "Gabarito não fornecido no PDF da prova. (Configure sua GEMINI_API_KEY no arquivo .env para gerar gabarito e explicação por IA)."

                    enunc_html = formatar_texto_fluido(q['enunciado'], modo_html=True)
                    html += f"<div class='card-questao' id='card_{q_id}'>\n"
                    html += f"<span class='tag-origem'>{q['origem']} | Questão {q['numero']}</span>\n"
                    html += f"<div class='enunciado'>{enunc_html}</div>\n"
                    
                    imgs = q.get("imagens") or ([q.get("imagem")] if q.get("imagem") else [])
                    if imgs:
                        html += f"<div class='questao-imagem-container'>\n"
                        for img_src in imgs:
                            num_q = q["numero"]
                            html += f"  <img src='{img_src}' alt='Figura da Questão {num_q}' class='img-questao'>\n"
                        html += f"</div>\n"
                    
                    if q['alternativas']:
                        html += f"<div class='alternativas-container'>\n"
                        for letra, alt in sorted(q['alternativas'].items()):
                            alt_html = formatar_texto_fluido(alt, modo_html=False)
                            html += f"<label class='alternativa' id='label_{q_id}_{letra}'>"
                            html += f"<input type='radio' name='{q_id}' value='{letra}' data-gabarito='{gab}' onchange='salvarResposta(\"{q_id}\", \"{letra}\", \"{gab}\")'>"
                            html += f"<span><strong>({letra})</strong> {alt_html}</span></label>\n"
                        html += f"</div>\n"
                    
                    if isinstance(exp, list):
                        exp_html = "<br>".join(str(item) for item in exp)
                    elif isinstance(exp, str):
                        exp_html = exp.replace(chr(10), '<br>')
                    else:
                        exp_html = str(exp or "")
                        
                    html += f"<button class='btn-resposta' onclick='toggleResposta(\"{q_id}\")'>✦ Ver Resposta e Comentário</button>\n"
                    html += f"<div class='gabarito-box' id='box_{q_id}' style='display: none;'>\n"
                    html += f"    <div class='badge-gabarito'>Gabarito Oficial: Alternativa ({gab})</div>\n"
                    html += f"    <div class='explicacao-texto'>{exp_html}</div>\n"
                    html += f"</div>\n"
                    
                    html += f"</div>\n"

    html += f"""
</div>

<script>
const TOTAL_QUESTOES = {total_questoes_com_alt};
const STORAGE_KEY = 'simulado_medicina_respostas_v1';

function atualizarBarra(qtd) {{
    const txt = document.getElementById('progress-text');
    const bar = document.getElementById('progress-bar');
    const pct = TOTAL_QUESTOES > 0 ? Math.round((qtd / TOTAL_QUESTOES) * 100) : 0;
    
    if (txt) {{
        txt.textContent = `${{qtd}} de ${{TOTAL_QUESTOES}} respondidas (${{pct}}%)`;
    }}
    if (bar) {{
        bar.style.width = `${{pct}}%`;
    }}
}}

function toggleResposta(qId) {{
    const box = document.getElementById('box_' + qId);
    if (box) {{
        const isHidden = (box.style.display === 'none' || box.style.display === '');
        box.style.display = isHidden ? 'block' : 'none';
        if (isHidden) {{
            revelarFeedbackGabarito(qId);
        }}
    }}
}}

function carregarRespostas() {{
    const dados = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}');
    let respondidas = 0;

    for (const [qId, valor] of Object.entries(dados)) {{
        const radio = document.querySelector(`input[name="${{qId}}"][value="${{valor}}"]`);
        if (radio) {{
            radio.checked = true;
            respondidas++;
            const gabarito = radio.getAttribute('data-gabarito');
            atualizarEstiloQuestao(qId, valor, gabarito);
        }}
    }}
    atualizarBarra(respondidas);
}}

function salvarResposta(qId, valor, gabarito) {{
    const dados = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}');
    dados[qId] = valor;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(dados));
    
    atualizarEstiloQuestao(qId, valor, gabarito);
    atualizarBarra(Object.keys(dados).length);
}}

function atualizarEstiloQuestao(qId, valor, gabarito) {{
    const card = document.getElementById('card_' + qId);
    if (card) card.classList.add('answered');
    
    document.querySelectorAll(`input[name="${{qId}}"]`).forEach(r => {{
        const lbl = document.getElementById(`label_${{qId}}_${{r.value}}`);
        if (lbl) lbl.classList.remove('selected', 'correct', 'incorrect');
    }});

    const labelSelecionada = document.getElementById(`label_${{qId}}_${{valor}}`);
    if (labelSelecionada) labelSelecionada.classList.add('selected');

    const box = document.getElementById('box_' + qId);
    if (box && box.style.display === 'block') {{
        revelarFeedbackGabarito(qId);
    }}
}}

function revelarFeedbackGabarito(qId) {{
    const radioSelecionado = document.querySelector(`input[name="${{qId}}"]:checked`);
    const valor = radioSelecionado ? radioSelecionado.value : null;
    const radioQualquer = document.querySelector(`input[name="${{qId}}"]`);
    const gabarito = radioQualquer ? radioQualquer.getAttribute('data-gabarito') : null;

    if (!gabarito || gabarito === 'N/A' || gabarito === 'ANULADA') return;

    const labelCorreta = document.getElementById(`label_${{qId}}_${{gabarito}}`);
    if (labelCorreta) labelCorreta.classList.add('correct');

    if (valor) {{
        const labelSelecionada = document.getElementById(`label_${{qId}}_${{valor}}`);
        if (valor === gabarito) {{
            if (labelSelecionada) labelSelecionada.classList.add('correct');
        }} else {{
            if (labelSelecionada) labelSelecionada.classList.add('incorrect');
        }}
    }}
}}

function limparRespostas() {{
    if (confirm('Tem certeza que deseja apagar todas as respostas e recomeçar o simulado?')) {{
        localStorage.removeItem(STORAGE_KEY);
        document.querySelectorAll('input[type="radio"]').forEach(r => r.checked = false);
        document.querySelectorAll('.card-questao').forEach(c => c.classList.remove('answered'));
        document.querySelectorAll('.alternativa').forEach(l => l.classList.remove('selected', 'correct', 'incorrect'));
        document.querySelectorAll('.gabarito-box').forEach(b => b.style.display = 'none');
        atualizarBarra(0);
    }}
}}

// Lógica de Alternância de Tema (Modo Escuro / Modo Claro)
function initTheme() {{
    const savedTheme = localStorage.getItem('simulado_theme_preference') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    setTheme(savedTheme);
}}

function setTheme(theme) {{
    const img = document.getElementById('theme-icon-img');
    if (theme === 'dark') {{
        document.documentElement.setAttribute('data-theme', 'dark');
        if (img) {{
            img.src = 'src/icons8-modo-claro-78.png';
            img.alt = 'Alternar para Modo Claro';
        }}
    }} else {{
        document.documentElement.removeAttribute('data-theme');
        if (img) {{
            img.src = 'src/dark-mode.png';
            img.alt = 'Alternar para Modo Escuro';
        }}
    }}
    localStorage.setItem('simulado_theme_preference', theme);
}}

function toggleTheme() {{
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    setTheme(isDark ? 'light' : 'dark');
}}

// Inicializa o tema e carrega as respostas ao abrir a página
initTheme();
window.addEventListener('DOMContentLoaded', carregarRespostas);
</script>

</body>
</html>
"""
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    BASE_DIR = Path(__file__).resolve().parent
    pasta_provas = BASE_DIR / "provas"
    pasta_saida = BASE_DIR / "saida"
    pasta_saida.mkdir(parents=True, exist_ok=True)
    pasta_provas.mkdir(parents=True, exist_ok=True)
    
    caminho_cache = pasta_saida / "cache_explicacoes.json"
    cache_explicacoes = carregar_cache_explicacoes(caminho_cache)
    
    api_key = os.environ.get("GEMINI_API_KEY")
    # Tenta carregar .env local se existir
    env_file = BASE_DIR / ".env"
    if not api_key and env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass

    arquivos_pdf = [f for f in pasta_provas.iterdir() if f.suffix.lower() == ".pdf"]
    
    if not arquivos_pdf:
        print(f"[!] Nenhum arquivo PDF encontrado na pasta '{pasta_provas.resolve()}'.")
        print("    Coloque seus PDFs na pasta 'provas' e execute o script novamente.")
        return

    print(f"[*] Encontrados {len(arquivos_pdf)} arquivos PDF. Iniciando extração, gabaritos e categorização...\n")
    
    total_questoes = 0
    banco_hierarquico = {}

    for caminho_pdf in arquivos_pdf:
        nome_arq = caminho_pdf.name
        nome_origem = nome_arq.replace(".pdf", "")
        print(f"-> Processando: {nome_arq}...")
        
        # Extrai gabarito oficial do PDF (se presente)
        gabarito_map = extrair_gabarito_pdf(caminho_pdf)
        if gabarito_map:
            print(f"   ✓ Gabarito oficial extraído do PDF ({len(gabarito_map)} respostas).")
            
        texto = extrair_texto_pdf(caminho_pdf)
        questoes = extrair_questoes_do_texto(texto, nome_arq)
        
        # Vincula o gabarito oficial a cada questão
        for q in questoes:
            q["gabarito"] = gabarito_map.get(q["numero"], "N/A")
            q_key = f"{nome_origem}_{q['numero']}"
            
            # Se tiver API Key e a explicação ainda não estiver em cache ou estiver vazia
            exp_existente = cache_explicacoes.get(q_key, {}).get("explicacao")
            if api_key and not exp_existente:
                print(f"   [IA] Gerando explicação via Gemini para {q_key}...")
                gab_gemini, exp_gemini = gerar_explicacao_gemini(q, q["gabarito"], api_key)
                if exp_gemini:
                    cache_explicacoes[q_key] = {
                        "gabarito": gab_gemini if q["gabarito"] == "N/A" else q["gabarito"],
                        "explicacao": exp_gemini
                    }
                    salvar_cache_explicacoes(caminho_cache, cache_explicacoes)

        print(f"   ✓ {len(questoes)} questões extraídas e processadas.")
        total_questoes += len(questoes)
        
        for q in questoes:
            esp = q["especialidade"]
            tema = q["tema"]
            subtema = q["subtema"]
            
            if esp not in banco_hierarquico:
                banco_hierarquico[esp] = {}
            if tema not in banco_hierarquico[esp]:
                banco_hierarquico[esp][tema] = {}
            if subtema not in banco_hierarquico[esp][tema]:
                banco_hierarquico[esp][tema][subtema] = []
                
            banco_hierarquico[esp][tema][subtema].append(q)

    # Caminhos finais de saída
    caminho_md = pasta_saida / "caderno_de_questoes_estudo.md"
    caminho_html = pasta_saida / "caderno_interativo.html"
    
    print("\n[*] Gerando arquivos finais de estudo...")
    exportar_caderno_markdown(banco_hierarquico, caminho_md, cache_explicacoes, tem_api_key=bool(api_key))
    exportar_caderno_html(banco_hierarquico, caminho_html, cache_explicacoes, tem_api_key=bool(api_key))

    print("\n========================================================")
    print(f"[SUCESSO] Processamento concluído com êxito!")
    print(f"Total de questões organizadas: {total_questoes}")
    print(f"1. Caderno em Markdown: '{caminho_md.resolve()}'")
    print(f"2. Simulado Interativo (HTML): '{caminho_html.resolve()}'")
    print("========================================================")


if __name__ == "__main__":
    main()
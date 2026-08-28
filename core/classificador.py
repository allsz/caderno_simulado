import re
import unicodedata

def normalizar_texto(texto):
    """Remove acentos, caracteres especiais e converte para minúsculas."""
    if not texto:
        return ""
    texto = texto.replace('\ufffd', '').replace('', '')
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).lower()

# ==============================================================================
# TAXONOMIA MÉDICA DE CLASSIFICAÇÃO COMPLETA (5 GRANDES ÁREAS DO REVALIDA / ENARE)
# ==============================================================================
TAXONOMIA_MEDICA = {
    "Cirurgia Geral": {
        "Trauma e Emergências Cirúrgicas": {
            "Neurotrauma e TCE": [
                "glasgow", "tce", "traumatismo cranio", "hematoma extradural", "hematoma subdural",
                "pupila midriatica", "anisocoria", "afundamento craniano", "fratura de base de cranio",
                "intervalo lucido", "concussao cerebral", "pressao intracraniana", "pic", "triade de cushing",
                "escala de coma"
            ],
            "Trauma Torácico": [
                "pneumotorax", "hemotorax", "tamponamento cardiaco", "triade de beck", "drenagem pleural",
                "toracocentese", "selo d'agua", "flail chest", "torax instavel", "drenagem de torax",
                "toracotomia", "lesao traqueobronquica", "enfisema subcutaneo", "atls"
            ],
            "Trauma Abdominal e Pélvico": [
                "fast", "e-fast", "lesao esplenica", "esplenectomia", "trauma hepatico", "hematoma subcapsular",
                "anel pelvico", "trauma renal", "choque hemorragico", "laparotomia exploradora", "trauma abdominal",
                "lesao de viscera oca", "retroperitonio", "damage control", "cirurgia de controle de danos",
                "arco de riolan", "artéria mesenterica", "mesenterica superior"
            ],
            "Queimaduras e Resposta Metabólica": [
                "parkland", "regra dos nove", "queimadura", "mioglobinuria", "scq", "enxertia", "enxerto",
                "retalho", "remt", "resposta metabolica ao trauma", "fase ebb", "fase flow", "hipotermia trauma",
                "triade letal", "rhabdomiolise"
            ]
        },
        "Abdome Agudo e Parede Abdominal": {
            "Apendicite Aguda": [
                "apendicite", "sinal de rovsing", "sinal de blumberg", "ponto de mcburney", "apendice retrocecal",
                "apendicectomia", "escore de alvarado", "bacteroides fragilis", "dor em fossa iliaca direita"
            ],
            "Obstrução Intestinal": [
                "obstrucao intestinal", "bridas", "aderencias", "niveis hidroaereos", "ileo paralitico",
                "ogilvie", "volvo de sigmoide", "volvo gastrico", "intussuscepcao", "distensao abdominal",
                "parada de eliminacao de fezes e gases", "suboclusao"
            ],
            "Doença Diverticular e Perfurativa": [
                "diverticulite", "hartmann", "abscesso pericolonico", "pneumoperitonio", "ulcera perfurada",
                "peritonite fecal", "diverticulo de meckel", "perfuracao intestinal", "hinchey"
            ],
            "Hérnias da Parede Abdominal": [
                "hernia inguinal", "lichtenstein", "canal inguinal", "hernia femoral", "hernia crural",
                "hernia hiatal", "hernia umbilical", "hernia incisional", "tapp", "tep", "shouldice",
                "hernia encarcerada", "hernia estrangulada"
            ]
        },
        "Vias Biliares, Fígado e Pâncreas": {
            "Doenças da Vesícula e Vias Biliares": [
                "colelitiase", "colecistite", "sinal de murphy", "colangite", "triade de charcot", "pentade de reynolds",
                "cpre", "coledocolitiase", "dreno de kehr", "colecistectomia", "lama biliar", "aerobilia", "vesicula em porcelana"
            ],
            "Pancreatite e Neoplasias Digestivas": [
                "pancreatite aguda", "escore bisap", "criterios de ranson", "pseudocisto pancreatico",
                "adenocarcinoma de cabeca de pancreas", "sinal de courvoisier", "cirurgia de whipple",
                "duodenopancreatectomia", "cancer gastrico", "linite plastica", "tumor neuroendocrino"
            ]
        },
        "Proctologia, Urologia e Técnica Cirúrgica": {
            "Doenças Orificiais e Anorretais": [
                "hemorroida", "hemorroidas", "trombose hemorroidaria", "fistula anorretal", "abscesso perianal",
                "linha denteada", "fissura anal", "prolapso retal", "plicoma", "ultrassonografia endorretal"
            ],
            "Urologia Cirúrgica": [
                "cancer de bexiga", "uretrocistoscopia", "calculo ureteral", "litotripsia", "tumor de testiculo",
                "hiperplasia prostatica", "hpb", "jup", "estenose de uretra", "priapismo", "torcao testicular",
                "orquiectomia", "calculo renal", "colica nefreti", "hematuria macroscopica"
            ],
            "Fios, Cicatrização e Profilaxia": [
                "cicatrizacao", "fases da cicatrizacao", "monocryl", "vicryl", "prolene", "fio inabsorvivel",
                "fio absorvivel", "cefazolina", "potencialmente contaminada", "ferida cirurgica", "deiscencia",
                "infeccao de sitio cirurgico", "isc", "cantoplastia", "antissepsia", "degermacao", "paramentacao",
                "anestesia local", "lidocaina", "bupivacaina", "bloqueio anestesico"
            ]
        },
        "Cirurgia Vascular e Esofagogástrica": {
            "Hemorragia Digestiva e Esôfago": [
                "hemorragia digestiva", "hda", "hdb", "estreitamento do esofago", "varizes esofagicas",
                "classificacao de forrest", "endoscopia digestiva", "eda", "mallory-weiss", "boerhaave",
                "megaesofago", "acalasia", "esofagectomia", "cancer de esofago", "constricao do esofago"
            ],
            "Doenças Vasculares e Aneurismas": [
                "aneurisma de aorta", "disseccao de aorta", "oclusao arterial aguda", "trombose venosa profunda",
                "tvp", "insuficiencia venosa", "empastamento de panturrilha", "claudicacao intermitente",
                "indice tornozelo-braquial", "itb", "ponte de safena", "enxerto vascular", "isquemia mesenterica"
            ]
        }
    },
    "Clínica Médica": {
        "Cardiologia": {
            "Arritmias e Eletrocardiografia": [
                "fibrilacao atrial", "flutter atrial", "taquicardia ventricular", "cardioversao", "bloqueio atrioventricular",
                "bavt", "marcapasso", "onda f", "extrassistole", "intervalo qt", "supra de st", "infra de st",
                "bradicardia", "eletrocardiograma", "ecg", "taquicardia supraventricular", "parada cardiorrespiratoria", "pcr"
            ],
            "Síndromes Coronarianas e Valvopatias": [
                "infarto agudo do miocardio", "iam", "trombose coronaria", "alteplase", "trombolitico", "angioplastia",
                "estenose mitral", "estenose aortica", "insuficiencia mitral", "insuficiencia aortica", "endocardite bacteriana",
                "angina estavel", "angina instavel", "troponina", "ck-mb", "cateterismo cardiaco", "coronariografia"
            ],
            "Hipertensão e Insuficiência Cardíaca": [
                "crise hipertensiva", "emergencia hipertensiva", "edema de papila", "nitroprussiato", "insuficiencia cardiaca",
                "fracao de ejecao", "sacubitril", "espironolactona", "furosemida", "bnp", "edema agudo de pulmao",
                "choque cardiogenico", "losartana", "enalapril", "hipertensao arterial", "anti-hipertensivo"
            ]
        },
        "Endocrinologia e Metabologia": {
            "Diabetes Mellitus": [
                "diabetes", "glicemia", "hemoglobina glicada", "hba1c", "metformina", "insulina", "cetoacidose diabetica",
                "cad", "estado hiperosmolar", "hipoglicemia", "retinopatia diabetica", "nefropatia diabetica", "pe diabetico"
            ],
            "Tireoide e Adrenal": [
                "hipotireoidismo", "hipertireoidismo", "tireoidite de hashimoto", "doenca de graves", "tsh", "t4 livre",
                "nodulo de tireoide", "puncao aspirativa", "paaf", "sindrome de cushing", "doenca de addison",
                "feocromocitoma", "hipercalcemia", "hipocalcemia", "paratormonio", "pth", "hiperparatireoidismo"
            ],
            "Distúrbios Hidroeletrolíticos e Ácido-Base": [
                "siadh", "hiponatremia", "hipernatremia", "hipocalemia", "hipercalemia", "mielinolise pontina",
                "osmolaridade plasmatica", "acidose metabolica", "alcalose metabolica", "gasometria arterial",
                "anion gap", "hiperuricemia", "disturbio hidroeletrolitico"
            ]
        },
        "Pneumologia": {
            "Doenças Obstrutivas e Asma": [
                "asma", "salbutamol", "beclometasona", "dpoc", "espirometria", "vef1", "cvf", "broncodilatador",
                "enfisema pulmonar", "bronquite cronica", "oxigenoterapia domiciliar", "cessacao do tabagismo", "tabagista"
            ],
            "Pneumonias, Pleura e Embolia": [
                "pneumonia", "pac", "escore curb-65", "derrame pleural", "criterios de light", "exsudato", "transudato",
                "empiema pleural", "tromboembolismo pulmonar", "tep", "dimero-d", "angiotomografia de torax", "hemoptise",
                "neoplasia de pulmao", "nodulo pulmonar"
            ]
        },
        "Nefrologia": {
            "Injúria Renal e Doença Renal Crônica": [
                "doenca renal cronica", "clearance de creatinina", "cockcroft-gault", "dialise", "hemodialise",
                "lesao renal aguda", "ira", "kdigo", "oliguria", "anuria", "uremia", "nefrite intersticial"
            ],
            "Glomerulopatias e Sedimento Urinário": [
                "sindrome nefrotica", "sindrome nefritica", "hematuria", "proteinuria", "gnpe", "glomerulonefrite",
                "cilindros hematicos", "nefropatia por iga", "doenca de berger", "nefropatia membranosa"
            ]
        },
        "Infectologia": {
            "Infecções Sistêmicas e Arboviroses": [
                "tuberculose", "trm-tb", "baciloscopia", "leptospirose", "sindrome de weil", "hepatite b", "hepatite c",
                "hiv", "tarv", "leishmaniose", "esporotricose", "dengue", "chikungunya", "zika", "malaria",
                "doenca de chagas", "febre amarela", "sepse", "choque septico", "qsofa", "hemocultura"
            ],
            "Meningites e Infecções Comuns": [
                "meningite", "puncao lombar", "liquor", "ceftriaxona", "vancomicina", "infeccao urinaria",
                "pielonefrite", "celulite", "erisipela", "infeccao de partes moles", "covid-19", "influenza", "oseltamivir"
            ]
        },
        "Neurologia e Psiquiatria": {
            "Neurologia Clínica": [
                "acidente vascular cerebral", "avc", "isquemico", "hemorragico", "trombolise", "rtpa",
                "ataque isquemico transitorio", "ait", "epilepsia", "crise convulsiva", "cefaleia", "migranea",
                "enxaqueca", "parkinson", "alzheimer", "demencia", "guillain-barre", "miastenia gravis", "neuropatia"
            ],
            "Psiquiatria e Saúde Mental": [
                "depressao", "isrs", "fluoxetina", "sertralina", "ansiedade", "transtorno do panico", "transtorno bipolar",
                "litio", "esquizofrenia", "antipsicotico", "haloperidol", "risperidona", "ideacao suicida", "suicidio",
                "delirium", "abstinencia alcoolica", "delirium tremens", "benzodiazepinico", "dependencia quimica"
            ]
        },
        "Gastroenterologia e Hepatologia": {
            "Aparelho Digestivo Alto e Fígado": [
                "dispepsia", "refluxo", "drge", "ulcera peptica", "h. pylori", "cirrose hepatica", "hipertensao portal",
                "ascite", "peritonite bacteriana espontanea", "pbe", "encefalopatia hepatica", "lactulose",
                "esteatose hepatica", "hepatite autoimune"
            ],
            "Intestino e Doença Inflamatória": [
                "doenca de crohn", "retocolite ulcerativa", "doenca inflamatoria intestinal", "diarreia cronica",
                "sindrome do intestino irritavel", "doenca celiaca", "antitransglutaminase"
            ]
        },
        "Hematologia, Reumatologia e Dermatologia": {
            "Hematologia": [
                "anemia ferropriva", "ferritina", "anemia megaloblastica", "vitamina b12", "acido folico", "anemia falciforme",
                "talassemia", "anemia hemolitica", "coombs direto", "leucemia", "linfoma", "mieloma multiplo",
                "plaquetopenia", "pti", "transfusao sanguinea", "concentrado de hemacias", "anticoagulante", "dabigatrana",
                "apixabana", "rivaroxabana", "edoxabana", "doac", "varfarina", "heparina", "fator xa"
            ],
            "Reumatologia e Autoimunidade": [
                "lupus eritematoso", "nefrite lupica", "fan", "anti-dna", "artrite reumatoide", "fator reumatoide",
                "metotrexato", "espondilite anquilosante", "fibromialgia", "gota", "vasculite", "esclerose sistemica", "sjogren"
            ],
            "Dermatologia": [
                "farmacodermia", "stevens-johnson", "psoriase", "dermatite atopica", "dermatite de contato",
                "eczema", "melanoma", "carcinoma basocelular", "carcinoma espinocelular", "hanseniase",
                "micose", "tinea", "escabiose", "urticaria", "brca"
            ]
        }
    },
    "Pediatria": {
        "Neonatologia": {
            "Sala de Parto e Reanimação": [
                "sala de parto", "clampeamento de cordao", "reanimacao neonatal", "vpp", "ventilacao com pressao positiva",
                "apgar", "teste do coracaozinho", "oximetria de pulso", "eritema toxico", "aspiracao de meconio",
                "membrana hialina", "surfactante exogeno", "recem-nascido termo", "prematuro", "alojamento conjunto",
                "recem-nascido", "rn a termo", "peso ao nascer"
            ],
            "Triagem e Icterícia Neonatal": [
                "ictericia neonatal", "fototerapia", "exsanguineotransfusao", "teste do pezinho", "toxoplasmose congenita",
                "citomegalovirus", "sifilis congenita", "reflexo vermelho", "leucocoria", "triagem neonatal",
                "ictericia patologica", "bilirrubina total", "bilirrubina indireta", "zona de kramer"
            ]
        },
        "Puericultura e Desenvolvimento": {
            "Crescimento e Nutrição": [
                "aleitamento materno", "leite materno", "alimentacao complementar", "escore-z", "baixo peso para idade",
                "desnutricao infantil", "baixa estatura", "marcos do desenvolvimento", "dnpm", "m-chat", "autismo infantil",
                "puberdade precoce", "estagios de tanner", "puericultura", "pediatra", "linfonodo palpavel"
            ],
            "Imunização Infantil": [
                "calendario vacinal", "vacina", "triplice viral", "tetraviral", "rotavirus", "vacina bcg",
                "pentavalente", "vacina vip", "vacina vop", "meningococica", "pneumococica conjugada"
            ]
        },
        "Doenças Respiratórias e Infecciosas Pediátricas": {
            "Vias Aéreas e Pulmão Infantil": [
                "bronquiolite", "bva", "virus sincicial respiratorio", "crupe viral", "laringite estridulosa",
                "estridor laringeo", "coqueluche", "pneumonia na infancia", "asma infantil", "lactente sibilante",
                "otite media aguda", "oma", "sinusite infantil", "amigdalite estreptococica"
            ],
            "Doenças Exantemáticas e Vasculites": [
                "exantema subito", "roseola infantil", "doenca de kawasaki", "sindrome mao-pe-boca",
                "purpura de henoch-schonlein", "varicela", "sarampo", "rubeola", "escarlatina", "eritema infeccioso"
            ]
        },
        "Gastroenterologia e Emergências Pediátricas": {
            "Trato Gastrointestinal Infantil": [
                "estenose hipertrofica de piloro", "invaginacao intestinal", "doenca de hirschsprung",
                "diarreia aguda", "desidratacao", "sro", "terapia de reidratacao oral",
                "parasitose intestinal", "ascaridiase", "giardiase", "zinco"
            ],
            "Emergências e Ortopedia Infantil": [
                "sindrome hemolitico-uremica", "shu", "sindrome do bebe sacudido", "shaken baby", "maus-tratos infantis",
                "convulsao febril", "epifisiolise proximal do femur", "osgood-schlatter", "sinovite transitoria do quadril",
                "artrite septica infantil", "manobra de ortolani", "manobra de barlow", "displasia do desenvolvimento do quadril"
            ]
        }
    },
    "Ginecologia e Obstetrícia": {
        "Obstetrícia": {
            "Pré-Natal e Modificações Gestacionais": [
                "pre-natal", "regra de naegele", "altura uterina", "manobras de leopold", "vitalidade fetal",
                "cardiotocografia", "dopplervelocimetria fetal", "ciur", "restricao de crescimento intrauterino",
                "polidramnio", "oligoidramnio", "beta-hcg", "idade gestacional", "gestante", "gravidez", "primigesta",
                "sinal de hegar", "sinal de nobile-budin", "sinal de piskacek", "probabilidade de gravidez",
                "fecundacao", "cardiovascular fetal", "bolsao vertical", "liquido amniotico"
            ],
            "Patologias da Gravidez": [
                "pre-eclampsia", "eclampsia", "sulfato de magnesio", "sindrome hellp", "diabetes gestacional",
                "totg", "isoimunizacao rh", "coombs indireto", "imunoglobulina anti-d", "bacteriuria assintomatica gestante",
                "sifilis na gestacao", "insuficiencia uteroplacentaria"
            ],
            "Sangramentos e Trabalho de Parto": [
                "descolamento prematuro de placenta", "dpp", "placenta previa", "abortamento", "gravidez ectopica",
                "trabalho de parto", "partograma", "rotura prematura de membranas", "rpm", "corioamnionite",
                "distocia de espaduas", "hemorragia pos-parto", "atonia uterina", "puerperio", "endometrite puerperal",
                "parto cesarea", "indice de bishop", "colo uterino", "apagamento", "dilatacao do colo"
            ]
        },
        "Ginecologia Geral e Climatério": {
            "Endocrinologia Ginecológica e Ciclo": [
                "ovarios policisticos", "sop", "amenorreia", "sindrome de rokitansky", "insuficiencia ovariana prematura",
                "galactorreia", "hiperprolactinemia", "anticoncepcional oral", "anticoncepcao", "contracepcao",
                "diu de cobre", "diu de levonorgestrel", "dismenorreia", "sangramento uterino anormal", "sua", "palm-coein",
                "progesterona", "estrogenios", "ovario", "ciclo menstrual", "fase lutea", "fase folicular"
            ],
            "Climatério, Miomas e Endometriose": [
                "climaterio", "fogachos", "terapia de reposicao hormonal", "trh", "mioma uterino", "miomatose",
                "endometriose", "adenomiose", "polipo endometrial", "cisto ovariano", "torcao anexial"
            ]
        },
        "Infectologia Ginecológica e Oncologia": {
            "Vulvovaginites e ISTs": [
                "vaginose bacteriana", "clue cells", "tricomoniase", "candidiase vulvovaginal", "herpes genital",
                "doenca inflamatoria pelvica", "dip", "cancro mole", "gonorreia", "clamidia", "corrimento vaginal", "cervicite"
            ],
            "Oncologia Ginecológica e Mastologia": [
                "cancer de colo de utero", "papanicolau", "citopatologico", "hsil", "lsil", "ascus", "colposcopia",
                "cancer de mama", "mamografia", "bi-rads", "linfonodo sentinela", "cancer de ovario", "cancer de endometrio",
                "nodulo mamario", "mastologia"
            ]
        }
    },
    "Medicina Preventiva e Social / MFC": {
        "Epidemiologia e Bioestatística": {
            "Indicadores de Saúde": [
                "incidencia", "prevalencia", "mortalidade infantil", "mortalidade proporcional", "swaroop-uemura",
                "transicao demografica", "transicao epidemiologica", "diagrama de controle", "taxa de letalidade",
                "esperanca de vida", "coeficiente de mortalidade"
            ],
            "Desenhos de Estudo e Diagnóstico": [
                "estudo de coorte", "caso-controle", "ensaio clinico randomizado", "estudo transversal",
                "sensibilidade", "especificidade", "valor preditivo positivo", "vpp", "vpn", "razao de verossimilhanca",
                "risco relativo", "odds ratio", "intervalo de confianca", "p-valor", "vies de selecao", "vies de confusao"
            ]
        },
        "Atenção Primária e Sistemas de Saúde": {
            "SUS e Políticas Públicas": [
                "pnab", "estrategia saude da familia", "esf", "unidade basica de saude", "ubs", "agente comunitario de saude",
                "territorializacao", "adstricao de clientela", "resolubilidade", "atributos da aps", "modelo beveridge",
                "modelo bismarck", "lei 8080", "lei 8142", "controle social", "conselho municipal de saude", "conferencia de saude",
                "saude indigena", "financiamento do sus", "universalidade", "integralidade", "equidade",
                "politica nacional de atencao basica", "portaria"
            ],
            "Medicina de Família e Comunidade (MFC)": [
                "metodo clinico centrado na pessoa", "mccp", "genograma", "ecomapa", "projeto terapeutico singular",
                "pts", "registro soap", "prevencao quaternaria", "prevencao primaria", "prevencao secundaria",
                "prevencao terciaria", "educacao popular em saude", "visita domiciliar", "cuidados paliativos",
                "escala de zarit", "indice de vulnerabilidade", "ivcf-20", "rastreamento", "tabagismo", "etilismo", "cessacao do tabagismo"
            ]
        },
        "Vigilância em Saúde, Ética e Saúde do Trabalhador": {
            "Vigilância e Notificação": [
                "notificacao compulsoria", "sinan", "vigilancia epidemiologica", "vigilancia sanitaria", "anvisa",
                "vigilancia ambiental", "surto epidemico", "epidemia", "pandemia", "bloqueio vacinal", "investigacao epidemiologica"
            ],
            "Saúde do Trabalhador e Medicina Legal": [
                "acidente de trabalho", "comunicacao de acidente de trabalho", "cat", "doenca ocupacional", "silicose",
                "saturnismo", "ler/dort", "perda auditiva induzida por ruido", "pair", "inss", "prontuario medico",
                "sigilo medico", "codigo de etica medica", "declaracao de obito", "atestado de obito", "autonomia do paciente",
                "beneficencia", "nao maleficencia", "justica distributiva", "mercurio", "chumbo", "cromo", "intoxicacao por metal"
            ]
        }
    }
}

# Pre-computa termos normalizados para busca instantânea
_TAXONOMIA_NORMALIZADA = []
for _esp, _temas in TAXONOMIA_MEDICA.items():
    for _tema, _subtemas in _temas.items():
        for _subtema, _kws in _subtemas.items():
            _kws_norm = [normalizar_texto(k) for k in _kws]
            _TAXONOMIA_NORMALIZADA.append((_esp, _tema, _subtema, _kws_norm))


def classificar_questao(texto_completo):
    """Classifica o enunciado/alternativas por frequência de termos-chave médicos normalizados."""
    texto_norm = normalizar_texto(texto_completo)
    melhor_match = ("Outros / Não Categorizados", "Geral", "Diversos")
    maior_score = 0

    for esp, tema, subtema, kws in _TAXONOMIA_NORMALIZADA:
        score = 0
        for kw in kws:
            if kw in texto_norm:
                score += 3 if ' ' in kw else 1
        
        if score > maior_score:
            maior_score = score
            melhor_match = (esp, tema, subtema)

    return melhor_match

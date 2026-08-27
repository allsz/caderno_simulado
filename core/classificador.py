import re

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
    """Classifica o enunciado/alternativas por frequência de termos-chave médicos."""
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

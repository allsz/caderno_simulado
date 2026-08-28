import sys
import os
import json
import re
import unicodedata

def remover_acentos(texto):
    if not texto:
        return ""
    # Substitui caracteres quebrados por espaco
    texto = texto.replace('\ufffd', '').replace('', '')
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).lower()

# TAXONOMIA EXPANDIDA E ROBUSTA COM TERMOS NORMALIZADOS
TAXONOMIA_COMPLETA = {
    "Cirurgia Geral": {
        "Trauma e Emergências Cirúrgicas": {
            "Neurotrauma e TCE": ["glasgow", "tce", "traumatismo cranio", "hematoma extradural", "hematoma subdural", "pupila midriatica", "anisocoria", "afundamento craniano", "fratura de base de cranio", "intervalo lucido", "concussao"],
            "Trauma Torácico": ["pneumotorax", "hemotorax", "tamponamento cardiaco", "triade de beck", "drenagem pleural", "toracocentese", "selo d'agua", "flail chest", "torax instavel", "drenagem de torax", "toracotomia"],
            "Trauma Abdominal e Pélvico": ["fast", "e-fast", "lesao esplenica", "esplenectomia", "trauma hepatico", "hematoma subcapsular", "anel pelvico", "trauma renal", "choque hemorragico", "laparotomia exploradora", "trauma abdominal", "lesao de viscus", "sangramento retroperitoneal"],
            "Queimaduras e Resposta Metabólica": ["parkland", "regra dos nove", "queimadura", "mioglobinuria", "scq", "enxertia", "enxerto", "retalho", "remt", "resposta metabolica ao trauma", "fase ebb", "fase flow", "hipotermia trauma", "triade letal"]
        },
        "Abdome Agudo e Parede Abdominal": {
            "Apendicite Aguda": ["apendicite", "rovsing", "blumberg", "mcburney", "apendice", "apendicectomia", "apendicite aguda"],
            "Obstrução Intestinal": ["obstrucao intestinal", "bridas", "aderencias", "niveis hidroaereos", "ileo paralitico", "ogilvie", "volvo de sigmoide", "volvo gastrico", "intussuscepcao", "empachamento", "distensao abdominal"],
            "Doença Diverticular e Perfurativa": ["diverticulite", "hartmann", "abscesso pericolonico", "pneumoperitonio", "ulcera perfurada", "peritonite fecal", "diverticulo de meckel", "perfuracao intestinal", "ar no retroperitonio"],
            "Hérnias da Parede Abdominal": ["hernia inguinal", "lichtenstein", "canal inguinal", "hernia femoral", "hernia hiatal", "hernia umbilical", "hernia incisional", "tapp", "tep", "shouldice", "incarceramento", "estrangulamento herniario"]
        },
        "Vias Biliares, Fígado e Pâncreas": {
            "Doenças da Vesícula e Vias Biliares": ["colelitiase", "colecistite", "sinal de murphy", "colangite", "charcot", "reynolds", "cpre", "coledocolitiase", "dreno de kehr", "colecistectomia", "lama biliar", "aerobilia"],
            "Pancreatite e Neoplasias Digestivas": ["pancreatite aguda", "bisap", "ranson", "pseudocisto", "adenocarcinoma de cabeca de pancreas", "courvoisier", "whipple", "duodenopancreatectomia", "cancer gastrico", "linite plastica", "tumor neuroendocrino"]
        },
        "Proctologia, Urologia e Técnica Cirúrgica": {
            "Doenças Orificiais e Anorretais": ["hemorroida", "hemorroidas", "trombose hemorroidaria", "fistula anorretal", "abscesso perianal", "linha denteada", "fissura anal", "prolapso retal", "plicoma"],
            "Urologia Cirúrgica": ["cancer de bexiga", "uretrocistoscopia", "calculo ureteral", "litotripsia", "tumor de testiculo", "hiperplasia prostatica", "hpb", "jup", "estenose de uretra", "priapismo", "torcao testicular", "orquiectomia", "calculo renal", "colica nefreti"],
            "Fios, Cicatrização e Profilaxia": ["cicatrizacao", "fases da cicatrizacao", "monocryl", "vicryl", "prolene", "nylon", "catgut", "cefazolina", "potencialmente contaminada", "deiscencia", "infeccao de sitio cirurgico", "isc", "cantoplastia", "antissepsia", "degermacao", "paramentacao", "anestesia local", "lidocaina", "bupivacaina"]
        },
        "Cirurgia Vascular e Esofagogástrica": {
            "Hemorragia Digestiva e Esôfago": ["hemorragia digestiva alta", "hda", "hdb", "estreitamento do esofago", "varizes esofagicas", "forrest", "endoscopia digestiva", "eda", "mallory-weiss", "boerhaave", "megaesofago", "acalasia", "esofagectomia", "cancer de esofago"],
            "Doenças Vasculares e Aneurismas": ["aneurisma de aorta", "disseccao de aorta", "oclusao arterial aguda", "trombose venosa profunda", "tvp", "insuficiencia venosa", "empastamento", "claudicacao intermitente", "indice tornozelo-braquial", "itb", "ponte de safena", "enxerto vascular"]
        }
    },
    "Clínica Médica": {
        "Cardiologia": {
            "Arritmias e Eletrocardiografia": ["fibrilacao atrial", "flutter atrial", "taquicardia ventricular", "cardioversao", "bloqueio atrioventricular", "bavt", "marcapasso", "onda f", "extrassistole", "intervalo qt", "supra de st", "infra de st", "bradicardia"],
            "Síndromes Coronarianas e Valvopatias": ["infarto agudo do miocardio", "iam", "trombose", "alteplase", "trombolitico", "angioplastia", "estenose mitral", "estenose aortica", "insuficiencia mitral", "insuficiencia aortica", "endocardite", "angina", "troponina", "ck-mb", "cateterismo cardiaco"],
            "Hipertensão e Insuficiência Cardíaca": ["crise hipertensiva", "emergencia hipertensiva", "edema de papila", "nitroprussiato", "insuficiencia cardiaca", "fracao de ejecao", "sacubitril", "espironolactona", "furosemida", "bnp", "edema agudo de pulmao", "choque cardiogenico"]
        },
        "Endocrinologia e Metabologia": {
            "Diabetes Mellitus": ["diabetes", "glicemia", "hemoglobina glicada", "hba1c", "metformina", "insulina", "cetoacidose diabetica", "cad", "estado hiperosmolar", "hipoglicemia", "retinopatia diabetica", "nefropatia diabetica", "pe diabetico"],
            "Tireoide e Adrenal": ["hipotireoidismo", "hipertireoidismo", "hashimoto", "doenca de graves", "tsh", "t4 livre", "nodulo de tireoide", "puncao aspirativa", "paaf", "cushing", "addison", "feocromocitoma", "hipercalcemia", "hipocalcemia", "paratormonio", "pth"],
            "Distúrbios Hidroeletrolíticos e Ácido-Base": ["siadh", "hiponatremia", "hipernatremia", "hipocalemia", "hipercalemia", "mielinolise pontina", "osmolaridade", "acidose metabolica", "alcalose metabolica", "gasometria", "anion gap", "hiperuricemia"]
        },
        "Pneumologia": {
            "Doenças Obstrutivas e Asma": ["asma", "salbutamol", "beclometasona", "dpoc", "espirometria", "vef1", "cvf", "broncodilatador", "enfisema", "bronquite cronica", "oxigenoterapia", "cessacao do tabagismo"],
            "Pneumonias, Pleura e Embolia": ["pneumonia", "pac", "curb-65", "derrame pleural", "criterios de light", "exsudato", "trasudato", "empiema", "tromboembolismo pulmonar", "tep", "dimero-d", "angiotomografia de torax", "hemoptise"]
        },
        "Nefrologia": {
            "Injúria Renal e Doença Renal Crônica": ["doenca renal cronica", "clearance de creatinina", "cockcroft-gault", "dialise", "hemodialise", "lesao renal aguda", "ira", "kdigo", "oliguria", "anuria", "uremia"],
            "Glomerulopatias e Sedimento Urinário": ["sindrome nefrotica", "sindrome nefritica", "hematuria", "proteinuria", "gnpe", "glomerulonefrite", "cilindros hematicos", "nefropatia por iga", "berger"]
        },
        "Infectologia": {
            "Infecções Sistêmicas e Arboviroses": ["tuberculose", "trm-tb", "baciloscopia", "leptospirose", "weil", "hepatite b", "hepatite c", "hiv", "tarv", "leishmaniose", "esporotricose", "dengue", "chikungunya", "zika", "malaria", "chagas", "febre amarela", "sepse", "choque septico", "qsofa", "hemocultura"],
            "Meningites e Infecções Comuns": ["meningite", "puncao lombar", "liquor", "ceftriaxona", "vancomicina", "infeccao urinaria", "pielonefrite", "celulite", "erisipela", "infeccao de partes moles", "covid", "influenza", "tamiflu"]
        },
        "Neurologia e Psiquiatria": {
            "Neurologia Clínica": ["acidente vascular cerebral", "avc", "isquemico", "hemorragico", "trombolise", "rtpa", "ataque isquemico transitorio", "ait", "epilepsia", "crise convulsiva", "cefaleia", "migranea", "enxaqueca", "parkinson", "alzheimer", "demencia", "guillain-barre", "miastenia"],
            "Psiquiatria e Saúde Mental": ["depressao", "isrs", "fluoxetina", "sertralina", "ansiedade", "transtorno do panico", "transtorno bipolar", "litio", "esquizofrenia", "antipsicotico", "haloperidol", "risperidona", "ideacao suicida", "suicidio", "delirium", "abstinencia alcoolica", "delirium tremens", "benzodiazepinico"]
        },
        "Gastroenterologia e Hepatologia": {
            "Aparelho Digestivo Alto e Fígado": ["dispepsia", "refluxo", "drge", "ulcera peptica", "h. pylori", "cirrose", "hipertensao portal", "ascite", "peritonite bacteriana espontanea", "pbe", "encefalopatia hepatica", "lactulose", "esteatose hepatica", "hepatite autoimune"],
            "Intestino e Doença Inflamatória": ["doenca de crohn", "retocolite ulcerativa", "doenca inflamatoria intestinal", "diarreia cronica", "sindrome do intestino irritavel", "doenca celiaca", "anticorpo antitransglutaminase"]
        },
        "Hematologia, Reumatologia e Dermatologia": {
            "Hematologia": ["anemia ferropriva", "ferritina", "anemia megaloblastica", "vitamina b12", "acido folico", "anemia falciforme", "talassemia", "anemia hemolitica", "coombs", "leucemia", "linfoma", "mieloma multiplo", "plaquetopenia", "pti", "transfusao", "concentrado de hemacias"],
            "Reumatologia e Autoimunidade": ["lupus", "nefrite lupica", "fan", "anti-dna", "artrite reumatoide", "fator reumatoide", "metotrexato", "espondilite anquilosante", "fibromialgia", "gota", "vasculite", "esclerose sistemica", "sjogren"],
            "Dermatologia": ["farmacodermia", "stevens-johnson", "psoriase", "dermatite atopica", "dermatite", "eczema", "melanoma", "carcinoma basocelular", "carcinoma espinocelular", "hanseniase", "micoses", "escabiose", "urticaria"]
        }
    },
    "Pediatria": {
        "Neonatologia": {
            "Sala de Parto e Reanimação": ["sala de parto", "clampeamento", "reanimacao neonatal", "vpp", "pressao positiva", "apgar", "teste do coracaozinho", "oximetria", "eritema toxico", "aspiracao de meconio", "doenca da membrana hialina", "surfactante"],
            "Triagem e Icterícia Neonatal": ["ictericia neonatal", "fototerapia", "exsanguineotransfusao", "teste do pezinho", "toxoplasmose congenita", "citomegalovirus", "sifilis congenita", "reflexo vermelho", "leucocoria"]
        },
        "Puericultura e Desenvolvimento": {
            "Crescimento e Nutrição": ["aleitamento materno", "leite materno", "alimentacao complementar", "escore-z", "baixo peso", "desnutricao", "estatura", "marcos do desenvolvimento", "dnpm", "m-chat", "autismo", "puberdade precoce", "tanner"],
            "Imunização Infantil": ["calendario vacinal", "vacina", "triplice viral", "tetraviral", "rotavirus", "bcg", "pentavalente", "vip", "vop", "meningococica", "pneumococica"]
        },
        "Doenças Respiratórias e Infecciosas Pediátricas": {
            "Vias Aéreas e Pulmão Infantil": ["bronquiolite", "bva", "virus sincicial", "crupe", "estridor", "coqueluche", "pneumonia infantil", "asma infantil", "sibilancia", "lactente sibilante", "otite media aguda", "oma", "sinusite infantil", "amigdalite bacteriana"],
            "Doenças Exantemáticas e Vasculites": ["exantema subito", "roseola", "kawasaki", "mao-pe-boca", "henoch-schonlein", "varicela", "sarampo", "rubeola", "escarlatina", "eritema infeccioso"]
        },
        "Gastroenterologia e Emergências Pediátricas": {
            "Trato Gastrointestinal Infantil": ["estenose hipertrofica de piloro", "invaginacao intestinal", "hirschsprung", "diarreia aguda", "desidratacao", "sro", "parasitose", "ascaris", "giardia", "refluxo gastroesofagico infantil"],
            "Emergências e Ortopedia Infantil": ["sindrome hemolitico-uremica", "shu", "shaken baby", "maus-tratos", "convulsao febril", "epifisiolise", "osgood-schlatter", "sinovite transitoria", "artrite septica infantil", "dor do crescimento"]
        }
    },
    "Ginecologia e Obstetrícia": {
        "Obstetrícia": {
            "Pré-Natal e Modificações Gestacionais": ["pre-natal", "naegele", "altura uterina", "leopold", "vitalidade fetal", "cardiotocografia", "dopplervelocimetria", "ciur", "polidramnio", "oligoidramnio", "beta-hcg", "idade gestacional"],
            "Patologias da Gravidez": ["pre-eclampsia", "eclampsia", "sulfato de magnesio", "hellp", "diabetes gestacional", "totg", "isoimunizacao", "coombs indireto", "anti-d", "infeccao urinaria gestacao", "sifilis na gestacao"],
            "Sangramentos e Trabalho de Parto": ["descolamento prematuro de placenta", "dpp", "placenta previa", "abortamento", "gravidez ectopica", "trabalho de parto", "partograma", "rotura prematura de membranas", "rpm", "corioamnionite", "distocia", "hemorragia pos-parto", "atonia uterina", "puerperio", "endometrite"]
        },
        "Ginecologia Geral e Climatério": {
            "Endocrinologia Ginecológica e Ciclo": ["ovarios policisticos", "sop", "amenorreia", "rokitansky", "insuficiencia ovariana", "galactorreia", "prolactina", "anticoncepcional", "contracepcao", "diu", "discenorroida", "sangramento uterino anormal", "sua", "palm-coein"],
            "Climatério, Miomas e Endometriose": ["climaterio", "fogachos", "terapia hormonal", "reposicao hormonal", "mioma", "miomatose", "endometriose", "adenomiose", "polipo endometrial", "cisto de ovario", "torcao ovariana"]
        },
        "Infectologia Ginecológica e Oncologia": {
            "Vulvovaginites e ISTs": ["vaginose bacteriana", "clue cells", "tricomoniase", "candidiase", "herpes genital", "doenca inflamatoria pelvica", "dip", "cancro mole", "gonorreia", "clamidia", "corrimento vaginal"],
            "Oncologia Ginecológica e Mastologia": ["cancer de colo de utero", "papanicolau", "citopatologico", "hsil", "lsil", "ascus", "colposcopia", "cancer de mama", "mamografia", "bi-rads", "linfonodo sentinela", "cancer de ovario", "cancer de endometrio"]
        }
    },
    "Medicina Preventiva e Social / MFC": {
        "Epidemiologia e Bioestatística": {
            "Indicadores de Saúde": ["incidencia", "prevalencia", "mortalidade infantil", "mortalidade proporcional", "swaroop-uemura", "transicao demografica", "transicao epidemiologica", "diagrama de controle", "letalidade", "esperanca de vida"],
            "Desenhos de Estudo e Diagnóstico": ["estudo de coorte", "caso-controle", "ensaio clinico", "estudo transversal", "sensibilidade", "especificidade", "vpp", "vpn", "razao de verossimilhanca", "risco relativo", "odds ratio", "intervalo de confianca", "p-valor", "vies de selecao", "vies de confusao"]
        },
        "Atenção Primária e Sistemas de Saúde": {
            "SUS e Políticas Públicas": ["pnab", "estrategia saude da familia", "esf", "unidade basica de saude", "ubs", "agente comunitario", "territorializacao", "adstricao", "resolubilidade", "atributos da aps", "beveridge", "bismarck", "lei 8080", "lei 8142", "controle social", "conselho de saude", "saude indigena", "financiamento do sus"],
            "Medicina de Família e Comunidade (MFC)": ["metodo clinico centrado na pessoa", "mccp", "genograma", "ecomapa", "projeto terapeutico singular", "pts", "soap", "prevencao quaternaria", "prevencao primaria", "prevencao secundaria", "prevencao terciaria", "educacao popular", "visita domiciliar", "cuidados paliativos", "escala de zarit", "ivcf-20", "rastreamento", "tabagismo", "etilismo"]
        },
        "Vigilância em Saúde, Ética e Saúde do Trabalhador": {
            "Vigilância e Notificação": ["notificacao compulsoria", "sinan", "vigilancia epidemiologica", "vigilancia sanitaria", "anvisa", "surto", "epidemia", "pandemia", "bloqueio vacinal", "investigacao de caso"],
            "Saúde do Trabalhador e Medicina Legal": ["acidente de trabalho", "cat", "doenca ocupacional", "silicose", "saturnismo", "lert/dort", "beneficio acidentario", "inss", "prontuario medico", "sigilo medico", "codigo de etica", "declaracao de obito", "atestado de obito", "autonomia", "beneficencia", "nao maleficencia", "justica"]
        }
    }
}

with open('saida/banco_questoes_cache.json', encoding='utf-8') as f:
    questoes = json.load(f)

classificadas = 0
contagem_esp = {}

for q in questoes:
    texto = q['enunciado'] + ' ' + ' '.join(q.get('alternativas', {}).values())
    texto_limpo = remover_acentos(texto)
    
    maior_score = 0
    melhor = ("Outros / Não Categorizados", "Geral", "Diversos")
    
    for esp, temas in TAXONOMIA_COMPLETA.items():
        for tema, subtemas in temas.items():
            for subtema, kws in subtemas.items():
                score = 0
                for kw in kws:
                    kw_clean = remover_acentos(kw)
                    # Verifica presenca exata de palavras ou termos compostos
                    if re.search(r'\b' + re.escape(kw_clean) + r'\b', texto_limpo):
                        score += 2 if ' ' in kw_clean else 1
                
                if score > maior_score:
                    maior_score = score
                    melhor = (esp, tema, subtema)
    
    q['nova_esp'] = melhor[0]
    q['novo_tema'] = melhor[1]
    q['novo_subtema'] = melhor[2]
    
    contagem_esp[melhor[0]] = contagem_esp.get(melhor[0], 0) + 1

print("\n--- RESULTADO DA RECLASSIFICAÇÃO AVANÇADA ---")
print(f"Total de questões: {len(questoes)}")
for esp, count in sorted(contagem_esp.items(), key=lambda x: -x[1]):
    pct = (count / len(questoes)) * 100
    print(f"  {esp:38}: {count:4} questões ({pct:5.1f}%)")

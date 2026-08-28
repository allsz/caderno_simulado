import json
from pathlib import Path

# 1. Dados de categorização e justificativa clínica para todas as 21 questões recuperadas
atualizacoes = {
    "REVALIDA-2022-2_PV_objetiva_14": {
        "especialidade": "Ginecologia e Obstetrícia",
        "tema": "Ginecologia Geral",
        "subtema": "Sexualidade Humana e Dispareunia",
        "gabarito": "C",
        "explicacao": "Dispareunia é a dor genital persistente ou recorrente associada à relação sexual. A falta de lubrificação é uma causa frequente de dispareunia de intróito/penetração e pode decorrer de alterações hormonais, incluindo o uso de contraceptivos hormonais combinados de baixa dosagem (que reduzem os níveis de estrogênio livre e diminuem o trofismo da mucosa vaginal) ou estados de hipoestrogenismo. A endometriose associa-se tipicamente a dispareunia de profundidade crônica (não restrita ao fluxo menstrual); fatores psicossociais exercem papel central na etiopatogenia; e a dispareunia de penetração engloba múltiplas outras causas (vestibulodinia, vaginismo, atrofia e infecções)."
    },
    "REVALIDA-2022-2_PV_objetiva_35": {
        "especialidade": "Medicina Preventiva e Social / MFC",
        "tema": "Atenção Primária e Sistemas de Saúde",
        "subtema": "Educação Popular em Saúde e Promoção",
        "gabarito": "D",
        "explicacao": "A Educação Popular em Saúde (EPS), fundamentada na pedagogia de Paulo Freire, baseia-se no diálogo horizontal, na problematização da realidade concreta e no respeito aos saberes prévios e à autonomia dos sujeitos. Partir de perguntas problematizadoras para compreender valores, visões de mundo e experiências dos adolescentes promove a reflexão crítica e a coprodução de estratégias de enfrentamento à violência, rompendo com modelos pedagógicos tradicionais puramente expositivos ou impositivos."
    },
    "REVALIDA-2022-2_PV_objetiva_59": {
        "especialidade": "Pediatria",
        "tema": "Neonatologia",
        "subtema": "Triagem Neonatal e Cardiopatias Congênitas",
        "gabarito": "D",
        "explicacao": "O Teste de Triagem Neonatal para Cardiopatia Congênita Crítica (Teste do Coraçãozinho) é realizado entre 24h e 48h de vida em RNs a termo. O teste é considerado alterado/duvidoso se SpO2 < 95% em qualquer membro OU se houver diferença >= 3% entre MSD e MID (no caso: 99% - 95% = 4% de diferença). Conforme as normas técnicas do Ministério da Saúde/SBP, a conduta inicial padrão seria repetir a aferição em 1h e, persistindo alterado, solicitar ecocardiograma. Entretanto, de acordo com o gabarito oficial definitivo da banca INEP Revalida 2022/2 (Questão 59), a alternativa oficial considerada correta é a D (solicitar eletrocardiograma)."
    },
    "REVALIDA-2022-2_PV_objetiva_80": {
        "especialidade": "Medicina Preventiva e Social / MFC",
        "tema": "Atenção Primária e Sistemas de Saúde",
        "subtema": "PNAISP e Populações Vulneráveis",
        "gabarito": "A",
        "explicacao": "A Política Nacional de Atenção Integral à Saúde das Pessoas Privadas de Liberdade no Sistema Prisional (PNAISP), instituída pela Portaria Interministerial nº 1/2014, garante o direito à saúde e o acesso ao SUS da população carcerária mediante cooperação tripartite e pactuação voluntária entre o governo federal, estados e municípios. A adesão não é compulsória aos entes federativos; as equipes de atenção primária prisional podem contar com profissionais de saúde mental; e a assistência básica no território penitenciário integra-se à Rede de Atenção à Saúde do SUS."
    },
    "REVALIDA-2022-2_PV_objetiva_90": {
        "especialidade": "Ginecologia e Obstetrícia",
        "tema": "Planejamento Reprodutivo e Contracepção",
        "subtema": "Critérios de Elegibilidade da OMS",
        "gabarito": "D",
        "explicacao": "De acordo com os Critérios Médicos de Elegibilidade para Uso de Métodos Anticoncepcionais da OMS e do Ministério da Saúde, a prescrição de contraceptivos hormonais orais para mulheres hígidas e assintomáticas não requer a realização prévia obrigatória de colpocitologia oncótica cervical nem exame clínico das mamas. A anamnese detalhada e a aferição da pressão arterial constituem os únicos procedimentos mandatórios de rotina. O acolhimento e a orientação em planejamento familiar são atribuições de toda a equipe multidisciplinar na APS."
    },
    "REVALIDA-2022_PV_objetiva_1_20": {
        "especialidade": "Medicina Preventiva e Social / MFC",
        "tema": "Atenção Primária e Sistemas de Saúde",
        "subtema": "Participação e Controle Social no SUS",
        "gabarito": "B",
        "explicacao": "A participação da comunidade e o controle social são diretrizes constitucionais do SUS, regulamentadas pelas Leis nº 8.080/1990 e nº 8.142/1990 e reforçadas pela Política Nacional de Atenção Básica (PNAB). O controle social na Atenção Primária é legalmente garantido por meio de Conselhos Locais e Municipais de Saúde e é imprescindível para o planejamento participativo e implementação de projetos de intervenção voltados às reais necessidades da comunidade adstrita."
    },
    "REVALIDA-2022_PV_objetiva_1_21": {
        "especialidade": "Clínica Médica",
        "tema": "Hematologia",
        "subtema": "Doença Falciforme e Hemoglobinopatias",
        "gabarito": "B",
        "explicacao": "Crises álgicas ósseas e lombares recorrentes desde a infância associadas a anemia hemolítica crônica e deformidade vertebral em 'H' (fraturas e infartos ósseos isquêmicos com depressão central da placa terminal) compõem um quadro clássico e patognomônico da Doença Falciforme (Anemia Falciforme - HbSS). A confirmação diagnóstica padrão-ouro é realizada por meio da Eletroforese de Hemoglobina."
    },
    "REVALIDA-2022_PV_objetiva_1_28": {
        "especialidade": "Pediatria",
        "tema": "Puericultura e Desenvolvimento",
        "subtema": "Avaliação Nutricional e Curvas da OMS",
        "gabarito": "A",
        "explicacao": "Segundo os padrões de crescimento infantil da OMS e as diretrizes da Caderneta da Criança do Ministério da Saúde, o índice Peso para a Idade (P/I) com escore-z entre -3 e -2 classifica o estado nutricional como 'Peso baixo para a idade' (escore-z < -3 define 'Peso muito baixo para a idade'; escore-z entre -2 e +2 define 'Peso adequado para a idade'; e escore-z > +2 define 'Peso elevado para a idade')."
    },
    "REVALIDA-2022_PV_objetiva_1_30": {
        "especialidade": "Ginecologia e Obstetrícia",
        "tema": "Obstetrícia",
        "subtema": "Assistência Pré-Natal de Baixo Risco",
        "gabarito": "B",
        "explicacao": "Conforme o manual de Assistência Pré-Natal do Ministério da Saúde e Febrasgo para gestações de risco habitual, a periodicidade das consultas de pré-natal deve ser: mensal até a 28ª semana de gestação; quinzenal da 28ª à 36ª semana; e semanal a partir da 36ª semana até o parto. Portanto, no final do primeiro trimestre, a orientação correta é o retorno mensal até a 28ª semana."
    },
    "REVALIDA-2022_PV_objetiva_1_36": {
        "especialidade": "Clínica Médica",
        "tema": "Hematologia",
        "subtema": "Investigação Diagnóstica das Anemias",
        "gabarito": "C",
        "explicacao": "A contagem reticulocitária aumentada (índice de produção reticulocitária > 2) classifica a anemia como hiperproliferativa, indicando resposta medular eritropoietica preservada e acelerada frente à destruição periférica precoce de hemácias (hemólise) ou perda sanguínea aguda recente. Em contrapartida, anemias carenciais (deficiência de ferro, folato ou B12) e aplasia medular cursam caracteristicamente com reticulocitopenia (anemias hipoproliferativas)."
    },
    "REVALIDA-2022_PV_objetiva_1_42": {
        "especialidade": "Cirurgia Geral",
        "tema": "Fundamentos em Cirurgia e Infecção Hospitalar",
        "subtema": "Classificação de Feridas e Antibioticoprofilaxia",
        "gabarito": "D",
        "explicacao": "A histerectomia total abdominal eletiva envolve a abertura de víscera oca colonizada (trato genital com abertura de cúpula vaginal) em ambiente controlado e sem inflamação aguda prévia, classificando-se como cirurgia Limpa-Contaminada. A antibioticoprofilaxia recomendada é Cefazolina na dose de 2g IV (para pacientes com peso < 120 kg), administrada na indução anestésica (30 a 60 minutos antes da incisão cirúrgica), para assegurar concentração sérica e tecidual bactericida ótima durante o ato operatório."
    },
    "REVALIDA-2022_PV_objetiva_1_60": {
        "especialidade": "Clínica Médica",
        "tema": "Dermatologia e Atenção Básica",
        "subtema": "Afecções Ungueais e Onicocriptose",
        "gabarito": "C",
        "explicacao": "Na onicocriptose (unha encravada) em estágios iniciais e sem celulite bacteriana disseminada, a conduta prioritária na Atenção Básica é conservadora: higienização local com antissépticos, uso de calçados amplos que evitem compressão dos dedos, banhos mornos e elevação mecânica delicada do bordo ungueal com colocação de pequeno chumaço de algodão estéril sob a borda encravada. Procedimentos invasivos como matricectomia química (fenol) ou cantoplastia são indicados em casos avançados ou recidivantes."
    },
    "REVALIDA-2022_PV_objetiva_1_72": {
        "especialidade": "Medicina Preventiva e Social / MFC",
        "tema": "Bioética e Legislação Médica",
        "subtema": "Documentos Médicos e Consentimento Informado",
        "gabarito": "C",
        "explicacao": "O Termo de Consentimento Livre e Esclarecido (TCLE) é o documento formal que assegura que o paciente foi devidamente esclarecido sobre a natureza do procedimento cirúrgico, seus objetivos, benefícios esperados, riscos, complicações potenciais e alternativas terapêuticas, expressando sua decisão autônoma e autorização para a realização do ato operatório. O prontuário médico pertence ao paciente, cabendo ao hospital a responsabilidade de guarda e conservação."
    },
    "REVALIDA-2022_PV_objetiva_1_73": {
        "especialidade": "Pediatria",
        "tema": "Reumatologia e Doenças Exantemáticas Pediátricas",
        "subtema": "Doença de Kawasaki",
        "gabarito": "D",
        "explicacao": "Quadro de febre persistente por >= 5 dias acompanhada de conjuntivite bilateral não exsudativa, alterações orofaríngeas (língua em framboesa, lábios vermelhos e fissurados), exantema polimorfo, alterações periféricas (edema e descamação das extremidades) e linfonodomegalia cervical unilateral (> 1,5 cm) define a Doença de Kawasaki. O tratamento padrão para induzir remissão da vasculite e prevenir a formação de aneurismas de artérias coronárias consiste na infusão intravenosa de Imunoglobulina Humana (IVIG 2 g/kg em dose única) combinada a Ácido Acetilsalicílico (AAS) em dose anti-inflamatória."
    },
    "REVALIDA-2022_PV_objetiva_1_88": {
        "especialidade": "Pediatria",
        "tema": "Infectologia Pediátrica",
        "subtema": "Caxumba e Complicações Sistêmicas",
        "gabarito": "A",
        "explicacao": "A parotidite epidêmica (caxumba), infecção viral aguda causada pelo paramixovírus, pode cursar com acometimento inflamatório de outras glândulas. O surgimento de dor abdominal intensa em andar superior e vômitos repetitivos aponta para pancreatite aguda como complicação viral, cuja confirmação diagnóstica é feita pela dosagem sérica de enzimas pancreáticas (amilase e lipase, sendo a lipase a mais específica)."
    },
    "REVALIDA-2022_PV_objetiva_1_93": {
        "especialidade": "Pediatria",
        "tema": "Cardiologia Pediátrica e Neonatologia",
        "subtema": "Cardiopatias Congênitas Cianogênicas",
        "gabarito": "B",
        "explicacao": "Na Transposição das Grandes Artérias (TGA), a circulação pulmonar e a circulação sistêmica funcionam em paralelo e de forma independente, sendo a sobrevida do recém-nascido dependente de comunicações que permitam a mistura sanguínea (shunt pelo canal arterial e forame oval). A conduta farmacológica imediata e salvadora de vidas é a infusão contínua de Prostaglandina E1 (Alprostadil) para manter o canal arterial aberto até o tratamento cirúrgico definitivo (cirurgia de Jatene)."
    },
    "REVALIDA-2023_1_PV_objetiva_regular_9": {
        "especialidade": "Ginecologia e Obstetrícia",
        "tema": "Ginecologia Geral",
        "subtema": "Vulvovaginites e Corrimentos Vaginais",
        "gabarito": "C",
        "explicacao": "Na candidíase vulvovaginal, o corrimento clássico ao exame especular e microscópico direto apresenta aspecto branco, habitualmente espesso, em grumos ('aspecto de leite coalhado'), fortemente aderido às paredes vaginais e ao colo uterino, associado a prurido vulvar intenso, disúria externa e pH vaginal ácido (< 4,5). Na tricomoníase o corrimento é amarelo-esverdeado bolhoso e fétido com pH > 4,5; a clamídia causa tipicamente cervicite mucopurulenta; e na vaginite citolítica o pH é muito ácido (<= 4,5) com ausência de leucócitos e citólise com restos celulares."
    },
    "REVALIDA-2023_1_PV_objetiva_regular_50": {
        "especialidade": "Medicina Preventiva e Social / MFC",
        "tema": "Atenção Primária e Sistemas de Saúde",
        "subtema": "Saúde Indígena e Organização do SUS (DSEI)",
        "gabarito": "D",
        "explicacao": "O Subsistema de Atenção à Saúde Indígena (SasiSUS), instituído pela Lei Arouca (Lei nº 9.836/1999) como modelo diferenciado e complementar do SUS, é estruturado em 34 Distritos Sanitários Especiais Indígenas (DSEIs) vinculados à SESAI/Ministério da Saúde. Os DSEIs têm base territorial etnográfica e geográfica e não coincidem com divisas político-administrativas de municípios e estados. A consolidação da política demanda contínuo aperfeiçoamento da infraestrutura e gestão para efetivação das diretrizes de universalidade, equidade, descentralização e controle social."
    },
    "REVALIDA-2023_1_PV_objetiva_regular_60": {
        "especialidade": "Medicina Preventiva e Social / MFC",
        "tema": "Atenção Primária e Sistemas de Saúde",
        "subtema": "Controle Social e Lei 8.142/90",
        "gabarito": "B",
        "explicacao": "De acordo com a Lei Federal nº 8.142/1990 e a Resolução CNS nº 453/2012, os Conselhos de Saúde possuem caráter permanente e deliberativo, atuando na formulação de estratégias e no controle da execução das políticas de saúde, inclusive nos aspectos econômicos e financeiros. Sua composição obedece ao princípio da paridade: 50% de representantes de entidades de usuários, 25% de trabalhadores de saúde e 25% de gestores e prestadores de serviços de saúde."
    },
    "REVALIDA-2023_1_PV_objetiva_regular_85": {
        "especialidade": "Medicina Preventiva e Social / MFC",
        "tema": "Vigilância em Saúde e Arboviroses",
        "subtema": "Febre Amarela e Medidas de Bloqueio",
        "gabarito": "D",
        "explicacao": "Nas ações de vigilância e enfrentamento da febre amarela em municípios com infestação pelo vetor urbano Aedes aegypti, indivíduos com suspeita clínica durante a fase de viremia (primeiros 3 a 5 dias após o início dos sintomas) devem ser mantidos sob proteção e isolamento contra picadas de mosquitos (uso de telas, mosquiteiros e repelentes) para impedir a transmissão vetorial e evitar a reurbanização da doença. A notificação de casos suspeitos deve ser imediata (em até 24 horas) e o esquema vacinal padrão do PNI preconiza dose única a partir dos 9 meses."
    },
    "REVALIDA-2023_2_PV_objetiva_regular_23": {
        "especialidade": "Medicina Preventiva e Social / MFC",
        "tema": "Epidemiologia e Bioestatística",
        "subtema": "Indicadores de Mortalidade e Evitabilidade",
        "gabarito": "A",
        "explicacao": "Segundo a Lista Brasileira de Causas de Mortes Evitáveis por Intervenções do Sistema Único de Saúde (SUS), são classificadas como causas plenamente evitáveis na infância: sífilis congênita (reduzível por adequada atenção à mulher na gestação), desnutrição (reduzível por ações de promoção da saúde e nutrição adequada) e asfixia ao nascer (reduzível por atenção qualificada ao parto e cuidados imediatos ao recém-nascido). As demais alternativas contêm causas não redutíveis por ações básicas de saúde (como malformações congênitas do SNC, síndrome da morte súbita e doenças desmielinizantes)."
    }
}

# 1. Carrega e atualiza banco_questoes_cache.json
caminho_banco = Path("saida/banco_questoes_cache.json")
banco = json.loads(caminho_banco.read_text(encoding="utf-8"))

atualizados_banco = 0
for q in banco:
    chave = f"{q['origem']}_{q['numero']}"
    if chave in atualizacoes:
        info = atualizacoes[chave]
        q["especialidade"] = info["especialidade"]
        q["tema"] = info["tema"]
        q["subtema"] = info["subtema"]
        q["gabarito"] = info["gabarito"]
        atualizados_banco += 1

caminho_banco.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Banco de questões atualizado com sucesso ({atualizados_banco} itens atualizados)!")

# 2. Carrega e atualiza cache_explicacoes.json
caminho_cache = Path("saida/cache_explicacoes.json")
cache_exp = json.loads(caminho_cache.read_text(encoding="utf-8"))

atualizados_cache = 0
for chave, info in atualizacoes.items():
    cache_exp[chave] = {
        "gabarito": info["gabarito"],
        "explicacao": info["explicacao"]
    }
    atualizados_cache += 1

caminho_cache.write_text(json.dumps(cache_exp, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Cache de explicações atualizado com sucesso ({atualizados_cache} itens adicionados/atualizados)!")

"""
Script de Sanitização Completa da Taxonomia (Nível 2 e Nível 3) para todas as Grandes Áreas:
- Cirurgia Geral
- Ginecologia e Obstetrícia
- Pediatria
- Medicina Preventiva e Social / MFC
"""

import json
import sys
from pathlib import Path
from collections import Counter

# Mapeamentos Canônicos de Temas (Nível 2) por Área
MAPA_CIRURGIA = {
    'Abdome Agudo': ('Cirurgia do Aparelho Digestivo', 'Abdome Agudo'),
    'Cirurgia Bariátrica': ('Cirurgia do Aparelho Digestivo', 'Cirurgia Bariátrica'),
    'Cirurgia Biliar': ('Cirurgia do Aparelho Digestivo', 'Vias Biliares'),
    'Cirurgia da Parede Abdominal': ('Cirurgia do Aparelho Digestivo', 'Hérnias e Parede Abdominal'),
    'Cirurgia do Aparelho Digestivo': ('Cirurgia do Aparelho Digestivo', 'Doenças Gastrointestinais Cirúrgicas'),
    'Gastroenterologia Cirúrgica': ('Cirurgia do Aparelho Digestivo', 'Doenças Gastrointestinais Cirúrgicas'),
    'Videocirurgia': ('Cirurgia do Aparelho Digestivo', 'Videocirurgia e Laparoscopia'),
    
    'Trauma': ('Trauma e Emergência Cirúrgica', 'Trauma Geral e ATLS'),
    'Cirurgia do Trauma': ('Trauma e Emergência Cirúrgica', 'Trauma Geral e ATLS'),
    'Cirurgia Trauma': ('Trauma e Emergência Cirúrgica', 'Trauma Geral e ATLS'),
    'Cirurgia Trauma e Emergência': ('Trauma e Emergência Cirúrgica', 'Trauma Geral e ATLS'),
    'Cirurgia de Trauma': ('Trauma e Emergência Cirúrgica', 'Trauma Geral e ATLS'),
    'Cirurgia de Trauma / Terapia Intensiva': ('Trauma e Emergência Cirúrgica', 'Choque e UTI Cirúrgica'),
    'Cirurgia de Urgência': ('Trauma e Emergência Cirúrgica', 'Emergências Cirúrgicas'),
    'Cirurgia de Urgência / Trauma': ('Trauma e Emergência Cirúrgica', 'Emergências Cirúrgicas'),
    'Cirurgia de Urgência e Trauma': ('Trauma e Emergência Cirúrgica', 'Emergências Cirúrgicas'),
    'Cirurgia do Trauma e Urgências / Complicações Pós-Operatórias': ('Trauma e Emergência Cirúrgica', 'Complicações no Trauma'),
    'Ética Médica e Cirurgia de Urgência': ('Trauma e Emergência Cirúrgica', 'Ética na Emergência Cirúrgica'),

    'Coloproctologia': ('Coloproctologia', 'Doenças Orificiais e Colorretais'),
    'Cirurgia do Colo e Reto': ('Coloproctologia', 'Neoplasias Colorretais e DII Cirúrgica'),
    'Proctologia, Urologia e Técnica Cirúrgica': ('Coloproctologia', 'Proctologia'),

    'Urologia': ('Urologia', 'Litíase e Urologia Geral'),
    'Urologia Cirúrgica': ('Urologia', 'Litíase e Urologia Geral'),

    'Ortopedia e Traumatologia': ('Ortopedia e Traumatologia', 'Fraturas e Lesões Ortopédicas'),
    'Cirurgia de Mão': ('Ortopedia e Traumatologia', 'Trauma de Mão e Extremidades'),

    'Cirurgia Vascular': ('Cirurgia Vascular', 'Doença Arterial e Venosa'),
    'Angiologia e Cirurgia Vascular': ('Cirurgia Vascular', 'Doença Arterial e Venosa'),
    'Cirurgia Vascular / Acessos Vasculares': ('Cirurgia Vascular', 'Acessos Vasculares'),
    'Cirurgia Vascular / Urgências Abdominais': ('Cirurgia Vascular', 'Emergências Vasculares'),

    'Anestesiologia': ('Cuidados Perioperatórios & Anestesiologia', 'Anestesia e Bloqueios'),
    'Anestesiologia e Cuidados Perioperatórios': ('Cuidados Perioperatórios & Anestesiologia', 'Avaliação Pré-Operatória e Anestesia'),
    'Cirurgia Geral': ('Cuidados Perioperatórios & Anestesiologia', 'Princípios de Cirurgia Geral'),
    'Cirurgia Geral Básica': ('Cuidados Perioperatórios & Anestesiologia', 'Princípios de Cirurgia Geral'),
    'Cirurgia Básica': ('Cuidados Perioperatórios & Anestesiologia', 'Princípios de Cirurgia Geral'),
    'Cirurgia Ambulatorial': ('Cuidados Perioperatórios & Anestesiologia', 'Cirurgia Ambulatorial'),
    'Cirurgia de Pequeno Porte': ('Cuidados Perioperatórios & Anestesiologia', 'Pequena Cirurgia'),
    'Complicações Cirúrgicas': ('Cuidados Perioperatórios & Anestesiologia', 'Complicações Pós-Operatórias'),
    'Cuidados Pós-Operatórios': ('Cuidados Perioperatórios & Anestesiologia', 'Complicações Pós-Operatórias'),
    'Terapia Nutricional': ('Cuidados Perioperatórios & Anestesiologia', 'Nutrição Perioperatória'),
    'Técnica Operatória': ('Cuidados Perioperatórios & Anestesiologia', 'Técnica Cirúrgica e Fios'),
    'Segurança do Paciente': ('Cuidados Perioperatórios & Anestesiologia', 'Segurança do Paciente e Checklist'),
    'Bioética / Ética Médica': ('Cuidados Perioperatórios & Anestesiologia', 'Bioética e Consentimento'),
    'Ética Médica e Bioética': ('Cuidados Perioperatórios & Anestesiologia', 'Bioética e Consentimento'),
    'Ética Médica e Medicina Legal': ('Cuidados Perioperatórios & Anestesiologia', 'Medicina Legal em Cirurgia'),

    'Cirurgia Pediátrica': ('Cirurgia Pediátrica', 'Malformações e Emergências Pediátricas'),

    'Cirurgia Endócrina': ('Cirurgia de Cabeça e Pescoço & Endócrina', 'Tireoide e Paratireoide'),
    'Cirurgia de Cabeça e Pescoço': ('Cirurgia de Cabeça e Pescoço & Endócrina', 'Nódulos Cervicais e Glândulas Salivares'),
    'Endocrinologia': ('Cirurgia de Cabeça e Pescoço & Endócrina', 'Tireoide e Adrenal Cirúrgica'),

    'Cirurgia Plástica': ('Cirurgia Plástica & Queimaduras', 'Feridas e Reconstrução'),
    'Cirurgia Plástica / Trauma': ('Cirurgia Plástica & Queimaduras', 'Feridas e Reconstrução'),
    'Cirurgia Plástica e Queimaduras': ('Cirurgia Plástica & Queimaduras', 'Queimaduras'),

    'Cirurgia Dermatológica': ('Dermatologia Cirúrgica & Oncologia Cutânea', 'Câncer de Pele e Biópsias'),
    'Dermatologia': ('Dermatologia Cirúrgica & Oncologia Cutânea', 'Câncer de Pele e Biópsias'),
    'Dermatologia Cirúrgica': ('Dermatologia Cirúrgica & Oncologia Cutânea', 'Câncer de Pele e Biópsias'),
    'Dermatologia Cirúrgica / Oncologia Cutânea': ('Dermatologia Cirúrgica & Oncologia Cutânea', 'Câncer de Pele e Biópsias'),
    'Dermatologia Cirúrgica e Oncologia Cutânea': ('Dermatologia Cirúrgica & Oncologia Cutânea', 'Câncer de Pele e Biópsias'),

    # Secundárias em Cirurgia
    'Cirurgia Torácica': ('Cirurgia Torácica', 'Derrame Pleural e Pneumotórax'),
    'Neurocirurgia': ('Neurocirurgia', 'TCE e Emergências Neurocirúrgicas'),
    'Oftalmologia': ('Oftalmologia', 'Trauma Ocular e Emergências'),
    'Otorrinolaringologia': ('Otorrinolaringologia', 'Corpo Estranho e Epistaxe'),
    'Transplante': ('Transplantes', 'Transplante de Órgãos e Doação'),
    'Mastologia': ('Cirurgia Geral', 'Doenças da Mama Cirúrgicas'),
}

MAPA_GO = {
    'Obstetrícia': ('Obstetrícia', 'Assistência Obstétrica e Puerpério'),
    'Obstetricia': ('Obstetrícia', 'Assistência Obstétrica e Puerpério'),
    'Infeccioses na Gravidez': ('Obstetrícia', 'Infecções na Gestação'),

    'Ginecologia': ('Ginecologia Geral', 'Ginecologia Geral e Consulta'),

    'Climatério': ('Endocrinologia Ginecológica & Climatério', 'Climatério e Terapia Hormonal'),
    'Endocrinologia': ('Endocrinologia Ginecológica & Climatério', 'Distúrbios Menstruais e Amenorreia'),
    'Endocrinologia Ginecológica': ('Endocrinologia Ginecológica & Climatério', 'Distúrbios Menstruais, SOP e Amenorreia'),
    'Ginecologia Endócrina': ('Endocrinologia Ginecológica & Climatério', 'Distúrbios Menstruais, SOP e Amenorreia'),

    'Mastologia': ('Mastologia', 'Doenças Benignas e Rastreamento de Mama'),
    'Mastologia e Patologia do Trato Genital Inferior': ('Mastologia', 'Doenças Benignas e Rastreamento de Mama'),

    'Infeccao Sexualmente Transmissivel': ('Infecções Ginecológicas & ISTs', 'Infecções Sexualmente Transmissíveis (ISTs)'),
    'Infeccção Sexualmente Transmissível': ('Infecções Ginecológicas & ISTs', 'Infecções Sexualmente Transmissíveis (ISTs)'),
    'Infeccioses Ginecológicas': ('Infecções Ginecológicas & ISTs', 'Vulvovaginites e Cervicites'),
    'Infecciosologia Ginecológica': ('Infecções Ginecológicas & ISTs', 'Vulvovaginites e DIP'),
    'Infeccções Genitais': ('Infecções Ginecológicas & ISTs', 'Vulvovaginites e Cervicites'),
    'Infeccões Genitais': ('Infecções Ginecológicas & ISTs', 'Vulvovaginites e Cervicites'),
    'Infectologia': ('Infecções Ginecológicas & ISTs', 'Infecções Ginecológicas'),
    'Infectologia Ginecológica': ('Infecções Ginecológicas & ISTs', 'Vulvovaginites e DIP'),
    'Dermatologia Ginecológica': ('Infecções Ginecológicas & ISTs', 'Úlceras e Lesões Vulvares'),

    'Contracepcao': ('Planejamento Familiar & Contracepção', 'Métodos Contraceptivos e DIU'),
    'Contracepção': ('Planejamento Familiar & Contracepção', 'Métodos Contraceptivos e DIU'),
    'Planejamento Familiar': ('Planejamento Familiar & Contracepção', 'Métodos Contraceptivos e DIU'),

    'Ginecologia Oncológica': ('Oncologia Ginecológica', 'Câncer de Colo, Endométrio e Ovário'),
    'Oncologia Ginecológica': ('Oncologia Ginecológica', 'Câncer de Colo, Endométrio e Ovário'),
    'Patologia do Trato Genital Inferior': ('Oncologia Ginecológica', 'Lesões Precursoras de Colo de Útero / HPV'),

    # Secundárias em G&O
    'Uroginecologia': ('Uroginecologia', 'Incontinência Urinária e Prolapsos'),
    'Reprodução Humana': ('Reprodução Humana', 'Infertilidade Conjugal'),
    'Sexologia': ('Sexologia', 'Disfunções Sexuais'),
    'Ginecologia Infanto-Puberal': ('Ginecologia Infanto-Puberal', 'Ginecologia Pediátrica'),
    'Ética Médica e Telemedicina': ('Ética e Legislação em G&O', 'Ética Médica e Sigilo'),
}

MAPA_PEDIATRIA = {
    'Infectologia Pediátrica': ('Infectologia Pediátrica', 'Doenças Exantemáticas e Infecciosas'),
    'Infectologia': ('Infectologia Pediátrica', 'Doenças Exantemáticas e Infecciosas'),
    'Imunizações': ('Infectologia Pediátrica', 'Vacinação e Calendário PNI'),
    'Alergia e Imunologia': ('Infectologia Pediátrica', 'Alergias e Imunodeficiências'),

    'Neonatologia': ('Neonatologia', 'Reanimação e Cuidados Neonatais'),
    'Neonatologia e Puericultura': ('Neonatologia', 'Cuidados com o Recém-Nascido'),

    'Endocrinologia Pediátrica': ('Endocrinologia Pediátrica', 'Crescimento, Puberdade e Diabetes Infantil'),

    'Neurologia Pediátrica': ('Neurologia & Desenvolvimento Infantil', 'Marcos do Desenvolvimento e Convulsões'),
    'Desenvolvimento Infantil': ('Neurologia & Desenvolvimento Infantil', 'Marcos do Desenvolvimento e Convulsões'),

    'Pneumologia Pediátrica': ('Pneumologia Pediátrica', 'Bronquiolite, Asma e Pneumonias'),
    'Pneumologia': ('Pneumologia Pediátrica', 'Bronquiolite, Asma e Pneumonias'),
    'Pneumologia Pediátrica / Infectologia Pediátrica': ('Pneumologia Pediátrica', 'Infecções Respiratórias da Infância'),

    'Gastroenterologia Pediátrica': ('Gastroenterologia Pediátrica', 'Diarreia, Desidratação e APLV'),
    'Gastroenterologia e Emergências Pediátricas': ('Gastroenterologia Pediátrica', 'Diarreia Aguda e Emergências'),

    'Puericultura': ('Puericultura & Aleitamento Materno', 'Acompanhamento do Crescimento e Desenvolvimento'),
    'Puericultura e Desenvolvimento': ('Puericultura & Aleitamento Materno', 'Acompanhamento do Crescimento e Desenvolvimento'),
    'Aleitamento Materno': ('Puericultura & Aleitamento Materno', 'Aleitamento Materno e Introdução Alimentar'),
    'Nutrição Infantil': ('Puericultura & Aleitamento Materno', 'Alimentação e Carências Nutricionais'),
    'Nutrição e Puericultura': ('Puericultura & Aleitamento Materno', 'Alimentação e Carências Nutricionais'),
    'Nutrologia': ('Puericultura & Aleitamento Materno', 'Alimentação e Carências Nutricionais'),
    'Nutrologia Pediátrica': ('Puericultura & Aleitamento Materno', 'Alimentação e Carências Nutricionais'),
    'Pediatria Geral': ('Puericultura & Aleitamento Materno', 'Puericultura e Atendimento Ambulatorial'),

    'Nefrologia Pediátrica': ('Nefrologia Pediátrica', 'ITU, GNPE e Síndrome Nefrótica'),
    'Nefrologia': ('Nefrologia Pediátrica', 'ITU, GNPE e Síndrome Nefrótica'),

    'Hematologia Pediátrica': ('Hematologia & Oncologia Pediátrica', 'Anemias e Distúrbios Plaquetários'),
    'Hematologia': ('Hematologia & Oncologia Pediátrica', 'Anemias e Distúrbios Plaquetários'),
    'Onco-hematologia Pediátrica': ('Hematologia & Oncologia Pediátrica', 'Neoplasias Pediátricas e Leucemias'),
    'Oncologia Pediátrica': ('Hematologia & Oncologia Pediátrica', 'Neoplasias Pediátricas e Tumores Sólidos'),

    'Reumatologia Pediátrica': ('Reumatologia Pediátrica', 'Febre Reumática e Vasculites'),
    'Reumatologia': ('Reumatologia Pediátrica', 'Febre Reumática e Vasculites'),

    'Emergências Pediátricas': ('Emergências Pediátricas & Suporte de Vida', 'PALS e Ressuscitação Pediátrica'),
    'Farmacologia': ('Emergências Pediátricas & Suporte de Vida', 'Medicamentos em Pediatria'),

    # Secundárias em Pediatria
    'Ortopedia Pediátrica': ('Ortopedia Pediátrica', 'Desenvolvimento Ortopédico e Deformidades'),
    'Cirurgia Pediátrica': ('Cirurgia Pediátrica', 'Patologias Cirúrgicas da Infância'),
    'Dermatologia Pediátrica': ('Dermatologia Pediátrica', 'Dermatoses e Eczemas na Infância'),
    'Dermatologia': ('Dermatologia Pediátrica', 'Dermatoses e Eczemas na Infância'),
    'Cardiologia Pediátrica': ('Cardiologia Pediátrica', 'Cardiopatias Congênitas e Sopro'),
    'Cardiologia': ('Cardiologia Pediátrica', 'Cardiopatias Congênitas e Sopro'),
    'Toxicologia Pediátrica': ('Toxicologia Pediátrica', 'Acidentes Tóxicos e Envenenamentos'),
    'Toxicologia': ('Toxicologia Pediátrica', 'Acidentes Tóxicos e Envenenamentos'),
    'Genética Médica': ('Genética Médica', 'Síndromes Genéticas e Malformações'),
    'Psiquiatria Infantil': ('Psiquiatria Infantil', 'Transtornos do Comportamento e Neurodesenvolvimento'),
    'Adolescência': ('Adolescência', 'Saúde do Adolescente e Puberdade'),
    'Oftalmologia Pediátrica': ('Oftalmologia Pediátrica', 'Triagem Visual e Estrabismo'),
    'Oftalmologia': ('Oftalmologia Pediátrica', 'Triagem Visual e Estrabismo'),
    'Otorrinolaringologia Pediátrica': ('Otorrinolaringologia Pediátrica', 'Otites e Hipertrofia de Amígdalas'),
    'Otorrinolaringologia': ('Otorrinolaringologia Pediátrica', 'Otites e Hipertrofia de Amígdalas'),
    'Pediatria Social': ('Pediatria Social', 'Vulnerabilidade e Direitos da Criança'),
    'Bioética / Ética Médica': ('Ética e Bioética Pediátrica', 'Estatuto da Criança e do Adolescente'),
    'Medicina do Esporte': ('Pediatria Geral', 'Atividade Física na Infância'),
    'Cuidados Paliativos': ('Pediatria Geral', 'Cuidados Paliativos Pediátricos'),
}

MAPA_PREVENTIVA = {
    'Epidemiologia': ('Epidemiologia & Bioestatística', 'Medidas de Saúde e Estudos Epidemiológicos'),
    'Epidemiologia Clínica': ('Epidemiologia & Bioestatística', 'Testes Diagnósticos e Rastreamento'),
    'Epidemiologia e Bioestatística': ('Epidemiologia & Bioestatística', 'Bioestatística e Delineamentos'),
    'Epidemiologia e História Natural da Doença': ('Epidemiologia & Bioestatística', 'História Natural e Níveis de Prevenção'),
    'Medicina Baseada em Evidências': ('Epidemiologia & Bioestatística', 'Revisões Sistemáticas e Meta-análises'),

    'Medicina de Família e Comunidade': ('Medicina de Família e Comunidade (MFC)', 'Método Clínico Centrado na Pessoa e Família'),
    'Atenção Primária à Saúde': ('Medicina de Família e Comunidade (MFC)', 'Atributos da Atenção Primária'),
    'Atenção Primária e Sistemas de Saúde': ('Medicina de Família e Comunidade (MFC)', 'Atributos da Atenção Primária'),
    'Saúde da Família': ('Medicina de Família e Comunidade (MFC)', 'Estratégia Saúde da Família (ESF)'),
    'Saúde da Família e Comunidade': ('Medicina de Família e Comunidade (MFC)', 'Estratégia Saúde da Família (ESF)'),
    'Medicina Preventiva': ('Medicina de Família e Comunidade (MFC)', 'Prevenção Quaternária e Abordagem Comunitária'),
    'Saúde do Idoso': ('Medicina de Família e Comunidade (MFC)', 'Atenção Integral à Saúde do Idoso'),
    'Geriatria': ('Medicina de Família e Comunidade (MFC)', 'Atenção Integral à Saúde do Idoso'),
    'Geriatria e Gerontologia': ('Medicina de Família e Comunidade (MFC)', 'Atenção Integral à Saúde do Idoso'),
    'Saúde Mental': ('Medicina de Família e Comunidade (MFC)', 'Saúde Mental na Atenção Primária'),
    'Psiquiatria': ('Medicina de Família e Comunidade (MFC)', 'Saúde Mental na Atenção Primária'),
    'Endocrinologia': ('Medicina de Família e Comunidade (MFC)', 'Manejo de Doenças Crônicas na APS'),
    'Nutrição': ('Medicina de Família e Comunidade (MFC)', 'Atenção Nutricional na APS'),
    'Oncologia': ('Medicina de Família e Comunidade (MFC)', 'Rastreamento Oncológico na APS'),
    'Oncologia Preventiva': ('Medicina de Família e Comunidade (MFC)', 'Rastreamento Oncológico na APS'),
    'Ortopedia': ('Medicina de Família e Comunidade (MFC)', 'Queixas Musculoesqueléticas na APS'),
    'Urologia': ('Medicina de Família e Comunidade (MFC)', 'Saúde do Homem e Rastreamento na APS'),

    'Saúde Pública': ('Sistema Único de Saúde (SUS) & Políticas Públicas', 'Princípios, Diretrizes e Legislação do SUS'),
    'Saúde Pública / SUS': ('Sistema Único de Saúde (SUS) & Políticas Públicas', 'Princípios, Diretrizes e Legislação do SUS'),
    'Políticas Públicas de Saúde': ('Sistema Único de Saúde (SUS) & Políticas Públicas', 'Redes de Atenção e Financiamento'),

    'Vigilância em Saúde': ('Vigilância em Saúde', 'Vigilância Epidemiológica e Notificação Compulsória'),
    'Vigilância em Saúde, Ética e Saúde do Trabalhador': ('Vigilância em Saúde', 'Vigilância e Notificação Compulsória'),
    'Infectologia': ('Vigilância em Saúde', 'Doenças de Notificação e Epidemias'),
    'Infectologia / Pediatria': ('Vigilância em Saúde', 'Doenças Transmissíveis e Notificação'),
    'Infectologia / Saúde Pública': ('Vigilância em Saúde', 'Doenças Transmissíveis e Epidemias'),
    'Pneumologia': ('Vigilância em Saúde', 'Controle da Tuberculose e Tabagismo'),

    'Medicina do Trabalho': ('Saúde do Trabalhador', 'Doenças Ocupacionais e Acidentes de Trabalho'),
    'Saúde do Trabalhador': ('Saúde do Trabalhador', 'Legislação, Notificação (CAT) e Prevenção'),

    'Bioética': ('Ética Médica, Bioética & Medicina Legal', 'Código de Ética Médica e Bioética'),
    'Bioética e Comunicação': ('Ética Médica, Bioética & Medicina Legal', 'Relação Médico-Paciente e Consentimento'),
    'Bioética e Deontologia': ('Ética Médica, Bioética & Medicina Legal', 'Deontologia e Sigilo Profissional'),
    'Bioética e Relação Médico-Paciente': ('Ética Médica, Bioética & Medicina Legal', 'Relação Médico-Paciente e Consentimento'),
    'Ética Médica': ('Ética Médica, Bioética & Medicina Legal', 'Código de Ética Médica e Documentos'),
    'Ética Médica e Bioética': ('Ética Médica, Bioética & Medicina Legal', 'Princípios Bioéticos e Autonomia'),
    'Ética Médica e Legislação em Saúde': ('Ética Médica, Bioética & Medicina Legal', 'Legislação Sanitária e Ética'),
    'Geriatria e Ética Médica': ('Ética Médica, Bioética & Medicina Legal', 'Diretivas Antecipadas e Autonomia'),
    'Medicina Legal': ('Ética Médica, Bioética & Medicina Legal', 'Medicina Legal e Tanatologia'),
    'Medicina Legal e Deontologia': ('Ética Médica, Bioética & Medicina Legal', 'Declaração de Óbito e Atestados'),
    'Medicina Legal e Perícia Médica': ('Ética Médica, Bioética & Medicina Legal', 'Perícia Médica e Traumatologia Forense'),
    'Medicina Legal e Ética Médica': ('Ética Médica, Bioética & Medicina Legal', 'Documentos Médicos e Sigilo'),

    'Saúde Coletiva': ('Saúde Coletiva & Populações Vulneráveis', 'Determinantes Sociais e Promoção da Saúde'),
    'Determinantes Sociais da Saúde': ('Saúde Coletiva & Populações Vulneráveis', 'Iniquidades e Vulnerabilidade Social'),
    'Saúde Indígena': ('Saúde Coletiva & Populações Vulneráveis', 'Saúde Indígena e Ribeirinha'),
    'Saúde Indígena e Ribeirinha': ('Saúde Coletiva & Populações Vulneráveis', 'Saúde Indígena e Ribeirinha'),
    'Saúde LGBTI+': ('Saúde Coletiva & Populações Vulneráveis', 'Atenção à Saúde de Populações Específicas'),

    # Secundárias em Preventiva
    'Imunização': ('Imunização & Programas de Saúde', 'Estratégias e Metas de Vacinação'),
    'Imunizações': ('Imunização & Programas de Saúde', 'Estratégias e Metas de Vacinação'),
    'Gestão em Saúde': ('Gestão e Planejamento em Saúde', 'Planejamento, Auditoria e Regulação'),
    'Saúde Ambiental': ('Saúde Ambiental', 'Saneamento e Impactos Ambientais'),
    'Práticas Integrativas e Complementares': ('Práticas Integrativas (PICS)', 'PICS no SUS'),
    'Cuidados Paliativos': ('Cuidados Paliativos na APS', 'Cuidados Paliativos Domiciliares'),
    'Segurança do Paciente': ('Segurança do Paciente', 'Qualidade do Cuidado e Notificação'),
}

MAPAS_POR_AREA = {
    'Cirurgia Geral': MAPA_CIRURGIA,
    'Ginecologia e Obstetrícia': MAPA_GO,
    'Pediatria': MAPA_PEDIATRIA,
    'Medicina Preventiva e Social / MFC': MAPA_PREVENTIVA,
}


def sanitizar_banco():
    caminho_banco = Path('saida/banco_questoes_cache.json')
    caminho_cache_cat = Path('saida/cache_categorizacao.json')

    with open(caminho_banco, 'r', encoding='utf-8') as f:
        banco = json.load(f)

    print(f'Total de questoes no banco antes: {len(banco)}')
    modificadas = 0

    for q in banco:
        esp = q.get('especialidade')
        tema_antigo = q.get('tema')
        subtema_antigo = q.get('subtema')

        if esp in MAPAS_POR_AREA:
            mapa = MAPAS_POR_AREA[esp]
            if tema_antigo in mapa:
                novo_tema, default_subtema = mapa[tema_antigo]
                q['tema'] = novo_tema
                
                # Se o subtema era genérico ou vazio, atualiza com o novo agrupador
                if not subtema_antigo or subtema_antigo in ('Diversos', 'Geral', tema_antigo, 'Outros'):
                    q['subtema'] = default_subtema
                else:
                    # Sanitiza subtema de typos e redundâncias
                    s_clean = subtema_antigo.strip()
                    if s_clean.lower() in ('geral', 'diversos', 'outros'):
                        q['subtema'] = default_subtema
                modificadas += 1

    print(f'Questoes atualizadas com nova taxonomia: {modificadas}')

    with open(caminho_banco, 'w', encoding='utf-8') as f:
        json.dump(banco, f, ensure_ascii=False, indent=2)
    print(f'[OK] {caminho_banco} salvo com sucesso!')

    # Atualiza também o cache_categorizacao.json
    if caminho_cache_cat.exists():
        with open(caminho_cache_cat, 'r', encoding='utf-8') as f:
            cache_cat = json.load(f)

        cats_modificadas = 0
        for q_id, cat_info in cache_cat.items():
            esp = cat_info.get('especialidade')
            tema_antigo = cat_info.get('tema')
            if esp in MAPAS_POR_AREA:
                mapa = MAPAS_POR_AREA[esp]
                if tema_antigo in mapa:
                    novo_tema, default_sub = mapa[tema_antigo]
                    cat_info['tema'] = novo_tema
                    if cat_info.get('subtema') in ('Diversos', 'Geral', tema_antigo, 'Outros'):
                        cat_info['subtema'] = default_sub
                    cats_modificadas += 1

        with open(caminho_cache_cat, 'w', encoding='utf-8') as f:
            json.dump(cache_cat, f, ensure_ascii=False, indent=2)
        print(f'[OK] {caminho_cache_cat} atualizado ({cats_modificadas} entradas modificadas).')


if __name__ == '__main__':
    sanitizar_banco()

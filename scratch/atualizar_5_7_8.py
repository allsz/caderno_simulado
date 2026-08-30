import json
from pathlib import Path

caminho_banco = Path('saida/banco_questoes_cache.json')
banco = json.load(open(caminho_banco, encoding='utf-8'))

novos_dados = {
    '5': {
        'especialidade': 'Medicina Preventiva e Social / MFC',
        'tema': 'Atenção Primária e Sistemas de Saúde',
        'subtema': 'Projeto Terapêutico Singular (PTS)',
        'enunciado': (
            'Um homem com 48 anos de idade é obeso, tabagista e hipertenso há 6 anos, quando, devido a esse quadro, '
            'foi-lhe recomendada mudança do estilo de vida e prescrita farmacoterapia. Procura hoje a Unidade Básica '
            'de Saúde (UBS) com níveis tensionais elevados, glicemia alterada e referindo ter deixado de usar os '
            'medicamentos anti-hipertensivos prescritos dizendo "eles estão me fazendo sentir doente". O paciente '
            'relata que, durante a pandemia da COVID-19, deixou de seguir as orientações alimentares, de atividade '
            'física e de cessação do tabagismo.\n\n'
            'Para esse caso, a conduta a ser adotada pela equipe da UBS é'
        ),
        'alternativas': {
            'A': 'construir um projeto terapêutico singular e pactuar com o paciente as propostas de ações para a mudança do estilo de vida e a adesão medicamentosa.',
            'B': 'esclarecer o paciente, no projeto terapêutico singular, sobre as consequências da não adesão ao tratamento, destacando o perigo dos potenciais danos clínicos e reiterando firmemente o aconselhamento.',
            'C': 'utilizar, no projeto terapêutico singular, a negação do paciente aos problemas apresentados e a adesão ao tratamento como formas de pressão para obtenção da mudança do estilo de vida.',
            'D': 'condicionar, na construção do projeto terapêutico singular, a adesão à mudança do estilo de vida e ao tratamento farmacológico e comunicar ao paciente que, se não seguir as orientações da equipe, não poderá mais ser atendido na UBS.'
        },
        'gabarito': 'A'
    },
    '7': {
        'especialidade': 'Cirurgia Geral',
        'tema': 'Trauma e Emergências Cirúrgicas',
        'subtema': 'Trauma Abdominal Fechado (Trauma Hepático)',
        'enunciado': (
            'Uma paciente com 35 anos de idade, vítima de acidente automobilístico, queixa-se de dor abdominal. '
            'Durante a admissão no setor de emergência, apresenta-se lúcida, cooperativa (Glasgow 15), pressão arterial: '
            '100 x 60 mmHg, frequência cardíaca: 88 batimentos por minuto, frequência respiratória: 20 incursões '
            'respiratórias por minuto. Foi indicada tomografia de abdome, que evidenciou moderada quantidade de líquido '
            'livre na cavidade abdominal, hematoma subcapsular no lobo direito do fígado, ocupando cerca de 40% da '
            'superfície do órgão e laceração de cerca de 5 cm em lobo esquerdo.\n\n'
            'Nesse caso, qual deve ser a conduta para a paciente?'
        ),
        'alternativas': {
            'A': 'Laparotomia com rafia da laceração hepática e drenagem do hematoma subcapsular.',
            'B': 'Laparotomia, hemostasia com compressas no fígado e reabordagem cirúrgica após 48 horas.',
            'C': 'Internação em Unidade de Terapia Intensiva com monitorização hemodinâmica e hematócrito seriado.',
            'D': 'Internação em Unidade de Terapia Intensiva com monitorização hemodinâmica, hematócrito seriado e tomografia de abdome a cada 48 horas.'
        },
        'gabarito': 'C'
    },
    '8': {
        'especialidade': 'Pediatria',
        'tema': 'Infectologia e Doenças Exantemáticas',
        'subtema': 'Artrite Séptica e Infecções Osteoarticulares',
        'enunciado': (
            'Um menino com 11 anos de idade apresenta febre diária há 4 dias e claudicação de membro inferior '
            'direito e vem usando ibuprofeno desde o início do quadro, sem melhora. Há 1 dia, recusa-se a andar, '
            'referindo muita dor em joelho direito, onde notou inchaço e vermelhidão. Refere ainda inapetência e '
            'indisposição geral. Tem antecedente de lesões crostosas de mucosa nasal e pele ao redor do nariz há '
            '2 semanas, tendo usado pomada à base de corticoide, sem melhora.\n'
            'Ao exame físico apresentou regular estado geral, corado, hidratado, febril (temperatura = 38 °C), '
            'frequência cardíaca: 103 batimentos por minuto, frequência respiratória: 16 incursões respiratórias '
            'por minuto, anictérico, acianótico, eupneico, pulsos cheios, boa perfusão periférica. Lesões pustulosas '
            'e crostosas em vestíbulo nasal. Joelho direito com edema, calor e intensa dor à mobilização. Restante '
            'dos aparelhos sem alterações.\n\n'
            'Para a elucidação diagnóstica, quais são os exames/procedimentos indicados?'
        ),
        'alternativas': {
            'A': 'Antiestreptolisina O e ecocardiograma.',
            'B': 'Anticorpo antinuclear e fator reumatoide.',
            'C': 'Ultrassonografia e punção articular de joelho.',
            'D': 'Hemograma e provas de atividade inflamatória.'
        },
        'gabarito': 'C'
    }
}

for q in banco:
    if q.get('origem') == 'REVALIDA-2022_PV_objetiva_1':
        num = str(q.get('numero'))
        if num in novos_dados:
            for k, v in novos_dados[num].items():
                q[k] = v
            print(f'Questão {num} atualizada!')

with open(caminho_banco, 'w', encoding='utf-8') as f:
    json.dump(banco, f, ensure_ascii=False, indent=2)

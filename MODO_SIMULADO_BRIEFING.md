# 📋 Briefing Executivo: Implementação do Modo Simulado Real

Este documento serve como **contexto completo e isolado** para guiar a continuidade do desenvolvimento da funcionalidade **Modo Simulado Real Cronometrado** no Caderno de Questões Médico.

---

## 🎯 1. Visão Geral da Feature
Criar uma experiência autêntica de prova de residência médica/Revalida no caderno interativo, com:
1. **Sorteio e Isolamento**: Selecionar $N$ questões aleatórias do banco (1.444 questões) com regra de 3 baseada no tempo escolhido.
2. **Blind Mode (Modo Cego)**: Sem revelar acerto/erro nem gabarito ou comentários de IA durante a prova.
3. **Sentinela Anti-Cola & Timer**: Barra fixa no topo com cronômetro regressivo e detecção de troca de aba / perda de foco (`blur` / `visibilitychange`).
4. **Dashboard de Apuração Final**: Nota final, taxa de acerto por especialidade, tempo médio por questão e modo revisão com gabarito liberado.

---

## 🛠️ 2. Arquitetura do Projeto
- **Arquivos do Frontend**:
  - `web/template.html`: Estrutura HTML do caderno.
  - `web/styles.css`: Design system Vanilla CSS (variáveis HSL, temas Claro/Escuro, fonte Inter).
  - `web/app.js`: Lógica cliente em Vanilla JS puro (sem dependências externas).
- **Compilação**:
  - `python recompilar.py`: Junta `template.html` + `styles.css` + `app.js` + `banco_questoes_cache.json` + `cache_explicacoes.json` e gera `index.html`.
- **Atenção Crítica**: Um script (`enriquecer_explicacoes_ia.py`) está enriquecendo justificativas em segundo plano e gravando em `saida/cache_explicacoes.json`. **NUNCA** modifique ou apague esse JSON!

---

## ✅ 3. O Que Já Foi Implementado (Módulo 1 - Concluído)
- **Aba no cabeçalho**: `Modo Simulado` ao lado de `Por Especialidade & Conteúdo` e `Por Prova Oficial`.
- **Setup Card (Wizard de Configuração)**:
  - Seleção de Tempo: `30 min`, `1h`, `2h`, `3h`, `4h`, `5h` e `Livre`.
  - No modo `Livre`: pills para escolher `15`, `30`, `50` ou `100` questões.
  - Box de Cálculo: Mostra o total de questões proporcional e critério de seleção aleatória.
  - Card de Regras de Prova: Alertas amarelos com as instruções e sentinela anti-cola.
  - Checkbox de Concordância: Habilita o botão **"Iniciar Simulado"** com gradiente azul.
- **Ajustes de UI já refinados**:
  - Sem efeito de zoom ao clicar nas abas.
  - Ícones minimalistas SVG sem numerações redundantes.
  - Total de questões e critérios perfeitamente centralizados e alinhados.
  - Tipografia 100% padronizada na fonte `Inter`.
  - Bug de restauração do grid de questões ao alternar de abas corrigido.

---

## ✅ 3.1. O Que Já Foi Implementado (Módulo 2 - Concluído)
- **Motor de Sorteio Aleatório**:
  - Algoritmo matemático uniforme *Fisher-Yates* $O(N)$ sobre as 1.444 questões do banco.
  - Sorteio proporcional ao tempo selecionado (ou customizado no Modo Livre).
  - Pode sortear qualquer questão do banco, inclusive questões já feitas no modo normal.
- **Ambiente de Prova Isolado (`simulado-ativo-container`)**:
  - Ocultação dos blocos superiores (hero, Ko-Fi) e da listagem comum do caderno.
  - Renderização das $N$ questões clonadas com IDs isolados (`sim_card_`, `sim_radio_`, etc.).
  - **Ocultação de Metadados Clínicos**: Exibição estrita da numeração ordinal (`Questão 1 de N`), sem pistas de banca, prova, ano, especialidade ou tema/subtema.
- **Relógio Cronometrado (Countdown)**:
  - Posicionado diretamente acima do botão "Abandonar Prova", em container com largura padronizada e homogênea (175px).
  - Regressivo no tempo fixo (`HH:MM:SS` / `MM:SS`), com alerta vermelho nos últimos 5 minutos, e progressivo no Modo Livre.
  - Crachá "Simulado em Andamento" em verde esmeralda com pulso animado.
- **Resiliência e Persistência de Sessão**:
  - Snapshot salvo em `sessionStorage` e `localStorage`.
  - Tolerância total a recarregamento acidental (F5): a prova é restaurada exatamente com o tempo decorrido real e alternativas marcadas.
  - Modal de abandono da prova com limpeza segura de sessão e restauração do caderno normal.

---

## ✅ 3.2. O Que Já Foi Implementado (Módulo 3 - Concluído)
- **Blind Mode Estrito**:
  - Alternativas selecionadas neutras e limpas (azul suave), sem pistas de acerto ou erro.
  - Gabaritos e comentários da IA completamente inacessíveis durante a prova.
- **Botões de Entrega de Prova**:
  - Botão destacado "Entregar Prova" no cabeçalho do exame com gradiente esmeralda (`#10b981` / `#059669`) e largura homogenizada (175px).
  - Botão de entrega redundante na barra inferior de navegação (`simulado-bottom-bar`).
- **Modal de Conferência de Entrega (`confirm-entregar-simulado-modal-overlay`)**:
  - Resumo métrico: Total de Questões, Respondidas e Em Branco.
  - Alerta inteligente dinâmico: mensagem positiva se 100% preenchido, ou aviso amber se houver questões não respondidas.
  - Pills interativas de questões pendentes: clique suave que rola a página diretamente até a questão correspondente com efeito de destaque visual pulsante.
- **Submissão e Regra de Ouro**:
  - `executarEntregaSimulado()`: encerra o cronômetro, apura métricas de prova, salva snapshot final e desativa botões de entrega.
  - **Regra de Ouro executada**: migração automática e transparente de questões inéditas para o progresso do modo normal (`caderno_respostas_simulado`).
- **Proteção Anti-Perda de Sessão**:
  - Listener global `beforeunload` que impede fechar a aba acidentalmente durante a realização do simulado.

---

## ✅ 3.3. O Que Já Foi Implementado (Módulo 4 - Concluído)
- **Sentinela Anti-Cola & Sentinela de Foco (Opção B - Tolerância Zero)**:
  - Monitoramento contínuo em tempo real de `document.visibilitychange` e `window.blur`.
  - **Proteção Robusta Contra Falsos Positivos**:
    - Detecção imediata de troca de aba / minimização (`document.visibilityState === 'hidden'`).
    - Buffer inteligente de 250ms com checagem de `!document.hasFocus()` para eventos `window.blur`.
    - Flag `window._interacaoInternaSegura` e chamadas integradas a `marcarInteracaoInternaSegura(true/false)` no lightbox de zoom de imagens médicas (`abrirZoomImagem`/`fecharZoomImagem`) e nos modais internos de confirmação de entrega e abandono. O estudante pode inspecionar imagens e interagir com modais internos sem risco de falso disparo.
  - **Desclassificação Instantânea & Anulação Oficial**:
    - Ao confirmar a saída de tela/troca de aba durante a prova (`status === 'em_andamento'`), a prova é imediatamente desclassificada (`status = 'desclassificado'`).
    - O cronômetro e a sentinela são interrompidos, acertos e erros parciais são congelados.
    - **Proteção da Regra de Ouro**: nenhuma resposta de prova desclassificada é migrada para o caderno de questões (`questoesMigradasParaCaderno = 0`).
  - **Modal Bloqueador de Desclassificação (`simulado-desclassificado-modal-overlay`)**:
    - Visual imersivo com ícone de alerta vermelho, explicação das regras de tolerância zero e grid de métricas parciais (tempo até bloqueio, respondidas, acertos parciais, pendentes).
    - Botões integrados: "Revisar Questões Realizadas" (desbloqueia modo revisão), "Fazer Novo Simulado" (limpa sessão e abre o Wizard) e "Voltar ao Caderno".
  - **Crachá Visual Sentinela**:
    - `#simulado-anticola-badge` na barra de metadados do simulado exibindo "Anti-Cola Ativo (Tolerância Zero)" em verde discreto e tornando-se vermelho "Violação de Foco (Anulada)" em caso de quebra de regras.

---

## 🚀 4. Módulos Restantes a Implementar

### 📍 Módulo 5: Finalização, Apuração e Painel de Desempenho
- **Ao clicar em "Entregar Simulado" ou quando o tempo esgotar**:
  - Desativar a sentinela de foco.
  - Comparar `respostas` do simulado com os gabaritos oficiais.
  - **Regra de Ouro de Progressão (NOVO REQUISITO)**:
    - O simulado pode sortear qualquer questão (já respondida ou não).
    - Para as questões que o estudante **ainda não havia respondido no modo normal** (`caderno_respostas_simulado`), as respostas dadas no simulado **deverão ser migradas e incorporadas automaticamente ao progresso do modo normal**, atualizando a contagem global e o histórico de estudos!
    - Questões que ele já tinha respondido previamente no modo normal não são sobrescritas.
  - **Exibir Dashboard do Simulado**:
    - Pontuação final (ex: `75% - 30/40 acertos`).
    - Tempo total utilizado e ritmo médio por questão.
    - Gráfico e taxa por Grande Área médica.
  - **Modo Revisão Liberado**:
    - Questões do simulado ganham cores verde/vermelho.
    - Gabaritos e comentários da IA são desbloqueados para consulta.

---

## ⚠️ 5. Cuidados e "Pegadinhas" Técnicas

| Pegadinha / Desafio | Solução Arquitetural Recomendada |
| :--- | :--- |
| **Recarregamento acidental (F5)** | Salvar snapshot do `simuladoAtivo` em `sessionStorage` e espelho em `localStorage`. Restauração instantânea. |
| **Falsos positivos de perda de foco** | Quando o usuário clica para abrir o zoom de uma imagem de questão, garantir que o modal de zoom seja filho do mesmo DOM para não acionar o `blur`. |
| **Não poluir histórico prematuramente** | As respostas do simulado ficam isoladas durante a prova. Apenas na conclusão oficial as questões inéditas são incorporadas ao `caderno_respostas_simulado`. |
| **Padrão Estético e Design** | Usar fonte `Inter`, ícones SVG minimalistas inline e variáveis CSS nativas (`var(--primary)`, `var(--card-bg)`, `var(--text-main)`). |
| **Processo em Background** | **NUNCA** editar ou sobrescrever `saida/cache_explicacoes.json`, pois o enriquecedor de IA está rodando em paralelo gravando nele. |

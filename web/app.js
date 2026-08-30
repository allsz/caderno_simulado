// Chaves de armazenamento suportadas para migração transparente
const STORAGE_KEY = 'caderno_respostas_simulado';
const LEGACY_STORAGE_KEYS = ['respostas_simulado', 'respostas_simulado_v1', 'simulado_respostas'];

// Helpers para acesso ultra-seguro ao localStorage (evita quebras em modo anônimo/privado)
function safeStorageGet(key, defaultVal = {}) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultVal;
    } catch (e) {
        console.warn('Storage indisponível ou inacessível:', e);
        return defaultVal;
    }
}

function safeStorageSet(key, val) {
    try {
        localStorage.setItem(key, JSON.stringify(val));
        return true;
    } catch (e) {
        console.warn('Não foi possível salvar no storage:', e);
        return false;
    }
}

function safeStorageRemove(key) {
    try {
        localStorage.removeItem(key);
    } catch (e) {
        // Ignora erros de remoção em storage restrito
    }
}

// ========================================================
// Estado da Paginação e Filtros
// ========================================================
let modoFiltroAtivo = 'clinico'; // 'clinico' | 'prova'
let especialidadeAtiva = 'TODAS';
let temaAtivo = 'TODOS';
let subtemaAtivo = 'TODOS';
let bancaAtiva = 'TODAS';
let edicaoAtiva = 'TODAS';
let numeroQuestaoFiltro = '';
let paginaAtual = 1;
let itensPorPagina = 25;
let todosCards = [];
let cardsFiltrados = [];
let taxonomiaEspecialidades = {};
let taxonomiaProvas = {};
let debounceTimerBusca = null;

// ========================================================
// Funções de Navegação e Estatísticas
// ========================================================
function irParaEstatisticas() {
    const painel = document.getElementById('painel-estatisticas');
    if (!painel) return;
    
    painel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    let tentativas = 0;
    const ajustarPosicao = () => {
        const rect = painel.getBoundingClientRect();
        if (rect.top > 100 && tentativas < 20) {
            painel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            tentativas++;
            setTimeout(ajustarPosicao, 120);
        }
    };
    setTimeout(ajustarPosicao, 150);
}

function resolverRadioQuestao(qId, valor) {
    if (!qId) return null;
    
    // 1. Match exato
    let radio = valor 
        ? document.querySelector(`input[name="${qId}"][value="${valor}"]`)
        : document.querySelector(`input[name="${qId}"]`);
    if (radio) return { radio, realQId: radio.name };

    // 2. Com ou sem prefixo q_
    const altId = qId.startsWith('q_') ? qId.substring(2) : 'q_' + qId;
    radio = valor 
        ? document.querySelector(`input[name="${altId}"][value="${valor}"]`)
        : document.querySelector(`input[name="${altId}"]`);
    if (radio) return { radio, realQId: radio.name };

    // 3. Removendo sufixo numérico antigo como _1, _2, _45 (índices voláteis antigos)
    const baseId1 = qId.replace(/_\d+$/, '');
    radio = valor 
        ? document.querySelector(`input[name="${baseId1}"][value="${valor}"]`)
        : document.querySelector(`input[name="${baseId1}"]`);
    if (radio) return { radio, realQId: radio.name };

    const baseId2 = altId.replace(/_\d+$/, '');
    radio = valor 
        ? document.querySelector(`input[name="${baseId2}"][value="${valor}"]`)
        : document.querySelector(`input[name="${baseId2}"]`);
    if (radio) return { radio, realQId: radio.name };

    // 4. Busca flexível por substring do nome da prova e questão
    const cleanId = qId.replace(/^q_/, '').replace(/_\d+$/, '');
    radio = valor 
        ? document.querySelector(`input[name^="q_${cleanId}"][value="${valor}"]`)
        : document.querySelector(`input[name^="q_${cleanId}"]`);
    if (radio) return { radio, realQId: radio.name };

    return null;
}

function atualizarBarra(qtd) {
    const txt = document.getElementById('progress-text');
    const bar = document.getElementById('progress-bar');
    const total = window.TOTAL_QUESTOES || 0;
    const pct = total > 0 ? Math.round((qtd / total) * 100) : 0;
    
    if (txt) {
        txt.textContent = `${qtd} de ${total} respondidas (${pct}%)`;
    }
    if (bar) {
        bar.style.width = `${pct}%`;
    }
}

function atualizarEstatisticas() {
    const dados = safeStorageGet(STORAGE_KEY, {});
    const total = window.TOTAL_QUESTOES || 0;
    let acertos = 0;
    let erros = 0;
    let respondidasValidas = 0;

    for (const [qId, valor] of Object.entries(dados)) {
        const match = resolverRadioQuestao(qId, valor);
        if (!match) continue;

        respondidasValidas++;
        const gabarito = match.radio.getAttribute('data-gabarito');
        if (gabarito && gabarito !== 'N/A' && gabarito !== 'ANULADA') {
            if (valor === gabarito) {
                acertos++;
            } else {
                erros++;
            }
        } else if (gabarito === 'ANULADA') {
            // Questões anuladas pontuam como acerto
            acertos++;
        }
    }

    const avaliadas = acertos + erros;
    const taxa = avaliadas > 0 ? Math.round((acertos / avaliadas) * 100) : 0;

    const elAcertos = document.getElementById('stat-acertos');
    const elErros = document.getElementById('stat-erros');
    const elTaxa = document.getElementById('stat-taxa');
    const elResp = document.getElementById('stat-respondidas');

    if (elAcertos) elAcertos.textContent = acertos;
    if (elErros) elErros.textContent = erros;
    if (elTaxa) elTaxa.textContent = taxa + '%';
    if (elResp) elResp.textContent = `${respondidasValidas} / ${total}`;

    // Sincroniza a barra de progresso superior
    atualizarBarra(respondidasValidas);
}

function toggleResposta(qId) {
    const card = typeof encontrarCardQuestao === 'function' ? encontrarCardQuestao(qId) : document.getElementById('card_' + qId);
    const realQId = card ? card.id.replace(/^card_/, '') : qId;
    const box = document.getElementById('box_' + realQId) || document.getElementById('box_' + qId);
    if (box) {
        const isHidden = (box.style.display === 'none' || box.style.display === '');
        box.style.display = isHidden ? 'block' : 'none';
        if (isHidden) {
            revelarFeedbackGabarito(realQId);
        }
    }
}

function carregarRespostas() {
    // 1. Carrega dados do armazenamento principal
    let dados = safeStorageGet(STORAGE_KEY, {});

    // 2. Migração automática de chaves legadas caso existam
    LEGACY_STORAGE_KEYS.forEach(legacyKey => {
        const legacyData = safeStorageGet(legacyKey, {});
        if (Object.keys(legacyData).length > 0) {
            dados = { ...legacyData, ...dados };
            safeStorageRemove(legacyKey);
        }
    });

    const dadosMigrados = {};

    // 3. Aplica as respostas e migra chaves para o padrão estável
    for (const [qId, valor] of Object.entries(dados)) {
        const match = resolverRadioQuestao(qId, valor);
        if (match) {
            match.radio.checked = true;
            dadosMigrados[match.realQId] = valor;
            const gabarito = match.radio.getAttribute('data-gabarito');
            atualizarEstiloQuestao(match.realQId, valor, gabarito);
        }
    }

    // Salva o banco limpo e migrado de forma segura
    safeStorageSet(STORAGE_KEY, dadosMigrados);
    atualizarEstatisticas();
}

function salvarResposta(qId, valor, gabarito) {
    const dados = safeStorageGet(STORAGE_KEY, {});
    const match = resolverRadioQuestao(qId, valor);
    const realQId = match ? match.realQId : qId;

    dados[realQId] = valor;
    safeStorageSet(STORAGE_KEY, dados);
    
    if (typeof gtag === 'function') {
        gtag('event', 'resposta_questao', {
            'questao_id': realQId,
            'acertou': (valor === gabarito)
        });
    }
    
    atualizarEstiloQuestao(realQId, valor, gabarito);
    atualizarEstatisticas();
}


function atualizarEstiloQuestao(qId, valor, gabarito) {
    const card = document.getElementById('card_' + qId);
    if (card) card.classList.add('answered');
    
    document.querySelectorAll(`input[name="${qId}"]`).forEach(r => {
        const lbl = document.getElementById(`label_${qId}_${r.value}`);
        if (lbl) lbl.classList.remove('selected', 'correct', 'incorrect');
    });

    const labelSelecionada = document.getElementById(`label_${qId}_${valor}`);
    if (labelSelecionada) labelSelecionada.classList.add('selected');

    const box = document.getElementById('box_' + qId);
    if (box && box.style.display === 'block') {
        revelarFeedbackGabarito(qId);
    }
}

function revelarFeedbackGabarito(qId) {
    const radioSelecionado = document.querySelector(`input[name="${qId}"]:checked`);
    const valor = radioSelecionado ? radioSelecionado.value : null;
    const radioQualquer = document.querySelector(`input[name="${qId}"]`);
    const gabarito = radioQualquer ? radioQualquer.getAttribute('data-gabarito') : null;

    if (!gabarito || gabarito === 'N/A' || gabarito === 'ANULADA') return;

    const labelCorreta = document.getElementById(`label_${qId}_${gabarito}`);
    if (labelCorreta) labelCorreta.classList.add('correct');

    if (valor) {
        const labelSelecionada = document.getElementById(`label_${qId}_${valor}`);
        if (valor === gabarito) {
            if (labelSelecionada) labelSelecionada.classList.add('correct');
        } else {
            if (labelSelecionada) labelSelecionada.classList.add('incorrect');
        }
    }
}

// ========================================================
// Lógica de Filtros (Especialidades/Temas e Provas/Anos/Questão) e Paginação
// ========================================================

function alternarModoFiltro(modo) {
    modoFiltroAtivo = modo;
    paginaAtual = 1;

    const tabClinico = document.getElementById('tab-modo-clinico');
    const tabProva = document.getElementById('tab-modo-prova');
    const painelClinico = document.getElementById('painel-filtro-clinico');
    const painelProva = document.getElementById('painel-filtro-prova');

    if (modo === 'clinico') {
        if (tabClinico) { tabClinico.classList.add('active'); tabClinico.setAttribute('aria-selected', 'true'); }
        if (tabProva) { tabProva.classList.remove('active'); tabProva.setAttribute('aria-selected', 'false'); }
        if (painelClinico) painelClinico.style.display = 'block';
        if (painelProva) painelProva.style.display = 'none';
    } else {
        if (tabClinico) { tabClinico.classList.remove('active'); tabClinico.setAttribute('aria-selected', 'false'); }
        if (tabProva) { tabProva.classList.add('active'); tabProva.setAttribute('aria-selected', 'true'); }
        if (painelClinico) painelClinico.style.display = 'none';
        if (painelProva) painelProva.style.display = 'block';
    }

    if (typeof gtag === 'function') {
        gtag('event', 'alternar_modo_filtro', { 'modo': modo });
    }

    aplicarFiltroEPaginacao(false);
}

function inicializarPaginacaoEFiltros() {
    todosCards = Array.from(document.querySelectorAll('.card-questao'));
    if (todosCards.length === 0) return;

    // 1. Constrói taxonomia clínica (Especialidade -> Temas -> Subtemas)
    taxonomiaEspecialidades = {};
    todosCards.forEach(card => {
        const esp = card.getAttribute('data-especialidade') || 'Outros / Não Categorizados';
        const tema = card.getAttribute('data-tema') || 'Geral';
        const subtema = card.getAttribute('data-subtema') || 'Diversos';
        
        if (!taxonomiaEspecialidades[esp]) {
            taxonomiaEspecialidades[esp] = { total: 0, temas: {} };
        }
        taxonomiaEspecialidades[esp].total++;

        if (!taxonomiaEspecialidades[esp].temas[tema]) {
            taxonomiaEspecialidades[esp].temas[tema] = { total: 0, subtemas: {} };
        }
        taxonomiaEspecialidades[esp].temas[tema].total++;
        taxonomiaEspecialidades[esp].temas[tema].subtemas[subtema] = (taxonomiaEspecialidades[esp].temas[tema].subtemas[subtema] || 0) + 1;
    });

    // Monta abas de Especialidades
    const containerPills = document.getElementById('filtro-pills-container');
    if (containerPills) {
        containerPills.innerHTML = '';

        // Aba "Todas"
        const btnTodas = document.createElement('button');
        btnTodas.type = 'button';
        btnTodas.className = 'filtro-pill active';
        btnTodas.setAttribute('data-esp', 'TODAS');
        btnTodas.innerHTML = `Todas <span class="filtro-pill-count">${todosCards.length}</span>`;
        btnTodas.onclick = () => filtrarPorEspecialidade('TODAS');
        containerPills.appendChild(btnTodas);

        // Abas individuais de Especialidade
        Object.keys(taxonomiaEspecialidades).sort().forEach(esp => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'filtro-pill';
            btn.setAttribute('data-esp', esp);
            btn.innerHTML = `${esp} <span class="filtro-pill-count">${taxonomiaEspecialidades[esp].total}</span>`;
            btn.onclick = () => filtrarPorEspecialidade(esp);
            containerPills.appendChild(btn);
        });
    }

    // 2. Constrói taxonomia de Provas (Banca -> Edições)
    inicializarTaxonomiaProvas();

    aplicarFiltroEPaginacao(false);
}

function inicializarTaxonomiaProvas() {
    taxonomiaProvas = {
        'ENARE': { total: 0, edicoes: {} },
        'REVALIDA': { total: 0, edicoes: {} }
    };

    todosCards.forEach(card => {
        const banca = (card.getAttribute('data-banca') || 'Outros').toUpperCase();
        const rotuloEdicao = card.getAttribute('data-rotulo-edicao') || card.getAttribute('data-origem') || 'Geral';
        const ano = card.getAttribute('data-ano') || '2026';
        
        if (!taxonomiaProvas[banca]) {
            taxonomiaProvas[banca] = { total: 0, edicoes: {} };
        }
        taxonomiaProvas[banca].total++;

        if (!taxonomiaProvas[banca].edicoes[rotuloEdicao]) {
            taxonomiaProvas[banca].edicoes[rotuloEdicao] = { total: 0, ano: ano, rotulo: rotuloEdicao };
        }
        taxonomiaProvas[banca].edicoes[rotuloEdicao].total++;
    });

    // Renderiza pills de bancas (Todas as Provas, ENARE, REVALIDA)
    const containerBancas = document.getElementById('filtro-bancas-pills');
    if (containerBancas) {
        containerBancas.innerHTML = '';

        // Pill "Todas as Provas"
        const btnTodas = document.createElement('button');
        btnTodas.type = 'button';
        btnTodas.className = 'filtro-pill active';
        btnTodas.setAttribute('data-banca', 'TODAS');
        btnTodas.innerHTML = `Todas as Provas <span class="filtro-pill-count">${todosCards.length}</span>`;
        btnTodas.onclick = () => filtrarPorBanca('TODAS');
        containerBancas.appendChild(btnTodas);

        // Pills ENARE e REVALIDA
        ['ENARE', 'REVALIDA'].forEach(banca => {
            if (taxonomiaProvas[banca] && taxonomiaProvas[banca].total > 0) {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'filtro-pill';
                btn.setAttribute('data-banca', banca);
                btn.innerHTML = `${banca} <span class="filtro-pill-count">${taxonomiaProvas[banca].total}</span>`;
                btn.onclick = () => filtrarPorBanca(banca);
                containerBancas.appendChild(btn);
            }
        });
    }

    renderizarPillsEdicoes();
}

function renderizarPillsEdicoes() {
    const edicoesWrapper = document.getElementById('filtro-edicoes-wrapper');
    const edicoesContainer = document.getElementById('filtro-edicoes-pills');
    if (!edicoesContainer) return;

    edicoesContainer.innerHTML = '';

    let listaEdicoes = [];
    if (bancaAtiva === 'TODAS') {
        Object.keys(taxonomiaProvas).forEach(b => {
            Object.keys(taxonomiaProvas[b].edicoes).forEach(rot => {
                listaEdicoes.push(taxonomiaProvas[b].edicoes[rot]);
            });
        });
    } else if (taxonomiaProvas[bancaAtiva]) {
        Object.keys(taxonomiaProvas[bancaAtiva].edicoes).forEach(rot => {
            listaEdicoes.push(taxonomiaProvas[bancaAtiva].edicoes[rot]);
        });
    }

    if (listaEdicoes.length === 0) {
        if (edicoesWrapper) edicoesWrapper.style.display = 'none';
        return;
    }

    if (edicoesWrapper) edicoesWrapper.style.display = 'block';

    // Ordena as edições de forma decrescente (mais recente primeiro)
    listaEdicoes.sort((a, b) => b.rotulo.localeCompare(a.rotulo));

    // Pill "Todas as Edições"
    const pillTodas = document.createElement('button');
    pillTodas.type = 'button';
    pillTodas.className = 'edicao-pill' + (edicaoAtiva === 'TODAS' ? ' active' : '');
    pillTodas.setAttribute('data-edicao', 'TODAS');
    const totalBanca = bancaAtiva === 'TODAS' ? todosCards.length : (taxonomiaProvas[bancaAtiva] ? taxonomiaProvas[bancaAtiva].total : 0);
    pillTodas.innerHTML = `Todas as Edições <span class="edicao-pill-count">${totalBanca}</span>`;
    pillTodas.onclick = () => filtrarPorEdicao('TODAS');
    edicoesContainer.appendChild(pillTodas);

    listaEdicoes.forEach(item => {
        const pill = document.createElement('button');
        pill.type = 'button';
        pill.className = 'edicao-pill' + (edicaoAtiva === item.rotulo ? ' active' : '');
        pill.setAttribute('data-edicao', item.rotulo);
        pill.innerHTML = `${item.rotulo} <span class="edicao-pill-count">${item.total}</span>`;
        pill.onclick = () => filtrarPorEdicao(item.rotulo);
        edicoesContainer.appendChild(pill);
    });
}

function filtrarPorBanca(banca) {
    bancaAtiva = banca;
    edicaoAtiva = 'TODAS';
    paginaAtual = 1;

    document.querySelectorAll('#filtro-bancas-pills .filtro-pill').forEach(btn => {
        if (btn.getAttribute('data-banca') === banca) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    renderizarPillsEdicoes();

    if (typeof gtag === 'function') {
        gtag('event', 'filtrar_banca', { 'banca': banca });
    }

    aplicarFiltroEPaginacao(true);
}

function filtrarPorEdicao(edicao) {
    edicaoAtiva = edicao;
    paginaAtual = 1;

    document.querySelectorAll('#filtro-edicoes-pills .edicao-pill').forEach(btn => {
        if (btn.getAttribute('data-edicao') === edicao) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    if (typeof gtag === 'function') {
        gtag('event', 'filtrar_edicao', { 'edicao': edicao });
    }

    aplicarFiltroEPaginacao(true);
}

function filtrarPorNumeroQuestao(numero) {
    clearTimeout(debounceTimerBusca);
    debounceTimerBusca = setTimeout(() => {
        numeroQuestaoFiltro = (numero || '').toString().trim();
        paginaAtual = 1;

        const btnLimpar = document.getElementById('btn-limpar-busca-q');
        if (btnLimpar) {
            btnLimpar.style.display = numeroQuestaoFiltro ? 'inline-block' : 'none';
        }

        aplicarFiltroEPaginacao(false);
    }, 120);
}


function alterarNumeroQuestao(delta) {
    const inputQ = document.getElementById('input-busca-questao');
    if (!inputQ) return;
    let val = parseInt(inputQ.value, 10);
    if (isNaN(val)) {
        val = delta > 0 ? 1 : 1;
    } else {
        val += delta;
    }
    if (val < 1) val = 1;
    if (val > 100) val = 100;
    inputQ.value = val;
    filtrarPorNumeroQuestao(val);
}

function limparBuscaQuestao() {
    const inputQ = document.getElementById('input-busca-questao');
    if (inputQ) inputQ.value = '';
    filtrarPorNumeroQuestao('');
}

function filtrarPorEspecialidade(esp) {
    especialidadeAtiva = esp;
    temaAtivo = 'TODOS';
    subtemaAtivo = 'TODOS';
    paginaAtual = 1;

    // Atualiza estado ativo das abas de especialidade
    document.querySelectorAll('#filtro-pills-container .filtro-pill').forEach(btn => {
        if (btn.getAttribute('data-esp') === esp) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Oculta subtemas ao trocar especialidade
    const subtemasWrapper = document.getElementById('filtro-subtemas-wrapper');
    if (subtemasWrapper) subtemasWrapper.style.display = 'none';

    // Atualiza container de temas com sub-botões diretos
    const temasWrapper = document.getElementById('filtro-temas-wrapper');
    const pillsContainer = document.getElementById('filtro-temas-pills');

    if (esp === 'TODAS' || !taxonomiaEspecialidades[esp]) {
        if (temasWrapper) temasWrapper.style.display = 'none';
    } else {
        if (temasWrapper) temasWrapper.style.display = 'block';

        const temasObj = taxonomiaEspecialidades[esp].temas || {};
        const listaTemas = Object.keys(temasObj).sort();

        // Popula Sub-pills de Temas
        if (pillsContainer) {
            pillsContainer.innerHTML = '';
            
            if (listaTemas.length === 1 && (listaTemas[0].toLowerCase() === 'geral' || listaTemas[0] === 'Outros / Não Categorizados')) {
                const p = document.createElement('button');
                p.type = 'button';
                p.className = 'subfiltro-pill active';
                p.setAttribute('data-tema', 'TODOS');
                p.innerHTML = `Geral <span class="subfiltro-pill-count">${taxonomiaEspecialidades[esp].total}</span>`;
                p.onclick = (e) => {
                    if (e) e.preventDefault();
                    filtrarPorTema('TODOS');
                };
                pillsContainer.appendChild(p);
            } else {
                const pillTodos = document.createElement('button');
                pillTodos.type = 'button';
                pillTodos.className = 'subfiltro-pill active';
                pillTodos.setAttribute('data-tema', 'TODOS');
                pillTodos.innerHTML = `Todos os Temas <span class="subfiltro-pill-count">${taxonomiaEspecialidades[esp].total}</span>`;
                pillTodos.onclick = (e) => {
                    if (e) e.preventDefault();
                    filtrarPorTema('TODOS');
                };
                pillsContainer.appendChild(pillTodos);

                listaTemas.forEach(t => {
                    const p = document.createElement('button');
                    p.type = 'button';
                    p.className = 'subfiltro-pill';
                    p.setAttribute('data-tema', t);
                    p.innerHTML = `${t} <span class="subfiltro-pill-count">${temasObj[t].total}</span>`;
                    p.onclick = (e) => {
                        if (e) e.preventDefault();
                        filtrarPorTema(t);
                    };
                    pillsContainer.appendChild(p);
                });
            }
        }
    }

    if (typeof gtag === 'function') {
        gtag('event', 'filtrar_especialidade', {
            'especialidade': esp
        });
    }

    aplicarFiltroEPaginacao(true);
}

function filtrarPorTema(tema) {
    temaAtivo = tema;
    subtemaAtivo = 'TODOS';
    paginaAtual = 1;

    // Sincroniza Sub-pills de Temas
    document.querySelectorAll('.subfiltro-pill').forEach(btn => {
        if (btn.getAttribute('data-tema') === tema) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Renderiza subtemas do tema selecionado (3º nível)
    const subtemasWrapper = document.getElementById('filtro-subtemas-wrapper');
    const subtemasContainer = document.getElementById('filtro-subtemas-pills');

    if (tema === 'TODOS' || !taxonomiaEspecialidades[especialidadeAtiva] || !taxonomiaEspecialidades[especialidadeAtiva].temas[tema]) {
        if (subtemasWrapper) subtemasWrapper.style.display = 'none';
    } else {
        const subtemasObj = taxonomiaEspecialidades[especialidadeAtiva].temas[tema].subtemas || {};
        const listaSubtemas = Object.keys(subtemasObj).sort();

        if (listaSubtemas.length <= 1 && (listaSubtemas[0] === 'Diversos' || listaSubtemas[0] === 'Geral')) {
            if (subtemasWrapper) subtemasWrapper.style.display = 'none';
        } else {
            if (subtemasWrapper) subtemasWrapper.style.display = 'block';
            if (subtemasContainer) {
                subtemasContainer.innerHTML = '';

                // Pill "Todos os Subtemas"
                const pillTodosSub = document.createElement('button');
                pillTodosSub.type = 'button';
                pillTodosSub.className = 'subtema-pill active';
                pillTodosSub.setAttribute('data-subtema', 'TODOS');
                pillTodosSub.innerHTML = `Todos os Subtemas <span class="subtema-pill-count">${taxonomiaEspecialidades[especialidadeAtiva].temas[tema].total}</span>`;
                pillTodosSub.onclick = (e) => {
                    if (e) e.preventDefault();
                    filtrarPorSubtema('TODOS');
                };
                subtemasContainer.appendChild(pillTodosSub);

                // Pills individuais de Subtemas
                listaSubtemas.forEach(s => {
                    const pillSub = document.createElement('button');
                    pillSub.type = 'button';
                    pillSub.className = 'subtema-pill';
                    pillSub.setAttribute('data-subtema', s);
                    pillSub.innerHTML = `${s} <span class="subtema-pill-count">${subtemasObj[s]}</span>`;
                    pillSub.onclick = (e) => {
                        if (e) e.preventDefault();
                        filtrarPorSubtema(s);
                    };
                    subtemasContainer.appendChild(pillSub);
                });
            }
        }
    }

    if (typeof gtag === 'function') {
        gtag('event', 'filtrar_tema', {
            'especialidade': especialidadeAtiva,
            'tema': tema
        });
    }

    aplicarFiltroEPaginacao(true);
}

function filtrarPorSubtema(subtema) {
    subtemaAtivo = subtema;
    paginaAtual = 1;

    // Sincroniza pills de subtemas
    document.querySelectorAll('.subtema-pill').forEach(btn => {
        if (btn.getAttribute('data-subtema') === subtema) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    if (typeof gtag === 'function') {
        gtag('event', 'filtrar_subtema', {
            'especialidade': especialidadeAtiva,
            'tema': temaAtivo,
            'subtema': subtema
        });
    }

    aplicarFiltroEPaginacao(true);
}

function aplicarFiltroEPaginacao(scroll = false) {
    if (todosCards.length === 0) return;

    if (modoFiltroAtivo === 'clinico') {
        const espFiltro = (especialidadeAtiva || 'TODAS').trim();
        const temaFiltro = (temaAtivo || 'TODOS').trim();
        const subtemaFiltro = (subtemaAtivo || 'TODOS').trim();

        cardsFiltrados = todosCards.filter(card => {
            const esp = (card.getAttribute('data-especialidade') || '').trim();
            const tema = (card.getAttribute('data-tema') || '').trim();
            const subtema = (card.getAttribute('data-subtema') || '').trim();

            if (espFiltro !== 'TODAS' && esp !== espFiltro) return false;
            if (temaFiltro !== 'TODOS' && tema !== temaFiltro) return false;
            if (subtemaFiltro !== 'TODOS' && subtema !== subtemaFiltro) return false;
            return true;
        });
    } else {
        // Modo Prova (Banca > Ano/Edição > Questão)
        const bancaFiltro = (bancaAtiva || 'TODAS').toUpperCase();
        const edicaoFiltro = (edicaoAtiva || 'TODAS').trim();
        const numFiltro = (numeroQuestaoFiltro || '').trim();

        cardsFiltrados = todosCards.filter(card => {
            const cardBanca = (card.getAttribute('data-banca') || '').toUpperCase();
            const cardRotulo = (card.getAttribute('data-rotulo-edicao') || card.getAttribute('data-origem') || '').trim();
            const cardNum = (card.getAttribute('data-numero') || '').trim();

            if (bancaFiltro !== 'TODAS' && cardBanca !== bancaFiltro) return false;
            if (edicaoFiltro !== 'TODAS' && cardRotulo !== edicaoFiltro) return false;
            if (numFiltro !== '' && cardNum !== numFiltro) return false;
            return true;
        });

        // Atualiza status textual da busca por questão
        const statusEl = document.getElementById('filtro-questao-status');
        if (statusEl) {
            if (numFiltro !== '') {
                statusEl.textContent = `${cardsFiltrados.length} resultado(s) para a Questão ${numFiltro}`;
            } else {
                statusEl.textContent = '';
            }
        }
    }

    const totalItens = cardsFiltrados.length;
    const totalPaginas = itensPorPagina === 'all' ? 1 : (Math.ceil(totalItens / itensPorPagina) || 1);

    if (paginaAtual > totalPaginas) paginaAtual = totalPaginas;
    if (paginaAtual < 1) paginaAtual = 1;

    // Faixa visível da página
    let inicio = 0;
    let fim = totalItens;
    if (itensPorPagina !== 'all') {
        inicio = (paginaAtual - 1) * itensPorPagina;
        fim = Math.min(inicio + itensPorPagina, totalItens);
    }

    const setVisiveis = new Set(cardsFiltrados.slice(inicio, fim));

    // Aplica visibilidade nos cards e atualiza contagem visível no container
    const wrapper = document.getElementById('lista-questoes-container');
    if (wrapper) {
        wrapper.setAttribute('data-cards-visiveis', setVisiveis.size.toString());
    }

    todosCards.forEach(card => {
        if (setVisiveis.has(card)) {
            card.classList.remove('paginacao-oculto');
        } else {
            card.classList.add('paginacao-oculto');
        }
    });

    // Renderiza barras de paginação
    renderizarBarrasPaginacao(totalItens, totalPaginas, inicio + 1, fim);

    if (scroll) {
        const section = document.querySelector('.filtro-section');
        if (section) {
            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

function renderizarBarrasPaginacao(totalItens, totalPaginas, itemInicio, itemFim) {
    const containers = [
        document.getElementById('paginacao-top'),
        document.getElementById('paginacao-bottom')
    ];

    containers.forEach(container => {
        if (!container) return;

        if (itensPorPagina === 'all' || totalPaginas <= 1) {
            container.style.display = 'none';
            container.innerHTML = '';
            return;
        }

        container.style.display = 'flex';
        container.innerHTML = '';

        // Botão Anterior
        const btnPrev = document.createElement('button');
        btnPrev.type = 'button';
        btnPrev.className = 'btn-paginacao';
        btnPrev.innerHTML = '‹ Anterior';
        btnPrev.disabled = (paginaAtual === 1);
        btnPrev.onclick = () => mudarPagina(paginaAtual - 1);
        container.appendChild(btnPrev);

        // Numeração de páginas com reticências
        const paginasNumeros = calcularRangePaginas(paginaAtual, totalPaginas);
        paginasNumeros.forEach(item => {
            if (item === '...') {
                const el = document.createElement('span');
                el.className = 'paginacao-ellipsis';
                el.textContent = '...';
                container.appendChild(el);
            } else {
                const btnNum = document.createElement('button');
                btnNum.type = 'button';
                btnNum.className = `btn-paginacao ${item === paginaAtual ? 'active' : ''}`;
                btnNum.textContent = item;
                btnNum.onclick = () => mudarPagina(item);
                container.appendChild(btnNum);
            }
        });

        // Botão Próxima
        const btnNext = document.createElement('button');
        btnNext.type = 'button';
        btnNext.className = 'btn-paginacao';
        btnNext.innerHTML = 'Próxima ›';
        btnNext.disabled = (paginaAtual === totalPaginas);
        btnNext.onclick = () => mudarPagina(paginaAtual + 1);
        container.appendChild(btnNext);

        // Badge Informativo
        const badge = document.createElement('span');
        badge.className = 'paginacao-info-badge';
        badge.textContent = `${itemInicio}–${itemFim} de ${totalItens}`;
        container.appendChild(badge);
    });
}

function calcularRangePaginas(atual, total) {
    if (total <= 7) {
        return Array.from({ length: total }, (_, i) => i + 1);
    }
    if (atual <= 4) {
        return [1, 2, 3, 4, 5, '...', total];
    }
    if (atual >= total - 3) {
        return [1, '...', total - 4, total - 3, total - 2, total - 1, total];
    }
    return [1, '...', atual - 1, atual, atual + 1, '...', total];
}

function mudarPagina(novaPagina) {
    paginaAtual = novaPagina;
    aplicarFiltroEPaginacao(true);
}

function mudarItensPorPagina(qtd) {
    itensPorPagina = (qtd === 'all') ? 'all' : parseInt(qtd, 10);
    paginaAtual = 1;
    aplicarFiltroEPaginacao(true);
}

// ========================================================
// Modal de Confirmação para Limpar Respostas
// ========================================================
function abrirConfirmResetModal() {
    const modal = document.getElementById('confirm-reset-modal-overlay');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function fecharConfirmResetModal(e) {
    if (!e || e.target.id === 'confirm-reset-modal-overlay' || e.target.closest('.confirm-modal-close') || e.target.closest('.btn-confirm-cancel')) {
        const modal = document.getElementById('confirm-reset-modal-overlay');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
}

function executarLimparRespostas() {
    localStorage.removeItem(STORAGE_KEY);
    document.querySelectorAll('input[type="radio"]').forEach(r => r.checked = false);
    document.querySelectorAll('.card-questao').forEach(c => c.classList.remove('answered'));
    document.querySelectorAll('.alternativa').forEach(l => l.classList.remove('selected', 'correct', 'incorrect'));
    document.querySelectorAll('.gabarito-box').forEach(b => b.style.display = 'none');
    atualizarBarra(0);
    atualizarEstatisticas();
    fecharConfirmResetModal();
}

// ========================================================
// Alternância de Tema Instantânea (Zero Lag / Zero Flash)
// ========================================================
function initTheme() {
    const savedTheme = localStorage.getItem('simulado_theme_preference') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    setTheme(savedTheme, false);
}

function setTheme(theme, skipTransition = true) {
    if (skipTransition) {
        document.documentElement.classList.add('disable-transitions');
    }
    const img = document.getElementById('theme-icon-img');
    if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        if (img && window.IMG_CLARO_B64) {
            img.src = window.IMG_CLARO_B64;
            img.alt = 'Alternar para Modo Claro';
        }
    } else {
        document.documentElement.removeAttribute('data-theme');
        if (img && window.IMG_DARK_B64) {
            img.src = window.IMG_DARK_B64;
            img.alt = 'Alternar para Modo Escuro';
        }
    }
    localStorage.setItem('simulado_theme_preference', theme);
    if (skipTransition) {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                document.documentElement.classList.remove('disable-transitions');
            });
        });
    }
}

function toggleTheme() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    setTheme(isDark ? 'light' : 'dark', true);
}

// ========================================================
// Funções do Modal de Apoio / Pix
// ========================================================
function abrirApoioModal() {
    if (typeof gtag === 'function') {
        gtag('event', 'abrir_modal_apoio', {
            'event_category': 'Engajamento',
            'event_label': 'Modal_Pix_Cafe'
        });
    }
    const modal = document.getElementById('apoio-modal-overlay');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function fecharApoioModal(e) {
    if (!e || e.target.id === 'apoio-modal-overlay' || e.target.closest('.kofi-modal-close') || e.target.closest('.btn-aviso-ok')) {
        const modal = document.getElementById('apoio-modal-overlay');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
}

function copiarChavePix() {
    const input = document.getElementById('pix-key-input');
    const btn = document.getElementById('btn-pix-copy');
    if (!input) return;

    const chave = input.value;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(chave).then(mostrarFeedbackCopiado);
    } else {
        input.select();
        document.execCommand('copy');
        mostrarFeedbackCopiado();
    }

    if (typeof gtag === 'function') {
        gtag('event', 'copiar_chave_pix', {
            'event_category': 'Conversao',
            'event_label': 'Chave_Pix_Copiada'
        });
    }
}

function mostrarFeedbackCopiado() {
    const btn = document.getElementById('btn-pix-copy');
    if (!btn) return;
    const textoOriginal = btn.innerHTML;
    btn.innerHTML = '<span>✓ Copiado!</span>';
    btn.classList.add('copied');
    setTimeout(() => {
        btn.innerHTML = textoOriginal;
        btn.classList.remove('copied');
    }, 2200);
}

function registrarCliqueKofi() {
    if (typeof gtag === 'function') {
        gtag('event', 'clique_kofi_doacao', {
            'event_category': 'Engajamento',
            'event_label': 'Botao_Apoio_Kofi'
        });
    }
}

// ========================================================
// Funções do Modal de Aviso
// ========================================================
function abrirAvisoModal() {
    const modal = document.getElementById('aviso-modal-overlay');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function fecharAvisoModal(e) {
    if (!e || e.target.id === 'aviso-modal-overlay' || e.target.closest('.aviso-modal-close') || e.target.closest('.btn-aviso-ok')) {
        const modal = document.getElementById('aviso-modal-overlay');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
}

// ========================================================
// Funções do Modal do Caderno de Erros (Drill-down Hierárquico)
// ========================================================
let cadernoErrosEstado = { esp: null, tema: null };

function encontrarCardQuestao(qId) {
    let card = document.getElementById('card_' + qId) || document.getElementById(qId);
    if (!card && qId.startsWith('q_')) {
        card = document.getElementById('card_' + qId.substring(2));
    }
    if (!card && !qId.startsWith('q_')) {
        card = document.getElementById('card_q_' + qId);
    }
    if (!card) {
        // Tenta remover índice final antigo como _1, _2, etc
        const baseQId = qId.replace(/_\d+$/, '');
        card = document.getElementById('card_' + baseQId) || document.getElementById(baseQId) || document.getElementById('card_q_' + baseQId.replace(/^q_/, ''));
    }
    if (!card) {
        // Busca flexível por prefixo de ID (ex: card_q_ENARE-2023-Objetiva_42)
        const cleanId = qId.replace(/^card_/, '').replace(/^q_/, '').replace(/_\d+$/, '');
        card = document.querySelector(`[id^="card_q_${cleanId}"]`) || document.querySelector(`[id*="${cleanId}"]`);
    }
    return card;
}

function coletarErrosHierarquicos() {
    const dados = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    const tree = {};
    let totalGeral = 0;
    let mudouStorage = false;

    for (const [qId, valorMarcado] of Object.entries(dados)) {
        const card = encontrarCardQuestao(qId);
        if (!card) {
            delete dados[qId];
            mudouStorage = true;
            continue;
        }

        const radio = card.querySelector('input[type="radio"]');
        if (!radio) continue;

        const gabarito = radio.getAttribute('data-gabarito');
        if (!gabarito || gabarito === 'N/A' || gabarito === 'ANULADA') continue;

        if (valorMarcado !== gabarito) {
            totalGeral++;
            const esp = card.getAttribute('data-especialidade') || 'Cirurgia Geral';
            const tema = card.getAttribute('data-tema') || 'Geral';
            
            // Extração infalível da tag
            let tagTexto = '';
            const tagOrigemEl = card.querySelector('.tag-origem');
            if (tagOrigemEl && tagOrigemEl.innerText.trim()) {
                tagTexto = tagOrigemEl.innerText.replace(/\s+/g, ' ').trim();
            } else {
                tagTexto = `${card.id.replace('card_q_', '').replace('card_', '')} • ${tema}`;
            }

            // Extração infalível do enunciado
            let enuncTexto = '';
            const enuncEl = card.querySelector('.enunciado');
            if (enuncEl && enuncEl.innerText.trim()) {
                enuncTexto = enuncEl.innerText.replace(/\s+/g, ' ').trim();
            }
            if (!enuncTexto) {
                const clone = card.cloneNode(true);
                clone.querySelectorAll('.alternativas-container, .gabarito-box, button, .tag-origem').forEach(el => el.remove());
                enuncTexto = clone.innerText.replace(/\s+/g, ' ').trim();
            }
            if (!enuncTexto) {
                enuncTexto = 'Clique em "Ver Questão 🔍" para visualizar esta questão completa no simulado.';
            }

            const realQId = card.id.replace(/^card_/, '');

            if (!tree[esp]) tree[esp] = {};
            if (!tree[esp][tema]) tree[esp][tema] = [];

            tree[esp][tema].push({
                qId: realQId,
                esp: esp,
                tema: tema,
                tag: tagTexto,
                enunciado: enuncTexto,
                marcada: valorMarcado,
                gabarito: gabarito
            });
        }
    }

    if (mudouStorage) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(dados));
    }

    return { tree, totalGeral };
}

function abrirCadernoErrosModal() {
    cadernoErrosEstado = { esp: null, tema: null };
    renderizarCadernoErros();

    const modal = document.getElementById('caderno-erros-modal-overlay');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    if (typeof gtag === 'function') {
        gtag('event', 'abrir_caderno_erros');
    }
}

function renderizarCadernoErros() {
    const listaContainer = document.getElementById('caderno-erros-lista');
    const subtitulo = document.getElementById('caderno-erros-subtitulo');
    if (!listaContainer) return;

    const { tree, totalGeral } = coletarErrosHierarquicos();

    if (totalGeral === 0) {
        if (subtitulo) subtitulo.textContent = 'Você ainda não possui erros registrados';
        listaContainer.innerHTML = `
            <div class="erro-empty-state">
                <div class="erro-empty-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                        <polyline points="22 4 12 14.01 9 11.01"></polyline>
                    </svg>
                </div>
                <h4>Nenhum erro registrado até o momento!</h4>
                <p>Continue respondendo às questões do simulado. Se errar alguma, ela aparecerá automaticamente aqui para você revisar.</p>
            </div>
        `;
        return;
    }

    listaContainer.innerHTML = '';

    // ==========================================
    // NÍVEL 1: Lista de Especialidades (Folders)
    // ==========================================
    if (cadernoErrosEstado.esp === null) {
        if (subtitulo) {
            subtitulo.textContent = `${totalGeral} ${totalGeral === 1 ? 'questão para revisão' : 'questões para revisão'} • Selecione uma especialidade`;
        }

        const folderList = document.createElement('div');
        folderList.className = 'caderno-folder-list';

        Object.keys(tree).sort().forEach(esp => {
            let totalEsp = 0;
            Object.values(tree[esp]).forEach(arr => totalEsp += arr.length);

            const folderItem = document.createElement('div');
            folderItem.className = 'caderno-folder-item';
            folderItem.onclick = () => selecionarEspCaderno(esp);

            folderItem.innerHTML = `
                <div class="caderno-folder-info">
                    <span class="caderno-folder-icon">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                        </svg>
                    </span>
                    <span class="caderno-folder-name">${esp}</span>
                </div>
                <div class="caderno-folder-meta">
                    <span class="erro-grupo-count">${totalEsp} ${totalEsp === 1 ? 'erro' : 'erros'}</span>
                    <span class="caderno-folder-arrow">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                    </span>
                </div>
            `;
            folderList.appendChild(folderItem);
        });

        listaContainer.appendChild(folderList);
    }
    // ==========================================
    // NÍVEL 2: Lista de Temas da Especialidade
    // ==========================================
    else if (cadernoErrosEstado.esp !== null && cadernoErrosEstado.tema === null) {
        const esp = cadernoErrosEstado.esp;
        const temasTree = tree[esp] || {};
        let totalEsp = 0;
        Object.values(temasTree).forEach(arr => totalEsp += arr.length);

        if (subtitulo) {
            subtitulo.textContent = `${totalEsp} ${totalEsp === 1 ? 'erro' : 'erros'} em ${esp} • Selecione um tema`;
        }

        // Breadcrumb limpo e sem redundâncias
        const breadcrumb = document.createElement('div');
        breadcrumb.className = 'caderno-breadcrumb-bar';
        breadcrumb.innerHTML = `
            <button type="button" class="btn-breadcrumb-back" onclick="voltarNivelCaderno()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="19" y1="12" x2="5" y2="12"></line>
                    <polyline points="12 19 5 12 12 5"></polyline>
                </svg>
                Voltar
            </button>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-current">${esp}</span>
        `;
        listaContainer.appendChild(breadcrumb);

        const folderList = document.createElement('div');
        folderList.className = 'caderno-folder-list';

        Object.keys(temasTree).sort().forEach(tema => {
            const totalTema = temasTree[tema].length;
            const folderItem = document.createElement('div');
            folderItem.className = 'caderno-folder-item';
            folderItem.onclick = () => selecionarTemaCaderno(esp, tema);

            folderItem.innerHTML = `
                <div class="caderno-folder-info">
                    <span class="caderno-folder-icon">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                        </svg>
                    </span>
                    <span class="caderno-folder-name">${tema}</span>
                </div>
                <div class="caderno-folder-meta">
                    <span class="erro-grupo-count">${totalTema} ${totalTema === 1 ? 'erro' : 'erros'}</span>
                    <span class="caderno-folder-arrow">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                    </span>
                </div>
            `;
            folderList.appendChild(folderItem);
        });

        listaContainer.appendChild(folderList);
    }
    // ==========================================
    // NÍVEL 3: Lista de Questões Erradas do Tema
    // ==========================================
    else {
        const esp = cadernoErrosEstado.esp;
        const tema = cadernoErrosEstado.tema;
        const itens = (tree[esp] && tree[esp][tema]) ? tree[esp][tema] : [];

        if (subtitulo) {
            subtitulo.textContent = `${itens.length} ${itens.length === 1 ? 'questão' : 'questões'} em ${tema}`;
        }

        // Breadcrumb limpo e sem redundâncias
        const breadcrumb = document.createElement('div');
        breadcrumb.className = 'caderno-breadcrumb-bar';
        breadcrumb.innerHTML = `
            <button type="button" class="btn-breadcrumb-back" onclick="voltarNivelCaderno()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="19" y1="12" x2="5" y2="12"></line>
                    <polyline points="12 19 5 12 12 5"></polyline>
                </svg>
                Voltar
            </button>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-current"><strong>${esp}</strong> › ${tema}</span>
        `;
        listaContainer.appendChild(breadcrumb);

        const grupoEl = document.createElement('div');
        grupoEl.className = 'erro-grupo-esp';

        itens.forEach(item => {
            const itemEl = document.createElement('div');
            itemEl.className = 'erro-item-card';

            const infoEl = document.createElement('div');
            infoEl.className = 'erro-item-info';

            const tagEl = document.createElement('span');
            tagEl.className = 'erro-item-tag';
            tagEl.textContent = item.tag;

            const snippetEl = document.createElement('div');
            snippetEl.className = 'erro-item-snippet';
            snippetEl.textContent = item.enunciado;
            snippetEl.setAttribute('title', item.enunciado);

            const feedbackEl = document.createElement('div');
            feedbackEl.className = 'erro-item-feedback';

            const badgeMarcada = document.createElement('span');
            badgeMarcada.className = 'erro-badge-marcada';
            badgeMarcada.textContent = `Sua resposta: (${item.marcada})`;

            const badgeGabarito = document.createElement('span');
            badgeGabarito.className = 'erro-badge-gabarito';
            badgeGabarito.textContent = `Gabarito: (${item.gabarito})`;

            feedbackEl.appendChild(badgeMarcada);
            feedbackEl.appendChild(badgeGabarito);

            infoEl.appendChild(tagEl);
            infoEl.appendChild(snippetEl);
            infoEl.appendChild(feedbackEl);

            const btnEl = document.createElement('button');
            btnEl.type = 'button';
            btnEl.className = 'btn-ver-questao-erro';
            btnEl.innerHTML = `Ver Questão <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px; margin-left: 4px;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
            btnEl.onclick = () => navegarParaQuestao(item.qId, item.esp, item.tema);

            itemEl.appendChild(infoEl);
            itemEl.appendChild(btnEl);
            grupoEl.appendChild(itemEl);
        });

        listaContainer.appendChild(grupoEl);
    }
}

function selecionarEspCaderno(esp) {
    cadernoErrosEstado.esp = esp;
    cadernoErrosEstado.tema = null;
    renderizarCadernoErros();
}

function selecionarTemaCaderno(esp, tema) {
    cadernoErrosEstado.esp = esp;
    cadernoErrosEstado.tema = tema;
    renderizarCadernoErros();
}

function voltarNivelCaderno() {
    if (cadernoErrosEstado.tema !== null) {
        cadernoErrosEstado.tema = null;
    } else {
        cadernoErrosEstado.esp = null;
    }
    renderizarCadernoErros();
}

function fecharCadernoErrosModal(e) {
    if (!e || e.target.id === 'caderno-erros-modal-overlay' || e.target.closest('.confirm-modal-close')) {
        const modal = document.getElementById('caderno-erros-modal-overlay');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
}

function navegarParaQuestao(qId, espAlvo, temaAlvo) {
    fecharCadernoErrosModal();

    // 1. Seta a especialidade
    if (especialidadeAtiva !== espAlvo) {
        filtrarPorEspecialidade(espAlvo);
    }

    // 2. Seta o tema se fornecido
    if (temaAlvo && temaAtivo !== temaAlvo) {
        filtrarPorTema(temaAlvo);
    }

    // 3. Localiza o card da questão
    const targetCard = encontrarCardQuestao(qId);
    if (!targetCard) return;

    const idx = cardsFiltrados.indexOf(targetCard);
    if (idx !== -1 && itensPorPagina !== 'all') {
        const paginaAlvo = Math.floor(idx / itensPorPagina) + 1;
        if (paginaAtual !== paginaAlvo) {
            mudarPagina(paginaAlvo);
        }
    }

    // 4. Scroll suave até o card e animação luminosa
    setTimeout(() => {
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        targetCard.classList.remove('highlight-target');
        void targetCard.offsetWidth; // Reflow para reiniciar animação
        targetCard.classList.add('highlight-target');
        setTimeout(() => {
            targetCard.classList.remove('highlight-target');
        }, 2200);
    }, 180);
}

// ========================================================
// Funções do Modal de Desempenho e Taxa de Acerto
// ========================================================
const CORES_ESPECIALIDADES = {
    'Cirurgia Geral': '#10b981',
    'Clínica Médica': '#2563eb',
    'Ginecologia e Obstetrícia': '#ec4899',
    'Medicina Preventiva e Social / MFC': '#06b6d4',
    'Pediatria': '#f59e0b',
    'Outros / Não Categorizados': '#64748b'
};

function abrirDesempenhoModal() {
    renderizarDesempenhoModal();
    const modal = document.getElementById('desempenho-modal-overlay');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    if (typeof gtag === 'function') {
        gtag('event', 'abrir_modal_desempenho');
    }
}

function fecharDesempenhoModal(e) {
    if (!e || e.target.id === 'desempenho-modal-overlay' || e.target.closest('.confirm-modal-close')) {
        const modal = document.getElementById('desempenho-modal-overlay');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
}

function renderizarDesempenhoModal() {
    const container = document.getElementById('desempenho-modal-conteudo');
    const subtitulo = document.getElementById('desempenho-modal-subtitulo');
    if (!container) return;

    const dados = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    const statsPorEsp = {};
    let totalAcertos = 0;
    let totalErros = 0;
    let totalRespondidas = 0;

    for (const [qId, valorMarcado] of Object.entries(dados)) {
        const card = encontrarCardQuestao(qId);
        if (!card) continue;

        const radio = card.querySelector('input[type="radio"]');
        if (!radio) continue;

        const gabarito = radio.getAttribute('data-gabarito');
        if (!gabarito || gabarito === 'N/A') continue;

        const esp = card.getAttribute('data-especialidade') || 'Cirurgia Geral';
        if (!statsPorEsp[esp]) {
            statsPorEsp[esp] = { acertos: 0, erros: 0, respondidas: 0 };
        }

        statsPorEsp[esp].respondidas++;
        totalRespondidas++;

        if (valorMarcado === gabarito || gabarito === 'ANULADA') {
            statsPorEsp[esp].acertos++;
            totalAcertos++;
        } else {
            statsPorEsp[esp].erros++;
            totalErros++;
        }
    }

    const taxaGeral = totalRespondidas > 0 ? Math.round((totalAcertos / totalRespondidas) * 100) : 0;

    if (totalRespondidas === 0) {
        if (subtitulo) subtitulo.textContent = 'Você ainda não respondeu a nenhuma questão';
        container.innerHTML = `
            <div class="erro-empty-state">
                <div class="erro-empty-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path>
                        <path d="M22 12A10 10 0 0 0 12 2v10z"></path>
                    </svg>
                </div>
                <h4>Nenhum dado registrado para análise</h4>
                <p>Comece a responder às questões do simulado para gerar seu gráfico de desempenho e diagnóstico clínico por especialidade.</p>
            </div>
        `;
        return;
    }

    if (subtitulo) {
        subtitulo.textContent = `${totalRespondidas} ${totalRespondidas === 1 ? 'questão avaliada' : 'questões avaliadas'} • Taxa geral de aproveitamento: ${taxaGeral}%`;
    }

    // Calcula taxas e identifica melhor / área de atenção
    let melhorEsp = null;
    let maiorTaxa = -1;
    let atencaoEsp = null;
    let menorTaxa = 101;

    Object.keys(statsPorEsp).forEach(esp => {
        const item = statsPorEsp[esp];
        item.taxa = Math.round((item.acertos / item.respondidas) * 100);
        if (item.taxa > maiorTaxa) {
            maiorTaxa = item.taxa;
            melhorEsp = esp;
        }
        if (item.taxa < menorTaxa) {
            menorTaxa = item.taxa;
            atencaoEsp = esp;
        }
    });

    if (Object.keys(statsPorEsp).length <= 1 || maiorTaxa === menorTaxa) {
        atencaoEsp = null;
    }

    // 1. Diagnóstico Clínico
    let diagnosticoHtml = `
        <div class="diagnostico-box">
            <div class="diagnostico-card diagnostico-card-melhor">
                <span class="diagnostico-icon diagnostico-icon-melhor">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M6 9H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h2"></path>
                        <path d="M18 9h2a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2h-2"></path>
                        <path d="M4 22h16"></path>
                        <path d="M10 14.66V17c0 .55-.45 1-1 1H7c-.55 0-1 .45-1 1v1c0 .55.45 1 1 1h10c.55 0 1-.45 1-1v-1c0-.55-.45-1-1-1h-2c-.55 0-1-.45-1-1v-2.34"></path>
                        <path d="M18 2H6v7a6 6 0 0 0 12 0V2z"></path>
                    </svg>
                </span>
                <div class="diagnostico-info">
                    <h4>Sua melhor especialidade é ${melhorEsp}</h4>
                    <p>Você atingiu <strong>${maiorTaxa}% de aproveitamento</strong> com ${statsPorEsp[melhorEsp].acertos} acertos em ${statsPorEsp[melhorEsp].respondidas} questões.</p>
                </div>
            </div>
    `;

    if (atencaoEsp) {
        diagnosticoHtml += `
            <div class="diagnostico-card diagnostico-card-atencao">
                <span class="diagnostico-icon diagnostico-icon-atencao">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <circle cx="12" cy="12" r="6"></circle>
                        <circle cx="12" cy="12" r="2"></circle>
                    </svg>
                </span>
                <div class="diagnostico-info">
                    <h4>Área recomendada para foco: ${atencaoEsp}</h4>
                    <p>Aproveitamento atual de <strong>${menorTaxa}%</strong> (${statsPorEsp[atencaoEsp].erros} ${statsPorEsp[atencaoEsp].erros === 1 ? 'erro' : 'erros'}). Revise os temas desta matéria no Caderno de Erros.</p>
                </div>
            </div>
        `;
    }

    diagnosticoHtml += `</div>`;

    // 2. Gráfico Donut SVG (Ajustado para maior espaçamento interno e raio amplo)
    const C = 565.48668; // 2 * PI * 90
    let svgDonutSlices = '';
    let offsetAcumulado = 0;

    if (totalAcertos === 0) {
        svgDonutSlices = `<circle cx="120" cy="120" r="90" fill="transparent" stroke="var(--border-color)" stroke-width="20"></circle>`;
    } else {
        Object.keys(statsPorEsp).sort().forEach(esp => {
            const acertos = statsPorEsp[esp].acertos;
            if (acertos > 0) {
                const frac = acertos / totalAcertos;
                const dash = (frac * C).toFixed(2);
                const cor = CORES_ESPECIALIDADES[esp] || '#2563eb';
                svgDonutSlices += `
                    <circle cx="120" cy="120" r="90" fill="transparent"
                        stroke="${cor}" stroke-width="20"
                        stroke-dasharray="${dash} ${C.toFixed(2)}"
                        stroke-dashoffset="-${offsetAcumulado.toFixed(2)}"
                        style="transition: stroke-dasharray 0.8s ease;">
                    </circle>
                `;
                offsetAcumulado += parseFloat(dash);
            }
        });
    }

    // 3. Detalhamento por Especialidades
    let listaEspHtml = `<div class="desempenho-lista-esp">`;
    Object.keys(statsPorEsp).sort().forEach(esp => {
        const item = statsPorEsp[esp];
        const cor = CORES_ESPECIALIDADES[esp] || '#2563eb';
        listaEspHtml += `
            <div class="esp-barra-item">
                <div class="esp-barra-header">
                    <span class="esp-barra-nome">
                        <span class="esp-cor-dot" style="background: ${cor};"></span>
                        ${esp}
                    </span>
                    <span class="esp-barra-metricas">${item.acertos} / ${item.respondidas} acertos <span style="color: ${cor}; margin-left: 6px;">(${item.taxa}%)</span></span>
                </div>
                <div class="esp-barra-track">
                    <div class="esp-barra-fill" style="width: ${item.taxa}%; background: ${cor};"></div>
                </div>
            </div>
        `;
    });
    listaEspHtml += `</div>`;

    container.innerHTML = `
        ${diagnosticoHtml}
        <div class="desempenho-grid">
            <div class="desempenho-chart-section">
                <div class="donut-container">
                    <svg width="240" height="240" viewBox="0 0 240 240" class="donut-svg">
                        <circle cx="120" cy="120" r="90" fill="transparent" stroke="var(--alt-hover-bg)" stroke-width="20"></circle>
                        ${svgDonutSlices}
                    </svg>
                    <div class="donut-center-text">
                        <div class="donut-center-taxa">${taxaGeral}%</div>
                        <div class="donut-center-label">Aproveitamento</div>
                    </div>
                </div>
            </div>
            ${listaEspHtml}
        </div>
    `;
}

// Fechamento de modais via Tecla ESC
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const apoioModal = document.getElementById('apoio-modal-overlay');
        if (apoioModal && apoioModal.classList.contains('active')) {
            fecharApoioModal();
        }
        const avisoModal = document.getElementById('aviso-modal-overlay');
        if (avisoModal && avisoModal.classList.contains('active')) {
            fecharAvisoModal();
        }
        const confirmModal = document.getElementById('confirm-reset-modal-overlay');
        if (confirmModal && confirmModal.classList.contains('active')) {
            fecharConfirmResetModal();
        }
        const errosModal = document.getElementById('caderno-erros-modal-overlay');
        if (errosModal && errosModal.classList.contains('active')) {
            fecharCadernoErrosModal();
        }
        const desempenhoModal = document.getElementById('desempenho-modal-overlay');
        if (desempenhoModal && desempenhoModal.classList.contains('active')) {
            fecharDesempenhoModal();
        }
    }
});

// Inicialização completa
initTheme();
window.addEventListener('DOMContentLoaded', () => {
    carregarRespostas();
    inicializarPaginacaoEFiltros();
});

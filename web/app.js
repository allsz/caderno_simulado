// Chaves de armazenamento suportadas para migração transparente e backup de segurança
const STORAGE_KEY = 'caderno_respostas_simulado';
const BACKUP_STORAGE_KEY = 'caderno_respostas_simulado_backup';
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
// Helper Universal para Google Analytics 4 (GA4)
// ========================================================
function trackGA4Event(eventName, params = {}) {
    try {
        if (typeof gtag === 'function') {
            gtag('event', eventName, params);
        } else if (window.dataLayer && Array.isArray(window.dataLayer)) {
            window.dataLayer.push({
                event: eventName,
                ...params
            });
        }
    } catch (err) {
        console.warn('[Analytics] Falha ao registrar evento:', eventName, err);
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

// Normalização e compatibilidade retroativa para IDs de questões renomeadas/migradas
function normalizarIdQuestao(qId) {
    if (!qId) return qId;
    let nId = String(qId);
    if (nId.includes('ENARE-2026-Objetiva_')) {
        nId = nId.replace('ENARE-2026-Objetiva_', 'ENARE-2025-Objetiva-Carderno1_');
    }
    if (nId.includes('ENARE-2025-Objetiva_') && !nId.includes('ENARE-2025-Objetiva-')) {
        nId = nId.replace('ENARE-2025-Objetiva_', 'ENARE-2025-Objetiva-AcessoDireto-Tipo3_');
    }
    return nId;
}

// Extrai sufixo volátil legado apenas se houver mais de um número no ID (ex: Prova_42_155 -> Prova_42)
// Preserva intacto o número da questão caso seja único (ex: Prova_42)
function extrairBaseIdAntigo(str) {
    if (!str) return str;
    const matchDuploNumero = str.match(/^(.*_\d+)_\d+$/);
    if (matchDuploNumero) return matchDuploNumero[1];
    return str;
}

// Índices em memória para lookups instantâneos O(1) de cards e inputs (Zero overhead no DOM)
let _indicesDOMConstruidos = false;
const _cardDOMCache = new Map();
const _radioDOMCache = new Map();
const _mapaRadiosPorNomeEValor = new Map();
const _mapaRadiosPorNome = new Map();
const _mapaRadiosPorCleanKey = new Map();
const _mapaCardsPorId = new Map();

function construirIndicesDOMSeNecessario() {
    if (_indicesDOMConstruidos && _mapaRadiosPorNomeEValor.size > 0) return;

    // Indexa todos os cards presentes no DOM
    const cards = document.querySelectorAll('.card-questao');
    for (let i = 0; i < cards.length; i++) {
        const card = cards[i];
        if (card.id) {
            _mapaCardsPorId.set(card.id, card);
            const rawId = card.id.replace(/^card_/, '');
            _mapaCardsPorId.set(rawId, card);
            const clean = rawId.replace(/^q_/, '');
            _mapaCardsPorId.set(clean, card);
            const baseClean = extrairBaseIdAntigo(clean);
            if (baseClean !== clean) {
                _mapaCardsPorId.set(baseClean, card);
                _mapaCardsPorId.set('card_' + baseClean, card);
            }
        }
    }

    // Indexa todos os inputs de radio de alternativas
    const radios = document.querySelectorAll('input[type="radio"]');
    for (let i = 0; i < radios.length; i++) {
        const r = radios[i];
        const name = r.name;
        const val = r.value;
        if (!name) continue;

        _mapaRadiosPorNomeEValor.set(`${name}:::${val}`, r);
        if (!_mapaRadiosPorNome.has(name)) {
            _mapaRadiosPorNome.set(name, r);
            const clean = name.replace(/^q_/, '');
            _mapaRadiosPorCleanKey.set(clean, name);
            const baseClean = extrairBaseIdAntigo(clean);
            if (baseClean !== clean) {
                _mapaRadiosPorCleanKey.set(baseClean, name);
            }
        }
    }

    _indicesDOMConstruidos = true;
}

function resolverRadioQuestao(qId, valor) {
    if (!qId) return null;
    const cacheKey = valor ? `${qId}:::${valor}` : `${qId}:::any`;
    if (_radioDOMCache.has(cacheKey)) {
        return _radioDOMCache.get(cacheKey);
    }

    construirIndicesDOMSeNecessario();

    const idNormalizado = normalizarIdQuestao(qId);
    const idsParaTentar = [idNormalizado, qId];

    for (const testId of idsParaTentar) {
        const baseId = extrairBaseIdAntigo(testId);
        const candidatos = [
            testId,
            testId.startsWith('q_') ? testId.substring(2) : 'q_' + testId,
            baseId,
            baseId.startsWith('q_') ? baseId.substring(2) : 'q_' + baseId
        ];

        for (const cand of candidatos) {
            if (valor) {
                const r = _mapaRadiosPorNomeEValor.get(`${cand}:::${valor}`);
                if (r) {
                    const res = { radio: r, realQId: r.name };
                    _radioDOMCache.set(cacheKey, res);
                    return res;
                }
            } else {
                const r = _mapaRadiosPorNome.get(cand);
                if (r) {
                    const res = { radio: r, realQId: r.name };
                    _radioDOMCache.set(cacheKey, res);
                    return res;
                }
            }
        }
    }

    // Busca flexível por clean key pré-indexada
    const cleanId = idNormalizado.replace(/^q_/, '');
    const baseClean = extrairBaseIdAntigo(cleanId);
    const realName = _mapaRadiosPorCleanKey.get(cleanId) || _mapaRadiosPorCleanKey.get(baseClean);
    if (realName) {
        const r = valor 
            ? _mapaRadiosPorNomeEValor.get(`${realName}:::${valor}`)
            : _mapaRadiosPorNome.get(realName);
        if (r) {
            const res = { radio: r, realQId: r.name };
            _radioDOMCache.set(cacheKey, res);
            return res;
        }
    }

    // Fallback O(1) direto no DOM
    let radio = valor 
        ? (document.querySelector(`input[name="${idNormalizado}"][value="${valor}"]`) || document.querySelector(`input[name="${qId}"][value="${valor}"]`))
        : (document.querySelector(`input[name="${idNormalizado}"]`) || document.querySelector(`input[name="${qId}"]`));
    if (radio) {
        const res = { radio, realQId: radio.name };
        _radioDOMCache.set(cacheKey, res);
        return res;
    }

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

    // Verificação O(1) de conclusão do simulado para efeitos fullscreen
    if (!window._inicializandoRespostas && total > 0 && respondidasValidas >= total && !window.simuladoFinalizadoJaDisparado) {
        window.simuladoFinalizadoJaDisparado = true;
        let cenario = 1;
        if (acertos === total) {
            cenario = 2; // Acertou todas (100%)
        } else if (acertos === 0) {
            cenario = 3; // Errou todas (0%)
        } else {
            cenario = 1; // Completou todas com acertos parciais
        }
        dispararEfeitoFinalizacao(cenario, { total, acertos, taxa });
    }
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
    window._inicializandoRespostas = true;
    construirIndicesDOMSeNecessario();

    // 1. Carrega dados do armazenamento principal
    let dados = safeStorageGet(STORAGE_KEY, {});

    // Salvaguarda contra corrupção: se os dados vierem vazios, tenta restaurar do backup automático
    if (!dados || Object.keys(dados).length === 0) {
        const backup = safeStorageGet(BACKUP_STORAGE_KEY, {});
        if (backup && Object.keys(backup).length > 0) {
            console.warn('[Simulado] Restaurando respostas automaticamente a partir do espelho de segurança...');
            dados = { ...backup };
        }
    }

    // 2. Migração automática e transparente de chaves legadas caso existam
    LEGACY_STORAGE_KEYS.forEach(legacyKey => {
        const legacyData = safeStorageGet(legacyKey, {});
        if (legacyData && Object.keys(legacyData).length > 0) {
            dados = { ...legacyData, ...dados };
        }
    });

    // 3. Cópia segura: inicializa com TODAS as respostas que o usuário já possui (nunca descarta nada)
    const dadosAtualizados = { ...dados };

    // 4. Aplica as respostas e migra chaves para o padrão estável SEM perder nenhuma resposta
    for (const [qId, valor] of Object.entries(dados)) {
        const match = resolverRadioQuestao(qId, valor);
        if (match) {
            match.radio.checked = true;
            // Se o ID mudou na migração/normalização, atualiza a chave para o novo formato
            if (match.realQId !== qId) {
                dadosAtualizados[match.realQId] = valor;
                delete dadosAtualizados[qId];
            }
            const gabarito = match.radio.getAttribute('data-gabarito');
            atualizarEstiloQuestao(match.realQId, valor, gabarito);
        }
        // Se NÃO der match no DOM atual (ex: questão em filtro ou variação de edição),
        // a resposta PERMANECE preservada em dadosAtualizados! Jamais descartamos dados do usuário.
    }

    // 5. Salva o banco seguro e atualizado
    safeStorageSet(STORAGE_KEY, dadosAtualizados);

    // 6. Atualiza o espelho de segurança automático
    if (Object.keys(dadosAtualizados).length > 0) {
        safeStorageSet(BACKUP_STORAGE_KEY, dadosAtualizados);
    }

    atualizarEstatisticas();
    window._inicializandoRespostas = false;
}

function salvarResposta(qId, valor, gabarito) {
    const dados = safeStorageGet(STORAGE_KEY, {});
    const match = resolverRadioQuestao(qId, valor);
    const realQId = match ? match.realQId : qId;

    dados[realQId] = valor;
    safeStorageSet(STORAGE_KEY, dados);
    safeStorageSet(BACKUP_STORAGE_KEY, dados);
    
    // 1. Atualização visual instantânea
    atualizarEstiloQuestao(realQId, valor, gabarito);

    // 2. Estatísticas e analytics em background (não bloqueiam o frame do clique)
    requestAnimationFrame(() => {
        atualizarEstatisticas();
        if (typeof gtag === 'function') {
            gtag('event', 'resposta_questao', {
                'questao_id': realQId,
                'acertou': (valor === gabarito)
            });
        }
    });
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

// ========================================================
// Estado e Funções do Modo Simulado Real (Etapa 1)
// ========================================================
let simuladoConfig = {
    tempoMinutos: 60,
    totalQuestoes: 20,
    modoLivre: false,
    questoesLivre: 30,
    termoAceito: false
};

function alternarModoFiltro(modo) {
    modoFiltroAtivo = modo;
    paginaAtual = 1;

    const tabClinico = document.getElementById('tab-modo-clinico');
    const tabProva = document.getElementById('tab-modo-prova');
    const tabSimulado = document.getElementById('tab-modo-simulado');
    const painelClinico = document.getElementById('painel-filtro-clinico');
    const painelProva = document.getElementById('painel-filtro-prova');
    const painelSimulado = document.getElementById('painel-filtro-simulado');
    const paginacaoQtdWrap = document.querySelector('.paginacao-qtd-select-wrap');
    const listaQuestoes = document.getElementById('lista-questoes-container');
    const paginacaoTop = document.getElementById('paginacao-top');
    const paginacaoBottom = document.getElementById('paginacao-bottom');

    if (modo === 'clinico') {
        if (tabClinico) { tabClinico.classList.add('active'); tabClinico.setAttribute('aria-selected', 'true'); }
        if (tabProva) { tabProva.classList.remove('active'); tabProva.setAttribute('aria-selected', 'false'); }
        if (tabSimulado) { tabSimulado.classList.remove('active'); tabSimulado.setAttribute('aria-selected', 'false'); }
        if (painelClinico) painelClinico.style.display = 'block';
        if (painelProva) painelProva.style.display = 'none';
        if (painelSimulado) painelSimulado.style.display = 'none';
        if (paginacaoQtdWrap) paginacaoQtdWrap.style.display = 'flex';
        if (listaQuestoes) listaQuestoes.style.display = '';
        aplicarFiltroEPaginacao(false);
    } else if (modo === 'prova') {
        if (tabClinico) { tabClinico.classList.remove('active'); tabClinico.setAttribute('aria-selected', 'false'); }
        if (tabProva) { tabProva.classList.add('active'); tabProva.setAttribute('aria-selected', 'true'); }
        if (tabSimulado) { tabSimulado.classList.remove('active'); tabSimulado.setAttribute('aria-selected', 'false'); }
        if (painelClinico) painelClinico.style.display = 'none';
        if (painelProva) painelProva.style.display = 'block';
        if (painelSimulado) painelSimulado.style.display = 'none';
        if (paginacaoQtdWrap) paginacaoQtdWrap.style.display = 'flex';
        if (listaQuestoes) listaQuestoes.style.display = '';
        aplicarFiltroEPaginacao(false);
    } else if (modo === 'simulado') {
        if (tabClinico) { tabClinico.classList.remove('active'); tabClinico.setAttribute('aria-selected', 'false'); }
        if (tabProva) { tabProva.classList.remove('active'); tabProva.setAttribute('aria-selected', 'false'); }
        if (tabSimulado) { tabSimulado.classList.add('active'); tabSimulado.setAttribute('aria-selected', 'true'); }
        if (painelClinico) painelClinico.style.display = 'none';
        if (painelProva) painelProva.style.display = 'none';
        if (painelSimulado) painelSimulado.style.display = 'block';
        if (paginacaoQtdWrap) paginacaoQtdWrap.style.display = 'none';
        if (paginacaoTop) paginacaoTop.style.display = 'none';
        if (paginacaoBottom) paginacaoBottom.style.display = 'none';
        if (listaQuestoes) listaQuestoes.style.display = 'none';

        // Sincroniza estado do botão iniciar com o checkbox
        atualizarEstadoBotaoIniciarSimulado();
        trackGA4Event('simulado_abrir_setup', { origem: 'aba_filtro' });
    }

    trackGA4Event('alternar_modo_filtro', { 'modo': modo });
}

function selecionarTempoSimulado(minutos) {
    simuladoConfig.tempoMinutos = minutos;
    
    // Atualiza pills ativas
    const pills = document.querySelectorAll('#simulado-tempo-pills .simulado-pill');
    pills.forEach(p => {
        if (parseInt(p.getAttribute('data-min'), 10) === minutos) {
            p.classList.add('active');
        } else {
            p.classList.remove('active');
        }
    });

    const livreOpcoes = document.getElementById('simulado-livre-opcoes');
    const resumoQuestoes = document.getElementById('simulado-resumo-questoes');
    const resumoRitmo = document.getElementById('simulado-resumo-ritmo');

    if (minutos === 0) {
        simuladoConfig.modoLivre = true;
        simuladoConfig.totalQuestoes = simuladoConfig.questoesLivre;
        if (livreOpcoes) livreOpcoes.style.display = 'flex';
        if (resumoQuestoes) resumoQuestoes.textContent = `${simuladoConfig.questoesLivre} questões selecionadas`;
        if (resumoRitmo) resumoRitmo.textContent = 'Sem cronômetro (Livre)';
    } else {
        simuladoConfig.modoLivre = false;
        if (livreOpcoes) livreOpcoes.style.display = 'none';
        // Regra de 3: 300 min (5h) = 100 questões -> 3 min por questão
        const qtd = Math.round(minutos / 3);
        simuladoConfig.totalQuestoes = qtd;
        if (resumoQuestoes) resumoQuestoes.textContent = `${qtd} questões oficiais`;
        if (resumoRitmo) resumoRitmo.textContent = '~3 min por questão';
    }

    trackGA4Event('simulado_selecionar_tempo', {
        tipo_controle: minutos === 0 ? 'livre' : 'tempo_limite',
        modo_livre: minutos === 0,
        tempo_minutos: minutos,
        questoes_estimadas: minutos === 0 ? simuladoConfig.questoesLivre : Math.round(minutos / 3)
    });
}

function selecionarQtdLivre(qtd) {
    simuladoConfig.questoesLivre = qtd;
    simuladoConfig.totalQuestoes = qtd;

    const pills = document.querySelectorAll('#simulado-livre-opcoes .simulado-pill-qtd');
    pills.forEach(p => {
        if (parseInt(p.textContent.trim(), 10) === qtd) {
            p.classList.add('active');
        } else {
            p.classList.remove('active');
        }
    });

    const resumoQuestoes = document.getElementById('simulado-resumo-questoes');
    if (resumoQuestoes) {
        resumoQuestoes.textContent = `${qtd} questões selecionadas`;
    }

    trackGA4Event('simulado_selecionar_qtd_livre', {
        qtd_questoes: qtd
    });
}

function atualizarEstadoBotaoIniciarSimulado() {
    const check = document.getElementById('check-termo-simulado');
    const btn = document.getElementById('btn-iniciar-simulado');
    const aceito = Boolean(check && check.checked);
    simuladoConfig.termoAceito = aceito;

    if (btn) {
        btn.disabled = !aceito;
        if (aceito) {
            btn.classList.add('ready');
        } else {
            btn.classList.remove('ready');
        }
    }
}

function confirmarInicioSimulado() {
    const check = document.getElementById('check-termo-simulado');
    if (check && check.checked) {
        simuladoConfig.termoAceito = true;
    }
    iniciarSimuladoReal();
}

// ========================================================
// Módulo 2: Motor de Sorteio, Isolamento de Questões e Estado
// ========================================================
window.simuladoAtivo = null;

function shuffleArrayFisherYates(arr) {
    const copy = arr.slice();
    for (let i = copy.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        const temp = copy[i];
        copy[i] = copy[j];
        copy[j] = temp;
    }
    return copy;
}

function obterCardsCandidatosSimulado() {
    if (!todosCards || todosCards.length === 0) {
        todosCards = Array.from(document.querySelectorAll('.card-questao'));
    }
    return todosCards.filter(card => {
        const radios = card.querySelectorAll('input[type="radio"]');
        return radios && radios.length > 0;
    });
}

function salvarSnapshotSimulado() {
    if (!window.simuladoAtivo) return;
    try {
        const json = JSON.stringify(window.simuladoAtivo);
        sessionStorage.setItem('caderno_simulado_ativo_snapshot', json);
        localStorage.setItem('caderno_simulado_ativo_snapshot', json);
    } catch (e) {
        console.warn('[Simulado] Falha ao persistir snapshot:', e);
    }
}

let intervalTimerSimulado = null;

function iniciarTimerSimulado() {
    pararTimerSimulado();

    if (!window.simuladoAtivo) return;

    atualizarDisplayTimerSimulado();

    intervalTimerSimulado = setInterval(() => {
        if (!window.simuladoAtivo || window.simuladoAtivo.status !== 'em_andamento') {
            pararTimerSimulado();
            return;
        }

        if (window.simuladoAtivo.modoLivre) {
            const decorrido = Math.floor((Date.now() - window.simuladoAtivo.inicioTimestamp) / 1000);
            window.simuladoAtivo.tempoDecorridoSegundos = decorrido;
            atualizarDisplayTimerSimulado();
        } else {
            const decorrido = Math.floor((Date.now() - window.simuladoAtivo.inicioTimestamp) / 1000);
            const restante = Math.max(0, window.simuladoAtivo.tempoTotalSegundos - decorrido);
            window.simuladoAtivo.tempoRestanteSegundos = restante;
            atualizarDisplayTimerSimulado();

            if (restante <= 0) {
                pararTimerSimulado();
                tratarTempoEsgotadoSimulado();
            }
        }
    }, 1000);
}

function pararTimerSimulado() {
    if (intervalTimerSimulado) {
        clearInterval(intervalTimerSimulado);
        intervalTimerSimulado = null;
    }
}

function formatarTempoTimer(segundos) {
    const s = Math.max(0, Math.floor(segundos));
    const horas = Math.floor(s / 3600);
    const minutos = Math.floor((s % 3600) / 60);
    const segs = s % 60;

    const pad = (n) => String(n).padStart(2, '0');

    if (horas > 0) {
        return `${pad(horas)}:${pad(minutos)}:${pad(segs)}`;
    }
    return `${pad(minutos)}:${pad(segs)}`;
}

function atualizarDisplayTimerSimulado() {
    const timerDisplay = document.getElementById('simulado-timer-display');
    const timerLabel = document.getElementById('simulado-countdown-label');
    const countdownBox = document.getElementById('simulado-countdown-box');

    if (!timerDisplay || !window.simuladoAtivo) return;

    if (window.simuladoAtivo.modoLivre) {
        if (timerLabel) timerLabel.textContent = 'TEMPO DECORRIDO';
        const decorrido = window.simuladoAtivo.tempoDecorridoSegundos || Math.floor((Date.now() - (window.simuladoAtivo.inicioTimestamp || Date.now())) / 1000);
        timerDisplay.textContent = formatarTempoTimer(decorrido);
        if (countdownBox) countdownBox.classList.remove('urgente');
    } else {
        if (timerLabel) timerLabel.textContent = 'TEMPO RESTANTE';
        const restante = typeof window.simuladoAtivo.tempoRestanteSegundos === 'number'
            ? window.simuladoAtivo.tempoRestanteSegundos
            : window.simuladoAtivo.tempoTotalSegundos;

        timerDisplay.textContent = formatarTempoTimer(restante);

        // Alerta visual de urgência quando faltar menos de 5 minutos
        if (countdownBox) {
            if (restante <= 300 && restante > 0) {
                countdownBox.classList.add('urgente');
            } else {
                countdownBox.classList.remove('urgente');
            }
        }
    }
}

function tratarTempoEsgotadoSimulado() {
    console.warn('[Simulado] Tempo de prova encerrado!');
    pararTimerSimulado();
    const timerDisplay = document.getElementById('simulado-timer-display');
    if (timerDisplay) {
        timerDisplay.textContent = '00:00:00';
    }
    // Fecha modal de conferência se estiver aberto
    fecharModalEntregaSimulado();
    alert('O tempo oficial do simulado esgotou! A prova será finalizada e entregue automaticamente para apuração.');
    executarEntregaSimulado(true);
}

function iniciarSimuladoReal() {
    if (!simuladoConfig.termoAceito) {
        alert('Por favor, aceite os termos e regras de prova para iniciar o simulado.');
        return;
    }

    const candidatos = obterCardsCandidatosSimulado();
    if (!candidatos || candidatos.length === 0) {
        alert('Nenhuma questão válida encontrada no banco para sortear.');
        return;
    }

    // Calcula N questões
    let qtdQuestoes = simuladoConfig.modoLivre ? (simuladoConfig.questoesLivre || 30) : (simuladoConfig.totalQuestoes || 20);
    if (qtdQuestoes > candidatos.length) {
        qtdQuestoes = candidatos.length;
    }

    // Embaralhamento matemático uniforme Fisher-Yates
    const sorteados = shuffleArrayFisherYates(candidatos).slice(0, qtdQuestoes);
    const questoesIds = sorteados.map(c => c.id.replace(/^card_/, ''));

    const duracaoSegundos = simuladoConfig.modoLivre ? 0 : (simuladoConfig.tempoMinutos * 60);

    window.simuladoAtivo = {
        id: 'sim_' + Date.now(),
        tempoTotalSegundos: duracaoSegundos,
        tempoRestanteSegundos: duracaoSegundos,
        modoLivre: simuladoConfig.modoLivre,
        tempoMinutos: simuladoConfig.tempoMinutos,
        totalQuestoes: qtdQuestoes,
        questoes: questoesIds,
        respostas: {},
        inicioTimestamp: Date.now(),
        status: 'em_andamento',
        marcosNotificados: {}
    };

    salvarSnapshotSimulado();
    document.documentElement.classList.add('simulado-sessao-ativa');
    renderizarTelaSimuladoAtivo(false);

    trackGA4Event('iniciar_simulado', {
        tipo_controle: simuladoConfig.modoLivre ? 'livre' : 'tempo_limite',
        modo_livre: Boolean(simuladoConfig.modoLivre),
        total_questoes: qtdQuestoes,
        tempo_minutos: simuladoConfig.tempoMinutos,
        tempo_estimado_por_questao: simuladoConfig.modoLivre ? 'livre' : 3
    });
}

function renderizarTelaSimuladoAtivo(isRestauracao = false) {
    if (!window.simuladoAtivo || !window.simuladoAtivo.questoes) return;

    // 1. Ocultar todos os cards e seções do modo caderno
    const hero = document.querySelector('.header-hero');
    if (hero) hero.style.display = 'none';

    const kofi = document.querySelector('.kofi-banner');
    if (kofi) kofi.style.display = 'none';

    const filtroSec = document.querySelector('.filtro-section');
    if (filtroSec) filtroSec.style.display = 'none';

    const pagTop = document.getElementById('paginacao-top');
    if (pagTop) pagTop.style.display = 'none';

    const pagBottom = document.getElementById('paginacao-bottom');
    if (pagBottom) pagBottom.style.display = 'none';

    const listaNormal = document.getElementById('lista-questoes-container');
    if (listaNormal) listaNormal.style.display = 'none';

    const painelStats = document.getElementById('painel-estatisticas');
    if (painelStats) painelStats.style.display = 'none';

    const progressTopbar = document.querySelector('.progress-container');
    if (progressTopbar) progressTopbar.style.display = 'none';

    const btnResetTopbar = document.getElementById('btn-reset-respostas');
    if (btnResetTopbar) btnResetTopbar.style.display = 'none';

    const btnExportar = document.getElementById('btn-exportar-backup');
    if (btnExportar) btnExportar.style.display = 'none';

    const btnImportar = document.getElementById('btn-importar-backup');
    if (btnImportar) btnImportar.style.display = 'none';

    // 2. Exibir o container exclusivo do Simulado
    const containerSimulado = document.getElementById('simulado-ativo-container');
    if (containerSimulado) containerSimulado.style.display = 'block';

    // Reset completo dos botões de controle para garantir funcionalidade total
    const btnsEntrega = document.querySelectorAll('.btn-entregar-simulado');
    btnsEntrega.forEach(btn => {
        btn.disabled = false;
        btn.style.opacity = '';
        btn.style.cursor = 'pointer';
        btn.style.display = 'inline-flex';
        const span = btn.querySelector('span');
        if (span) span.textContent = btn.classList.contains('btn-entregar-simulado-bottom') ? 'Entregar Simulado' : 'Entregar Prova';
    });

    const btnVerRes = document.getElementById('btn-ver-resultado-simulado');
    if (btnVerRes) btnVerRes.style.display = 'none';
    const btnVerResBottom = document.getElementById('btn-ver-resultado-bottom');
    if (btnVerResBottom) btnVerResBottom.style.display = 'none';

    const btnNovo = document.getElementById('btn-novo-simulado-header');
    if (btnNovo) btnNovo.style.display = 'none';
    const btnNovoBottom = document.getElementById('btn-novo-simulado-bottom');
    if (btnNovoBottom) btnNovoBottom.style.display = 'none';

    const btnCancelar = document.getElementById('btn-cancelar-simulado');
    if (btnCancelar) {
        btnCancelar.style.display = 'inline-flex';
        btnCancelar.title = 'Abandonar este simulado e retornar ao caderno';
        const span = btnCancelar.querySelector('span');
        if (span) span.textContent = 'Abandonar Prova';
    }

    const badgeTexto = document.getElementById('simulado-status-texto');
    const dot = document.querySelector('.simulado-exam-dot');
    const examBadge = document.querySelector('.simulado-exam-badge');
    if (badgeTexto) badgeTexto.textContent = 'Simulado em Andamento';
    if (dot) dot.style.display = '';
    if (examBadge) {
        examBadge.style.background = '';
        examBadge.style.border = '';
        examBadge.style.borderColor = '';
        examBadge.style.padding = '';
        examBadge.style.color = '';
    }

    const badgeAnticola = document.getElementById('simulado-anticola-badge');
    const textoAnticola = document.getElementById('simulado-anticola-texto');
    if (badgeAnticola) {
        badgeAnticola.classList.remove('violacao');
        badgeAnticola.title = 'Sentinela Anti-Cola: Tolerância Zero para troca de aba ou saída de tela';
    }
    if (textoAnticola) {
        textoAnticola.textContent = 'Anti-Cola Ativo (Tolerância Zero)';
    }

    const countdownBox = document.getElementById('simulado-countdown-box');
    if (countdownBox) countdownBox.classList.remove('urgente');

    const listaSimWrap = document.getElementById('simulado-questoes-lista');
    if (listaSimWrap) {
        listaSimWrap.classList.remove('modo-revisao');
        listaSimWrap.classList.remove('desclassificado');
    }

    // 3. Atualizar metadados do cabeçalho
    const tempoTexto = document.getElementById('simulado-tempo-texto');
    if (tempoTexto) {
        if (window.simuladoAtivo.modoLivre) {
            tempoTexto.textContent = 'Modo Livre (sem timer)';
        } else {
            const horas = window.simuladoAtivo.tempoMinutos >= 60 ? (window.simuladoAtivo.tempoMinutos / 60) : 0;
            const labelTempo = horas >= 1 ? `${horas} hora${horas > 1 ? 's' : ''}` : `${window.simuladoAtivo.tempoMinutos} min`;
            tempoTexto.textContent = `Duração: ${labelTempo}`;
        }
    }

    // 4. Renderizar a lista isolada das N questões sorteadas
    const listaSim = document.getElementById('simulado-questoes-lista');
    if (listaSim) {
        listaSim.innerHTML = '';
        const fragment = document.createDocumentFragment();

        window.simuladoAtivo.questoes.forEach((qId, idx) => {
            const cardOriginal = document.getElementById('card_' + qId);
            if (cardOriginal) {
                const respSalva = window.simuladoAtivo.respostas ? window.simuladoAtivo.respostas[qId] : null;
                const cardClonado = renderizarCardQuestaoSimulado(cardOriginal, idx + 1, window.simuladoAtivo.totalQuestoes, respSalva);
                fragment.appendChild(cardClonado);
            }
        });

        listaSim.appendChild(fragment);
    }

    // 5. Atualizar barra e texto de progresso
    atualizarProgressoSimulado();

    // 6. Iniciar o relógio cronometrado regressivo (Countdown)
    iniciarTimerSimulado();

    // 7. Ativar a Sentinela Anti-Cola & Foco se a prova estiver em andamento
    if (window.simuladoAtivo.status === 'em_andamento') {
        ativarSentinelaFoco();
    } else {
        desativarSentinelaFoco();
    }

    // 8. Scroll suave para o topo do simulado
    if (!isRestauracao) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function renderizarCardQuestaoSimulado(cardOriginal, numeroSimulado, totalSimulado, respostaSalva) {
    const qId = cardOriginal.id.replace(/^card_/, '');
    const esp = cardOriginal.getAttribute('data-especialidade') || '';
    const tema = cardOriginal.getAttribute('data-tema') || '';
    const subtema = cardOriginal.getAttribute('data-subtema') || '';
    const origem = cardOriginal.getAttribute('data-origem') || '';
    const numOriginal = cardOriginal.getAttribute('data-numero') || '';

    // Clone profundo para isolar completamente o DOM do banco original
    const cardSim = cardOriginal.cloneNode(true);
    cardSim.id = `sim_card_${qId}`;
    cardSim.className = 'card-questao card-questao-simulado';
    cardSim.classList.remove('paginacao-oculto');
    cardSim.setAttribute('data-sim-numero', numeroSimulado);
    cardSim.setAttribute('data-sim-qid', qId);

    // Ajusta Header Tags: no Simulado, exibe estritamente o número da questão ordinal (ex: Questão 1 de 20)
    // Oculta qualquer pista sobre banca, prova, especialidade ou tema
    const headerTags = cardSim.querySelector('.card-header-tags');
    if (headerTags) {
        headerTags.innerHTML = `
            <span class="tag-origem tag-simulado-badge">Questão ${numeroSimulado} de ${totalSimulado}</span>
        `;
    }

    // Configura inputs e labels de alternativas
    const radios = cardSim.querySelectorAll('input[type="radio"]');
    radios.forEach(radio => {
        const letra = radio.value;
        radio.name = `sim_radio_${qId}`;
        radio.id = `sim_input_${qId}_${letra}`;
        radio.removeAttribute('onchange');
        radio.disabled = false;

        const label = radio.closest('.alternativa');
        if (label) {
            label.id = `sim_label_${qId}_${letra}`;
            label.classList.remove('correct', 'incorrect', 'selected');
            label.style.pointerEvents = '';
            label.style.opacity = '';
            label.style.cursor = 'pointer';

            if (respostaSalva && respostaSalva === letra) {
                radio.checked = true;
                label.classList.add('selected');
            } else {
                radio.checked = false;
            }
        }
    });

    // Blind Mode: Botão e Box de Gabarito/Comentário IA ficam ocultos durante a prova
    const btnResposta = cardSim.querySelector('.btn-resposta');
    if (btnResposta) {
        btnResposta.id = `sim_btn_resposta_${qId}`;
        btnResposta.setAttribute('onclick', `toggleRespostaSimulado('${qId}')`);
        btnResposta.style.display = 'none';
    }
    const boxGabarito = cardSim.querySelector('.gabarito-box');
    if (boxGabarito) {
        boxGabarito.id = `sim_box_${qId}`;
        boxGabarito.style.display = 'none';
    }

    return cardSim;
}

function selecionarRespostaSimulado(qId, letra) {
    if (!window.simuladoAtivo || window.simuladoAtivo.status !== 'em_andamento') return;

    window.simuladoAtivo.respostas[qId] = letra;
    salvarSnapshotSimulado();

    atualizarEstiloQuestaoSimulado(qId, letra);
    atualizarProgressoSimulado();
}

function atualizarEstiloQuestaoSimulado(qId, letra) {
    const cardSim = document.getElementById(`sim_card_${qId}`);
    if (!cardSim) return;

    const labels = cardSim.querySelectorAll('.alternativa');
    labels.forEach(l => l.classList.remove('selected', 'correct', 'incorrect'));

    if (letra) {
        const labelEscolhida = document.getElementById(`sim_label_${qId}_${letra}`);
        if (labelEscolhida) {
            labelEscolhida.classList.add('selected');
        }
        const radio = document.getElementById(`sim_input_${qId}_${letra}`);
        if (radio) {
            radio.checked = true;
        }
    }
}

function atualizarProgressoSimulado() {
    if (!window.simuladoAtivo) return;

    const total = window.simuladoAtivo.totalQuestoes;
    const respondidas = Object.keys(window.simuladoAtivo.respostas || {}).length;
    const pct = total > 0 ? Math.round((respondidas / total) * 100) : 0;

    const txtProgresso = document.getElementById('simulado-progresso-texto');
    if (txtProgresso) {
        txtProgresso.textContent = `${respondidas} de ${total} respondidas (${pct}%)`;
    }

    const barraFill = document.getElementById('simulado-progress-bar-fill');
    if (barraFill) {
        barraFill.style.width = `${pct}%`;
    }

    const bottomProgresso = document.getElementById('simulado-bottom-progresso');
    if (bottomProgresso) {
        bottomProgresso.textContent = `${respondidas} de ${total} questões preenchidas (${pct}%)`;
    }

    // Telemetria GA4: Marcos de progresso (25%, 50%, 75%, 100%)
    if (!window.simuladoAtivo.marcosNotificados) {
        window.simuladoAtivo.marcosNotificados = {};
    }
    const marcos = [25, 50, 75, 100];
    const decorrido = Math.floor((Date.now() - (window.simuladoAtivo.inicioTimestamp || Date.now())) / 1000);
    marcos.forEach(m => {
        if (pct >= m && !window.simuladoAtivo.marcosNotificados[m]) {
            window.simuladoAtivo.marcosNotificados[m] = true;
            salvarSnapshotSimulado();
            trackGA4Event('simulado_progresso_milestone', {
                milestone_percentual: m,
                respondidas: respondidas,
                total_questoes: total,
                tempo_decorrido_segundos: decorrido,
                tipo_controle: window.simuladoAtivo.modoLivre ? 'livre' : 'tempo_limite'
            });
        }
    });
}

function verificarRestauracaoSimulado() {
    try {
        const raw = sessionStorage.getItem('caderno_simulado_ativo_snapshot') || localStorage.getItem('caderno_simulado_ativo_snapshot');
        if (!raw) return;

        const snapshot = JSON.parse(raw);
        if (snapshot && snapshot.status === 'em_andamento' && Array.isArray(snapshot.questoes) && snapshot.questoes.length > 0) {
            console.log(`[Modo Simulado] Restaurando simulado em andamento (${Object.keys(snapshot.respostas || {}).length}/${snapshot.totalQuestoes} respondidas)...`);
            window.simuladoAtivo = snapshot;
            renderizarTelaSimuladoAtivo(true);
        } else if (snapshot && (snapshot.status === 'finalizado' || snapshot.status === 'desclassificado') && Array.isArray(snapshot.questoes) && snapshot.questoes.length > 0) {
            console.log(`[Modo Simulado] Restaurando simulado ${snapshot.status} para revisão...`);
            window.simuladoAtivo = snapshot;
            renderizarTelaSimuladoAtivo(true);
            if (snapshot.status === 'desclassificado') {
                aplicarEstadoDesclassificadoUI();
                abrirModalDesclassificado();
            } else {
                aplicarEstadoFinalizadoUI();
            }
        }
    } catch (e) {
        console.warn('[Modo Simulado] Falha ao restaurar sessão de simulado ativo:', e);
    }
}

// Modal de Confirmação para Abandono do Simulado
function abrirConfirmAbandonarModal() {
    marcarInteracaoInternaSegura(true);
    const modal = document.getElementById('confirm-abandonar-simulado-modal-overlay');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function fecharConfirmAbandonarModal(e) {
    if (!e || e.target.id === 'confirm-abandonar-simulado-modal-overlay' || e.target.closest('.confirm-modal-close') || e.target.closest('.btn-confirm-cancel')) {
        const modal = document.getElementById('confirm-abandonar-simulado-modal-overlay');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
        setTimeout(() => marcarInteracaoInternaSegura(false), 300);
    }
}

function executarAbandonarSimulado() {
    if (window.simuladoAtivo) {
        const decorrido = Math.floor((Date.now() - (window.simuladoAtivo.inicioTimestamp || Date.now())) / 1000);
        const respondidas = Object.keys(window.simuladoAtivo.respostas || {}).length;
        const total = window.simuladoAtivo.totalQuestoes || 0;
        const pct = total > 0 ? Math.round((respondidas / total) * 100) : 0;

        trackGA4Event('simulado_abandonar', {
            tipo_controle: window.simuladoAtivo.modoLivre ? 'livre' : 'tempo_limite',
            total_questoes: total,
            respondidas: respondidas,
            percentual_concluido: pct,
            tempo_decorrido_segundos: decorrido
        });
    }

    retornarAoCadernoNormal();
}

// ========================================================
// Módulo 3: Preparação de Entrega, Conferência e Finalização
// ========================================================

function abrirModalEntregaSimulado() {
    if (!window.simuladoAtivo || window.simuladoAtivo.status !== 'em_andamento') return;
    marcarInteracaoInternaSegura(true);

    const total = window.simuladoAtivo.totalQuestoes || (window.simuladoAtivo.questoes ? window.simuladoAtivo.questoes.length : 0);
    const respondidasKeys = Object.keys(window.simuladoAtivo.respostas || {}).filter(k => Boolean(window.simuladoAtivo.respostas[k]));
    const respondidas = respondidasKeys.length;
    const emBranco = Math.max(0, total - respondidas);

    const elTotal = document.getElementById('entrega-stat-total');
    const elResp = document.getElementById('entrega-stat-respondidas');
    const elPend = document.getElementById('entrega-stat-pendentes');
    const feedbackBox = document.getElementById('entrega-feedback-box');
    const pendentesContainer = document.getElementById('entrega-pendentes-container');
    const pillsWrap = document.getElementById('entrega-pills-wrap');

    if (elTotal) elTotal.textContent = total;
    if (elResp) elResp.textContent = respondidas;
    if (elPend) elPend.textContent = emBranco;

    if (emBranco === 0) {
        if (feedbackBox) {
            feedbackBox.className = 'entrega-feedback-box feedback-sucesso';
            feedbackBox.innerHTML = `
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1e6b5c" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; margin-top: 2px;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
                    <div>
                        <div class="feedback-alerta-titulo" style="color: #065f46;">Todas as ${total} questões foram respondidas</div>
                        <div class="feedback-alerta-desc">Pronto para entregar sua prova? Ao confirmar a entrega, o cronômetro será finalizado e o gabarito oficial apurado.</div>
                    </div>
                </div>
            `;
        }
        if (pendentesContainer) pendentesContainer.style.display = 'none';
        if (pillsWrap) pillsWrap.innerHTML = '';
    } else {
        if (feedbackBox) {
            feedbackBox.className = 'entrega-feedback-box feedback-alerta';
            feedbackBox.innerHTML = `
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; margin-top: 2px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    <div>
                        <div class="feedback-alerta-titulo">Você tem ${emBranco} ${emBranco === 1 ? 'questão em branco' : 'questões em branco'}</div>
                        <div class="feedback-alerta-desc">Questões não respondidas serão contadas como erro. Você pode respondê-las agora ou confirmar a entrega.</div>
                    </div>
                </div>
            `;
        }

        if (pendentesContainer && pillsWrap) {
            pendentesContainer.style.display = 'block';
            pillsWrap.innerHTML = '';

            window.simuladoAtivo.questoes.forEach((qId, idx) => {
                if (!window.simuladoAtivo.respostas || !window.simuladoAtivo.respostas[qId]) {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'pill-questao-pendente';
                    btn.setAttribute('title', `Ir diretamente para a Questão ${idx + 1}`);
                    btn.innerHTML = `
                        <span class="pill-radio-dot"></span>
                        <span>Questão ${idx + 1}</span>
                    `;
                    btn.onclick = () => irParaQuestaoSimulado(qId);
                    pillsWrap.appendChild(btn);
                }
            });
        }
    }

    const modal = document.getElementById('confirm-entregar-simulado-modal-overlay');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function fecharModalEntregaSimulado(e) {
    if (!e || e.target.id === 'confirm-entregar-simulado-modal-overlay' || e.target.closest('.confirm-modal-close') || e.target.closest('.btn-confirm-cancel')) {
        const modal = document.getElementById('confirm-entregar-simulado-modal-overlay');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
        setTimeout(() => marcarInteracaoInternaSegura(false), 300);
    }
}

function irParaQuestaoSimulado(qId) {
    fecharModalEntregaSimulado();
    trackGA4Event('simulado_navegar_questao_pendente', {
        questao_id: qId
    });
    const cardSim = document.getElementById(`sim_card_${qId}`);
    if (cardSim) {
        cardSim.scrollIntoView({ behavior: 'smooth', block: 'center' });
        cardSim.classList.remove('destaque-navegacao');
        void cardSim.offsetWidth; // Força reflow CSS para reiniciar a animação de pulso
        cardSim.classList.add('destaque-navegacao');
        setTimeout(() => {
            cardSim.classList.remove('destaque-navegacao');
        }, 2200);
    }
}

// Regra de Ouro de Progressão:
// Questões que o estudante respondeu no simulado e que ainda não estavam respondidas
// no caderno normal são migradas automaticamente, preservando as já feitas anteriormente.
function migrarProgressoSimuladoParaModoNormal() {
    if (!window.simuladoAtivo || !window.simuladoAtivo.respostas) return 0;
    const dadosNormais = safeStorageGet(STORAGE_KEY, {});
    let migradas = 0;

    for (const [qId, letra] of Object.entries(window.simuladoAtivo.respostas)) {
        if (!letra) continue;
        if (!dadosNormais[qId]) {
            dadosNormais[qId] = letra;
            migradas++;
        }
    }

    if (migradas > 0) {
        safeStorageSet(STORAGE_KEY, dadosNormais);
        // Atualiza seleção visual nos cards normais correspondentes
        for (const [qId, letra] of Object.entries(window.simuladoAtivo.respostas)) {
            const match = resolverRadioQuestao(qId, letra);
            if (match && match.radio) {
                match.radio.checked = true;
                const label = match.radio.closest('.alternativa');
                if (label) {
                    label.classList.add('selected');
                }
            }
        }
        if (typeof atualizarEstatisticas === 'function') {
            atualizarEstatisticas();
        }
        console.log(`[Modo Simulado] Regra de Ouro: ${migradas} nova(s) questão(ões) incorporada(s) ao progresso do modo normal.`);
    }
    return migradas;
}

function executarEntregaSimulado(porTempo = false) {
    fecharModalEntregaSimulado();

    if (!window.simuladoAtivo) return;

    desativarSentinelaFoco();
    pararTimerSimulado();

    const fimTimestamp = Date.now();
    const tempoGasto = Math.floor((fimTimestamp - (window.simuladoAtivo.inicioTimestamp || fimTimestamp)) / 1000);

    window.simuladoAtivo.status = 'finalizado';
    window.simuladoAtivo.fimTimestamp = fimTimestamp;
    window.simuladoAtivo.tempoGastoSegundos = tempoGasto;
    window.simuladoAtivo.finalizadoPorTempo = Boolean(porTempo);

    // Apuração dos acertos e erros
    const total = window.simuladoAtivo.totalQuestoes;
    let acertos = 0;
    let erros = 0;
    let emBranco = 0;
    const detalhes = {};

    window.simuladoAtivo.questoes.forEach(qId => {
        const respDada = window.simuladoAtivo.respostas ? window.simuladoAtivo.respostas[qId] : null;
        const cardOriginal = document.getElementById('card_' + qId);
        let gabarito = null;

        if (cardOriginal) {
            const radio = cardOriginal.querySelector('input[type="radio"]');
            if (radio) {
                gabarito = radio.getAttribute('data-gabarito');
            }
        }

        if (gabarito === 'ANULADA') {
            acertos++;
            detalhes[qId] = { resposta: respDada, gabarito, resultado: 'anulada', correta: true };
        } else if (!respDada) {
            emBranco++;
            erros++;
            detalhes[qId] = { resposta: null, gabarito, resultado: 'em_branco', correta: false };
        } else if (gabarito && respDada === gabarito) {
            acertos++;
            detalhes[qId] = { resposta: respDada, gabarito, resultado: 'correta', correta: true };
        } else {
            erros++;
            detalhes[qId] = { resposta: respDada, gabarito, resultado: 'incorreta', correta: false };
        }
    });

    const taxa = total > 0 ? Math.round((acertos / total) * 100) : 0;
    window.simuladoAtivo.resultado = {
        total,
        acertos,
        erros,
        emBranco,
        taxa,
        detalhes
    };

    // Telemetria GA4: Conclusão do simulado com métricas completas
    const tempoMedioPorQuestao = (total > 0 && tempoGasto > 0) ? Math.round(tempoGasto / total) : 0;
    let faixaDesempenho = '<50%';
    if (taxa >= 80) faixaDesempenho = '80%+';
    else if (taxa >= 70) faixaDesempenho = '70-79%';
    else if (taxa >= 50) faixaDesempenho = '50-69%';

    trackGA4Event('simulado_concluir', {
        motivo_finalizacao: porTempo ? 'tempo_esgotado' : 'entrega_voluntaria',
        tipo_controle: window.simuladoAtivo.modoLivre ? 'livre' : 'tempo_limite',
        modo_livre: Boolean(window.simuladoAtivo.modoLivre),
        total_questoes: total,
        respondidas: total - emBranco,
        em_branco: emBranco,
        acertos: acertos,
        erros: erros,
        taxa_acerto: taxa,
        faixa_desempenho: faixaDesempenho,
        tempo_gasto_segundos: tempoGasto,
        tempo_medio_por_questao_segundos: tempoMedioPorQuestao
    });

    // Aplica a Regra de Ouro de Progressão
    const novasQuestoes = migrarProgressoSimuladoParaModoNormal();
    window.simuladoAtivo.questoesMigradasParaCaderno = novasQuestoes;

    salvarSnapshotSimulado();

    // Aplica layout e botões do estado finalizado
    aplicarEstadoFinalizadoUI();

    console.log(`[Modo Simulado] Prova finalizada com sucesso! Acertos: ${acertos}/${total} (${taxa}%). Tempo: ${formatarTempoTimer(tempoGasto)}.`);

    // Abre imediatamente o painel oficial de resultados
    abrirModalResultadoSimulado();
}

function aplicarEstadoFinalizadoUI() {
    if (!window.simuladoAtivo) return;

    desativarSentinelaFoco();

    // 1. Atualiza badge
    const badgeTexto = document.getElementById('simulado-status-texto');
    const dot = document.querySelector('.simulado-exam-dot');
    const examBadge = document.querySelector('.simulado-exam-badge');
    if (badgeTexto) badgeTexto.textContent = 'Simulado Finalizado';
    if (dot) dot.style.display = 'none';
    if (examBadge) {
        examBadge.style.background = 'transparent';
        examBadge.style.border = 'none';
        examBadge.style.borderColor = 'transparent';
        examBadge.style.padding = '0';
        examBadge.style.color = 'var(--text-muted)';
    }

    // Atualiza status do badge Anti-Cola no cabeçalho
    const badgeAnticola = document.getElementById('simulado-anticola-badge');
    const textoAnticola = document.getElementById('simulado-anticola-texto');
    if (badgeAnticola) {
        badgeAnticola.classList.remove('violacao');
        badgeAnticola.title = 'Simulado finalizado sem infrações de tela';
    }
    if (textoAnticola) {
        textoAnticola.textContent = 'Anti-Cola: Concluído';
    }

    // 2. Atualiza Timer
    const labelTimer = document.getElementById('simulado-countdown-label');
    const timerDisplay = document.getElementById('simulado-timer-display');
    const countdownBox = document.getElementById('simulado-countdown-box');
    if (labelTimer) labelTimer.textContent = 'TEMPO DE PROVA';
    if (timerDisplay) timerDisplay.textContent = formatarTempoTimer(window.simuladoAtivo.tempoGastoSegundos || 0);
    if (countdownBox) countdownBox.classList.remove('urgente');

    // 3. Atualiza botões
    const btnEntregar = document.getElementById('btn-entregar-simulado');
    if (btnEntregar) btnEntregar.style.display = 'none';
    const btnEntregarBottom = document.getElementById('btn-entregar-bottom');
    if (btnEntregarBottom) btnEntregarBottom.style.display = 'none';

    const btnVerRes = document.getElementById('btn-ver-resultado-simulado');
    if (btnVerRes) btnVerRes.style.display = 'inline-flex';
    const btnVerResBottom = document.getElementById('btn-ver-resultado-bottom');
    if (btnVerResBottom) btnVerResBottom.style.display = 'inline-flex';

    const btnNovo = document.getElementById('btn-novo-simulado-header');
    if (btnNovo) btnNovo.style.display = 'inline-flex';
    const btnNovoBottom = document.getElementById('btn-novo-simulado-bottom');
    if (btnNovoBottom) btnNovoBottom.style.display = 'inline-flex';

    const btnCancelar = document.getElementById('btn-cancelar-simulado');
    if (btnCancelar) {
        btnCancelar.style.display = 'inline-flex';
        btnCancelar.title = 'Sair do simulado e retornar ao modo de estudos';
        const span = btnCancelar.querySelector('span');
        if (span) span.textContent = 'Voltar ao Caderno';
    }
}

function abrirModalResultadoSimulado() {
    if (!window.simuladoAtivo) return;
    if (window.simuladoAtivo.status === 'desclassificado') {
        abrirModalDesclassificado();
        return;
    }
    if (!window.simuladoAtivo.resultado) return;

    const res = window.simuladoAtivo.resultado;
    const total = res.total;
    const acertos = res.acertos;
    const erros = res.erros;
    const emBranco = res.emBranco;
    const taxa = res.taxa;
    const tempoGasto = window.simuladoAtivo.tempoGastoSegundos || 0;
    const novasQuestoes = window.simuladoAtivo.questoesMigradasParaCaderno || 0;

    const elTaxa = document.getElementById('resultado-taxa-display');
    const elSub = document.getElementById('resultado-score-sub');
    const elTempo = document.getElementById('resultado-tempo-gasto');
    const elAcertos = document.getElementById('resultado-total-acertos');
    const elErros = document.getElementById('resultado-total-erros');
    const elBranco = document.getElementById('resultado-total-branco');
    const elTitulo = document.getElementById('modal-resultado-titulo');
    const elSubTitulo = document.getElementById('resultado-modal-sub');
    const boxRegra = document.getElementById('resultado-regra-ouro-box');
    const txtRegra = document.getElementById('resultado-regra-ouro-texto');

    const barFill = document.getElementById('resultado-progress-bar');
    const helperBranco = document.getElementById('resultado-branco-helper-text');

    if (elTaxa) elTaxa.textContent = taxa + '%';
    if (elSub) elSub.textContent = `${acertos} de ${total} questões acertadas`;
    if (elTempo) elTempo.textContent = formatarTempoTimer(tempoGasto);
    if (elAcertos) elAcertos.textContent = acertos;
    if (elErros) elErros.textContent = erros;
    if (elBranco) elBranco.textContent = emBranco;
    if (barFill) barFill.style.width = Math.min(100, Math.max(0, taxa)) + '%';

    if (helperBranco) {
        if (emBranco > 0) {
            helperBranco.textContent = `As ${emBranco} ${emBranco === 1 ? 'questão em branco está incluída' : 'questões em branco estão incluídas'} nos ${erros} erros.`;
            helperBranco.style.display = 'block';
        } else {
            helperBranco.textContent = `Todas as ${total} questões foram contabilizadas no seu resultado.`;
            helperBranco.style.display = 'block';
        }
    }

    if (elTitulo && elSubTitulo) {
        elTitulo.textContent = 'Simulado concluído';
        elSubTitulo.textContent = 'Cada tentativa é uma oportunidade de aprender. Revise os comentários com IA para fixar os conteúdos.';
    }

    if (boxRegra && txtRegra) {
        if (novasQuestoes > 0) {
            boxRegra.style.display = 'flex';
            txtRegra.innerHTML = `<strong>Progresso:</strong> ${novasQuestoes} nova(s) questão(ões) foram automaticamente adicionadas ao seu progresso no modo normal!`;
        } else {
            boxRegra.style.display = 'none';
        }
    }

    const modal = document.getElementById('simulado-resultado-modal-overlay');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function fecharModalResultadoSimulado(e) {
    if (!e || e.target.id === 'simulado-resultado-modal-overlay' || e.target.closest('.confirm-modal-close') || e.target.closest('.btn-resultado-caderno')) {
        const modal = document.getElementById('simulado-resultado-modal-overlay');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
}

function liberarModoRevisaoSimulado() {
    fecharModalResultadoSimulado();
    fecharModalDesclassificado();

    if (!window.simuladoAtivo) return;

    const res = window.simuladoAtivo.resultado || {};
    trackGA4Event('simulado_iniciar_revisao', {
        status_simulado: window.simuladoAtivo.status || 'finalizado',
        taxa_acerto: res.taxa || 0,
        total_questoes: window.simuladoAtivo.totalQuestoes || 0,
        tipo_controle: window.simuladoAtivo.modoLivre ? 'livre' : 'tempo_limite'
    });

    const listaSim = document.getElementById('simulado-questoes-lista');
    if (listaSim) {
        listaSim.classList.add('modo-revisao');
        listaSim.classList.remove('desclassificado');
        const radios = listaSim.querySelectorAll('input[type="radio"]');
        radios.forEach(r => r.disabled = false);
    }

    window.simuladoAtivo.questoes.forEach((qId, idx) => {
        const cardSim = document.getElementById(`sim_card_${qId}`);
        if (!cardSim) return;

        cardSim.classList.add('modo-revisao');

        // Descobre gabarito oficial do card original
        const cardOriginal = document.getElementById('card_' + qId);
        let gabarito = null;
        if (cardOriginal) {
            const radio = cardOriginal.querySelector('input[type="radio"]');
            if (radio) gabarito = radio.getAttribute('data-gabarito');
        }

        const respDada = window.simuladoAtivo.respostas ? window.simuladoAtivo.respostas[qId] : null;

        // Revela botão de comentário / gabarito
        const btnResposta = cardSim.querySelector('.btn-resposta');
        if (btnResposta) {
            btnResposta.style.display = 'inline-flex';
        }

        // Destaca alternativas apenas se o aluno tiver respondido à questão
        // Questões em branco permanecem neutras (sem highlight verde de gabarito)
        const labels = cardSim.querySelectorAll('.alternativa');
        labels.forEach(lbl => lbl.classList.remove('correct', 'incorrect'));

        if (respDada) {
            if (gabarito) {
                const labelGabarito = cardSim.querySelector(`#sim_label_${qId}_${gabarito}`);
                if (labelGabarito) {
                    labelGabarito.classList.add('correct');
                }
            }

            if (respDada !== gabarito) {
                const labelErrada = cardSim.querySelector(`#sim_label_${qId}_${respDada}`);
                if (labelErrada) {
                    labelErrada.classList.add('incorrect');
                }
            }
        }

        // Adiciona badge de acerto/erro no header do card se ainda não tiver
        const headerTags = cardSim.querySelector('.card-header-tags');
        if (headerTags && !headerTags.querySelector('.tag-revisao-status')) {
            const tagStatus = document.createElement('span');
            tagStatus.className = 'tag-revisao-status';
            tagStatus.style.fontSize = '12px';
            tagStatus.style.fontWeight = '700';
            tagStatus.style.padding = '4px 10px';
            tagStatus.style.borderRadius = '20px';
            tagStatus.style.marginLeft = '8px';

            if (gabarito === 'ANULADA') {
                tagStatus.textContent = 'Questão Anulada';
                tagStatus.style.background = '#f59e0b';
                tagStatus.style.color = '#ffffff';
            } else if (!respDada) {
                tagStatus.textContent = 'Em Branco';
                tagStatus.style.background = '#f59e0b';
                tagStatus.style.color = '#ffffff';
            } else if (respDada === gabarito) {
                tagStatus.textContent = 'Acertou';
                tagStatus.style.background = '#10b981';
                tagStatus.style.color = '#ffffff';
            } else {
                tagStatus.textContent = 'Errou';
                tagStatus.style.background = '#ef4444';
                tagStatus.style.color = '#ffffff';
            }
            headerTags.appendChild(tagStatus);
        }
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function toggleRespostaSimulado(qId) {
    const box = document.getElementById(`sim_box_${qId}`);
    if (box) {
        const isHidden = (box.style.display === 'none' || box.style.display === '');
        box.style.display = isHidden ? 'block' : 'none';

        if (isHidden) {
            let statusResp = 'sem_resposta';
            if (window.simuladoAtivo && window.simuladoAtivo.resultado && window.simuladoAtivo.resultado.detalhes) {
                const det = window.simuladoAtivo.resultado.detalhes[qId];
                if (det) statusResp = det.resultado;
            }
            trackGA4Event('simulado_ver_explicacao_ia', {
                questao_id: qId,
                status_resposta: statusResp
            });
        }
    }
}

// ========================================================
// Módulo 4: Monitor Anti-Cola & Sentinela de Foco (Tolerância Zero)
// ========================================================

let sentinelaFocoAtiva = false;
let sentinelaPollingInterval = null;
window._interacaoInternaSegura = false;
window._recarregandoPagina = false;

function marcarInteracaoInternaSegura(ativa = true) {
    window._interacaoInternaSegura = Boolean(ativa);
}

function dispararVerificacaoPerdaFoco(origem) {
    if (!window.simuladoAtivo || window.simuladoAtivo.status !== 'em_andamento') return;
    if (window._interacaoInternaSegura || window._recarregandoPagina) {
        console.log(`[Sentinela Anti-Cola] Evento '${origem}' ignorado por ser interação interna segura ou reload de página.`);
        return;
    }

    if (window.simuladoAtivo) {
        window.simuladoAtivo.origemPerdaFoco = origem;
    }
    console.warn(`[Sentinela Anti-Cola] Perda de foco confirmada via '${origem}'. Desclassificando prova imediatamente...`);
    executarDesclassificacaoSimulado();
}

function handleSentinelaVisibilityChange() {
    if (document.visibilityState === 'hidden') {
        dispararVerificacaoPerdaFoco('visibilitychange');
    }
}

function handleSentinelaWindowBlur() {
    dispararVerificacaoPerdaFoco('blur');
}

function ativarSentinelaFoco() {
    if (sentinelaFocoAtiva) return;
    sentinelaFocoAtiva = true;

    // Proteção de 1500ms para acomodar o clique de início de prova ou reload sem disparar micro-blur
    window._interacaoInternaSegura = true;
    setTimeout(() => {
        window._interacaoInternaSegura = false;
    }, 1500);

    document.addEventListener('visibilitychange', handleSentinelaVisibilityChange);
    window.addEventListener('blur', handleSentinelaWindowBlur);

    // Camada de Batimento Cardíaco (Heartbeat Polling a cada 200ms)
    // Garante detecção mesmo se o sistema operacional ou navegador não disparar blur síncrono
    if (sentinelaPollingInterval) clearInterval(sentinelaPollingInterval);
    sentinelaPollingInterval = setInterval(() => {
        if (!window.simuladoAtivo || window.simuladoAtivo.status !== 'em_andamento') return;
        if (window._interacaoInternaSegura || window._recarregandoPagina) return;

        // Se a janela perdeu o foco (clicou em outro monitor/aplicativo/desktop) ou foi minimizada/trocou de aba
        if (!document.hasFocus() || document.visibilityState === 'hidden') {
            dispararVerificacaoPerdaFoco('heartbeat');
        }
    }, 200);

    console.log('[Sentinela Anti-Cola] Monitoramento de foco ativado com Tolerância Zero (Eventos + Heartbeat Polling 200ms).');
}

function desativarSentinelaFoco() {
    if (!sentinelaFocoAtiva) return;
    sentinelaFocoAtiva = false;
    if (sentinelaPollingInterval) {
        clearInterval(sentinelaPollingInterval);
        sentinelaPollingInterval = null;
    }
    document.removeEventListener('visibilitychange', handleSentinelaVisibilityChange);
    window.removeEventListener('blur', handleSentinelaWindowBlur);
    console.log('[Sentinela Anti-Cola] Monitoramento de foco desativado.');
}

function executarDesclassificacaoSimulado() {
    if (!window.simuladoAtivo || window.simuladoAtivo.status !== 'em_andamento') return;

    pararTimerSimulado();
    desativarSentinelaFoco();

    fecharModalEntregaSimulado();
    fecharConfirmAbandonarModal();
    fecharZoomImagem();

    const fimTimestamp = Date.now();
    const tempoGasto = Math.floor((fimTimestamp - (window.simuladoAtivo.inicioTimestamp || fimTimestamp)) / 1000);

    window.simuladoAtivo.status = 'desclassificado';
    window.simuladoAtivo.motivoDesclassificacao = 'perda_de_foco';
    window.simuladoAtivo.fimTimestamp = fimTimestamp;
    window.simuladoAtivo.tempoGastoSegundos = tempoGasto;

    // Apuração dos acertos e erros parciais até o momento do bloqueio
    const total = window.simuladoAtivo.totalQuestoes;
    let acertos = 0;
    let erros = 0;
    let emBranco = 0;
    const detalhes = {};

    window.simuladoAtivo.questoes.forEach(qId => {
        const respDada = window.simuladoAtivo.respostas ? window.simuladoAtivo.respostas[qId] : null;
        const cardOriginal = document.getElementById('card_' + qId);
        let gabarito = null;

        if (cardOriginal) {
            const radio = cardOriginal.querySelector('input[type="radio"]');
            if (radio) {
                gabarito = radio.getAttribute('data-gabarito');
            }
        }

        if (gabarito === 'ANULADA') {
            acertos++;
            detalhes[qId] = { resposta: respDada, gabarito, resultado: 'anulada', correta: true };
        } else if (!respDada) {
            emBranco++;
            erros++;
            detalhes[qId] = { resposta: null, gabarito, resultado: 'em_branco', correta: false };
        } else if (gabarito && respDada === gabarito) {
            acertos++;
            detalhes[qId] = { resposta: respDada, gabarito, resultado: 'correta', correta: true };
        } else {
            erros++;
            detalhes[qId] = { resposta: respDada, gabarito, resultado: 'incorreta', correta: false };
        }
    });

    const taxa = total > 0 ? Math.round((acertos / total) * 100) : 0;
    window.simuladoAtivo.resultado = {
        total,
        acertos,
        erros,
        emBranco,
        taxa,
        detalhes
    };

    // Na desclassificação por quebra de regulamento, nenhuma questão é migrada
    window.simuladoAtivo.questoesMigradasParaCaderno = 0;

    salvarSnapshotSimulado();
    aplicarEstadoDesclassificadoUI();

    const respondidasCount = Object.keys(window.simuladoAtivo.respostas || {}).length;
    const pctConcluido = total > 0 ? Math.round((respondidasCount / total) * 100) : 0;

    trackGA4Event('simulado_desclassificado', {
        motivo: 'perda_de_foco',
        origem_deteccao: window.simuladoAtivo.origemPerdaFoco || 'sentinela',
        tipo_controle: window.simuladoAtivo.modoLivre ? 'livre' : 'tempo_limite',
        total_questoes: total,
        respondidas: respondidasCount,
        acertos_parciais: acertos,
        erros_parciais: erros,
        tempo_ate_bloqueio_segundos: tempoGasto,
        percentual_respondido: pctConcluido
    });

    console.warn(`[Sentinela Anti-Cola] Prova DESCLASSIFICADA por perda de foco. Acertos parciais: ${acertos}/${total}.`);
    abrirModalDesclassificado();
}

function aplicarEstadoDesclassificadoUI() {
    if (!window.simuladoAtivo) return;

    desativarSentinelaFoco();

    // 1. Atualiza badge de status principal
    const badgeTexto = document.getElementById('simulado-status-texto');
    const dot = document.querySelector('.simulado-exam-dot');
    const examBadge = document.querySelector('.simulado-exam-badge');
    if (badgeTexto) badgeTexto.textContent = 'Prova Desclassificada';
    if (dot) dot.style.display = 'none';
    if (examBadge) {
        examBadge.style.background = 'transparent';
        examBadge.style.border = 'none';
        examBadge.style.borderColor = 'transparent';
        examBadge.style.padding = '0';
        examBadge.style.color = '#ef4444';
    }

    // 2. Atualiza badge Anti-Cola no cabeçalho
    const badgeAnticola = document.getElementById('simulado-anticola-badge');
    const textoAnticola = document.getElementById('simulado-anticola-texto');
    if (badgeAnticola) {
        badgeAnticola.classList.add('violacao');
        badgeAnticola.title = 'Prova anulada: Saída de tela ou troca de aba detectada';
    }
    if (textoAnticola) {
        textoAnticola.textContent = 'Violação de Foco (Anulada)';
    }

    // 3. Atualiza Timer
    const labelTimer = document.getElementById('simulado-countdown-label');
    const timerDisplay = document.getElementById('simulado-timer-display');
    const countdownBox = document.getElementById('simulado-countdown-box');
    if (labelTimer) labelTimer.textContent = 'TEMPO DE PROVA';
    if (timerDisplay) timerDisplay.textContent = formatarTempoTimer(window.simuladoAtivo.tempoGastoSegundos || 0);
    if (countdownBox) countdownBox.classList.remove('urgente');

    // 4. Bloqueia alternativas e atualiza botões
    const listaSim = document.getElementById('simulado-questoes-lista');
    if (listaSim) {
        listaSim.classList.add('desclassificado');
        const radios = listaSim.querySelectorAll('input[type="radio"]');
        radios.forEach(r => r.disabled = true);
    }

    const btnEntregar = document.getElementById('btn-entregar-simulado');
    if (btnEntregar) btnEntregar.style.display = 'none';
    const btnEntregarBottom = document.getElementById('btn-entregar-bottom');
    if (btnEntregarBottom) btnEntregarBottom.style.display = 'none';

    const btnVerRes = document.getElementById('btn-ver-resultado-simulado');
    if (btnVerRes) btnVerRes.style.display = 'inline-flex';
    const btnVerResBottom = document.getElementById('btn-ver-resultado-bottom');
    if (btnVerResBottom) btnVerResBottom.style.display = 'inline-flex';

    const btnNovo = document.getElementById('btn-novo-simulado-header');
    if (btnNovo) btnNovo.style.display = 'inline-flex';
    const btnNovoBottom = document.getElementById('btn-novo-simulado-bottom');
    if (btnNovoBottom) btnNovoBottom.style.display = 'inline-flex';

    const btnCancelar = document.getElementById('btn-cancelar-simulado');
    if (btnCancelar) {
        btnCancelar.style.display = 'inline-flex';
        btnCancelar.title = 'Sair do simulado e retornar ao modo de estudos';
        const span = btnCancelar.querySelector('span');
        if (span) span.textContent = 'Voltar ao Caderno';
    }
}

function abrirModalDesclassificado() {
    if (!window.simuladoAtivo) return;

    const res = window.simuladoAtivo.resultado || {};
    const total = window.simuladoAtivo.totalQuestoes || 0;
    const acertos = res.acertos || 0;
    const erros = res.erros || 0;
    const respondidas = Object.keys(window.simuladoAtivo.respostas || {}).length;
    const tempoGasto = window.simuladoAtivo.tempoGastoSegundos || 0;

    const elTempo = document.getElementById('desclassificado-tempo-gasto');
    const elResp = document.getElementById('desclassificado-total-respondidas');
    const elAcertos = document.getElementById('desclassificado-total-acertos');
    const elErros = document.getElementById('desclassificado-total-erros');

    if (elTempo) elTempo.textContent = formatarTempoTimer(tempoGasto);
    if (elResp) elResp.textContent = `${respondidas} de ${total}`;
    if (elAcertos) elAcertos.textContent = acertos;
    if (elErros) elErros.textContent = erros;

    const modal = document.getElementById('simulado-desclassificado-modal-overlay');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function fecharModalDesclassificado() {
    const modal = document.getElementById('simulado-desclassificado-modal-overlay');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function liberarModoRevisaoDesclassificado() {
    fecharModalDesclassificado();
    liberarModoRevisaoSimulado();
}

function iniciarNovoSimuladoSetup() {
    trackGA4Event('simulado_novo_clique', {
        origem: (window.simuladoAtivo && window.simuladoAtivo.status) || 'setup'
    });

    fecharModalDesclassificado();
    fecharModalResultadoSimulado();
    fecharModalEntregaSimulado();
    fecharConfirmAbandonarModal();
    desativarSentinelaFoco();
    pararTimerSimulado();

    // Limpa a sessão
    sessionStorage.removeItem('caderno_simulado_ativo_snapshot');
    localStorage.removeItem('caderno_simulado_ativo_snapshot');
    window.simuladoAtivo = null;
    document.documentElement.classList.remove('simulado-sessao-ativa');

    // Ocultar container de simulado ativo
    const containerSimulado = document.getElementById('simulado-ativo-container');
    if (containerSimulado) containerSimulado.style.display = 'none';

    const listaSim = document.getElementById('simulado-questoes-lista');
    if (listaSim) {
        listaSim.innerHTML = '';
        listaSim.classList.remove('modo-revisao');
        listaSim.classList.remove('desclassificado');
    }

    // Restaurar visão
    const hero = document.querySelector('.header-hero');
    if (hero) hero.style.display = '';

    const kofi = document.querySelector('.kofi-banner');
    if (kofi) kofi.style.display = '';

    const filtroSec = document.querySelector('.filtro-section');
    if (filtroSec) filtroSec.style.display = '';

    // Entra na aba do simulado (Wizard)
    alternarModoFiltro('simulado');

    // Reseta checkbox e termo
    const check = document.getElementById('check-termo-simulado');
    if (check) check.checked = false;
    simuladoConfig.termoAceito = false;
    atualizarEstadoBotaoIniciarSimulado();

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function retornarAoCadernoNormal() {
    trackGA4Event('simulado_voltar_caderno', {
        status_simulado: (window.simuladoAtivo && window.simuladoAtivo.status) || 'encerrado'
    });

    fecharModalDesclassificado();
    fecharModalResultadoSimulado();
    fecharModalEntregaSimulado();
    fecharConfirmAbandonarModal();
    desativarSentinelaFoco();
    pararTimerSimulado();

    sessionStorage.removeItem('caderno_simulado_ativo_snapshot');
    localStorage.removeItem('caderno_simulado_ativo_snapshot');
    window.simuladoAtivo = null;
    document.documentElement.classList.remove('simulado-sessao-ativa');

    // Ocultar container de simulado ativo
    const containerSimulado = document.getElementById('simulado-ativo-container');
    if (containerSimulado) containerSimulado.style.display = 'none';

    const listaSim = document.getElementById('simulado-questoes-lista');
    if (listaSim) {
        listaSim.innerHTML = '';
        listaSim.classList.remove('modo-revisao');
        listaSim.classList.remove('desclassificado');
    }

    // Restaurar visão normal do caderno
    const hero = document.querySelector('.header-hero');
    if (hero) hero.style.display = '';

    const kofi = document.querySelector('.kofi-banner');
    if (kofi) kofi.style.display = '';

    const filtroSec = document.querySelector('.filtro-section');
    if (filtroSec) filtroSec.style.display = '';

    const listaNormal = document.getElementById('lista-questoes-container');
    if (listaNormal) listaNormal.style.display = '';

    const painelStats = document.getElementById('painel-estatisticas');
    if (painelStats) painelStats.style.display = '';

    const progressTopbar = document.querySelector('.progress-container');
    if (progressTopbar) progressTopbar.style.display = '';

    const btnResetTopbar = document.getElementById('btn-reset-respostas');
    if (btnResetTopbar) btnResetTopbar.style.display = '';

    const btnExportar = document.getElementById('btn-exportar-backup');
    if (btnExportar) btnExportar.style.display = '';

    const btnImportar = document.getElementById('btn-importar-backup');
    if (btnImportar) btnImportar.style.display = '';

    // Retorna ao modo clínico (estudos normais)
    alternarModoFiltro('clinico');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function tratarCliqueBotaoSair() {
    if (window.simuladoAtivo && window.simuladoAtivo.status === 'em_andamento') {
        abrirConfirmAbandonarModal();
    } else {
        retornarAoCadernoNormal();
    }
}

// Proteção Anti-Perda de Sessão: Blindagem para Recarregamento Seguro (F5 / Reload / Navegação)
function prepararReloadSeguro() {
    if (window.simuladoAtivo && window.simuladoAtivo.status === 'em_andamento') {
        window._recarregandoPagina = true;
        desativarSentinelaFoco();
        salvarSnapshotSimulado();
    }
}

window.addEventListener('keydown', function(e) {
    if (e.key === 'F5' || (e.key === 'r' && (e.ctrlKey || e.metaKey))) {
        prepararReloadSeguro();
    }
});

window.addEventListener('beforeunload', function(e) {
    prepararReloadSeguro();
});

window.addEventListener('pagehide', function(e) {
    prepararReloadSeguro();
});

// Delegação global de eventos para interações de alternativas no Modo Simulado
document.addEventListener('change', function(e) {
    if (e.target && e.target.name && e.target.name.startsWith('sim_radio_')) {
        const qId = e.target.name.replace(/^sim_radio_/, '');
        const letra = e.target.value;
        selecionarRespostaSimulado(qId, letra);
    }
});

document.addEventListener('click', function(e) {
    const label = e.target.closest('.card-questao-simulado .alternativa');
    if (!label) return;
    const radio = label.querySelector('input[type="radio"]');
    if (radio && e.target !== radio) {
        radio.checked = true;
        const qId = radio.name.replace(/^sim_radio_/, '');
        const letra = radio.value;
        selecionarRespostaSimulado(qId, letra);
    }
});

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
        const ORDEM_GRANDES_AREAS = [
            'Clínica Médica',
            'Cirurgia Geral',
            'Ginecologia e Obstetrícia',
            'Pediatria',
            'Medicina Preventiva e Social / MFC'
        ];
        const esps = Object.keys(taxonomiaEspecialidades).sort((a, b) => {
            const idxA = ORDEM_GRANDES_AREAS.indexOf(a);
            const idxB = ORDEM_GRANDES_AREAS.indexOf(b);
            if (idxA !== -1 && idxB !== -1) return idxA - idxB;
            if (idxA !== -1) return -1;
            if (idxB !== -1) return 1;
            return a.localeCompare(b);
        });

        esps.forEach(esp => {
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

    // 3. Inicializa listeners do Combobox de Subtemas
    inicializarEventosComboboxSubtemas();

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

    aplicarFiltroEPaginacao(false);
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

    aplicarFiltroEPaginacao(false);
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

const TEMAS_NUCLEARES_POR_AREA = {
    'Clínica Médica': [
        'Cardiologia',
        'Pneumologia',
        'Gastroenterologia & Hepatologia',
        'Nefrologia',
        'Endocrinologia & Metabologia',
        'Reumatologia',
        'Infectologia',
        'Hematologia',
        'Neurologia',
        'Dermatologia',
        'Psiquiatria',
        'Emergência e Cuidados Críticos',
        'Angiologia & Vascular'
    ],
    'Cirurgia Geral': [
        'Cirurgia do Aparelho Digestivo',
        'Trauma e Emergência Cirúrgica',
        'Cuidados Perioperatórios & Anestesiologia',
        'Coloproctologia',
        'Urologia',
        'Ortopedia e Traumatologia',
        'Cirurgia Vascular',
        'Cirurgia Pediátrica',
        'Cirurgia de Cabeça e Pescoço & Endócrina',
        'Cirurgia Plástica & Queimaduras',
        'Dermatologia Cirúrgica & Oncologia Cutânea'
    ],
    'Ginecologia e Obstetrícia': [
        'Obstetrícia',
        'Ginecologia Geral',
        'Endocrinologia Ginecológica & Climatério',
        'Infecções Ginecológicas & ISTs',
        'Mastologia',
        'Planejamento Familiar & Contracepção',
        'Oncologia Ginecológica'
    ],
    'Pediatria': [
        'Infectologia Pediátrica',
        'Neonatologia',
        'Endocrinologia Pediátrica',
        'Puericultura & Aleitamento Materno',
        'Neurologia & Desenvolvimento Infantil',
        'Pneumologia Pediátrica',
        'Hematologia & Oncologia Pediátrica',
        'Gastroenterologia Pediátrica',
        'Nefrologia Pediátrica',
        'Reumatologia Pediátrica',
        'Emergências Pediátricas & Suporte de Vida'
    ],
    'Medicina Preventiva e Social / MFC': [
        'Medicina de Família e Comunidade (MFC)',
        'Vigilância em Saúde',
        'Epidemiologia & Bioestatística',
        'Ética Médica, Bioética & Medicina Legal',
        'Sistema Único de Saúde (SUS) & Políticas Públicas',
        'Saúde Coletiva & Populações Vulneráveis',
        'Saúde do Trabalhador'
    ]
};

let comboboxSubtemasInicializado = false;

function inicializarEventosComboboxSubtemas() {
    if (comboboxSubtemasInicializado) return;
    comboboxSubtemasInicializado = true;

    const inputCombobox = document.getElementById('input-subtema-combobox');
    const dropdownCombobox = document.getElementById('subtema-combobox-dropdown');
    const btnLimpar = document.getElementById('btn-limpar-subtema');
    const btnToggle = document.getElementById('btn-toggle-subtema');

    if (!inputCombobox || !dropdownCombobox) return;

    // Abre dropdown ao focar no input de busca
    inputCombobox.addEventListener('focus', () => {
        dropdownCombobox.style.display = 'block';
    });

    // Filtro dinâmico com autocomplete instantâneo
    inputCombobox.addEventListener('input', () => {
        const query = (inputCombobox.value || '').trim().toLowerCase();
        dropdownCombobox.style.display = 'block';

        const options = dropdownCombobox.querySelectorAll('.subtema-combobox-option');
        let visiveis = 0;
        options.forEach(opt => {
            const sub = opt.getAttribute('data-subtema');
            const nome = opt.querySelector('.subtema-option-name')?.textContent || sub;
            if (sub === 'TODOS') {
                const show = (!query || query === 'todos');
                opt.style.display = show ? 'flex' : 'none';
                if (show) visiveis++;
            } else if (!query || nome.toLowerCase().includes(query)) {
                opt.style.display = 'flex';
                visiveis++;
            } else {
                opt.style.display = 'none';
            }
        });

        // Feedback visual se nenhum subtema for encontrado
        let emptyEl = dropdownCombobox.querySelector('.subtema-combobox-empty');
        if (visiveis === 0) {
            if (!emptyEl) {
                emptyEl = document.createElement('div');
                emptyEl.className = 'subtema-combobox-empty';
                emptyEl.textContent = 'Nenhum subtema encontrado';
                dropdownCombobox.appendChild(emptyEl);
            }
            emptyEl.style.display = 'block';
        } else if (emptyEl) {
            emptyEl.style.display = 'none';
        }
    });

    // Teclas: Enter seleciona o primeiro item visível; Escape fecha
    inputCombobox.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const visiveis = Array.from(dropdownCombobox.querySelectorAll('.subtema-combobox-option'))
                .filter(el => el.style.display !== 'none');
            if (visiveis.length > 0) {
                visiveis[0].click();
                inputCombobox.blur();
            }
        } else if (e.key === 'Escape') {
            dropdownCombobox.style.display = 'none';
            inputCombobox.blur();
        }
    });

    // Botão de alternância (caret) do Combobox
    if (btnToggle) {
        btnToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            const aberto = dropdownCombobox.style.display === 'block';
            dropdownCombobox.style.display = aberto ? 'none' : 'block';
            if (!aberto) {
                inputCombobox.focus();
            }
        });
    }

    // Botão de limpar seleção de subtema
    if (btnLimpar) {
        btnLimpar.addEventListener('click', (e) => {
            e.stopPropagation();
            filtrarPorSubtema('TODOS');
            inputCombobox.focus();
        });
    }

    // Fecha dropdown de subtemas e menu suspenso de especialidades ao clicar fora
    document.addEventListener('click', (e) => {
        const subtemaWrapper = document.getElementById('filtro-subtemas-wrapper');
        if (subtemaWrapper && !subtemaWrapper.contains(e.target)) {
            dropdownCombobox.style.display = 'none';
        }

        const wrapOutras = document.getElementById('wrap-outras-especialidades');
        const menuOutras = document.getElementById('menu-outras-especialidades');
        if (wrapOutras && menuOutras && !wrapOutras.contains(e.target)) {
            menuOutras.style.display = 'none';
        }
    });
}

function filtrarPorEspecialidade(esp) {
    especialidadeAtiva = esp;
    temaAtivo = 'TODOS';
    subtemaAtivo = 'TODOS';
    paginaAtual = 1;

    // Atualiza estado ativo das abas de especialidade (Nível 1)
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

    // Atualiza container de temas (Nível 2)
    const temasWrapper = document.getElementById('filtro-temas-wrapper');
    const pillsContainer = document.getElementById('filtro-temas-pills');

    if (esp === 'TODAS' || !taxonomiaEspecialidades[esp]) {
        if (temasWrapper) temasWrapper.style.display = 'none';
    } else {
        if (temasWrapper) temasWrapper.style.display = 'block';

        const temasObj = taxonomiaEspecialidades[esp].temas || {};
        const listaTemas = Object.keys(temasObj);

        if (pillsContainer) {
            pillsContainer.innerHTML = '';

            // Pill "Todos os Temas"
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

            const nuclearesDef = TEMAS_NUCLEARES_POR_AREA[esp] || [];

            if (nuclearesDef.length > 0) {
                // Separa Especialidades Nucleares (botões diretos) vs Secundárias (menu suspenso)
                const nucleares = [];
                const secundarias = [];

                listaTemas.forEach(t => {
                    if (nuclearesDef.includes(t)) {
                        nucleares.push(t);
                    } else {
                        secundarias.push(t);
                    }
                });

                // Ordena nucleares pela ordem de relevância clínica predefinida
                nucleares.sort((a, b) => {
                    const idxA = nuclearesDef.indexOf(a);
                    const idxB = nuclearesDef.indexOf(b);
                    return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
                });

                // Renderiza botões diretos das nucleares
                nucleares.forEach(t => {
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

                // Agrupa secundárias / baixo volume em dropdown
                if (secundarias.length > 0) {
                    const totalSecundarias = secundarias.reduce((acc, t) => acc + (temasObj[t]?.total || 0), 0);
                    const wrapDropdown = document.createElement('div');
                    wrapDropdown.className = 'filtro-dropdown-wrap';
                    wrapDropdown.id = 'wrap-outras-especialidades';

                    const rotuloDropdown = (esp === 'Clínica Médica' || esp === 'Cirurgia Geral' || esp === 'Pediatria') 
                        ? 'Outras Especialidades' 
                        : 'Outros Temas';

                    const btnDropdown = document.createElement('button');
                    btnDropdown.type = 'button';
                    btnDropdown.className = 'subfiltro-pill filtro-dropdown-btn';
                    btnDropdown.id = 'btn-outras-especialidades';
                    btnDropdown.innerHTML = `<span id="label-outras-especialidades">${rotuloDropdown} (${totalSecundarias})</span> <span class="filtro-dropdown-caret">▾</span>`;

                    const menuDropdown = document.createElement('div');
                    menuDropdown.className = 'filtro-dropdown-menu';
                    menuDropdown.id = 'menu-outras-especialidades';
                    menuDropdown.style.display = 'none';

                    btnDropdown.onclick = (e) => {
                        if (e) e.stopPropagation();
                        const isAberto = menuDropdown.style.display === 'block';
                        menuDropdown.style.display = isAberto ? 'none' : 'block';
                    };

                    secundarias.sort().forEach(t => {
                        const item = document.createElement('button');
                        item.type = 'button';
                        item.className = 'filtro-dropdown-item';
                        item.setAttribute('data-tema', t);
                        item.innerHTML = `<span>${t}</span> <span class="filtro-dropdown-item-count">${temasObj[t].total}</span>`;
                        item.onclick = (e) => {
                            if (e) {
                                e.preventDefault();
                                e.stopPropagation();
                            }
                            menuDropdown.style.display = 'none';
                            filtrarPorTema(t);
                        };
                        menuDropdown.appendChild(item);
                    });

                    wrapDropdown.appendChild(btnDropdown);
                    wrapDropdown.appendChild(menuDropdown);
                    pillsContainer.appendChild(wrapDropdown);
                }
            } else {
                listaTemas.sort().forEach(t => {
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

    aplicarFiltroEPaginacao(false);
}

function filtrarPorTema(tema) {
    temaAtivo = tema;
    subtemaAtivo = 'TODOS';
    paginaAtual = 1;

    // Sincroniza Sub-pills de Temas
    document.querySelectorAll('.subfiltro-pill').forEach(btn => {
        if (btn.id === 'btn-outras-especialidades') return;
        if (btn.getAttribute('data-tema') === tema) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Sincroniza menu suspenso de Outras Especialidades caso pertença a ele
    const btnOutras = document.getElementById('btn-outras-especialidades');
    const labelOutras = document.getElementById('label-outras-especialidades');
    const menuOutras = document.getElementById('menu-outras-especialidades');
    if (btnOutras && menuOutras) {
        let isSecundariaAtiva = false;
        menuOutras.querySelectorAll('.filtro-dropdown-item').forEach(item => {
            const itemTema = item.getAttribute('data-tema');
            if (itemTema === tema) {
                item.classList.add('active');
                isSecundariaAtiva = true;
            } else {
                item.classList.remove('active');
            }
        });

        if (isSecundariaAtiva) {
            btnOutras.classList.add('active');
            if (labelOutras) {
                const count = taxonomiaEspecialidades[especialidadeAtiva]?.temas?.[tema]?.total || 0;
                labelOutras.textContent = `${tema} (${count})`;
            }
        } else {
            btnOutras.classList.remove('active');
            if (labelOutras) {
                const rotuloDropdown = (especialidadeAtiva === 'Clínica Médica' || especialidadeAtiva === 'Cirurgia Geral' || especialidadeAtiva === 'Pediatria') 
                    ? 'Outras Especialidades' 
                    : 'Outros Temas';
                const totalSecundarias = Array.from(menuOutras.querySelectorAll('.filtro-dropdown-item-count'))
                    .reduce((acc, el) => acc + (parseInt(el.textContent, 10) || 0), 0);
                labelOutras.textContent = `${rotuloDropdown} (${totalSecundarias})`;
            }
        }
    }

    // Renderiza subtemas do tema selecionado (Nível 3) via Combobox
    const subtemasWrapper = document.getElementById('filtro-subtemas-wrapper');
    const inputCombobox = document.getElementById('input-subtema-combobox');
    const dropdownCombobox = document.getElementById('subtema-combobox-dropdown');
    const totalBadge = document.getElementById('subtema-combobox-total');
    const btnLimpar = document.getElementById('btn-limpar-subtema');

    if (tema === 'TODOS' || !taxonomiaEspecialidades[especialidadeAtiva] || !taxonomiaEspecialidades[especialidadeAtiva].temas[tema]) {
        if (subtemasWrapper) subtemasWrapper.style.display = 'none';
    } else {
        const subtemasObj = taxonomiaEspecialidades[especialidadeAtiva].temas[tema].subtemas || {};
        const listaSubtemas = Object.keys(subtemasObj).sort();

        if (listaSubtemas.length <= 1 && (listaSubtemas[0] === 'Diversos' || listaSubtemas[0] === 'Geral')) {
            if (subtemasWrapper) subtemasWrapper.style.display = 'none';
        } else {
            if (subtemasWrapper) subtemasWrapper.style.display = 'block';
            const totalTema = taxonomiaEspecialidades[especialidadeAtiva].temas[tema].total;

            if (inputCombobox) {
                inputCombobox.value = '';
                inputCombobox.placeholder = `Pesquisar ou selecionar subtema em ${tema}...`;
            }
            if (btnLimpar) btnLimpar.style.display = 'none';
            if (totalBadge) totalBadge.textContent = `Todos (${totalTema})`;

            if (dropdownCombobox) {
                dropdownCombobox.innerHTML = '';
                dropdownCombobox.style.display = 'none';

                // Opção "Todos os Subtemas"
                const optTodos = document.createElement('div');
                optTodos.className = 'subtema-combobox-option active';
                optTodos.setAttribute('data-subtema', 'TODOS');
                optTodos.innerHTML = `<span class="subtema-option-name">Todos os Subtemas</span> <span class="subtema-combobox-option-count">${totalTema}</span>`;
                optTodos.onclick = (e) => {
                    if (e) e.stopPropagation();
                    filtrarPorSubtema('TODOS');
                };
                dropdownCombobox.appendChild(optTodos);

                // Opções individuais de Subtemas
                listaSubtemas.forEach(s => {
                    const opt = document.createElement('div');
                    opt.className = 'subtema-combobox-option';
                    opt.setAttribute('data-subtema', s);
                    opt.innerHTML = `<span class="subtema-option-name">${s}</span> <span class="subtema-combobox-option-count">${subtemasObj[s]}</span>`;
                    opt.onclick = (e) => {
                        if (e) e.stopPropagation();
                        filtrarPorSubtema(s);
                    };
                    dropdownCombobox.appendChild(opt);
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

    aplicarFiltroEPaginacao(false);
}

function filtrarPorSubtema(subtema) {
    subtemaAtivo = subtema;
    paginaAtual = 1;

    const inputCombobox = document.getElementById('input-subtema-combobox');
    const dropdownCombobox = document.getElementById('subtema-combobox-dropdown');
    const totalBadge = document.getElementById('subtema-combobox-total');
    const btnLimpar = document.getElementById('btn-limpar-subtema');

    if (inputCombobox) {
        inputCombobox.value = (subtema === 'TODOS' ? '' : subtema);
    }
    if (btnLimpar) {
        btnLimpar.style.display = (subtema !== 'TODOS' ? 'inline-flex' : 'none');
    }
    if (dropdownCombobox) {
        dropdownCombobox.style.display = 'none';
        dropdownCombobox.querySelectorAll('.subtema-combobox-option').forEach(opt => {
            if (opt.getAttribute('data-subtema') === subtema) {
                opt.classList.add('active');
            } else {
                opt.classList.remove('active');
            }
            opt.style.display = 'flex'; // restaura visibilidade
        });
    }

    if (totalBadge && taxonomiaEspecialidades[especialidadeAtiva]?.temas?.[temaAtivo]) {
        const temasInfo = taxonomiaEspecialidades[especialidadeAtiva].temas[temaAtivo];
        if (subtema === 'TODOS') {
            totalBadge.textContent = `Todos (${temasInfo.total})`;
        } else {
            const count = temasInfo.subtemas[subtema] || 0;
            totalBadge.textContent = `${count} ${count === 1 ? 'questão' : 'questões'}`;
        }
    }

    if (typeof gtag === 'function') {
        gtag('event', 'filtrar_subtema', {
            'especialidade': especialidadeAtiva,
            'tema': temaAtivo,
            'subtema': subtema
        });
    }

    aplicarFiltroEPaginacao(false);
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
            const topBar = document.querySelector('.top-bar');
            const topBarHeight = topBar ? topBar.offsetHeight + 16 : 80;
            const rect = section.getBoundingClientRect();

            // Só realiza scroll se o topo dos filtros estiver acima da tela (escondido) ou se o usuário estiver muito abaixo navegando
            if (rect.top < topBarHeight || rect.top > window.innerHeight) {
                const targetY = window.pageYOffset + rect.top - topBarHeight;
                window.scrollTo({ top: Math.max(0, targetY), behavior: 'smooth' });
            }
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

        const fragment = document.createDocumentFragment();

        // Botão Anterior
        const btnPrev = document.createElement('button');
        btnPrev.type = 'button';
        btnPrev.className = 'btn-paginacao';
        btnPrev.innerHTML = '‹ Anterior';
        btnPrev.disabled = (paginaAtual === 1);
        btnPrev.onclick = () => mudarPagina(paginaAtual - 1);
        fragment.appendChild(btnPrev);

        // Numeração de páginas com reticências
        const paginasNumeros = calcularRangePaginas(paginaAtual, totalPaginas);
        paginasNumeros.forEach(item => {
            if (item === '...') {
                const el = document.createElement('span');
                el.className = 'paginacao-ellipsis';
                el.textContent = '...';
                fragment.appendChild(el);
            } else {
                const btnNum = document.createElement('button');
                btnNum.type = 'button';
                btnNum.className = `btn-paginacao ${item === paginaAtual ? 'active' : ''}`;
                btnNum.textContent = item;
                btnNum.onclick = () => mudarPagina(item);
                fragment.appendChild(btnNum);
            }
        });

        // Botão Próxima
        const btnNext = document.createElement('button');
        btnNext.type = 'button';
        btnNext.className = 'btn-paginacao';
        btnNext.innerHTML = 'Próxima ›';
        btnNext.disabled = (paginaAtual === totalPaginas);
        btnNext.onclick = () => mudarPagina(paginaAtual + 1);
        fragment.appendChild(btnNext);

        // Badge Informativo
        const badge = document.createElement('span');
        badge.className = 'paginacao-info-badge';
        badge.textContent = `${itemInicio}–${itemFim} de ${totalItens}`;
        fragment.appendChild(badge);

        container.appendChild(fragment);
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

// Controle do Seletor Customizado de Itens por Página (Dropdown Arredondado com Animação)
function toggleCustomSelectItens() {
    const container = document.getElementById('custom-select-itens-wrap');
    const trigger = document.getElementById('custom-select-trigger');
    if (!container) return;
    const isOpen = container.classList.toggle('open');
    if (trigger) {
        trigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    }
}

function selecionarOpcaoItens(valor, rotulo) {
    const container = document.getElementById('custom-select-itens-wrap');
    const labelSpan = document.getElementById('custom-select-label');
    const trigger = document.getElementById('custom-select-trigger');
    const hiddenSelect = document.getElementById('select-itens-por-pagina');

    if (labelSpan) labelSpan.textContent = rotulo;
    if (hiddenSelect) hiddenSelect.value = valor;

    // Atualiza classe 'selected' nas opções
    if (container) {
        container.querySelectorAll('.custom-select-option').forEach(opt => {
            if (opt.getAttribute('data-value') === valor) {
                opt.classList.add('selected');
            } else {
                opt.classList.remove('selected');
            }
        });
        container.classList.remove('open');
    }

    if (trigger) {
        trigger.setAttribute('aria-expanded', 'false');
    }

    mudarItensPorPagina(valor);
}

// Fechar dropdown de itens ao clicar fora
document.addEventListener('click', (e) => {
    const container = document.getElementById('custom-select-itens-wrap');
    if (container && container.classList.contains('open')) {
        if (!container.contains(e.target)) {
            container.classList.remove('open');
            const trigger = document.getElementById('custom-select-trigger');
            if (trigger) trigger.setAttribute('aria-expanded', 'false');
        }
    }
});

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
    encerrarEfeitosSimulado(true);
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
    if (!e || e.target.id === 'apoio-modal-overlay' || e.target.closest('.kofi-modal-close') || e.target.closest('.modal-close-btn') || e.target.closest('.btn-aviso-ok') || e.target.closest('.btn-modal-secondary')) {
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
let cadernoErrosEstado = { esp: null, tema: null, pagina: 1 };

function encontrarCardQuestao(qId) {
    if (!qId) return null;
    if (_cardDOMCache.has(qId)) {
        const cached = _cardDOMCache.get(qId);
        if (cached && document.body.contains(cached)) return cached;
    }

    construirIndicesDOMSeNecessario();

    const idNormalizado = normalizarIdQuestao(qId);
    const idsParaTentar = [idNormalizado, qId];

    for (const testId of idsParaTentar) {
        const baseId = extrairBaseIdAntigo(testId);
        const candidatos = [
            'card_' + testId,
            testId,
            testId.startsWith('q_') ? 'card_' + testId.substring(2) : 'card_q_' + testId,
            'card_' + baseId,
            baseId,
            baseId.startsWith('q_') ? 'card_' + baseId.substring(2) : 'card_q_' + baseId
        ];

        for (const cand of candidatos) {
            let card = _mapaCardsPorId.get(cand) || document.getElementById(cand);
            if (card) {
                _cardDOMCache.set(qId, card);
                if (idNormalizado !== qId) _cardDOMCache.set(idNormalizado, card);
                return card;
            }
        }
    }

    // Busca flexível por prefixo seguro de ID
    const cleanId = idNormalizado.replace(/^card_/, '').replace(/^q_/, '');
    const baseClean = extrairBaseIdAntigo(cleanId);
    let card = _mapaCardsPorId.get(cleanId) || _mapaCardsPorId.get('card_' + cleanId)
        || _mapaCardsPorId.get(baseClean) || _mapaCardsPorId.get('card_' + baseClean);

    if (card) {
        _cardDOMCache.set(qId, card);
        if (idNormalizado !== qId) _cardDOMCache.set(idNormalizado, card);
        return card;
    }

    return null;
}

function coletarErrosHierarquicos() {
    const dados = safeStorageGet(STORAGE_KEY, {});
    const tree = {};
    let totalGeral = 0;

    for (const [qId, valorMarcado] of Object.entries(dados)) {
        const card = encontrarCardQuestao(qId);
        if (!card) continue; // Nunca deletar do storage; apenas ignora no relatório se o card não estiver disponível

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

    return { tree, totalGeral };
}

function abrirCadernoErrosModal() {
    const { tree, totalGeral } = coletarErrosHierarquicos();
    
    // Se a especialidade ou tema gravado não tiver mais erros pendentes, recua graciosamente
    if (cadernoErrosEstado.esp && (!tree[cadernoErrosEstado.esp] || Object.keys(tree[cadernoErrosEstado.esp]).length === 0)) {
        cadernoErrosEstado.esp = null;
        cadernoErrosEstado.tema = null;
        cadernoErrosEstado.pagina = 1;
    } else if (cadernoErrosEstado.esp && cadernoErrosEstado.tema && (!tree[cadernoErrosEstado.esp][cadernoErrosEstado.tema] || tree[cadernoErrosEstado.esp][cadernoErrosEstado.tema].length === 0)) {
        cadernoErrosEstado.tema = null;
        cadernoErrosEstado.pagina = 1;
    }

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
    // NÍVEL 3: Lista de Questões Erradas do Tema (Paginada: 10 por página)
    // ==========================================
    else {
        const esp = cadernoErrosEstado.esp;
        const tema = cadernoErrosEstado.tema;
        const itens = (tree[esp] && tree[esp][tema]) ? tree[esp][tema] : [];
        const ITENS_POR_PAGINA = 10;
        const totalPaginas = Math.ceil(itens.length / ITENS_POR_PAGINA) || 1;

        if (cadernoErrosEstado.pagina > totalPaginas) cadernoErrosEstado.pagina = totalPaginas;
        if (cadernoErrosEstado.pagina < 1) cadernoErrosEstado.pagina = 1;

        const paginaAtual = cadernoErrosEstado.pagina;
        const inicio = (paginaAtual - 1) * ITENS_POR_PAGINA;
        const fim = Math.min(inicio + ITENS_POR_PAGINA, itens.length);
        const itensPagina = itens.slice(inicio, fim);

        if (subtitulo) {
            if (totalPaginas > 1) {
                subtitulo.textContent = `${itens.length} ${itens.length === 1 ? 'questão' : 'questões'} em ${tema} • Página ${paginaAtual} de ${totalPaginas} (Exibindo ${inicio + 1}–${fim})`;
            } else {
                subtitulo.textContent = `${itens.length} ${itens.length === 1 ? 'questão' : 'questões'} em ${tema}`;
            }
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

        itensPagina.forEach(item => {
            const itemEl = document.createElement('div');
            itemEl.className = 'erro-item-card';
            itemEl.id = `erro_item_${item.qId}`;

            const headerRow = document.createElement('div');
            headerRow.className = 'erro-item-header-row';

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

            feedbackEl.appendChild(badgeMarcada);

            infoEl.appendChild(tagEl);
            infoEl.appendChild(snippetEl);
            infoEl.appendChild(feedbackEl);

            const btnEl = document.createElement('button');
            btnEl.type = 'button';
            btnEl.className = 'btn-ver-questao-erro';
            btnEl.innerHTML = `Ver Questão <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px; margin-left: 4px;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
            btnEl.onclick = () => toggleExpandirQuestaoErro(item.qId, btnEl);

            headerRow.appendChild(infoEl);
            headerRow.appendChild(btnEl);
            itemEl.appendChild(headerRow);

            const expandidoContainer = document.createElement('div');
            expandidoContainer.className = 'erro-item-expandido-container';
            expandidoContainer.style.display = 'none';
            itemEl.appendChild(expandidoContainer);

            grupoEl.appendChild(itemEl);
        });

        listaContainer.appendChild(grupoEl);

        // Barra de Paginação (se houver mais de 1 página)
        if (totalPaginas > 1) {
            const paginacaoEl = document.createElement('div');
            paginacaoEl.className = 'caderno-paginacao-bar';

            const infoEl = document.createElement('div');
            infoEl.className = 'caderno-paginacao-info';
            infoEl.textContent = `Exibindo ${inicio + 1}–${fim} de ${itens.length} questões`;

            const botoesEl = document.createElement('div');
            botoesEl.className = 'caderno-paginacao-botoes';

            // Botão Anterior
            const btnPrev = document.createElement('button');
            btnPrev.type = 'button';
            btnPrev.className = 'btn-caderno-pag';
            btnPrev.innerHTML = `&larr; Anterior`;
            btnPrev.disabled = (paginaAtual === 1);
            btnPrev.onclick = () => mudarPaginaCaderno(paginaAtual - 1);
            botoesEl.appendChild(btnPrev);

            // Botões com números de páginas
            for (let p = 1; p <= totalPaginas; p++) {
                const btnNum = document.createElement('button');
                btnNum.type = 'button';
                btnNum.className = `btn-caderno-pag-num ${p === paginaAtual ? 'active' : ''}`;
                btnNum.textContent = p;
                btnNum.onclick = () => mudarPaginaCaderno(p);
                botoesEl.appendChild(btnNum);
            }

            // Botão Próximo
            const btnNext = document.createElement('button');
            btnNext.type = 'button';
            btnNext.className = 'btn-caderno-pag';
            btnNext.innerHTML = `Próximo &rarr;`;
            btnNext.disabled = (paginaAtual === totalPaginas);
            btnNext.onclick = () => mudarPaginaCaderno(paginaAtual + 1);
            botoesEl.appendChild(btnNext);

            paginacaoEl.appendChild(infoEl);
            paginacaoEl.appendChild(botoesEl);
            listaContainer.appendChild(paginacaoEl);
        }
    }
}

function mudarPaginaCaderno(novaPagina) {
    cadernoErrosEstado.pagina = novaPagina;
    renderizarCadernoErros();
    const lista = document.getElementById('caderno-erros-lista');
    if (lista) {
        lista.scrollTop = 0;
    }
}

function selecionarEspCaderno(esp) {
    cadernoErrosEstado.esp = esp;
    cadernoErrosEstado.tema = null;
    cadernoErrosEstado.pagina = 1;
    renderizarCadernoErros();
}

function selecionarTemaCaderno(esp, tema) {
    cadernoErrosEstado.esp = esp;
    cadernoErrosEstado.tema = tema;
    cadernoErrosEstado.pagina = 1;
    renderizarCadernoErros();
}

function voltarNivelCaderno() {
    if (cadernoErrosEstado.tema !== null) {
        cadernoErrosEstado.tema = null;
    } else {
        cadernoErrosEstado.esp = null;
    }
    cadernoErrosEstado.pagina = 1;
    renderizarCadernoErros();
}

function atualizarCoresAlternativasClone(clone, gabarito, forcarExibicaoCores = null) {
    if (!clone) return;
    const gabBox = clone.querySelector('.gabarito-box');
    const isGabAberto = (forcarExibicaoCores !== null) 
        ? forcarExibicaoCores 
        : (gabBox && gabBox.style.display !== 'none' && gabBox.style.display !== '');

    const inputMarcado = clone.querySelector('input[type="radio"]:checked');
    const valorMarcado = inputMarcado ? inputMarcado.value : '';

    clone.querySelectorAll('.alternativa').forEach(altLabel => {
        const input = altLabel.querySelector('input[type="radio"]');
        if (!input) return;
        const val = input.value;
        altLabel.classList.remove('selected', 'correct', 'incorrect');

        if (isGabAberto) {
            if (val === valorMarcado && val !== gabarito) {
                altLabel.classList.add('incorrect');
            } else if (val === gabarito) {
                altLabel.classList.add('correct');
            }
        } else {
            if (val === valorMarcado) {
                altLabel.classList.add('selected');
            }
        }
    });
}

function resetarQuestaoExpandida(expandidoContainer, qId) {
    if (!expandidoContainer) return;
    const clone = expandidoContainer.querySelector('.questao-expandida-conteudo');
    if (!clone) return;

    const cardOriginal = encontrarCardQuestao(qId);
    const radioOriginal = cardOriginal ? cardOriginal.querySelector('input[type="radio"]') : null;
    const gabarito = radioOriginal ? radioOriginal.getAttribute('data-gabarito') : '';
    const dados = safeStorageGet(STORAGE_KEY, {});
    const marcada = dados[qId] || dados[qId.replace(/^q_/, '')] || '';

    const gabBox = clone.querySelector('.gabarito-box');
    if (gabBox) gabBox.style.display = 'none';

    const btnResposta = clone.querySelector('.btn-resposta');
    if (btnResposta) btnResposta.innerHTML = `&#10022; Ver Gabarito e Comentário`;

    clone.querySelectorAll('.alternativa').forEach(altLabel => {
        altLabel.classList.remove('correct', 'incorrect', 'selected');
        const input = altLabel.querySelector('input[type="radio"]');
        if (input) {
            if (input.value === marcada) {
                altLabel.classList.add('selected');
                input.checked = true;
            } else {
                input.checked = false;
            }
        }
    });
}

function resetarTodasQuestoesExpandidasErros() {
    document.querySelectorAll('.erro-item-card.expanded').forEach(cardItem => {
        cardItem.classList.remove('expanded');
        const expandido = cardItem.querySelector('.erro-item-expandido-container');
        if (expandido) expandido.style.display = 'none';
        const snippetEl = cardItem.querySelector('.erro-item-snippet');
        if (snippetEl) snippetEl.style.display = 'block';
        const btnEl = cardItem.querySelector('.btn-ver-questao-erro');
        if (btnEl) {
            btnEl.className = 'btn-ver-questao-erro';
            btnEl.innerHTML = `Ver Questão <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px; margin-left: 4px;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
        }
        const qId = cardItem.id.replace(/^erro_item_/, '');
        resetarQuestaoExpandida(expandido, qId);
    });
}

function toggleExpandirQuestaoErro(qId, btnEl) {
    const cardItem = document.getElementById(`erro_item_${qId}`);
    if (!cardItem) return;

    const expandidoContainer = cardItem.querySelector('.erro-item-expandido-container');
    const snippetEl = cardItem.querySelector('.erro-item-snippet');
    if (!expandidoContainer) return;

    const isExpanded = cardItem.classList.contains('expanded');

    if (isExpanded) {
        // Recolher e resetar highlights
        expandidoContainer.style.display = 'none';
        cardItem.classList.remove('expanded');
        resetarQuestaoExpandida(expandidoContainer, qId);
        if (snippetEl) snippetEl.style.display = 'block';
        if (btnEl) {
            btnEl.className = 'btn-ver-questao-erro';
            btnEl.innerHTML = `Ver Questão <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px; margin-left: 4px;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
        }
    } else {
        // Expandir (Modo Estudo Ativo / Sem Spoiler)
        if (!expandidoContainer.dataset.loaded) {
            const cardOriginal = encontrarCardQuestao(qId);
            if (cardOriginal) {
                // Clona a estrutura da questão original
                const clone = cardOriginal.cloneNode(true);
                clone.removeAttribute('id');
                clone.removeAttribute('style');
                clone.className = 'questao-expandida-conteudo';
                clone.style.display = 'block';
                clone.querySelectorAll('[id]').forEach(el => el.removeAttribute('id'));

                // Remove classes e estilos de ocultação que possam ter vindo do simulado
                clone.classList.remove('paginacao-oculto', 'filtro-oculto', 'answered', 'highlight-target');

                // Remove a tag de origem do clone pois já está no topo do card
                const tagOrigemClone = clone.querySelector('.tag-origem');
                if (tagOrigemClone) tagOrigemClone.remove();

                // Mantém a caixa de gabarito e explicação OCULTA até o clique
                const gabBox = clone.querySelector('.gabarito-box');
                if (gabBox) {
                    gabBox.style.display = 'none';
                }

                // Recupera gabarito e resposta marcada
                const radioOriginal = cardOriginal.querySelector('input[type="radio"]');
                const gabarito = radioOriginal ? radioOriginal.getAttribute('data-gabarito') : '';
                const dados = safeStorageGet(STORAGE_KEY, {});
                const marcada = dados[qId] || dados[qId.replace(/^q_/, '')] || '';

                // Configura as alternativas para permitir alternar a seleção dinamicamente e limpa cores herdadas
                clone.querySelectorAll('.alternativa').forEach(altLabel => {
                    altLabel.classList.remove('selected', 'correct', 'incorrect');
                    const input = altLabel.querySelector('input[type="radio"]');
                    if (input) {
                        const val = input.value;
                        if (val === marcada) {
                            altLabel.classList.add('selected');
                            input.checked = true;
                        } else {
                            input.checked = false;
                        }

                        // Atualiza as cores dinamicamente ao trocar de alternativa (mesmo com gabarito aberto)
                        input.addEventListener('change', () => {
                            atualizarCoresAlternativasClone(clone, gabarito);
                        });
                    }
                });

                // Garante a existência do botão "Ver Gabarito e Comentário"
                let btnResposta = clone.querySelector('.btn-resposta');
                if (!btnResposta) {
                    btnResposta = document.createElement('button');
                    btnResposta.type = 'button';
                    btnResposta.className = 'btn-resposta';
                    if (gabBox) {
                        clone.insertBefore(btnResposta, gabBox);
                    } else {
                        clone.appendChild(btnResposta);
                    }
                }

                btnResposta.innerHTML = `&#10022; Ver Gabarito e Comentário`;
                btnResposta.onclick = () => {
                    if (!gabBox) return;
                    const isHidden = (gabBox.style.display === 'none' || gabBox.style.display === '');
                    gabBox.style.display = isHidden ? 'block' : 'none';
                    btnResposta.innerHTML = isHidden 
                        ? `&#10006; Ocultar Gabarito e Comentário` 
                        : `&#10022; Ver Gabarito e Comentário`;

                    atualizarCoresAlternativasClone(clone, gabarito, isHidden);
                };

                expandidoContainer.innerHTML = '';
                expandidoContainer.appendChild(clone);
                expandidoContainer.dataset.loaded = 'true';
            } else {
                expandidoContainer.innerHTML = `<p style="color: var(--text-muted); font-size: 14px; margin: 8px 0;">Não foi possível carregar o conteúdo completo desta questão.</p>`;
            }
        } else {
            // Garante reset limpo se já estava carregado previamente
            resetarQuestaoExpandida(expandidoContainer, qId);
        }

        expandidoContainer.style.display = 'flex';
        cardItem.classList.add('expanded');
        if (snippetEl) snippetEl.style.display = 'none';
        if (btnEl) {
            btnEl.className = 'btn-ver-questao-erro btn-recolher';
            btnEl.innerHTML = `Ver Menos <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px; margin-left: 4px;"><polyline points="18 15 12 9 6 15"></polyline></svg>`;
        }
    }
}

function fecharCadernoErrosModal(e) {
    if (!e || e.target.id === 'caderno-erros-modal-overlay' || e.target.closest('.confirm-modal-close')) {
        const modal = document.getElementById('caderno-erros-modal-overlay');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
        // Reseta o estado expandido e os highlights para manter o modo de estudo ativo
        resetarTodasQuestoesExpandidasErros();
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

// ========================================================
// LIGHTBOX / ZOOM INTERATIVO DE IMAGENS DAS QUESTÕES
// ========================================================
let zoomState = {
    currentZoom: 1,
    panX: 0,
    panY: 0,
    isDragging: false,
    startX: 0,
    startY: 0
};

function configurarContainerPorResolucao(img) {
    const viewport = document.getElementById('image-zoom-viewport');
    if (!viewport) return;

    const natW = img.naturalWidth || 0;
    const natH = img.naturalHeight || 0;

    // Imagens de baixa resolução (ex: largura < 650px e altura < 500px)
    // são iniciadas em um container expandido maior para dar conforto visual e espaço de navegação
    if (natW > 0 && natW < 650 && natH < 500) {
        viewport.classList.add('container-expandido');
    } else {
        viewport.classList.remove('container-expandido');
    }
}

function aplicarTransformZoom() {
    const zoomImg = document.getElementById('image-zoom-img');
    const badge = document.getElementById('zoom-level-badge');
    const viewport = document.getElementById('image-zoom-viewport');
    if (!zoomImg) return;

    zoomImg.style.transform = `translate(${zoomState.panX}px, ${zoomState.panY}px) scale(${zoomState.currentZoom})`;
    
    if (badge) {
        const perc = Math.round(zoomState.currentZoom * 100);
        badge.textContent = `${perc}%`;
    }

    if (viewport) {
        viewport.style.cursor = zoomState.currentZoom > 1.05 ? 'grab' : 'zoom-in';
    }
}

function alterarZoomImagem(delta) {
    const novoZoom = Math.min(Math.max(zoomState.currentZoom + delta, 0.5), 4.0);
    if (Math.abs(novoZoom - zoomState.currentZoom) < 0.01) return;
    
    zoomState.currentZoom = parseFloat(novoZoom.toFixed(2));
    if (zoomState.currentZoom <= 1) {
        zoomState.panX = 0;
        zoomState.panY = 0;
    }
    aplicarTransformZoom();
}

function resetarZoomImagem(silencioso = false) {
    zoomState.currentZoom = 1;
    zoomState.panX = 0;
    zoomState.panY = 0;
    zoomState.isDragging = false;
    const viewport = document.getElementById('image-zoom-viewport');
    if (viewport) {
        viewport.classList.remove('is-dragging');
    }
    if (!silencioso) {
        aplicarTransformZoom();
    }
}

function abrirZoomImagem(src, caption) {
    marcarInteracaoInternaSegura(true);
    const overlay = document.getElementById('image-zoom-overlay');
    const zoomImg = document.getElementById('image-zoom-img');
    const zoomCaption = document.getElementById('image-zoom-caption');
    if (!overlay || !zoomImg) return;

    // Reseta estado para iniciar rigorosamente em seu tamanho nativo (100%)
    resetarZoomImagem(true);

    zoomImg.src = src;

    const inicializarDimensoes = () => {
        configurarContainerPorResolucao(zoomImg);
        aplicarTransformZoom();
    };

    if (zoomImg.complete && zoomImg.naturalWidth > 0) {
        inicializarDimensoes();
    } else {
        zoomImg.onload = inicializarDimensoes;
    }

    if (zoomCaption) {
        if (caption) {
            zoomCaption.textContent = caption;
            zoomCaption.style.display = 'block';
        } else {
            zoomCaption.style.display = 'none';
        }
    }

    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function fecharZoomImagem(e) {
    if (e && e.target && e.target.closest('.image-zoom-container') && !e.target.closest('.image-zoom-close')) {
        return;
    }
    const overlay = document.getElementById('image-zoom-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
    resetarZoomImagem(true);
    const viewport = document.getElementById('image-zoom-viewport');
    if (viewport) {
        viewport.classList.remove('container-expandido');
    }
    document.body.style.overflow = '';
    setTimeout(() => marcarInteracaoInternaSegura(false), 300);
}

// Configura eventos de interação rica com o Zoom (Wheel, Drag/Pan, Touch e Duplo Clique)
function configurarInteracoesZoom() {
    const viewport = document.getElementById('image-zoom-viewport');
    const zoomImg = document.getElementById('image-zoom-img');
    if (!viewport || viewport.dataset.zoomConfigured) return;
    viewport.dataset.zoomConfigured = 'true';

    // Previne qualquer tentativa de arrasto nativo de imagem do navegador
    viewport.addEventListener('dragstart', function(e) {
        e.preventDefault();
        return false;
    });
    if (zoomImg) {
        zoomImg.addEventListener('dragstart', function(e) {
            e.preventDefault();
            return false;
        });
    }

    // 1. Zoom via Roda do Mouse (Wheel)
    viewport.addEventListener('wheel', function(e) {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 0.2 : -0.2;
        alterarZoomImagem(delta);
    }, { passive: false });

    function finalizarArrasto(e) {
        if (zoomState.isDragging) {
            zoomState.isDragging = false;
            viewport.classList.remove('is-dragging');
            if (e && e.pointerId) {
                try {
                    viewport.releasePointerCapture(e.pointerId);
                } catch (_) {}
            }
        }
    }

    // 2. Drag / Pan com Pointer Events (arrasto SOMENTE enquanto o botão primário estiver pressionado)
    viewport.addEventListener('pointerdown', function(e) {
        // Apenas botão primário (esquerdo do mouse ou toque)
        if (e.pointerType === 'mouse' && e.button !== 0) return;

        e.preventDefault();
        zoomState.isDragging = true;
        zoomState.startX = e.clientX - zoomState.panX;
        zoomState.startY = e.clientY - zoomState.panY;
        viewport.classList.add('is-dragging');

        try {
            viewport.setPointerCapture(e.pointerId);
        } catch (_) {}
    });

    viewport.addEventListener('pointermove', function(e) {
        if (!zoomState.isDragging) return;

        // Se for mouse, verifica se o botão esquerdo continua ativamente pressionado
        if (e.pointerType === 'mouse' && (e.buttons & 1) === 0) {
            finalizarArrasto(e);
            return;
        }

        e.preventDefault();
        zoomState.panX = e.clientX - zoomState.startX;
        zoomState.panY = e.clientY - zoomState.startY;
        aplicarTransformZoom();
    });

    viewport.addEventListener('pointerup', finalizarArrasto);
    viewport.addEventListener('pointercancel', finalizarArrasto);
    window.addEventListener('mouseup', finalizarArrasto);

    // 3. Duplo clique para alternar zoom (100% <-> 200%)
    viewport.addEventListener('dblclick', function(e) {
        e.preventDefault();
        if (zoomState.currentZoom > 1.1) {
            resetarZoomImagem();
        } else {
            zoomState.currentZoom = 2.0;
            aplicarTransformZoom();
        }
    });
}

// Delegação de clique para todas as imagens de questões
document.addEventListener('click', function(e) {
    const imgEl = e.target.closest('.img-questao');
    if (!imgEl) return;

    e.preventDefault();
    e.stopPropagation();

    // Recupera contexto da questão para exibir na legenda
    const cardEl = imgEl.closest('.card-questao');
    let legenda = imgEl.getAttribute('alt') || 'Imagem da Questão';
    if (cardEl) {
        const tagOrigem = cardEl.querySelector('.tag-origem');
        if (tagOrigem) {
            legenda = `${tagOrigem.textContent.trim()} — Visualização Ampliada`;
        }
    }

    abrirZoomImagem(imgEl.src, legenda);
});

// Atalhos de teclado (ESC para fechar modais, + / - / 0 para zoom)
document.addEventListener('keydown', function(e) {
    const zoomModal = document.getElementById('image-zoom-overlay');
    if (zoomModal && zoomModal.classList.contains('active')) {
        if (e.key === 'Escape') {
            fecharZoomImagem();
            return;
        }
        if (e.key === '+' || e.key === '=') {
            e.preventDefault();
            alterarZoomImagem(0.25);
            return;
        }
        if (e.key === '-' || e.key === '_') {
            e.preventDefault();
            alterarZoomImagem(-0.25);
            return;
        }
        if (e.key === '0') {
            e.preventDefault();
            resetarZoomImagem();
            return;
        }
    }

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

// ========================================================
// Backup Seguro: Exportar e Importar Respostas (JSON)
// ========================================================
function exportarBackupRespostas() {
    const dados = safeStorageGet(STORAGE_KEY, {});
    const total = Object.keys(dados).length;
    
    if (total === 0) {
        alert('Você ainda não possui nenhuma questão respondida para exportar.');
        return;
    }

    const backupPayload = {
        app: 'Simulado Residência Médica',
        versao: '2.0',
        dataExportacao: new Date().toISOString(),
        totalQuestoesRespondidas: total,
        respostas: dados
    };

    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(backupPayload, null, 2));
    const dataAtual = new Date().toISOString().slice(0, 10);
    const fileName = `simulado_respostas_backup_${dataAtual}.json`;

    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", fileName);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();

    if (typeof gtag === 'function') {
        gtag('event', 'exportar_backup', { total: total });
    }
}

function dispararSeletorImportarBackup() {
    const input = document.getElementById('input-importar-backup');
    if (input) {
        input.value = '';
        input.click();
    }
}

function processarArquivoImportacaoBackup(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const parsed = JSON.parse(e.target.result);
            let novasRespostas = {};

            if (parsed && typeof parsed === 'object') {
                if (parsed.respostas && typeof parsed.respostas === 'object') {
                    novasRespostas = parsed.respostas;
                } else {
                    novasRespostas = parsed;
                }
            }

            const chaves = Object.keys(novasRespostas);
            if (chaves.length === 0) {
                alert('O arquivo selecionado não contém respostas válidas.');
                return;
            }

            const dadosAtuais = safeStorageGet(STORAGE_KEY, {});
            const dadosMesclados = { ...dadosAtuais, ...novasRespostas };
            
            safeStorageSet(STORAGE_KEY, dadosMesclados);
            safeStorageSet(BACKUP_STORAGE_KEY, dadosMesclados);

            // Re-executa a carga para atualizar os radios e estatísticas
            carregarRespostas();

            alert(`Backup importado com sucesso!\n${chaves.length} respostas sincronizadas (Total salvo no seu navegador: ${Object.keys(dadosMesclados).length}).`);
            
            if (typeof gtag === 'function') {
                gtag('event', 'importar_backup', { total: Object.keys(dadosMesclados).length });
            }
        } catch (err) {
            console.error('Erro ao importar backup:', err);
            alert('Não foi possível ler o arquivo de backup. Certifique-se de que é um arquivo .json válido gerado pelo simulado.');
        }
    };
    reader.readAsText(file);
}

// ========================================================
// Efeito Fullscreen e Modal de Conclusão do Simulado (Canvas 2D)
// ========================================================
let animIdFinalizacao = null;
let timeoutModalFinalizacao = null;
let canvasFinalizacao = null;
window.simuladoFinalizadoJaDisparado = false;

function dispararEfeitoFinalizacao(cenario = 1, stats = {}, isTest = false) {
    // 1. Limpa qualquer efeito residual ativo
    encerrarEfeitosSimulado(false);

    // 2. Prepara o canvas em tela cheia com alta densidade de pixels (Retina / High-DPI)
    canvasFinalizacao = document.createElement('canvas');
    canvasFinalizacao.id = 'canvas-confetes-simulado';
    document.body.appendChild(canvasFinalizacao);

    const ctx = canvasFinalizacao.getContext('2d');
    let dpr = window.devicePixelRatio || 1;
    let width = window.innerWidth;
    let height = window.innerHeight;

    function redimensionarCanvas() {
        if (!canvasFinalizacao) return;
        dpr = window.devicePixelRatio || 1;
        width = window.innerWidth;
        height = window.innerHeight;
        canvasFinalizacao.width = Math.round(width * dpr);
        canvasFinalizacao.height = Math.round(height * dpr);
        canvasFinalizacao.style.width = width + 'px';
        canvasFinalizacao.style.height = height + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    redimensionarCanvas();
    window.addEventListener('resize', redimensionarCanvas);

    // 3. Configuração dos parâmetros visuais por cenário
    let particulas = [];
    let fogos = [];
    let contadorFrames = 0;

    let totalParticulas = 160;
    let paletaCores = ['#2563eb', '#38bdf8', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#f43f5e'];
    let permitirFogos = false;
    let velocidadeBase = 3.5;

    if (cenario === 2) {
        // CASO 2: 100% Acertos -> Confetes Dourados + Fogos de Artifício
        totalParticulas = 220;
        paletaCores = ['#ffd700', '#f59e0b', '#fbbf24', '#fff8dc', '#fef08a', '#d97706', '#ffffff'];
        permitirFogos = true;
        velocidadeBase = 4.0;
    } else if (cenario === 3) {
        // CASO 3: 0% Acertos -> Mínimo de confetes (sutil, cinzento, lento)
        totalParticulas = 15;
        paletaCores = ['#94a3b8', '#64748b', '#cbd5e1', '#a1a1aa'];
        permitirFogos = false;
        velocidadeBase = 1.6;
    }

    // Criação inicial das partículas de confete
    for (let i = 0; i < totalParticulas; i++) {
        particulas.push(criarConfete(width, height, paletaCores, velocidadeBase, true));
    }

    function criarConfete(w, h, cores, velBase, inicial = false) {
        const cor = cores[Math.floor(Math.random() * cores.length)];
        const tamanhoL = Math.random() * 8 + 6;
        const tamanhoA = Math.random() * 5 + 4;
        return {
            x: Math.random() * w,
            y: inicial ? Math.random() * -h : -20 - Math.random() * 40,
            largura: tamanhoL,
            altura: tamanhoA,
            cor: cor,
            velY: (Math.random() * 2 + velBase) * 0.8,
            velX: Math.random() * 2 - 1,
            oscilacao: Math.random() * Math.PI * 2,
            velOscilacao: Math.random() * 0.05 + 0.02,
            rotacao: Math.random() * Math.PI,
            velRotacao: Math.random() * 0.08 + 0.03,
            redondo: Math.random() > 0.65
        };
    }

    // Função auxiliar para fogos de artifício (Cenário 2)
    function lancarFoguete() {
        if (!permitirFogos) return;
        const xOrigem = Math.random() * (width * 0.8) + (width * 0.1);
        const yAlvo = Math.random() * (height * 0.35) + (height * 0.15);
        fogos.push({
            tipo: 'foguete',
            x: xOrigem,
            y: height,
            yAlvo: yAlvo,
            velY: -(Math.random() * 4 + 12),
            velX: (Math.random() - 0.5) * 2,
            cor: paletaCores[Math.floor(Math.random() * paletaCores.length)],
            rastro: []
        });
    }

    function explodirFoguete(f) {
        const numCentelhas = Math.floor(Math.random() * 20) + 40;
        for (let i = 0; i < numCentelhas; i++) {
            const angulo = (Math.PI * 2 * i) / numCentelhas + (Math.random() * 0.2 - 0.1);
            const forca = Math.random() * 5 + 2;
            fogos.push({
                tipo: 'centelha',
                x: f.x,
                y: f.y,
                velX: Math.cos(angulo) * forca,
                velY: Math.sin(angulo) * forca,
                cor: f.cor,
                alpha: 1,
                vida: Math.random() * 30 + 45
            });
        }
    }

    // 4. Loop de renderização fluida a 60 FPS (O(N) in-memory)
    function loop() {
        ctx.clearRect(0, 0, width, height);
        contadorFrames++;

        // Renderiza e atualiza confetes
        for (let i = 0; i < particulas.length; i++) {
            const p = particulas[i];
            p.oscilacao += p.velOscilacao;
            p.rotacao += p.velRotacao;
            p.y += p.velY;
            p.x += Math.sin(p.oscilacao) * 1.5 + p.velX;

            ctx.save();
            ctx.translate(p.x, p.y);
            ctx.rotate(p.rotacao);
            const escalaY = Math.cos(p.oscilacao);
            ctx.scale(1, escalaY);

            ctx.fillStyle = p.cor;
            if (p.redondo) {
                ctx.beginPath();
                ctx.arc(0, 0, p.largura * 0.45, 0, Math.PI * 2);
                ctx.fill();
            } else {
                ctx.fillRect(-p.largura / 2, -p.altura / 2, p.largura, p.altura);
            }
            ctx.restore();

            // Recicla continuamente as partículas no topo enquanto os efeitos estiverem na tela
            if (p.y > height + 20) {
                particulas[i] = criarConfete(width, height, paletaCores, velocidadeBase, false);
            }
        }

        // Renderiza e atualiza fogos de artifício (Cenário 2)
        if (permitirFogos) {
            if (contadorFrames % 45 === 0 || contadorFrames === 5) {
                lancarFoguete();
            }

            for (let i = fogos.length - 1; i >= 0; i--) {
                const f = fogos[i];
                if (f.tipo === 'foguete') {
                    f.y += f.velY;
                    f.x += f.velX;
                    f.velY *= 0.98;

                    // Desenha o foguete em ascensão
                    ctx.save();
                    ctx.fillStyle = f.cor;
                    ctx.shadowColor = f.cor;
                    ctx.shadowBlur = 10;
                    ctx.beginPath();
                    ctx.arc(f.x, f.y, 3, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.restore();

                    if (f.y <= f.yAlvo || f.velY >= -1.5) {
                        explodirFoguete(f);
                        fogos.splice(i, 1);
                    }
                } else if (f.tipo === 'centelha') {
                    f.x += f.velX;
                    f.y += f.velY;
                    f.velX *= 0.96;
                    f.velY *= 0.96;
                    f.velY += 0.08; // Gravidade leve
                    f.alpha -= 1 / f.vida;

                    if (f.alpha <= 0) {
                        fogos.splice(i, 1);
                        continue;
                    }

                    ctx.save();
                    ctx.globalAlpha = Math.max(0, f.alpha);
                    ctx.fillStyle = f.cor;
                    ctx.shadowColor = f.cor;
                    ctx.shadowBlur = 8;
                    ctx.beginPath();
                    ctx.arc(f.x, f.y, 2.5, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.restore();
                }
            }
        }

        animIdFinalizacao = requestAnimationFrame(loop);
    }

    loop();

    // 5. O modal deve aparecer exatamente 10 segundos após o trigger dos efeitos
    timeoutModalFinalizacao = setTimeout(() => {
        abrirModalFinalizacao(cenario, stats);
    }, 10000);
}

function abrirModalFinalizacao(cenario, stats = {}) {
    const overlay = document.getElementById('simulado-concluido-modal-overlay');
    const card = document.getElementById('simulado-concluido-modal-card');
    const badge = document.getElementById('simulado-concluido-badge');
    const titulo = document.getElementById('simulado-concluido-titulo');
    const mensagem = document.getElementById('simulado-concluido-mensagem');
    const statTotal = document.getElementById('concluido-stat-total');
    const statAcertos = document.getElementById('concluido-stat-acertos');
    const statTaxa = document.getElementById('concluido-stat-taxa');

    if (!overlay || !card) return;

    // Remove modificadores anteriores
    card.classList.remove('cenario-perfeito', 'cenario-critico', 'cenario-comum');

    const total = stats.total ?? (window.TOTAL_QUESTOES || 0);
    const acertos = stats.acertos ?? 0;
    const taxa = stats.taxa ?? (total > 0 ? Math.round((acertos / total) * 100) : 0);

    if (cenario === 2) {
        // CASO 2
        card.classList.add('cenario-perfeito');
        if (badge) badge.textContent = '🏆';
        if (titulo) titulo.textContent = 'Desempenho Impecável!';
        if (mensagem) mensagem.textContent = 'Parabéns por completar este simulado, espero que você vá tão bem nas provas quanto foi aqui!';
    } else if (cenario === 3) {
        // CASO 3
        card.classList.add('cenario-critico');
        if (badge) badge.textContent = '📚';
        if (titulo) titulo.textContent = 'Simulado Finalizado';
        if (mensagem) mensagem.textContent = 'Por favor, estude mais!';
    } else {
        // CASO 1
        card.classList.add('cenario-comum');
        if (badge) badge.textContent = '🎉';
        if (titulo) titulo.textContent = 'Parabéns!';
        if (mensagem) mensagem.textContent = 'Parabéns por completar este simulado, espero que você vá bem nas provas!';
    }

    if (statTotal) statTotal.textContent = total;
    if (statAcertos) statAcertos.textContent = acertos;
    if (statTaxa) statTaxa.textContent = taxa + '%';

    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function encerrarEfeitosSimulado(resetFlag = false) {
    if (animIdFinalizacao) {
        cancelAnimationFrame(animIdFinalizacao);
        animIdFinalizacao = null;
    }
    if (timeoutModalFinalizacao) {
        clearTimeout(timeoutModalFinalizacao);
        timeoutModalFinalizacao = null;
    }
    if (canvasFinalizacao) {
        canvasFinalizacao.remove();
        canvasFinalizacao = null;
    }

    const overlay = document.getElementById('simulado-concluido-modal-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
    document.body.style.overflow = '';

    if (resetFlag) {
        window.simuladoFinalizadoJaDisparado = false;
    }
}

// Helper global para teste imediato de qualquer cenário via Console
window.testarEfeitoSimulado = function(cenario = 1) {
    const total = window.TOTAL_QUESTOES || 50;
    let acertos = Math.round(total * 0.75);
    if (cenario === 2) acertos = total;
    if (cenario === 3) acertos = 0;
    const taxa = Math.round((acertos / total) * 100);
    console.log(`[Simulado] Testando Cenário ${cenario} (Acertos: ${acertos}/${total} - ${taxa}%)... O modal abrirá em 10 segundos.`);
    dispararEfeitoFinalizacao(cenario, { total, acertos, taxa }, true);
};

// Inicialização completa
initTheme();
window.addEventListener('DOMContentLoaded', () => {
    carregarRespostas();
    inicializarPaginacaoEFiltros();
    configurarInteracoesZoom();
    verificarRestauracaoSimulado();
});
if (document.readyState !== 'loading') {
    configurarInteracoesZoom();
}


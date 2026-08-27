const STORAGE_KEY = 'caderno_respostas_simulado';

function irParaEstatisticas() {
    const painel = document.getElementById('painel-estatisticas');
    if (!painel) return;
    
    painel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Acompanha a renderização dinâmica dos 1.500 cards até cravar no painel
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
    const dados = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    const total = window.TOTAL_QUESTOES || 0;
    let acertos = 0;
    let erros = 0;
    let avaliadas = 0;

    for (const [qId, valor] of Object.entries(dados)) {
        const radio = document.querySelector(`input[name="${qId}"]`);
        if (radio) {
            const gabarito = radio.getAttribute('data-gabarito');
            if (gabarito && gabarito !== 'N/A' && gabarito !== 'ANULADA') {
                avaliadas++;
                if (valor === gabarito) {
                    acertos++;
                } else {
                    erros++;
                }
            }
        }
    }

    const totalRespondidas = Object.keys(dados).length;
    const taxa = avaliadas > 0 ? Math.round((acertos / avaliadas) * 100) : 0;

    const elAcertos = document.getElementById('stat-acertos');
    const elErros = document.getElementById('stat-erros');
    const elTaxa = document.getElementById('stat-taxa');
    const elResp = document.getElementById('stat-respondidas');

    if (elAcertos) elAcertos.textContent = acertos;
    if (elErros) elErros.textContent = erros;
    if (elTaxa) elTaxa.textContent = taxa + '%';
    if (elResp) elResp.textContent = `${totalRespondidas} / ${total}`;
}

function toggleResposta(qId) {
    const box = document.getElementById('box_' + qId);
    if (box) {
        const isHidden = (box.style.display === 'none' || box.style.display === '');
        box.style.display = isHidden ? 'block' : 'none';
        if (isHidden) {
            revelarFeedbackGabarito(qId);
        }
    }
}

function carregarRespostas() {
    const dados = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    let respondidas = 0;

    for (const [qId, valor] of Object.entries(dados)) {
        const radio = document.querySelector(`input[name="${qId}"][value="${valor}"]`);
        if (radio) {
            radio.checked = true;
            respondidas++;
            const gabarito = radio.getAttribute('data-gabarito');
            atualizarEstiloQuestao(qId, valor, gabarito);
        }
    }
    atualizarBarra(respondidas);
    atualizarEstatisticas();
}

function salvarResposta(qId, valor, gabarito) {
    const dados = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    dados[qId] = valor;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(dados));
    
    // Rastreamento de evento no Google Analytics 4
    if (typeof gtag === 'function') {
        gtag('event', 'resposta_questao', {
            'questao_id': qId,
            'acertou': (valor === gabarito)
        });
    }
    
    atualizarEstiloQuestao(qId, valor, gabarito);
    atualizarBarra(Object.keys(dados).length);
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

// Modal de Confirmação para Limpar Respostas
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

// Lógica de Alternância de Tema Instantânea (Zero Lag / Zero Flash)
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

// Funções do Modal de Apoio / Pix
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

// Rastreamento de Doação Ko-fi (Abertura Direta em Nova Aba)
function registrarCliqueKofi() {
    if (typeof gtag === 'function') {
        gtag('event', 'clique_kofi_doacao', {
            'event_category': 'Engajamento',
            'event_label': 'Botao_Apoio_Kofi'
        });
    }
}

// Funções do Modal de Aviso sobre IA e Gabarito
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
    }
});

// Inicializa o tema e carrega as respostas ao abrir a página
initTheme();
window.addEventListener('DOMContentLoaded', () => {
    carregarRespostas();
});

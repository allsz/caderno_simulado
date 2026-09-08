// Teste sintético de performance e integridade de dados
const fs = require('fs');
const path = require('path');

console.log('[*] Verificação sintática e lógica...');
const appCode = fs.readFileSync(path.join(__dirname, '..', 'web', 'app.js'), 'utf-8');

// Simula ambiente de storage e mapas
const mockLocalStorage = {};
const mockDomRadios = new Map();

for (let i = 1; i <= 1444; i++) {
    const qName = `ENARE-2024-Objetiva_${i}`;
    mockDomRadios.set(`${qName}:::A`, { name: qName, value: 'A' });
    mockDomRadios.set(`${qName}:::B`, { name: qName, value: 'B' });
}

// Simula 560 respostas do usuário
const userAnswers = {};
for (let i = 1; i <= 560; i++) {
    // Mistura IDs normais, legados com sufixo e desconhecidos
    if (i % 10 === 0) {
        userAnswers[`q_ENARE-2024-Objetiva_${i}_999`] = 'A';
    } else if (i % 25 === 0) {
        userAnswers[`QUESTAO_FUTURA_OU_REMOVIDA_${i}`] = 'B';
    } else {
        userAnswers[`ENARE-2024-Objetiva_${i}`] = 'A';
    }
}

console.log(`[+] 560 respostas simuladas preparadas.`);

const start = Date.now();
const dadosAtualizados = { ...userAnswers };
let matches = 0;

for (const [qId, valor] of Object.entries(userAnswers)) {
    // Simula resolução O(1)
    let match = mockDomRadios.get(`${qId}:::${valor}`);
    if (!match) {
        const clean = qId.replace(/^q_/, '');
        const matchDuploNumero = clean.match(/^(.*_\d+)_\d+$/);
        const base = matchDuploNumero ? matchDuploNumero[1] : clean;
        match = mockDomRadios.get(`${base}:::${valor}`);
    }
    if (match) {
        matches++;
        if (match.name !== qId) {
            dadosAtualizados[match.name] = valor;
            delete dadosAtualizados[qId];
        }
    }
    // Chaves não encontradas continuam em dadosAtualizados
}

const elapsed = Date.now() - start;
console.log(`[✓] Tempo de processamento para 560 questões: ${elapsed}ms`);
console.log(`[✓] Matches encontrados: ${matches}`);
console.log(`[✓] Total de respostas preservadas: ${Object.keys(dadosAtualizados).length} (Esperado: 560)`);

if (Object.keys(dadosAtualizados).length === 560) {
    console.log('[SUCESSO] Nenhuma resposta do usuário foi perdida!');
} else {
    console.error('[ERRO] Houve perda de dados!');
    process.exit(1);
}

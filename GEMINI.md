# Diretrizes Globais do Projeto (Caderno de Questões Médicas)

Este documento define padrões inegociáveis de design (UI/UX), formatação de explicações médicas por IA, políticas de API e arquitetura do projeto.

---

## 1. Padrões Visuais e de UI (Design System)

Toda alteração de interface ou novo elemento visual deve seguir rigorosamente:

* **Ícones Minimalistas:**
  * Usar sempre ícones de estilo *outline* (linhas limpas e finas, sem preenchimentos pesados).
  * Preferência por SVG inline com `stroke-width="1.75"` ou `stroke-width="2"`, viewBox `0 0 24 24`.
  * Nunca usar ícones coloridos, excessivamente grossos ou emojis em botões de ação do sistema.

* **Menus Flutuantes, Modais e Dropdowns:**
  * **Bordas Arredondadas:** Sempre usar `border-radius: 12px` ou `16px` (nunca cantos retos ou quadrados padrão de navegador).
  * **Acabamento idêntico ao botão "Exibir":** 
    * Fundo sutil com blur translúcido (`backdrop-filter: blur(12px)` e background com `rgba` correspondente ao tema).
    * Borda suave de 1px com transparência (`rgba(..., 0.1)`).
    * Sombra difusa e elegante (`box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)`).
  * **Animações suaves:** Transições de abertura com `cubic-bezier(0.16, 1, 0.3, 1)` e duração de ~150ms a 200ms.

---

## 2. Política de IA e Respostas Clínicas

* **Uso exclusivo da API Paga (Robustez Máxima):**
  * Usar estritamente a chave primária `GEMINI_API_KEY` com modelos de ponta (`gemini-2.5-flash`, `gemini-1.5-pro` ou modelos premium equivalentes).
  * **SEM FALLBACK PARA CHAVE GRATUITA:** Não alternar automaticamente para `GEMINI_API_KEY_FREE` ou tiers gratuitos para evitar degradação na qualidade da resposta médica.
  * **Tratamento de cota/crédito:** Se os créditos da API se esgotarem ou a cota bater no limite, a execução deve **interromper a chamada**, salvar o progresso atômico no cache e emitir um relatório claro:
    * `"Atenção: Os créditos da API se esgotaram. Questões processadas: X / Faltaram: Y questões."`

---

## 3. Padrão de Negrito nas Explicações Médicas (Clean & Elegante)

As justificativas geradas ou editadas devem ter uma leitura fluida e limpa, inspirada nas diretrizes do print de referência:

* **Headers da Resposta:** Em negrito simples (nunca usar `#` ou markdown headers pesados):
  * `**Justificativa Médica:**`
  * `**Raciocínio Clínico e Fisiopatológico:**`
  * `**Análise das alternativas incorretas:**` (ou análise de alternativas)
* **Nas Alternativas:** Apenas o identificador e status no início:
  * `• **Alternativa A: Correta.** [texto normal sem negrito adicional]`
  * `• **Alternativa B: Incorreta.** [texto normal sem negrito adicional]`
* **No Corpo da Explicação (Raciocínio Clínico):**
  * **Negrito ultra-cirúrgico:** No máximo 1 a 2 termos médicos indispensáveis em todo o texto (por exemplo, apenas o nome da patologia central como **invaginação intestinal** ou agente etiológico determinante).
  * **Análise das alternativas:** NENHUM negrito no texto explicativo de cada alternativa (apenas o `• **Alternativa X: Incorreta.**` no início). Todo o resto em texto normal.

---

## 4. Arquitetura e Integridade de Arquivos

* O arquivo final de produção para navegação é única e exclusivamente o `index.html` na raiz.
* **Nunca** recriar arquivos redundantes como `saida/caderno_interativo.html` ou `saida/caderno_de_questoes_estudo.md`.
* Todas as manipulações de banco de dados devem ocorrer no `saida/banco_questoes_cache.json` utilizando escrita atômica para prevenir corrupção de dados.


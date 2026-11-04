---
name: adicionar-prova
description: >-
  Adiciona novas provas médicas (ENARE, Revalida, etc.) ao caderno interativo usando Gemini Vision.
  Mantém quebras de linha e estrutura idênticas ao original, extrai imagens, valida gabaritos oficiais,
  classifica com taxonomia canônica e gera explicações no padrão do projeto.
---

# Skill: Adicionar Nova Prova ao Caderno

Esta skill é acionada quando o usuário solicita adicionar uma nova prova e gabarito (ex: *"Adicione a prova do Revalida 2026/2"* ou *"Adicione a prova do ENARE 2026"*).

Ela executa o pipeline ponta a ponta garantindo integridade visual, taxonômica e médica.

---

## Fluxo de Execução Passo a Passo

### Passo 1: Localização dos Arquivos de Entrada
1. Verificar a pasta `provas/` para localizar:
   * O PDF do Caderno de Questões (ex: `ENARE-2026-Objetiva.pdf`).
   * O PDF do Gabarito Oficial Definitivo (ex: `GABARITO_ENARE_2026.pdf`).
2. Se o gabarito for uma folha de imagem/escaneada, utilizar o extrator vision em `core/extrair_gabarito_vision.py`.

---

### Passo 2: Extração Fiel com Gemini Vision
1. Para cada página da prova que contenha diagramas, ECGs, tabelas ou formatação complexa de colunas:
   * Renderizar a página em alta resolução como imagem.
   * Usar o Gemini Vision com a chave paga primária (`GEMINI_API_KEY`).
2. **Diretrizes Estritas de Extração de Texto:**
   * **Quebras de Linha e Parágrafos Idênticos:** Preservar a exata estrutura do texto impresso na prova. Se o caso clínico tem quebra de linha após valores laboratoriais, mantenha a quebra.
   * **Posição Exata das Imagens:** Recortar a região da imagem/figura/tabela e salvar em `saida/imagens/` com o padrão de nomenclatura `{nome_prova}_{num_questao}.png`. Vincular o caminho relativo no campo `"imagem"` da questão.
   * **Alternativas:** Manter as letras `A)`, `B)`, `C)`, `D)` (e `E)` quando houver) com seu texto exato.

---

### Passo 3: Associação e Validação do Gabarito Oficial
1. Mapear o gabarito de cada questão (1 a 100).
2. Se alguma questão foi anulada pela banca, registrar expressamente:
   * `"gabarito": "ANULADA"`
3. Se o gabarito foi alterado por recurso, adotar estritamente a alternativa final definitiva.

---

### Passo 4: Classificação Médica (Taxonomia Canônica)
1. Para cada questão extraída, definir:
   * **Especialidade (Grande Área):** Exatamente uma das 5 canônicas:
     * `Clínica Médica`
     * `Cirurgia Geral`
     * `Pediatria`
     * `Ginecologia e Obstetrícia`
     * `Medicina Preventiva e Social / MFC`
   * **Tema e Subtema:** Usar o mapa de padronização em `core/sanitizar_taxonomia.py` e `core/categorizador_ia.py` (evitar termos genéricos como "Diversos", "Geral" ou "Outros").

---

### Passo 5: Geração de Respostas Clínicas por IA
1. Utilizar **exclusivamente a chave paga** (`GEMINI_API_KEY`) no modelo robusto (`gemini-2.5-flash` ou superior).
2. **NÃO USAR FALLBACK PARA CHAVE GRATUITA.**
   * Caso os créditos se esgotem ou ocorra erro de cota (429/402):
     * Salvar imediatamente todo o progresso no cache `saida/cache_explicacoes.json`.
     * Interromper o lote e informar ao usuário:
       `"Os créditos da API GEMINI_API_KEY se esgotaram. Questões processadas: X / Faltaram Y questões."`
3. **Padrão de Negrito Obrigatório (Clean):**
   * **Headers:**
     `**Justificativa Médica:**`
     `**Raciocínio Clínico e Fisiopatológico:**`
     `**Análise das alternativas incorretas:**`
   * **Corpo do Raciocínio Clínico:** No máximo **1 a 2 termos médicos indispensáveis** em negrito em todo o texto (ex: nome da patologia central).
   * **Análise das Alternativas:** Apenas o identificador em negrito:
     `• **Alternativa A: Correta.** [análise em texto normal, sem negrito extra]`
     `• **Alternativa B: Incorreta.** [análise em texto normal, sem negrito extra]`
     *(Nenhum negrito adicional dentro do texto de análise de cada alternativa)*.

---

### Passo 6: Integração no Banco e Recompilação
1. Fazer o merge atômico das novas questões em `saida/banco_questoes_cache.json`.
2. Salvar as explicações em `saida/cache_explicacoes.json`.
3. Executar a recompilação limpa:
   ```powershell
   python recompilar.py
   ```
4. Confirmar que apenas o `index.html` foi atualizado e que nenhum arquivo redundante foi recriado.


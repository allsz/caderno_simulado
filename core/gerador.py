from html import escape as html_escape
from pathlib import Path

from .utils import obter_base64_imagem, formatar_texto_fluido


def exportar_caderno_markdown(banco_questoes, caminho_saida: Path, cache_explicacoes: dict = None, tem_api_key: bool = False):
    """Gera um arquivo Markdown organizado hierarquicamente para estudo com respostas colapsáveis."""
    if cache_explicacoes is None:
        cache_explicacoes = {}
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("# CADERNO DE QUESTÕES CATEGORIZADAS PARA ESTUDO\n")
        f.write("> **Material de Simulado e Prática de Residência Médica / Revalidação com Gabarito e Comentários**\n\n")
        f.write("---\n\n")
        
        for esp in sorted(banco_questoes.keys()):
            f.write(f"# 📂 {esp.upper()}\n\n")
            for tema in sorted(banco_questoes[esp].keys()):
                f.write(f"## 📌 Tema: {tema}\n\n")
                for subtema in sorted(banco_questoes[esp][tema].keys()):
                    lista_q = banco_questoes[esp][tema][subtema]
                    f.write(f"### 🔖 Subtema: {subtema} ({len(lista_q)} questões)\n\n")
                    
                    for q in lista_q:
                        q_key = f"{q['origem']}_{q['numero']}"
                        dados_cache = cache_explicacoes.get(q_key, {})
                        gab = q.get("gabarito", "N/A")
                        if gab == "N/A" and dados_cache.get("gabarito"):
                            gab = dados_cache.get("gabarito")
                            
                        exp = dados_cache.get("explicacao")
                        if not exp:
                            if tem_api_key:
                                if gab != "N/A":
                                    exp = f"Gabarito oficial extraído do PDF da prova: **{gab}**. (O comentário detalhado por IA para esta questão está sendo processado)."
                                else:
                                    exp = "Gabarito não fornecido no PDF. (O comentário por IA para esta questão está sendo processado)."
                            else:
                                if gab != "N/A":
                                    exp = f"Gabarito oficial extraído do PDF da prova: **{gab}**. (Configure sua GEMINI_API_KEY no arquivo .env para gerar justificativas clínicas por IA)."
                                else:
                                    exp = "Gabarito não fornecido no PDF. (Configure sua GEMINI_API_KEY no arquivo .env para gerar justificativas clínicas por IA)."
                        
                        f.write(f"#### **[{q['origem']} | Questão {q['numero']}]**\n\n")
                        enunc_md = formatar_texto_fluido(q['enunciado'], modo_html=False)
                        f.write(f"{enunc_md}\n\n")
                        
                        imgs = q.get("imagens") or ([q.get("imagem")] if q.get("imagem") else [])
                        if imgs:
                            for img_path in imgs:
                                f.write(f"![Figura da Questão]({img_path})\n\n")
                        
                        if q['alternativas']:
                            for letra, alt in sorted(q['alternativas'].items()):
                                f.write(f"- [ ] **({letra})** {alt}\n")
                            f.write("\n")
                            
                        f.write("<details>\n")
                        f.write(f"<summary><b>👁️ Ver Resposta e Comentário (Gabarito: {gab})</b></summary>\n\n")
                        f.write(f"> **Gabarito Oficial:** Alternativa **({gab})**\n>\n")
                        f.write(f"> **Comentário Médica:** {exp}\n")
                        f.write("</details>\n\n")
                        f.write("---\n\n")


def exportar_caderno_html(banco_questoes, caminho_saida: Path, cache_explicacoes: dict = None, tem_api_key: bool = False, base_dir: Path = None):
    """Gera um simulado interativo em HTML usando o template desacoplado de web/."""
    if cache_explicacoes is None:
        cache_explicacoes = {}
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    
    total_questoes_com_alt = 0
    for esp in banco_questoes:
        for tema in banco_questoes[esp]:
            for subtema in banco_questoes[esp][tema]:
                for q in banco_questoes[esp][tema][subtema]:
                    if q['alternativas']:
                        total_questoes_com_alt += 1

    # Carrega assets em Base64
    img_dark_b64 = obter_base64_imagem("src/dark-mode.png", base_dir=base_dir)
    img_claro_b64 = obter_base64_imagem("src/icons8-modo-claro-78.png", base_dir=base_dir)
    img_kofi_badge_b64 = obter_base64_imagem("src/ffbe___cloud_strife_gif_3_by_zerolympiustrife_dbuxzfm.gif", base_dir=base_dir)
    img_kofi_logo_b64 = obter_base64_imagem("src/logomarkLogo.png", base_dir=base_dir)
    img_aviso_b64 = obter_base64_imagem("src/aviso.png", base_dir=base_dir)
    img_lampada_b64 = obter_base64_imagem("src/lampada.png", base_dir=base_dir)
    img_check_b64 = obter_base64_imagem("src/check.png", base_dir=base_dir)
    img_lixeira_b64 = obter_base64_imagem("src/lixeira.png", base_dir=base_dir)
    img_atencao_b64 = obter_base64_imagem("src/atenção.png", base_dir=base_dir)
    img_pix_b64 = obter_base64_imagem("src/pix.png", base_dir=base_dir)
    img_qrcode_b64 = obter_base64_imagem("src/qr-code.png", base_dir=base_dir)
    favicon_b64 = obter_base64_imagem("src/favicon.svg", base_dir=base_dir)

    # Carrega CSS e JS dos arquivos modulares
    caminho_css = base_dir / "web" / "styles.css"
    caminho_js = base_dir / "web" / "app.js"
    caminho_template = base_dir / "web" / "template.html"

    css_content = caminho_css.read_text(encoding="utf-8") if caminho_css.exists() else ""
    js_content = caminho_js.read_text(encoding="utf-8") if caminho_js.exists() else ""
    template_html = caminho_template.read_text(encoding="utf-8") if caminho_template.exists() else ""

    # Gera HTML dos cards de questões
    html_parts = []
    q_global_idx = 0
    for esp in sorted(banco_questoes.keys()):
        esp_attr = html_escape(esp)
        for tema in sorted(banco_questoes[esp].keys()):
            tema_attr = html_escape(tema)
            for subtema in sorted(banco_questoes[esp][tema].keys()):
                subtema_attr = html_escape(subtema)
                lista_q = banco_questoes[esp][tema][subtema]
                
                for q in lista_q:
                    q_global_idx += 1
                    q_id = f"q_{q['origem']}_{q['numero']}"
                    q_key = f"{q['origem']}_{q['numero']}"
                    dados_cache = cache_explicacoes.get(q_key, {})
                    gab = q.get("gabarito", "N/A")
                    if gab == "N/A" and dados_cache.get("gabarito"):
                        gab = dados_cache.get("gabarito")
                        
                    exp = dados_cache.get("explicacao")
                    if not exp:
                        if tem_api_key:
                            if gab != "N/A":
                                exp = f"Gabarito oficial extraído do PDF da prova: <strong>{gab}</strong>. (O comentário detalhado por IA para esta questão está sendo processado)."
                            else:
                                exp = "Gabarito não fornecido no PDF da prova. (O comentário por IA para esta questão está sendo processado)."
                        else:
                            if gab != "N/A":
                                exp = f"Gabarito oficial extraído do PDF da prova: <strong>{gab}</strong>. (Configure sua GEMINI_API_KEY no arquivo .env para gerar comentários detalhados por IA)."
                            else:
                                exp = "Gabarito não fornecido no PDF da prova. (Configure sua GEMINI_API_KEY no arquivo .env para gerar gabarito e explicação por IA)."

                    enunc_html = formatar_texto_fluido(q['enunciado'], modo_html=True)
                    html_parts.append(f"<div class='card-questao' id='card_{q_id}' data-especialidade='{esp_attr}' data-tema='{tema_attr}' data-subtema='{subtema_attr}' data-idx='{q_global_idx}'>\n")
                    html_parts.append(f"<span class='tag-origem'>{q['origem']} | Questão {q['numero']} • <span class='tag-tema-destaque'>{tema}</span></span>\n")
                    html_parts.append(f"<div class='enunciado'>{enunc_html}</div>\n")
                    
                    imgs = q.get("imagens") or ([q.get("imagem")] if q.get("imagem") else [])
                    if imgs:
                        html_parts.append("<div class='questao-imagem-container'>\n")
                        for img_src in imgs:
                            num_q = q["numero"]
                            img_b64 = obter_base64_imagem(img_src, base_dir=base_dir)
                            html_parts.append(f"  <img src='{img_b64}' alt='Figura da Questão {num_q}' class='img-questao' loading='lazy' decoding='async'>\n")
                        html_parts.append("</div>\n")
                    
                    if q['alternativas']:
                        html_parts.append("<div class='alternativas-container'>\n")
                        for letra, alt in sorted(q['alternativas'].items()):
                            alt_html = html_escape(formatar_texto_fluido(alt, modo_html=False))
                            html_parts.append(f"<label class='alternativa' id='label_{q_id}_{letra}'>")
                            html_parts.append(f"<input type='radio' name='{q_id}' value='{letra}' data-gabarito='{gab}' onchange='salvarResposta(\"{q_id}\", \"{letra}\", \"{gab}\")'>")
                            html_parts.append(f"<span><strong>({letra})</strong> {alt_html}</span></label>\n")
                        html_parts.append("</div>\n")
                        
                    html_parts.append(f"<button type='button' class='btn-resposta' onclick='toggleResposta(\"{q_id}\")'>&#10022; Ver Gabarito e Comentário</button>\n")
                    html_parts.append(f"<div class='gabarito-box' id='box_{q_id}' style='display: none;'>\n")
                    html_parts.append(f"  <span class='badge-gabarito'>Gabarito Oficial: Alternativa ({gab})</span>\n")
                    html_parts.append(f"  <div class='explicacao-texto'><strong>Justificativa Médica:</strong><br>{exp}</div>\n")
                    html_parts.append("</div>\n")
                    
                    html_parts.append("</div>\n\n")

    questoes_html = "".join(html_parts)

    # Injeta no template final (com suporte a formatação flexível do VS Code)
    import re
    html_final = template_html
    substituicoes = {
        "FAVICON_B64": favicon_b64,
        "CSS_CONTENT": css_content,
        "IMG_AVISO_B64": img_aviso_b64,
        "IMG_DARK_B64": img_dark_b64,
        "IMG_CLARO_B64": img_claro_b64,
        "IMG_KOFI_BADGE_B64": img_kofi_badge_b64,
        "IMG_KOFI_LOGO_B64": img_kofi_logo_b64,
        "IMG_LAMPADA_B64": img_lampada_b64,
        "IMG_CHECK_B64": img_check_b64,
        "IMG_LIXEIRA_B64": img_lixeira_b64,
        "IMG_ATENCAO_B64": img_atencao_b64,
        "IMG_PIX_B64": img_pix_b64,
        "IMG_QRCODE_B64": img_qrcode_b64,
        "TOTAL_QUESTOES": str(total_questoes_com_alt),
        "QUESTOES_HTML": questoes_html,
        "JS_CONTENT": js_content,
    }

    for chave, valor in substituicoes.items():
        # Substitui tanto {{CHAVE}} quanto {{ CHAVE }} ou { { \n CHAVE \n } }
        padrao = re.compile(r'\{\s*\{\s*' + re.escape(chave) + r'\s*\}\s*\}')
        html_final = padrao.sub(lambda _: valor, html_final)

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html_final)

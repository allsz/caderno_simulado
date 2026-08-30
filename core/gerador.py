from html import escape as html_escape
from pathlib import Path
import re

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
                    f.write(f"### Subtema: {subtema} ({len(lista_q)} questões)\n\n")
                    
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
                        imgs = q.get("imagens") or ([q.get("imagem")] if q.get("imagem") else [])
                        enunc_raw = q.get('enunciado', '')
                        if imgs and re.search(r'\[(?:IMAGEM|FIGURA|TABELA)\]', enunc_raw, flags=re.IGNORECASE):
                            partes = re.split(r'\[(?:IMAGEM|FIGURA|TABELA)\]', enunc_raw, flags=re.IGNORECASE)
                            bloco_imgs = "\n\n".join([f"![Figura da Questão]({img_path})" for img_path in imgs])
                            md_completo = []
                            for i, parte in enumerate(partes):
                                if parte.strip():
                                    md_completo.append(formatar_texto_fluido(parte, modo_html=False))
                                if i == 0 and bloco_imgs:
                                    md_completo.append(bloco_imgs)
                            f.write("\n\n".join(md_completo) + "\n\n")
                        else:
                            enunc_md = formatar_texto_fluido(enunc_raw, modo_html=False)
                            f.write(f"{enunc_md}\n\n")
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


def extrair_metadados_origem(origem: str):
    """Extrai banca (ENARE/REVALIDA), ano, edição (1/2/Única) e rótulo amigável da string de origem."""
    origem_str = origem or ""
    origem_upper = origem_str.upper()
    banca = "ENARE" if "ENARE" in origem_upper else "REVALIDA"
    ano_match = re.search(r'(202\d)', origem_str)
    ano = ano_match.group(1) if ano_match else "Outros"
    
    if banca == "ENARE":
        edicao = "Única"
        rotulo_edicao = f"ENARE {ano}"
    else:
        if "_2_" in origem_str or "-2_" in origem_str or "_2" in origem_str:
            edicao = "2"
            rotulo_edicao = f"REVALIDA {ano}.2 (Prova 2)"
        elif "_1_" in origem_str or "-1_" in origem_str or "_1" in origem_str or "caderno_1" in origem_str:
            edicao = "1"
            rotulo_edicao = f"REVALIDA {ano}.1 (Prova 1)"
        else:
            edicao = "1"
            rotulo_edicao = f"REVALIDA {ano} (Prova 1)"
            
    return banca, ano, edicao, rotulo_edicao


def gerar_cards_questoes_html(banco_questoes, cache_explicacoes=None, tem_api_key=False, base_dir=None):
    """Gera blocos HTML para cada questão agrupada hierarquicamente."""
    if cache_explicacoes is None:
        cache_explicacoes = {}
    
    html_parts = []
    q_global_idx = 0
    
    for esp in sorted(banco_questoes.keys()):
        for tema in sorted(banco_questoes[esp].keys()):
            for subtema in sorted(banco_questoes[esp][tema].keys()):
                for q in banco_questoes[esp][tema][subtema]:
                    q_global_idx += 1
                    q_id = f"{q['origem']}_{q['numero']}".replace(" ", "_").replace(".", "_")
                    esp_attr = html_escape(esp, quote=True)
                    tema_attr = html_escape(tema, quote=True)
                    subtema_attr = html_escape(subtema, quote=True)
                    
                    banca, ano, edicao, rotulo_edicao = extrair_metadados_origem(q.get('origem', ''))
                    banca_attr = html_escape(banca, quote=True)
                    ano_attr = html_escape(ano, quote=True)
                    edicao_attr = html_escape(edicao, quote=True)
                    rotulo_attr = html_escape(rotulo_edicao, quote=True)
                    num_attr = html_escape(str(q.get('numero', '')), quote=True)
                    origem_attr = html_escape(str(q.get('origem', '')), quote=True)
                    
                    dados_cache = cache_explicacoes.get(f"{q['origem']}_{q['numero']}", {})
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

                    html_parts.append(f"<div class='card-questao' id='card_{q_id}' data-especialidade='{esp_attr}' data-tema='{tema_attr}' data-subtema='{subtema_attr}' data-banca='{banca_attr}' data-ano='{ano_attr}' data-edicao='{edicao_attr}' data-rotulo-edicao='{rotulo_attr}' data-numero='{num_attr}' data-origem='{origem_attr}' data-idx='{q_global_idx}'>\n")
                    html_parts.append("  <div class='card-header-tags'>\n")
                    html_parts.append(f"    <span class='tag-origem'>{q['origem']} | Questão {q['numero']}</span>\n")
                    html_parts.append(f"    <span class='tag-tema'>{tema}</span>\n")
                    html_parts.append(f"    <span class='tag-subtema'>{subtema}</span>\n")
                    html_parts.append("  </div>\n")
                    
                    imgs = q.get("imagens") or ([q.get("imagem")] if q.get("imagem") else [])
                    img_container_html = ""
                    if imgs:
                        img_parts = ["  <div class='questao-imagem-container'>\n"]
                        for img_src in imgs:
                            num_q = q["numero"]
                            img_b64 = obter_base64_imagem(img_src, base_dir=base_dir)
                            img_parts.append(f"    <img src='{img_b64}' alt='Figura da Questão {num_q}' class='img-questao' loading='lazy' decoding='async'>\n")
                        img_parts.append("  </div>\n")
                        img_container_html = "".join(img_parts)

                    enunc_raw = q.get('enunciado', '')
                    tem_placeholder = bool(imgs and re.search(r'\[(?:IMAGEM|FIGURA|TABELA)\]', enunc_raw, flags=re.IGNORECASE))

                    if tem_placeholder:
                        partes = re.split(r'\[(?:IMAGEM|FIGURA|TABELA)\]', enunc_raw, flags=re.IGNORECASE)
                        for i, parte in enumerate(partes):
                            if parte.strip():
                                p_html = formatar_texto_fluido(parte, modo_html=True)
                                html_parts.append(f"  <div class='enunciado'>{p_html}</div>\n")
                            if i == 0 and img_container_html:
                                html_parts.append(img_container_html)
                    else:
                        enunc_html = formatar_texto_fluido(enunc_raw, modo_html=True)
                        html_parts.append(f"  <div class='enunciado'>{enunc_html}</div>\n")
                        if img_container_html:
                            html_parts.append(img_container_html)
                    
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

    return "".join(html_parts)


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

    questoes_html = gerar_cards_questoes_html(banco_questoes, cache_explicacoes=cache_explicacoes, tem_api_key=tem_api_key, base_dir=base_dir)

    # Injeta no template final (com suporte a formatação flexível do VS Code)
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
        padrao = re.compile(r'\{\s*\{\s*' + re.escape(chave) + r'\s*\}\s*\}')
        html_final = padrao.sub(lambda _: valor, html_final)

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html_final)

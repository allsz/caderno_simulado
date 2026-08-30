"""
Módulo Core para extração, classificação, enriquecimento com IA e geração
do Caderno de Questões Médicas e Simulado Interativo.
"""

from .utils import (
    obter_base64_imagem,
    formatar_texto_fluido,
    salvar_json_atomico,
    carregar_json_seguro,
    validar_schema_questao,
)
from .validador import auditar_banco_questoes
from .classificador import TAXONOMIA_MEDICA, classificar_questao
from .extrator import (
    carregar_mapa_gabaritos_revalida,
    extrair_gabarito_pdf,
    extrair_texto_pdf,
    extrair_alternativas,
    extrair_questoes_do_texto,
)
from .gemini_ia import (
    gerar_explicacao_gemini,
    carregar_cache_explicacoes,
    salvar_cache_explicacoes,
)
from .gerador import (
    exportar_caderno_markdown,
    exportar_caderno_html,
)

__all__ = [
    "obter_base64_imagem",
    "formatar_texto_fluido",
    "salvar_json_atomico",
    "carregar_json_seguro",
    "validar_schema_questao",
    "auditar_banco_questoes",
    "TAXONOMIA_MEDICA",
    "classificar_questao",
    "carregar_mapa_gabaritos_revalida",
    "extrair_gabarito_pdf",
    "extrair_texto_pdf",
    "extrair_alternativas",
    "extrair_questoes_do_texto",
    "gerar_explicacao_gemini",
    "carregar_cache_explicacoes",
    "salvar_cache_explicacoes",
    "exportar_caderno_markdown",
    "exportar_caderno_html",
]


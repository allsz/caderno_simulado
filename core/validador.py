"""
Módulo de Validação e Auditoria de Integridade do Banco de Questões Médicas.
"""

import re
from typing import Dict, List, Tuple


def auditar_banco_questoes(questoes: List[dict]) -> Tuple[bool, Dict[str, any]]:
    """
    Executa auditoria completa de schema, consistência de gabaritos e heurísticas clínicas
    para prevenir erros de categorização ou formatação.
    """
    relatorio = {
        "total_questoes": len(questoes),
        "erros_schema": [],
        "alertas_categorizacao": [],
        "estatisticas": {
            "especialidades": {},
            "bancas": {},
            "sem_gabarito": 0,
            "anuladas": 0
        }
    }

    # Heurísticas de termos clínicos para detecção precoce de classificação trocada
    regras_heuristica = [
        {
            "termos": [r"\bvaginose\b", r"\bleucorreia\b", r"\bcolo uterino\b", r"\bclue cells\b", r"\bcandidíase vaginal\b", r"\bwhiff test\b"],
            "especialidade_esperada": "Ginecologia e Obstetrícia",
            "especialidades_incompativeis": ["Clínica Médica", "Cirurgia Geral"],
            "motivo": "Termos clássicos de Vulvovaginites/Ginecologia encontrados em outra especialidade"
        },
        {
            "termos": [r"\blactente\b", r"\brecém-nascido\b", r"\bpuericultura\b", r"\bescore-z\b", r"\bapgar\b"],
            "especialidade_esperada": "Pediatria",
            "especialidades_incompativeis": ["Ginecologia e Obstetrícia", "Cirurgia Geral"],
            "motivo": "Termos típicos de Pediatria/Neonatologia encontrados fora da especialidade infantil"
        }
    ]

    for q in questoes:
        q_id = f"{q.get('origem', 'ORIGEM_DESCONHECIDA')}_{q.get('numero', '?')}"
        esp = q.get("especialidade", "N/A")
        tema = q.get("tema", "N/A")
        gab = str(q.get("gabarito", "")).strip().upper()
        enunc = str(q.get("enunciado", "")).lower()
        alts = q.get("alternativas", {})

        # 1. Contadores
        relatorio["estatisticas"]["especialidades"][esp] = relatorio["estatisticas"]["especialidades"].get(esp, 0) + 1
        banca = "ENARE" if "ENARE" in q_id.upper() else "REVALIDA"
        relatorio["estatisticas"]["bancas"][banca] = relatorio["estatisticas"]["bancas"].get(banca, 0) + 1
        
        if not gab or gab == "N/A":
            relatorio["estatisticas"]["sem_gabarito"] += 1
        if gab == "ANULADA":
            relatorio["estatisticas"]["anuladas"] += 1

        # 2. Validação de Schema
        if not alts or len(alts) < 2:
            relatorio["erros_schema"].append(f"[{q_id}] Alternativas ausentes ou insuficientes (< 2)")
        if gab not in ["A", "B", "C", "D", "E", "ANULADA", "N/A"]:
            relatorio["erros_schema"].append(f"[{q_id}] Gabarito inválido ou inesperado: '{gab}'")
        if not enunc.strip():
            relatorio["erros_schema"].append(f"[{q_id}] Enunciado vazio")

        # 3. Heurística de Categorização Clínica
        for regra in regras_heuristica:
            if esp in regra["especialidades_incompativeis"]:
                for termo in regra["termos"]:
                    if re.search(termo, enunc):
                        relatorio["alertas_categorizacao"].append({
                            "id": q_id,
                            "especialidade_atual": esp,
                            "tema_atual": tema,
                            "sugestao": regra["especialidade_esperada"],
                            "motivo": f"{regra['motivo']} (Termo detectado: '{termo}')"
                        })
                        break

    valido = len(relatorio["erros_schema"]) == 0
    return valido, relatorio

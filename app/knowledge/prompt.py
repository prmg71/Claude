"""Renderização da Base de Conhecimento para o prompt do LLM (RAG)."""
from __future__ import annotations

from app import config
from app.knowledge.models import BaseConhecimento


def _render_regra(idx: int, regra) -> str:
    linhas = [f"{idx}. {regra.topico} (severidade: {regra.severidade})"]
    if regra.texto_padrao:
        linhas.append(f"   Texto padrão: {regra.texto_padrao}")
    if regra.limites:
        linhas.append("   Limites: " + "; ".join(regra.limites))
    if regra.flexibilidades:
        linhas.append("   Flexibilidades: " + "; ".join(regra.flexibilidades))
    if regra.correcoes:
        linhas.append("   Correções/notas: " + "; ".join(regra.correcoes))
    return "\n".join(linhas)


def render_base_conhecimento(base: BaseConhecimento | None) -> str:
    """Gera o bloco de texto da base para injeção no prompt.

    Inclui as regras de cláusula curadas e (se houver) o contrato padrão.
    Retorna string vazia se não houver conhecimento útil.
    """
    if base is None:
        return ""

    partes: list[str] = []

    regras = base.regras_ativas()
    if regras:
        corpo = "\n".join(_render_regra(i, r) for i, r in enumerate(regras, 1))
        partes.append(
            "Regras de cláusula curadas (use-as como critério de conformidade; "
            "sinalize violações de limites e avalie as flexibilidades):\n" + corpo
        )

    if base.contrato_padrao and base.contrato_padrao.texto.strip():
        padrao = base.contrato_padrao.texto.strip()
        partes.append("Contrato padrão (golden) de referência:\n" + padrao)

    bloco = "\n\n".join(partes).strip()
    if not bloco:
        return ""

    if len(bloco) > config.MAX_CHARS_CONHECIMENTO:
        bloco = bloco[: config.MAX_CHARS_CONHECIMENTO] + "\n[...base truncada...]"
    return "=== BASE DE CONHECIMENTO DO TIPO ===\n" + bloco

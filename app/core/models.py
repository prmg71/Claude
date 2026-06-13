"""Modelos pydantic para a saída estruturada da análise."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severidade = Literal["alta", "média", "baixa"]


class Resumo(BaseModel):
    """Resumo dos elementos essenciais do contrato."""

    titulo: str = Field(default="", description="Título ou tipo do contrato")
    cliente: str = Field(
        default="",
        description="Nome do cliente (a contraparte; não o Mercado Eletrônico)",
    )
    partes: list[str] = Field(
        default_factory=list, description="Partes envolvidas no contrato"
    )
    objeto: str = Field(default="", description="Objeto/finalidade do contrato")
    valores: list[str] = Field(
        default_factory=list, description="Valores, preços ou contrapartidas"
    )
    prazos: list[str] = Field(
        default_factory=list, description="Prazos, datas e durações relevantes"
    )
    sintese: str = Field(default="", description="Síntese em texto corrido")


class ComparacaoItem(BaseModel):
    """Um ponto de comparação entre o contrato e as referências/base."""

    aspeto: str = Field(description="Aspeto comparado")
    referencia: str = Field(default="", description="O que as referências exigem/esperam")
    contrato: str = Field(default="", description="O que o contrato estabelece")
    conforme: bool = Field(
        default=False, description="True se o contrato está em conformidade"
    )
    observacao: str = Field(default="", description="Comentário ou divergência")


class Risco(BaseModel):
    """Risco ou alerta identificado no contrato."""

    descricao: str = Field(description="Descrição do risco")
    severidade: Severidade = Field(default="média")
    clausula: str = Field(default="", description="Cláusula/secção relacionada")
    recomendacao: str = Field(default="", description="Ação recomendada")


class AnaliseContrato(BaseModel):
    """Resultado completo da análise de um contrato."""

    resumo: Resumo = Field(default_factory=Resumo)
    comparacao: list[ComparacaoItem] = Field(default_factory=list)
    riscos: list[Risco] = Field(default_factory=list)

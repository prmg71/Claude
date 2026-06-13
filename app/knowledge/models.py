"""Modelos da Base de Conhecimento (estruturada por cláusula, versionada)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severidade = Literal["alta", "média", "baixa"]
Origem = Literal["semente", "manual", "feedback"]


class RegraClausula(BaseModel):
    """Conhecimento curado sobre uma cláusula/tópico do contrato.

    Estruturada (decisão do projeto): cada regra separa o texto padrão, os
    limites objetivos, o que é negociável (flexibilidades) e correções/notas.
    """

    id: str = Field(description="Identificador estável da regra")
    topico: str = Field(description="Cláusula/tópico, ex.: 'Reajuste'")
    texto_padrao: str = Field(default="", description="Redação padrão de referência")
    limites: list[str] = Field(
        default_factory=list,
        description="Limiares objetivos, ex.: 'reajuste anual ≤ IPCA'",
    )
    flexibilidades: list[str] = Field(
        default_factory=list,
        description="O que é negociável e em que faixa",
    )
    correcoes: list[str] = Field(
        default_factory=list,
        description="Correções/notas a erros anteriores ou orientações",
    )
    severidade: Severidade = Field(
        default="média", description="Severidade se a regra for violada"
    )
    origem: Origem = Field(default="manual")
    ativo: bool = True

    # Versionamento/autoria por regra.
    versao: int = 1
    autor: str = ""
    criado_em: str = ""       # ISO 8601, preenchido pela camada de serviço
    atualizado_em: str = ""


class ContratoPadrao(BaseModel):
    """O contrato-modelo (golden) que serve de baseline para o tipo."""

    nome_arquivo: str = ""
    texto: str = ""
    versao: int = 1
    autor: str = ""
    atualizado_em: str = ""


class RegistroAuditoria(BaseModel):
    """Trilha de auditoria de mudanças na base (rastreabilidade jurídica)."""

    quando: str            # ISO 8601
    autor: str
    acao: str              # ex.: 'criar_regra', 'editar_regra', 'definir_padrao'
    alvo: str = ""         # id da regra afetada, quando aplicável
    detalhe: str = ""


class BaseConhecimento(BaseModel):
    """Base de Conhecimento completa de um tipo de contrato."""

    tipo_id: str
    contrato_padrao: ContratoPadrao | None = None
    regras: list[RegraClausula] = Field(default_factory=list)
    versao: int = 1                 # versão geral da base (incrementa a cada mudança)
    atualizado_em: str = ""
    historico: list[RegistroAuditoria] = Field(default_factory=list)

    def regras_ativas(self) -> list[RegraClausula]:
        return [r for r in self.regras if r.ativo]

    def obter_regra(self, regra_id: str) -> RegraClausula | None:
        return next((r for r in self.regras if r.id == regra_id), None)

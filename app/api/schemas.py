"""Schemas (entrada/saída) da API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.knowledge.models import Severidade


# ---- Tipos de contrato ----
class TipoOut(BaseModel):
    id: str
    nome: str
    descricao: str
    ativo: bool


# ---- Base de Conhecimento ----
class RegraIn(BaseModel):
    id: str = Field(default="", description="Vazio para criar; preenchido para editar")
    topico: str
    texto_padrao: str = ""
    limites: list[str] = Field(default_factory=list)
    flexibilidades: list[str] = Field(default_factory=list)
    correcoes: list[str] = Field(default_factory=list)
    severidade: Severidade = "média"


class ContratoPadraoIn(BaseModel):
    nome_arquivo: str = ""
    texto: str


# ---- Análises ----
class AnaliseOut(BaseModel):
    id: str
    tipo_id: str
    nome_arquivo: str
    status: str
    erro: str = ""
    tem_relatorio: bool = False
    resultado: dict | None = None
    tokens_total: int | None = None
    custo_usd: float | None = None
    duracao_seg: float | None = None


class FeedbackIn(BaseModel):
    topico: str
    observacao: str
    correto: bool = False
    severidade: Severidade = "média"

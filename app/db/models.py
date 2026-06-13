"""Modelos ORM (tabelas) do banco.

Usa JSON genérico do SQLAlchemy (compatível com SQLite e PostgreSQL)
em vez do JSONB específico do PostgreSQL.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeBaseRow(Base):
    """Base de Conhecimento de um tipo de contrato (serializada em JSON)."""

    __tablename__ = "knowledge_bases"

    tipo_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dados: Mapped[dict] = mapped_column(JSON, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_agora, onupdate=_agora
    )


class Analysis(Base):
    """Uma análise de contrato (assíncrona)."""

    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tipo_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    nome_arquivo: Mapped[str] = mapped_column(String(512), nullable=False)
    caminho_arquivo: Mapped[str] = mapped_column(String(1024), default="")
    # pendente | processando | concluida | erro
    status: Mapped[str] = mapped_column(String(20), default="pendente", index=True)
    resultado: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    caminho_relatorio: Mapped[str] = mapped_column(String(1024), default="")
    erro: Mapped[str] = mapped_column(Text, default="")
    autor: Mapped[str] = mapped_column(String(255), default="")
    # Métricas da análise.
    tokens_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    custo_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    duracao_seg: Mapped[float | None] = mapped_column(Float, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    concluido_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Feedback(Base):
    """Feedback de um curador sobre um achado de análise (ciclo de melhoria)."""

    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    tipo_id: Mapped[str] = mapped_column(String(64), index=True)
    topico: Mapped[str] = mapped_column(String(255), default="")
    observacao: Mapped[str] = mapped_column(Text, default="")
    correto: Mapped[str] = mapped_column(String(5), default="nao")  # sim | nao
    autor: Mapped[str] = mapped_column(String(255), default="")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)

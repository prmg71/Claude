"""Implementação do KnowledgeRepository sobre PostgreSQL (Supabase).

Guarda a BaseConhecimento como JSONB (uma linha por tipo). Preserva a mesma
interface da implementação JSON, então o KnowledgeService funciona sem alteração.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import KnowledgeBaseRow
from app.knowledge.models import BaseConhecimento
from app.knowledge.repository import KnowledgeRepository


class SqlKnowledgeRepository(KnowledgeRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    def existe(self, tipo_id: str) -> bool:
        return self.db.get(KnowledgeBaseRow, tipo_id) is not None

    def carregar(self, tipo_id: str) -> BaseConhecimento:
        row = self.db.get(KnowledgeBaseRow, tipo_id)
        if row is None:
            return BaseConhecimento(tipo_id=tipo_id)
        return BaseConhecimento.model_validate(row.dados)

    def salvar(self, base: BaseConhecimento) -> None:
        dados = base.model_dump()
        row = self.db.get(KnowledgeBaseRow, base.tipo_id)
        if row is None:
            row = KnowledgeBaseRow(tipo_id=base.tipo_id, dados=dados)
            self.db.add(row)
        else:
            row.dados = dados
        self.db.commit()

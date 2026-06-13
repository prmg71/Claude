"""Endpoints de curadoria da Base de Conhecimento (RAG).

São os que a futura UI do papel "Curador" usará para enriquecer a base.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import Usuario, get_current_user, require_curador
from app.api.schemas import ContratoPadraoIn, RegraIn
from app.core.contract_types import get_tipo
from app.db.base import get_session
from app.knowledge.models import BaseConhecimento, RegraClausula
from app.knowledge.service import KnowledgeService
from app.knowledge.sql_repository import SqlKnowledgeRepository

router = APIRouter(prefix="/tipos/{tipo_id}/conhecimento", tags=["conhecimento"])


def _servico(db: Session) -> KnowledgeService:
    return KnowledgeService(SqlKnowledgeRepository(db))


def _tipo_ou_404(tipo_id: str):
    try:
        return get_tipo(tipo_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Tipo de contrato desconhecido.")


@router.get("", response_model=BaseConhecimento)
def obter_base(
    tipo_id: str,
    db: Session = Depends(get_session),
    _: Usuario = Depends(get_current_user),
) -> BaseConhecimento:
    tipo = _tipo_ou_404(tipo_id)
    return _servico(db).obter_base(tipo)


@router.post("/regras", response_model=BaseConhecimento)
def upsert_regra(
    tipo_id: str,
    regra: RegraIn,
    db: Session = Depends(get_session),
    curador: Usuario = Depends(require_curador),
) -> BaseConhecimento:
    _tipo_ou_404(tipo_id)
    modelo = RegraClausula(**regra.model_dump())
    return _servico(db).upsert_regra(tipo_id, modelo, autor=curador.email)


@router.delete("/regras/{regra_id}", response_model=BaseConhecimento)
def desativar_regra(
    tipo_id: str,
    regra_id: str,
    db: Session = Depends(get_session),
    curador: Usuario = Depends(require_curador),
) -> BaseConhecimento:
    _tipo_ou_404(tipo_id)
    try:
        return _servico(db).desativar_regra(tipo_id, regra_id, autor=curador.email)
    except KeyError:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")


@router.put("/contrato-padrao", response_model=BaseConhecimento)
def definir_contrato_padrao(
    tipo_id: str,
    corpo: ContratoPadraoIn,
    db: Session = Depends(get_session),
    curador: Usuario = Depends(require_curador),
) -> BaseConhecimento:
    _tipo_ou_404(tipo_id)
    return _servico(db).definir_contrato_padrao(
        tipo_id, corpo.nome_arquivo, corpo.texto, autor=curador.email
    )

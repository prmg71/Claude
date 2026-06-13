"""Endpoints dos tipos de contrato (alimentam o dropdown da UI)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.auth import Usuario, get_current_user
from app.api.schemas import TipoOut
from app.core.contract_types import listar_para_ui

router = APIRouter(prefix="/tipos", tags=["tipos"])


@router.get("", response_model=list[TipoOut])
def listar_tipos(_: Usuario = Depends(get_current_user)) -> list[dict]:
    """Lista todos os tipos de contrato (inclui inativos como 'em breve')."""
    return listar_para_ui()

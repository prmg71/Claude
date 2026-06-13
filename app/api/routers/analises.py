"""Endpoints de análise de contratos (upload → processamento → relatório)."""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.api.auth import Usuario, get_current_user, require_curador
from app.api.runner import executar_analise
from app.api.schemas import AnaliseOut, FeedbackIn
from app.core.contract_types import get_tipo
from app.core.extract import SUPORTADOS
from app.db.base import get_session
from app.db.models import Analysis, Feedback
from app.knowledge.service import KnowledgeService
from app.knowledge.sql_repository import SqlKnowledgeRepository

router = APIRouter(prefix="/analises", tags=["analises"])


def _nome_relatorio(a: Analysis) -> str:
    """Nome do arquivo do relatório: Relatório_<cliente>.docx.

    Usa o cliente identificado na análise; se ausente, recai no nome do arquivo
    enviado. Remove caracteres inválidos para nome de arquivo.
    """
    cliente = ""
    if a.resultado:
        cliente = (a.resultado.get("resumo") or {}).get("cliente") or ""
    base = cliente.strip() or Path(a.nome_arquivo).stem
    base = re.sub(r'[\\/:*?"<>|]+', " ", base)
    base = re.sub(r"\s+", " ", base).strip() or "contrato"
    return f"Relatório_{base}.docx"


def _to_out(a: Analysis) -> AnaliseOut:
    return AnaliseOut(
        id=a.id,
        tipo_id=a.tipo_id,
        nome_arquivo=a.nome_arquivo,
        status=a.status,
        erro=a.erro or "",
        tem_relatorio=bool(a.caminho_relatorio),
        resultado=a.resultado,
        tokens_total=a.tokens_total,
        custo_usd=a.custo_usd,
        duracao_seg=a.duracao_seg,
    )


@router.post("", response_model=AnaliseOut, status_code=201)
async def criar_analise(
    background: BackgroundTasks,
    tipo_id: str = Form(...),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> AnaliseOut:
    tipo = None
    try:
        tipo = get_tipo(tipo_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Tipo de contrato desconhecido.")
    if not tipo.ativo:
        raise HTTPException(status_code=400, detail=f"Tipo '{tipo_id}' não está ativo.")

    nome = arquivo.filename or "contrato"
    sufixo = Path(nome).suffix.lower()
    if sufixo not in SUPORTADOS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado: {sufixo}. Aceitos: {sorted(SUPORTADOS)}.",
        )

    analysis_id = uuid.uuid4().hex
    config.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    destino = config.UPLOADS_DIR / f"{analysis_id}{sufixo}"
    destino.write_bytes(await arquivo.read())

    a = Analysis(
        id=analysis_id,
        tipo_id=tipo_id,
        nome_arquivo=nome,
        caminho_arquivo=str(destino),
        status="pendente",
        autor=usuario.email,
    )
    db.add(a)
    db.commit()

    background.add_task(executar_analise, analysis_id)
    return _to_out(a)


@router.get("", response_model=list[AnaliseOut])
def listar_analises(
    db: Session = Depends(get_session),
    _: Usuario = Depends(get_current_user),
) -> list[AnaliseOut]:
    linhas = db.execute(select(Analysis).order_by(Analysis.criado_em.desc())).scalars().all()
    return [_to_out(a) for a in linhas]


@router.get("/{analysis_id}", response_model=AnaliseOut)
def obter_analise(
    analysis_id: str,
    db: Session = Depends(get_session),
    _: Usuario = Depends(get_current_user),
) -> AnaliseOut:
    a = db.get(Analysis, analysis_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada.")
    return _to_out(a)


@router.get("/{analysis_id}/relatorio")
def baixar_relatorio(
    analysis_id: str,
    db: Session = Depends(get_session),
    _: Usuario = Depends(get_current_user),
) -> FileResponse:
    a = db.get(Analysis, analysis_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada.")
    if not a.caminho_relatorio or not Path(a.caminho_relatorio).exists():
        raise HTTPException(status_code=409, detail="Relatório ainda não disponível.")
    return FileResponse(
        a.caminho_relatorio,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=_nome_relatorio(a),
    )


@router.post("/{analysis_id}/feedback", status_code=201)
def enviar_feedback(
    analysis_id: str,
    corpo: FeedbackIn,
    db: Session = Depends(get_session),
    curador: Usuario = Depends(require_curador),
) -> dict:
    """Registra feedback sobre um achado e o incorpora à Base de Conhecimento."""
    a = db.get(Analysis, analysis_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada.")

    db.add(
        Feedback(
            analysis_id=analysis_id,
            tipo_id=a.tipo_id,
            topico=corpo.topico,
            observacao=corpo.observacao,
            correto="sim" if corpo.correto else "nao",
            autor=curador.email,
        )
    )
    db.commit()

    # Ciclo de melhoria contínua: vira regra na base.
    servico = KnowledgeService(SqlKnowledgeRepository(db))
    servico.registrar_feedback(
        a.tipo_id,
        topico=corpo.topico,
        observacao=corpo.observacao,
        autor=curador.email,
        severidade=corpo.severidade,
        correto=corpo.correto,
    )
    return {"ok": True}

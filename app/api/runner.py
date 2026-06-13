"""Execução da análise em segundo plano.

Por ora roda como tarefa em segundo plano do FastAPI (no próprio processo).
Em produção, esta função é o ponto natural para ser movida a uma fila (arq/Celery).
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.core.analyze import analisar
from app.core.contract_types import get_tipo
from app.core.extract import extract_text
from app.core.references import load_references
from app.core.report import gerar_docx
from app.db.base import get_sessionmaker
from app.db.models import Analysis
from app.knowledge.service import KnowledgeService
from app.knowledge.sql_repository import SqlKnowledgeRepository


def executar_analise(analysis_id: str) -> None:
    """Processa uma análise pendente identificada por `analysis_id`."""
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        analise_row = db.get(Analysis, analysis_id)
        if analise_row is None:
            return
        analise_row.status = "processando"
        db.commit()

        inicio = time.monotonic()
        try:
            tipo = get_tipo(analise_row.tipo_id)
            texto = extract_text(Path(analise_row.caminho_arquivo))
            if not texto.strip():
                raise ValueError("Não foi possível extrair texto do contrato.")

            base = KnowledgeService(SqlKnowledgeRepository(db)).obter_base(tipo)
            referencias = load_references(tipo)
            resultado, metricas = analisar(texto, referencias, tipo, base)

            destino = config.RELATORIOS_DIR / f"{Path(analise_row.nome_arquivo).stem}_{analysis_id}.docx"
            gerar_docx(resultado, destino, analise_row.nome_arquivo, tipo.nome)

            analise_row.resultado = resultado.model_dump()
            analise_row.caminho_relatorio = str(destino)
            analise_row.tokens_total = metricas.get("tokens_total")
            analise_row.custo_usd = metricas.get("custo_usd")
            analise_row.duracao_seg = round(time.monotonic() - inicio, 1)
            analise_row.status = "concluida"
            analise_row.concluido_em = datetime.now(timezone.utc)
            db.commit()
        except Exception as exc:  # noqa: BLE001 - registra a falha na própria análise
            analise_row.status = "erro"
            analise_row.erro = str(exc)
            analise_row.concluido_em = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()

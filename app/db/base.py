"""Engine, sessão e base declarativa do SQLAlchemy."""
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app import config

_engine = None
_SessionLocal = None


class Base(DeclarativeBase):
    pass


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def get_engine():
    """Cria (uma vez) e devolve o engine."""
    global _engine, _SessionLocal
    if _engine is None:
        url = config.database_url()
        kwargs: dict = {"future": True}
        if _is_sqlite(url):
            # check_same_thread=False permite uso em threads do FastAPI/uvicorn.
            kwargs["connect_args"] = {"check_same_thread": False}
        else:
            # pool_pre_ping evita conexões mortas em poolers gerenciados.
            kwargs["pool_pre_ping"] = True
        _engine = create_engine(url, **kwargs)
        _SessionLocal = sessionmaker(
            bind=_engine, autoflush=False, expire_on_commit=False
        )
    return _engine


def get_sessionmaker():
    get_engine()
    return _SessionLocal


def init_db() -> None:
    """Cria as tabelas que ainda não existirem e aplica migrações leves."""
    from app.db import models  # noqa: F401 - garante o registro dos modelos

    Base.metadata.create_all(bind=get_engine())
    _migracoes_leves()


def _migracoes_leves() -> None:
    """Colunas adicionadas após a criação inicial (idempotente)."""
    url = config.database_url()
    if _is_sqlite(url):
        # SQLite não suporta ADD COLUMN IF NOT EXISTS; usamos try/except.
        stmts = [
            "ALTER TABLE analyses ADD COLUMN tokens_total INTEGER",
            "ALTER TABLE analyses ADD COLUMN custo_usd REAL",
            "ALTER TABLE analyses ADD COLUMN duracao_seg REAL",
        ]
        with get_engine().begin() as c:
            for s in stmts:
                try:
                    c.execute(text(s))
                except Exception:  # coluna já existe
                    pass
    else:
        stmts = [
            "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS tokens_total INTEGER",
            "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS custo_usd DOUBLE PRECISION",
            "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS duracao_seg DOUBLE PRECISION",
        ]
        with get_engine().begin() as c:
            for s in stmts:
                c.execute(text(s))


def get_session():
    """Dependência FastAPI: fornece uma sessão e garante o fechamento."""
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

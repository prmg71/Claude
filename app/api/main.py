"""Aplicação FastAPI do Analisador de Contratos.

Executar (a partir da raiz do projeto):
    venv/bin/uvicorn app.api.main:app --reload

- Interface web: /
- Documentação automática (OpenAPI/Swagger): /docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import config
from app.api.auth import Usuario, get_current_user
from app.api.routers import analises, conhecimento, tipos
from app.db.base import init_db

_WEB = Path(__file__).resolve().parent.parent / "web"
templates = Jinja2Templates(directory=str(_WEB / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas no arranque (idempotente).
    init_db()
    yield


app = FastAPI(
    title="Analisador de Contratos",
    description="Análise de contratos por tipo, enriquecida por Base de Conhecimento (RAG).",
    version="0.3.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(_WEB / "static")), name="static")

app.include_router(tipos.router)
app.include_router(conhecimento.router)
app.include_router(analises.router)


@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok"}


@app.get("/me", tags=["auth"])
def me(usuario: Usuario = Depends(get_current_user)) -> dict:
    """Dados do usuário autenticado (e-mail e papel)."""
    return {"email": usuario.email, "papel": usuario.papel}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request) -> HTMLResponse:
    """Interface web. Injeta a configuração pública do Supabase (URL + anon key)."""
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "supabase_url": config.supabase_url(),
            "supabase_anon_key": config.supabase_anon_key(),
        },
    )

"""Autenticação e controle de papéis.

Em modo desenvolvimento (DEV_MODE=true no .env), o Supabase Auth é ignorado
e todas as requisições são tratadas como o usuário local 'dev@local' com papel
de curador. Nunca ative DEV_MODE em produção.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
from fastapi import Depends, Header, HTTPException

from app import config


@dataclass
class Usuario:
    id: str
    email: str
    papel: str  # 'usuario' | 'curador'

    @property
    def is_curador(self) -> bool:
        return self.papel == "curador"


# Usuário fixo injetado quando DEV_MODE=true.
_DEV_USER = Usuario(id="dev-local", email="dev@local", papel="curador")


def _dev_mode() -> bool:
    return os.environ.get("DEV_MODE", "").lower() in ("1", "true", "yes")


def _extrair_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token ausente.")
    return authorization.split(" ", 1)[1].strip()


def get_current_user(authorization: str | None = Header(default=None)) -> Usuario:
    """Dependência: retorna o usuário autenticado.

    Em DEV_MODE ignora o token e devolve _DEV_USER (curador local).
    Em produção valida o JWT via Supabase Auth.
    """
    if _dev_mode():
        return _DEV_USER

    token = _extrair_token(authorization)
    url = config.supabase_url()
    anon = config.supabase_anon_key()
    if not url or not anon:
        raise HTTPException(
            status_code=500,
            detail="Auth não configurada (SUPABASE_URL / SUPABASE_ANON_KEY).",
        )
    try:
        resp = httpx.get(
            f"{url}/auth/v1/user",
            headers={"apikey": anon, "Authorization": f"Bearer {token}"},
            timeout=10,
        )
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Falha ao validar o token.")
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    dados = resp.json()
    email = (dados.get("email") or "").lower()
    papel = "curador" if email in config.curador_emails() else "usuario"
    return Usuario(id=dados.get("id", ""), email=email, papel=papel)


def require_curador(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Dependência: exige papel de curador."""
    if not usuario.is_curador:
        raise HTTPException(
            status_code=403, detail="Ação restrita a curadores da Base de Conhecimento."
        )
    return usuario

"""Configuração central: variáveis de ambiente e caminhos do projeto."""
from __future__ import annotations

import os
from pathlib import Path

# Raiz do projeto (pasta-mãe de app/)
BASE_DIR = Path(__file__).resolve().parent.parent

CONTRATOS_DIR = BASE_DIR / "contratos"
REFERENCIAS_DIR = BASE_DIR / "referencias"
RELATORIOS_DIR = BASE_DIR / "relatorios"

# Dados da aplicação (Base de Conhecimento por enquanto em ficheiros JSON;
# será migrado para PostgreSQL na Etapa B).
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
UPLOADS_DIR = DATA_DIR / "uploads"


def _ref_do_database_url() -> str:
    """Extrai o ref do projeto Supabase a partir da DATABASE_URL."""
    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        return ""
    try:
        corpo = raw.split("://", 1)[1]
        cred, host = corpo.split("@", 1)
        host = host.split("/")[0].split(":")[0]
        user = cred.split(":", 1)[0]
        if "." in user and user.startswith("postgres."):
            return user.split(".", 1)[1]
        if host.startswith("db.") and host.endswith(".supabase.co"):
            return host.split(".")[1]
    except Exception:  # noqa: BLE001
        return ""
    return ""


def supabase_url() -> str:
    """URL do projeto Supabase (https://<ref>.supabase.co). Derivada se possível."""
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    if url:
        return url
    ref = _ref_do_database_url()
    return f"https://{ref}.supabase.co" if ref else ""


def supabase_anon_key() -> str:
    return os.environ.get("SUPABASE_ANON_KEY", "").strip()


def curador_emails() -> set[str]:
    """E-mails com papel de curador."""
    raw = os.environ.get("CURADOR_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def database_url() -> str:
    """URL de conexão do banco.

    - Se DATABASE_URL não estiver definida, usa SQLite local (app.db na raiz).
    - Se começar com sqlite://, devolve como está.
    - Se for URL PostgreSQL (Supabase), normaliza para postgresql+psycopg://.
    """
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return f"sqlite:///{BASE_DIR / 'app.db'}"
    if url.startswith("sqlite://"):
        return url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


# Limite defensivo de caracteres enviados ao modelo.
MAX_CHARS_CONTRATO = int(os.environ.get("MAX_CHARS_CONTRATO", "120000"))
MAX_CHARS_REFERENCIAS = int(os.environ.get("MAX_CHARS_REFERENCIAS", "60000"))
MAX_CHARS_CONHECIMENTO = int(os.environ.get("MAX_CHARS_CONHECIMENTO", "40000"))


def _load_dotenv() -> None:
    """Carrega um ficheiro .env simples (KEY=VALUE) se existir, sem dependências."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


# Carrega .env no import do módulo.
_load_dotenv()

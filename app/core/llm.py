"""Abstração do provedor de LLM.

Selecione via variável de ambiente LLM_PROVIDER:
  - "openai_compat" -> endpoint privado compatível com OpenAI (padrão local)
  - "azure"         -> Azure OpenAI
  - "openrouter"    -> OpenRouter (apenas dev/protótipo)
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from app import config  # noqa: F401  (efeito colateral: carrega o .env)


@dataclass
class LLMConfig:
    provider: str          # openai_compat | azure | openrouter
    model: str
    api_key: str
    base_url: str = ""     # usado por openai_compat / openrouter
    azure_endpoint: str = ""
    azure_api_version: str = "2024-10-21"


def load_llm_config() -> LLMConfig:
    provider = os.environ.get("LLM_PROVIDER", "openai_compat").strip().lower()

    if provider == "azure":
        return LLMConfig(
            provider="azure",
            model=os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
            api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            azure_api_version=os.environ.get(
                "AZURE_OPENAI_API_VERSION", "2024-10-21"
            ),
        )
    if provider == "openrouter":
        return LLMConfig(
            provider="openrouter",
            model=os.environ.get("OPENROUTER_MODEL", ""),
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            base_url=os.environ.get(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
        )
    # default: openai_compat
    return LLMConfig(
        provider="openai_compat",
        model=os.environ.get("LLM_MODEL", ""),
        api_key=os.environ.get("LLM_API_KEY", ""),
        base_url=os.environ.get("LLM_BASE_URL", ""),
    )


def build_client(cfg: LLMConfig):
    """Cria o cliente OpenAI/AzureOpenAI adequado ao provedor configurado."""
    if cfg.provider == "azure":
        if not (cfg.api_key and cfg.azure_endpoint and cfg.model):
            raise RuntimeError(
                "Configuração Azure incompleta: defina AZURE_OPENAI_API_KEY, "
                "AZURE_OPENAI_ENDPOINT e AZURE_OPENAI_DEPLOYMENT."
            )
        from openai import AzureOpenAI

        return AzureOpenAI(
            api_key=cfg.api_key,
            azure_endpoint=cfg.azure_endpoint,
            api_version=cfg.azure_api_version,
        )

    # openai_compat e openrouter usam o cliente OpenAI padrão com base_url.
    if not cfg.api_key:
        raise RuntimeError(
            f"Chave de API não definida para o provedor '{cfg.provider}'."
        )
    if not cfg.base_url:
        raise RuntimeError(
            f"LLM_BASE_URL não definida para o provedor '{cfg.provider}'."
        )
    from openai import OpenAI

    return OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)

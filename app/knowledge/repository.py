"""Persistência da Base de Conhecimento.

Abstração de repositório com implementação em ficheiros JSON (uma base por
tipo, em data/knowledge/<tipo_id>.json). Na Etapa B trocamos por uma
implementação PostgreSQL preservando esta interface.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from app import config
from app.knowledge.models import BaseConhecimento


class KnowledgeRepository(ABC):
    @abstractmethod
    def carregar(self, tipo_id: str) -> BaseConhecimento:
        """Devolve a base do tipo (vazia se ainda não existir)."""

    @abstractmethod
    def salvar(self, base: BaseConhecimento) -> None:
        """Persiste a base."""

    @abstractmethod
    def existe(self, tipo_id: str) -> bool:
        ...


class JsonKnowledgeRepository(KnowledgeRepository):
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or config.KNOWLEDGE_DIR

    def _caminho(self, tipo_id: str) -> Path:
        return self.base_dir / f"{tipo_id}.json"

    def existe(self, tipo_id: str) -> bool:
        return self._caminho(tipo_id).exists()

    def carregar(self, tipo_id: str) -> BaseConhecimento:
        caminho = self._caminho(tipo_id)
        if not caminho.exists():
            return BaseConhecimento(tipo_id=tipo_id)
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        return BaseConhecimento.model_validate(dados)

    def salvar(self, base: BaseConhecimento) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        caminho = self._caminho(base.tipo_id)
        caminho.write_text(
            json.dumps(base.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

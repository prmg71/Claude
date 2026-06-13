"""Serviço de curadoria da Base de Conhecimento.

Camada que a futura API/UI usará para enriquecer a base: criar/editar regras,
definir o contrato padrão e registrar feedback de análises. Cuida de
versionamento, timestamps e trilha de auditoria.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from app.core.contract_types import TipoContrato
from app.knowledge.models import (
    BaseConhecimento,
    ContratoPadrao,
    RegistroAuditoria,
    RegraClausula,
)
from app.knowledge.repository import JsonKnowledgeRepository, KnowledgeRepository


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _novo_id(prefixo: str = "regra") -> str:
    return f"{prefixo}_{uuid.uuid4().hex[:12]}"


def _slug(texto: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")
    return base[:40] or "regra"


class KnowledgeService:
    def __init__(self, repo: KnowledgeRepository | None = None) -> None:
        self.repo = repo or JsonKnowledgeRepository()

    # ---- leitura / criação ----
    def obter_base(self, tipo: TipoContrato) -> BaseConhecimento:
        """Carrega a base do tipo; semeia a partir do checklist se ainda não existir."""
        if self.repo.existe(tipo.id):
            return self.repo.carregar(tipo.id)
        base = self.semear(tipo)
        self.repo.salvar(base)
        return base

    def semear(self, tipo: TipoContrato) -> BaseConhecimento:
        """Cria a base inicial convertendo o checklist do tipo em regras-semente."""
        agora = _agora()
        regras = [
            RegraClausula(
                id=f"sem_{_slug(item)}",
                topico=item,
                origem="semente",
                criado_em=agora,
                atualizado_em=agora,
                autor="sistema",
            )
            for item in tipo.checklist
        ]
        base = BaseConhecimento(
            tipo_id=tipo.id,
            regras=regras,
            atualizado_em=agora,
            historico=[
                RegistroAuditoria(
                    quando=agora,
                    autor="sistema",
                    acao="semear_base",
                    detalhe=f"{len(regras)} regra(s) a partir do checklist do tipo",
                )
            ],
        )
        return base

    # ---- mutações (curadoria) ----
    def _commit(self, base: BaseConhecimento, registro: RegistroAuditoria) -> BaseConhecimento:
        base.versao += 1
        base.atualizado_em = registro.quando
        base.historico.append(registro)
        self.repo.salvar(base)
        return base

    def upsert_regra(
        self, tipo_id: str, regra: RegraClausula, autor: str
    ) -> BaseConhecimento:
        """Cria ou atualiza uma regra, incrementando a sua versão."""
        base = self.repo.carregar(tipo_id)
        agora = _agora()
        existente = base.obter_regra(regra.id) if regra.id else None
        if existente is None:
            if not regra.id:
                regra.id = _novo_id()
            regra.versao = 1
            regra.criado_em = agora
            regra.atualizado_em = agora
            regra.autor = autor or regra.autor
            base.regras.append(regra)
            acao = "criar_regra"
        else:
            regra.versao = existente.versao + 1
            regra.criado_em = existente.criado_em
            regra.atualizado_em = agora
            regra.autor = autor or regra.autor
            base.regras = [regra if r.id == regra.id else r for r in base.regras]
            acao = "editar_regra"
        return self._commit(
            base,
            RegistroAuditoria(quando=agora, autor=autor, acao=acao, alvo=regra.id,
                              detalhe=regra.topico),
        )

    def desativar_regra(self, tipo_id: str, regra_id: str, autor: str) -> BaseConhecimento:
        base = self.repo.carregar(tipo_id)
        regra = base.obter_regra(regra_id)
        if regra is None:
            raise KeyError(f"Regra não encontrada: {regra_id}")
        agora = _agora()
        regra.ativo = False
        regra.versao += 1
        regra.atualizado_em = agora
        return self._commit(
            base,
            RegistroAuditoria(quando=agora, autor=autor, acao="desativar_regra",
                              alvo=regra_id, detalhe=regra.topico),
        )

    def definir_contrato_padrao(
        self, tipo_id: str, nome_arquivo: str, texto: str, autor: str
    ) -> BaseConhecimento:
        """Define/atualiza o contrato padrão (golden) do tipo."""
        base = self.repo.carregar(tipo_id)
        agora = _agora()
        versao = (base.contrato_padrao.versao + 1) if base.contrato_padrao else 1
        base.contrato_padrao = ContratoPadrao(
            nome_arquivo=nome_arquivo,
            texto=texto,
            versao=versao,
            autor=autor,
            atualizado_em=agora,
        )
        return self._commit(
            base,
            RegistroAuditoria(quando=agora, autor=autor, acao="definir_contrato_padrao",
                              detalhe=nome_arquivo),
        )

    def registrar_feedback(
        self,
        tipo_id: str,
        topico: str,
        observacao: str,
        autor: str,
        severidade: str = "média",
        correto: bool = False,
    ) -> BaseConhecimento:
        """Registra correção de um achado de análise como nova regra (origem=feedback).

        É o ciclo de melhoria contínua: o curador transforma o que o sistema
        acertou/errou em conhecimento reutilizável.
        """
        base = self.repo.carregar(tipo_id)
        agora = _agora()
        prefixo = "Confirmação" if correto else "Correção"
        regra = RegraClausula(
            id=_novo_id("fb"),
            topico=topico,
            correcoes=[f"[{prefixo}] {observacao}"],
            severidade=severidade,  # type: ignore[arg-type]
            origem="feedback",
            autor=autor,
            criado_em=agora,
            atualizado_em=agora,
        )
        base.regras.append(regra)
        return self._commit(
            base,
            RegistroAuditoria(quando=agora, autor=autor, acao="feedback",
                              alvo=regra.id, detalhe=topico),
        )

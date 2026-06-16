"""Tipos de contrato suportados pelo analisador."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TipoContrato:
    id: str
    nome: str
    descricao: str
    ativo: bool = False
    instrucoes: str = ""
    checklist: list[str] = field(default_factory=list)
    campos_extras: dict = field(default_factory=dict)


_CLIENTES = TipoContrato(
    id="contrato_clientes",
    nome="Contrato Clientes",
    descricao="Contrato comercial com clientes da Wort.",
    ativo=False,
    instrucoes="Analise o contrato com foco nas obrigações e direitos dos clientes da Wort.",
    checklist=[
        "Identificação das partes",
        "Objeto do contrato",
        "Prazo de vigência",
        "Condições de pagamento",
        "Obrigações do cliente",
        "Obrigações da Wort",
        "Cláusula de rescisão",
        "Foro",
    ],
)

_FORNECEDORES = TipoContrato(
    id="contrato_fornecedores",
    nome="Contrato Fornecedores",
    descricao="Contrato comercial com fornecedores da Wort.",
    ativo=False,
    instrucoes="Analise o contrato com foco nas obrigações e direitos dos fornecedores perante a Wort.",
    checklist=[
        "Identificação das partes",
        "Objeto do contrato",
        "Prazo de vigência",
        "Condições de pagamento",
        "Obrigações do fornecedor",
        "Obrigações da Wort",
        "Garantias e SLA",
        "Cláusula de rescisão",
        "Foro",
    ],
)

_NDA_CLIENTES = TipoContrato(
    id="nda_clientes",
    nome="NDA Clientes",
    descricao="Acordo de confidencialidade com clientes da Wort.",
    ativo=False,
    instrucoes="Analise o NDA com foco nas cláusulas de confidencialidade e restrições de uso das informações.",
    checklist=[
        "Identificação das partes",
        "Definição de informações confidenciais",
        "Obrigações de confidencialidade",
        "Exceções à confidencialidade",
        "Prazo de vigência",
        "Penalidades por descumprimento",
        "Foro",
    ],
)

_NDA_FORNECEDORES = TipoContrato(
    id="nda_fornecedores_parceiros",
    nome="NDA Fornecedores e Parceiros",
    descricao="Acordo de confidencialidade com fornecedores e parceiros da Wort.",
    ativo=False,
    instrucoes="Analise o NDA com foco nas cláusulas de confidencialidade aplicáveis a fornecedores e parceiros.",
    checklist=[
        "Identificação das partes",
        "Definição de informações confidenciais",
        "Obrigações de confidencialidade",
        "Exceções à confidencialidade",
        "Prazo de vigência",
        "Penalidades por descumprimento",
        "Foro",
    ],
)


TIPOS: dict[str, TipoContrato] = {
    t.id: t
    for t in [_CLIENTES, _FORNECEDORES, _NDA_CLIENTES, _NDA_FORNECEDORES]
}


def listar_tipos(apenas_ativos: bool = False) -> list[TipoContrato]:
    tipos = list(TIPOS.values())
    if apenas_ativos:
        tipos = [t for t in tipos if t.ativo]
    return tipos


def obter_tipo(tipo_id: str) -> Optional[TipoContrato]:
    return TIPOS.get(tipo_id)


def listar_para_ui() -> list[dict]:
    return [
        {
            "id": t.id,
            "nome": t.nome,
            "descricao": t.descricao,
            "ativo": t.ativo,
        }
        for t in TIPOS.values()
    ]


# aliases para compatibilidade com código existente
get_tipo = obter_tipo

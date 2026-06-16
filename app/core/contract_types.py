"""Registro dos tipos de contrato suportados.

Fonte única de verdade para as opções que a interface web vai exibir e para a
especialização da análise por tipo. Apenas os tipos com `ativo=True` podem ser
analisados; os demais aparecem na UI como "em breve".

O `checklist` aqui é a SEMENTE inicial de cada tipo: ao criar a Base de
Conhecimento (app.knowledge), os tópicos do checklist viram regras de cláusula
que os curadores passam a enriquecer.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TipoContrato:
    id: str
    nome: str
    descricao: str
    pasta_referencias: str
    instrucoes: str
    checklist: list[str] = field(default_factory=list)
    ativo: bool = False


_SAAS = TipoContrato(
    id="saas_mensalidade",
    nome="Contrato Mensalidade SaaS",
    descricao="Software como serviço com cobrança recorrente (mensalidade).",
    pasta_referencias="contrato_saas_mensalidade",
    ativo=True,
    instrucoes=(
        "Este é um contrato de SaaS (software como serviço) com cobrança mensal "
        "recorrente. Neste tipo de contrato, a Wort é SEMPRE o "
        "FORNECEDOR/PRESTADOR do serviço (a outra parte é o cliente/contratante). "
        "Analise SOB A ÓTICA DA WORT COMO FORNECEDOR, destacando cláusulas que "
        "exponham a Wort a risco enquanto prestadora — por exemplo: responsabilidade "
        "ilimitada ou desproporcional da Wort, penalidades/SLA excessivos impostos à "
        "Wort, cessão indevida da propriedade intelectual do software da Wort, "
        "obrigações vagas que ampliem o escopo sem contrapartida, ou condições de "
        "pagamento/reajuste desfavoráveis à Wort. "
        "Avalie a presença e a adequação de cada item do checklist abaixo; para "
        "cada item, registre na seção 'comparacao' o que se espera (referencia) e "
        "o que o contrato estabelece (contrato), marcando 'conforme' como false "
        "quando o item estiver ausente, vago ou desfavorável à Wort."
    ),
    checklist=[
        "Objeto e escopo do serviço SaaS (módulos, usuários, limites de uso)",
        "Valor da mensalidade, periodicidade e forma de pagamento",
        "Reajuste de preços (índice, ex.: IPCA/IGP-M, e periodicidade)",
        "Vigência, renovação automática e prazo de aviso prévio",
        "Hipóteses de rescisão, multa e aviso prévio",
        "Portabilidade e devolução/exclusão de dados ao término do contrato",
        "SLA: disponibilidade, suporte, tempos de resposta e penalidades",
        "Proteção de dados e LGPD (papéis controlador/operador, subprocessadores, incidentes)",
        "Propriedade intelectual do software e titularidade dos dados do cliente",
        "Confidencialidade",
        "Limitação de responsabilidade e indenização",
        "Garantias, conformidade e legislação aplicável",
        "Foro de eleição",
    ],
)

_MARKETPLACE = TipoContrato(
    id="marketplace_privado",
    nome="Contrato Marketplace Privado",
    descricao="Prestação de serviços de sistema de compras / marketplace privado, com intermediação.",
    pasta_referencias="contrato_marketplace_privado",
    ativo=True,
    instrucoes=(
        "Este é um contrato de prestação de serviços de sistema de compras / "
        "marketplace privado, com intermediação. Neste tipo, a Wort é SEMPRE o "
        "FORNECEDOR/OPERADOR da plataforma (a outra parte é o cliente/contratante). "
        "Analise SOB A ÓTICA DA WORT COMO FORNECEDOR, "
        "comparando o contrato do cliente com o contrato padrão da Wort e destacando "
        "cláusulas que exponham a Wort a risco enquanto operadora — por exemplo: "
        "responsabilidade ilimitada ou desproporcional da Wort, garantias/níveis de "
        "serviço excessivos, cessão indevida da propriedade intelectual dos sistemas "
        "da Wort, obrigações vagas que ampliem o escopo sem contrapartida, condições "
        "comerciais/intermediação/reajuste desfavoráveis à Wort, ou riscos de LGPD e "
        "anticorrupção. Avalie cada item do checklist; marque 'conforme' como false "
        "quando o contrato do cliente divergir do padrão da Wort de forma desfavorável "
        "ou quando um ponto estiver ausente, vago ou arriscado para a Wort."
    ),
    checklist=[
        "Objeto e escopo dos serviços (Anexos I/II/III)",
        "Condições comerciais: valores, intermediação/comissão e forma de pagamento",
        "Reajuste de preços (índice e periodicidade)",
        "Reembolso de despesas",
        "Obrigações da Wort (níveis de serviço, prazos)",
        "Obrigações do cliente (pagamento e uso adequado)",
        "Responsabilidades e garantias (limitação de responsabilidade da Wort)",
        "Propriedade intelectual (titularidade dos sistemas da Wort)",
        "Isenção de vínculo trabalhista",
        "Sigilo e confidencialidade",
        "Declarações e garantias anticorrupção",
        "Tratamento de dados pessoais (LGPD)",
        "Vigência, rescisão e denúncia (aviso prévio)",
        "Cessão e transferência",
        "Foro de eleição",
    ],
)
_COMPRAS_FREE = TipoContrato(
    id="compras_free",
    nome="Contrato ComprasFree",
    descricao="Contrato da modalidade ComprasFree.",
    pasta_referencias="contrato_compras_free",
    instrucoes="",
)
_FORNECEDORES = TipoContrato(
    id="fornecedores",
    nome="Contrato Fornecedores",
    descricao="Contrato com fornecedores.",
    pasta_referencias="contrato_fornecedores",
    instrucoes="",
)
_NDA = TipoContrato(
    id="nda",
    nome="NDA",
    descricao="Acordo de confidencialidade (Non-Disclosure Agreement).",
    pasta_referencias="contrato_nda",
    instrucoes="",
)

TIPOS: dict[str, TipoContrato] = {
    t.id: t
    for t in (_SAAS, _MARKETPLACE, _COMPRAS_FREE, _FORNECEDORES, _NDA)
}


def get_tipo(tipo_id: str) -> TipoContrato:
    if tipo_id not in TIPOS:
        raise KeyError(f"Tipo de contrato desconhecido: {tipo_id!r}")
    return TIPOS[tipo_id]


def tipos_ativos() -> list[TipoContrato]:
    return [t for t in TIPOS.values() if t.ativo]


def listar_para_ui() -> list[dict]:
    return [
        {"id": t.id, "nome": t.nome, "descricao": t.descricao, "ativo": t.ativo}
        for t in TIPOS.values()
    ]

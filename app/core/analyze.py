"""Análise de contratos via LLM privado, com saída estruturada por tipo.

A análise é enriquecida pela Base de Conhecimento (RAG): as regras de cláusula
curadas e o contrato padrão do tipo são injetados no prompt.
"""
from __future__ import annotations

import json
import re

from app import config
from app.core.contract_types import TipoContrato
from app.core.llm import build_client, load_llm_config
from app.core.models import AnaliseContrato
from app.knowledge.models import BaseConhecimento
from app.knowledge.prompt import render_base_conhecimento

SYSTEM_PROMPT = (
    "Você é um analista jurídico especializado na revisão de contratos. "
    "Analisa o contrato fornecido de forma rigorosa e objetiva, em português do Brasil. "
    "Use a base de conhecimento e os documentos de referência como critério de "
    "conformidade, identificando divergências, violações de limites e pontos de "
    "atenção. Responde SEMPRE com um único objeto JSON válido, sem texto antes ou "
    "depois, seguindo exatamente o esquema indicado."
)

JSON_SCHEMA_HINT = """Responda com um objeto JSON com esta estrutura:
{
  "resumo": {
    "titulo": "string",
    "cliente": "string",
    "partes": ["string"],
    "objeto": "string",
    "valores": ["string"],
    "prazos": ["string"],
    "sintese": "string"
  },
  "comparacao": [
    {"aspeto": "string", "referencia": "string", "contrato": "string",
     "conforme": true, "observacao": "string"}
  ],
  "riscos": [
    {"descricao": "string", "severidade": "alta|média|baixa",
     "clausula": "string", "recomendacao": "string"}
  ]
}

No campo "cliente", informe o nome da contraparte (o cliente) — NÃO o Mercado
Eletrônico, que é o fornecedor. Se não conseguir identificar, deixe vazio."""


def _parse_json(conteudo: str) -> dict:
    """Extrai o objeto JSON da resposta do modelo.

    Tolera respostas embrulhadas em bloco markdown (```json ... ```) ou com
    texto antes/depois, isolando o primeiro objeto {...} válido.
    """
    texto = (conteudo or "").strip()
    # Remove cercas de código markdown, ex.: ```json ... ```
    cerca = re.match(r"^```[a-zA-Z]*\s*(.*?)\s*```$", texto, re.DOTALL)
    if cerca:
        texto = cerca.group(1).strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        # Última tentativa: do primeiro '{' ao último '}'.
        ini, fim = texto.find("{"), texto.rfind("}")
        if ini != -1 and fim > ini:
            return json.loads(texto[ini : fim + 1])
        raise


def _bloco_tipo(tipo: TipoContrato | None) -> str:
    if tipo is None:
        return ""
    partes = [f"=== TIPO DE CONTRATO: {tipo.nome} ===", tipo.instrucoes]
    if tipo.checklist:
        itens = "\n".join(f"- {item}" for item in tipo.checklist)
        partes.append(f"\nChecklist obrigatório a avaliar:\n{itens}")
    return "\n".join(p for p in partes if p.strip())


def _build_user_prompt(
    texto_contrato: str,
    referencias: str,
    tipo: TipoContrato | None,
    base: BaseConhecimento | None,
) -> str:
    contrato = texto_contrato[: config.MAX_CHARS_CONTRATO]
    if len(texto_contrato) > config.MAX_CHARS_CONTRATO:
        contrato += "\n\n[...contrato truncado por exceder o limite...]"

    bloco_ref = (
        f"\n\n=== DOCUMENTOS DE REFERÊNCIA ===\n{referencias}"
        if referencias.strip()
        else ""
    )
    bloco_base = render_base_conhecimento(base)
    bloco_base = f"\n\n{bloco_base}" if bloco_base else ""

    cabecalho = f"{JSON_SCHEMA_HINT}\n\n{_bloco_tipo(tipo)}".strip()

    return (
        f"{cabecalho}"
        f"{bloco_base}"
        f"\n\n=== CONTRATO A ANALISAR ===\n{contrato}"
        f"{bloco_ref}"
    )


def analisar(
    texto_contrato: str,
    referencias: str = "",
    tipo: TipoContrato | None = None,
    base: BaseConhecimento | None = None,
) -> tuple[AnaliseContrato, dict]:
    """Analisa um contrato.

    Devolve uma tupla (AnaliseContrato, metricas), onde `metricas` traz tokens e
    custo em US$ (quando o provedor informa — ex.: OpenRouter).
    """
    cfg = load_llm_config()
    client = build_client(cfg)
    resposta = client.chat.completions.create(
        model=cfg.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(texto_contrato, referencias, tipo, base),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    conteudo = resposta.choices[0].message.content or "{}"
    dados = _parse_json(conteudo)
    analise = AnaliseContrato.model_validate(dados)

    usage = getattr(resposta, "usage", None)
    metricas = {
        "tokens_total": getattr(usage, "total_tokens", None),
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        # OpenRouter expõe o custo em US$ em usage.cost; outros provedores não.
        "custo_usd": getattr(usage, "cost", None),
    }
    return analise, metricas

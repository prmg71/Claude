#!/usr/bin/env python3
"""CLI: analisa contratos de um tipo em contratos/ e gera relatórios DOCX.

Executar a partir da raiz do projeto:
    venv/bin/python -m app.cli [--tipo <id>]

Nesta fase, apenas o tipo "Contrato Mensalidade SaaS" está ativo. A análise é
enriquecida pela Base de Conhecimento (RAG) do tipo.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from app import config
from app.core.analyze import analisar
from app.core.contract_types import get_tipo, tipos_ativos
from app.core.extract import SUPORTADOS, extract_text
from app.core.llm import load_llm_config
from app.core.references import load_references
from app.core.report import gerar_docx
from app.knowledge.service import KnowledgeService

console = Console()


def _listar_contratos() -> list[Path]:
    pasta = config.CONTRATOS_DIR
    if not pasta.exists():
        return []
    return sorted(
        f for f in pasta.iterdir() if f.is_file() and f.suffix.lower() in SUPORTADOS
    )


def main() -> int:
    ativos = tipos_ativos()
    parser = argparse.ArgumentParser(description="Analisador de Contratos")
    parser.add_argument(
        "--tipo",
        default=ativos[0].id if ativos else None,
        help="ID do tipo de contrato (ativos: "
        + ", ".join(t.id for t in ativos) + ")",
    )
    args = parser.parse_args()

    console.rule("[bold]Analisador de Contratos")

    try:
        tipo = get_tipo(args.tipo) if args.tipo else None
    except KeyError as exc:
        console.print(f"[red]Erro:[/] {exc}")
        return 1
    if tipo is None or not tipo.ativo:
        console.print(
            f"[red]Erro:[/] tipo '{args.tipo}' não está ativo. "
            f"Ativos: {', '.join(t.id for t in ativos) or 'nenhum'}."
        )
        return 1

    cfg = load_llm_config()
    if not cfg.api_key:
        console.print(
            f"[red]Erro:[/] chave de API não definida para o provedor "
            f"'{cfg.provider}'. Crie um ficheiro .env (ver .env.example)."
        )
        return 1

    contratos = _listar_contratos()
    if not contratos:
        console.print(
            f"[yellow]Nenhum contrato encontrado em[/] {config.CONTRATOS_DIR} "
            "(formatos suportados: .pdf, .docx)."
        )
        return 1

    # Base de Conhecimento (semeada do checklist do tipo se ainda não existir).
    base = KnowledgeService().obter_base(tipo)

    console.print(f"[cyan]Tipo:[/] {tipo.nome}")
    console.print(f"[cyan]Provedor LLM:[/] {cfg.provider}  [cyan]Modelo:[/] {cfg.model}")
    console.print(
        f"[cyan]Base de conhecimento:[/] {len(base.regras_ativas())} regra(s) ativa(s)"
        + (", contrato padrão definido" if base.contrato_padrao else "")
    )
    console.print(f"[cyan]Contratos encontrados:[/] {len(contratos)}")

    referencias = load_references(tipo)
    if referencias:
        console.print("[green]Referências de arquivo carregadas.[/]")

    sucessos = 0
    for contrato in contratos:
        console.print(f"\n[bold]→ {contrato.name}[/]")
        try:
            texto = extract_text(contrato)
            if not texto.strip():
                console.print("  [yellow]Aviso:[/] sem texto extraível, ignorado.")
                continue
            console.print("  Analisando via LLM…")
            analise, metricas = analisar(texto, referencias, tipo, base)
            destino = config.RELATORIOS_DIR / f"{contrato.stem}_relatorio.docx"
            gerar_docx(analise, destino, contrato.name, tipo.nome)
            tok = metricas.get("tokens_total")
            custo = metricas.get("custo_usd")
            extra = (f" [{tok} tokens" + (f", US$ {custo:.4f}]" if custo else "]")) if tok else ""
            console.print(f"  [green]✓ Relatório:[/] {destino}{extra}")
            sucessos += 1
        except Exception as exc:  # noqa: BLE001 - isolar falha por contrato
            console.print(f"  [red]✗ Falha:[/] {exc}")

    console.rule()
    console.print(f"[bold]Concluído:[/] {sucessos}/{len(contratos)} relatório(s) gerado(s).")
    return 0 if sucessos else 1


if __name__ == "__main__":
    sys.exit(main())

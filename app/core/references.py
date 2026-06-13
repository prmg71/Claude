"""Carregamento dos documentos de referência (por tipo de contrato)."""
from __future__ import annotations

from pathlib import Path

from app import config
from app.core.contract_types import TipoContrato
from app.core.extract import extract_text

EXTENSOES_REFERENCIA = {".pdf", ".docx", ".txt", ".md"}


def _ler_pasta(pasta: Path) -> list[str]:
    blocos: list[str] = []
    if not pasta.exists():
        return blocos
    for ficheiro in sorted(pasta.iterdir()):
        if not ficheiro.is_file() or ficheiro.suffix.lower() not in EXTENSOES_REFERENCIA:
            continue
        try:
            texto = extract_text(ficheiro)
        except Exception as exc:  # noqa: BLE001 - referência inválida não aborta
            texto = f"[Falha ao ler esta referência: {exc}]"
        if texto.strip():
            blocos.append(f"### Referência: {ficheiro.name}\n{texto}")
    return blocos


def load_references(tipo: TipoContrato | None = None) -> str:
    """Lê os documentos de referência e concatena num bloco rotulado.

    Quando `tipo` é fornecido, lê de referencias/<pasta_referencias>/ e também
    da raiz de referencias/ (referências comuns a todos os tipos). Trunca de
    forma defensiva ao limite config.MAX_CHARS_REFERENCIAS.
    """
    blocos: list[str] = []
    raiz = config.REFERENCIAS_DIR
    blocos.extend(_ler_pasta(raiz))
    if tipo is not None:
        blocos.extend(_ler_pasta(raiz / tipo.pasta_referencias))

    combinado = "\n\n".join(blocos).strip()
    if len(combinado) > config.MAX_CHARS_REFERENCIAS:
        combinado = (
            combinado[: config.MAX_CHARS_REFERENCIAS]
            + "\n\n[...referências truncadas...]"
        )
    return combinado

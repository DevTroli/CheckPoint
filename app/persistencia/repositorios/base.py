from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalizar_texto(valor: str) -> str:
    return " ".join(valor.strip().split())


def converter_hash(dados: dict[str, Any]) -> dict[str, Any]:
    """Converte valores lidos como texto nos tipos básicos esperados."""
    resultado = dict(dados)
    for campo in ("id", "usuario_id", "jogo_id", "progresso", "tempo_jogado_minutos"):
        if campo in resultado:
            resultado[campo] = int(resultado[campo])
    if "nota" in resultado:
        resultado["nota"] = float(resultado["nota"])
    return resultado

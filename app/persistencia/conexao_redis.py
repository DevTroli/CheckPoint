from __future__ import annotations

import os
from dataclasses import dataclass

import redis


@dataclass(frozen=True)
class ConfiguracaoRedis:
    host: str = os.getenv("REDIS_HOST", "localhost")
    porta: int = int(os.getenv("REDIS_PORT", "6379"))
    banco: int = int(os.getenv("REDIS_DB", "0"))
    senha: str | None = os.getenv("REDIS_PASSWORD") or None


def criar_cliente(configuracao: ConfiguracaoRedis | None = None) -> redis.Redis:
    """Cria um cliente Redis compartilhável pela aplicação."""
    config = configuracao or ConfiguracaoRedis()
    return redis.Redis(
        host=config.host,
        port=config.porta,
        db=config.banco,
        password=config.senha,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


def verificar_conexao(cliente: redis.Redis) -> bool:
    """Retorna True quando o Redis responde ao comando PING."""
    return bool(cliente.ping())

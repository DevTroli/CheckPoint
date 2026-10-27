from __future__ import annotations

from datetime import date, timedelta

from redis import Redis

from app.persistencia import chaves

CHAVE_RANKING_XP = "ranking:xp"
XP_REGISTRO_CRIADO = 25
XP_REGISTRO_ATUALIZADO = 5
XP_ATIVIDADE_DIARIA = 5


def _chave_gamificacao(usuario_id: int) -> str:
    return f"gamificacao:{usuario_id}"


def _chave_atividade(usuario_id: int, dia: date) -> str:
    return f"atividade:{usuario_id}:{dia.isoformat()}"


def _incrementar_xp(cliente: Redis, usuario_id: int, quantidade: int) -> int:
    return int(cliente.zincrby(CHAVE_RANKING_XP, quantidade, f"usuario:{usuario_id}"))


def registrar_atividade(cliente: Redis, usuario_id: int, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    chave_hoje = _chave_atividade(usuario_id, hoje)
    primeira_atividade = bool(cliente.set(chave_hoje, "1", ex=172800, nx=True))
    gamificacao = cliente.hgetall(_chave_gamificacao(usuario_id))
    streak = int(gamificacao.get("streak", 0))
    ultima = gamificacao.get("ultima_atividade")

    if primeira_atividade:
        if ultima == (hoje - timedelta(days=1)).isoformat():
            streak += 1
        else:
            streak = 1
        _incrementar_xp(cliente, usuario_id, XP_ATIVIDADE_DIARIA)
        cliente.hset(
            _chave_gamificacao(usuario_id),
            mapping={"streak": streak, "ultima_atividade": hoje.isoformat()},
        )

    return consultar_gamificacao(cliente, usuario_id)


def conceder_xp(cliente: Redis, usuario_id: int, quantidade: int) -> dict:
    _incrementar_xp(cliente, usuario_id, quantidade)
    return consultar_gamificacao(cliente, usuario_id)


def consultar_gamificacao(cliente: Redis, usuario_id: int) -> dict:
    xp = int(cliente.zscore(CHAVE_RANKING_XP, f"usuario:{usuario_id}") or 0)
    posicao = cliente.zrevrank(CHAVE_RANKING_XP, f"usuario:{usuario_id}")
    dados = cliente.hgetall(_chave_gamificacao(usuario_id))
    return {
        "usuario_id": usuario_id,
        "xp": xp,
        "streak": int(dados.get("streak", 0)),
        "ultima_atividade": dados.get("ultima_atividade"),
        "posicao": (posicao + 1) if posicao is not None else None,
    }


def listar_ranking(cliente: Redis, limite: int = 10) -> list[dict]:
    itens = cliente.zrange(CHAVE_RANKING_XP, 0, limite - 1, desc=True, withscores=True)
    return [
        {"usuario_id": int(membro.split(":")[1]), "xp": int(pontuacao), "posicao": posicao}
        for posicao, (membro, pontuacao) in enumerate(itens, start=1)
    ]

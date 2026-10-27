from __future__ import annotations

from typing import Any

from redis import Redis

from app.persistencia import chaves
from app.persistencia.excecoes import RecursoDuplicado, RecursoNaoEncontrado, RelacaoInvalida
from app.persistencia.repositorios.base import agora_iso, converter_hash


class RepositorioRegistro:
    def __init__(self, cliente: Redis):
        self.cliente = cliente

    def criar(self, *, usuario_id: int, jogo_id: int, progresso: int = 0,
              tempo_jogado_minutos: int = 0, nota: float = 0,
              status: str = "planejado", avaliacao: str = "") -> dict[str, Any]:
        self._validar_relacoes(usuario_id, jogo_id)
        indice = chaves.indice_registro(usuario_id, jogo_id)
        if self.cliente.exists(indice):
            raise RecursoDuplicado("O usuário já possui um registro para este jogo.")
        registro_id = int(self.cliente.incr(chaves.sequencia("registro")))
        agora = agora_iso()
        dados = {
            "id": registro_id,
            "usuario_id": usuario_id,
            "jogo_id": jogo_id,
            "progresso": progresso,
            "tempo_jogado_minutos": tempo_jogado_minutos,
            "nota": nota,
            "status": status,
            "avaliacao": avaliacao.strip(),
            "criado_em": agora,
            "atualizado_em": agora,
        }
        self.cliente.hset(chaves.registro(registro_id), mapping=dados)
        self.cliente.set(indice, registro_id)
        self.cliente.sadd(chaves.registros_do_usuario(usuario_id), registro_id)
        self.cliente.sadd(chaves.registros_do_jogo(jogo_id), registro_id)
        return dados

    def _validar_relacoes(self, usuario_id: int, jogo_id: int) -> None:
        if not self.cliente.exists(chaves.usuario(usuario_id)):
            raise RelacaoInvalida("O usuário informado não existe.")
        if not self.cliente.exists(chaves.jogo(jogo_id)):
            raise RelacaoInvalida("O jogo informado não existe.")

    def buscar_por_id(self, registro_id: int) -> dict[str, Any]:
        dados = self.cliente.hgetall(chaves.registro(registro_id))
        if not dados:
            raise RecursoNaoEncontrado("Registro não encontrado.")
        return converter_hash(dados)

    def buscar_do_usuario_e_jogo(self, usuario_id: int, jogo_id: int) -> dict[str, Any]:
        registro_id = self.cliente.get(chaves.indice_registro(usuario_id, jogo_id))
        if registro_id is None:
            raise RecursoNaoEncontrado("Registro não encontrado.")
        return self.buscar_por_id(int(registro_id))

    def listar_do_usuario(self, usuario_id: int) -> list[dict[str, Any]]:
        ids = self.cliente.smembers(chaves.registros_do_usuario(usuario_id))
        return sorted((self.buscar_por_id(int(registro_id)) for registro_id in ids), key=lambda item: item["id"])

    def atualizar(self, registro_id: int, **campos: Any) -> dict[str, Any]:
        atual = self.buscar_por_id(registro_id)
        permitidos = {"progresso", "tempo_jogado_minutos", "nota", "status", "avaliacao"}
        alteracoes = {chave: valor for chave, valor in campos.items() if chave in permitidos}
        if alteracoes:
            alteracoes["atualizado_em"] = agora_iso()
            self.cliente.hset(chaves.registro(registro_id), mapping=alteracoes)
        return self.buscar_por_id(registro_id)

    def excluir(self, registro_id: int) -> None:
        registro = self.buscar_por_id(registro_id)
        self.cliente.delete(
            chaves.registro(registro_id),
            chaves.indice_registro(registro["usuario_id"], registro["jogo_id"]),
        )
        self.cliente.srem(chaves.registros_do_usuario(registro["usuario_id"]), registro_id)
        self.cliente.srem(chaves.registros_do_jogo(registro["jogo_id"]), registro_id)

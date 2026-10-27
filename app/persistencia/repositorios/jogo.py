from __future__ import annotations

from typing import Any

from redis import Redis

from app.persistencia import chaves
from app.persistencia.excecoes import RecursoDuplicado, RecursoNaoEncontrado
from app.persistencia.repositorios.base import agora_iso, converter_hash, normalizar_texto


class RepositorioJogo:
    def __init__(self, cliente: Redis):
        self.cliente = cliente

    def criar(self, *, nome: str, categoria: str, data_lancamento: str,
              publicadora: str = "", desenvolvedora: str = "", descricao: str = "") -> dict[str, Any]:
        nome = normalizar_texto(nome)
        if self.cliente.exists(chaves.indice_nome_jogo(nome)):
            raise RecursoDuplicado("O jogo já está cadastrado.")
        jogo_id = int(self.cliente.incr(chaves.sequencia("jogo")))
        agora = agora_iso()
        dados = {
            "id": jogo_id,
            "nome": nome,
            "descricao": descricao.strip(),
            "categoria": normalizar_texto(categoria),
            "data_lancamento": data_lancamento,
            "publicadora": normalizar_texto(publicadora),
            "desenvolvedora": normalizar_texto(desenvolvedora),
            "criado_em": agora,
            "atualizado_em": agora,
        }
        self.cliente.hset(chaves.jogo(jogo_id), mapping=dados)
        self.cliente.set(chaves.indice_nome_jogo(nome), jogo_id)
        return dados

    def buscar_por_id(self, jogo_id: int) -> dict[str, Any]:
        dados = self.cliente.hgetall(chaves.jogo(jogo_id))
        if not dados:
            raise RecursoNaoEncontrado("Jogo não encontrado.")
        return converter_hash(dados)

    def buscar_por_nome(self, nome: str) -> dict[str, Any]:
        jogo_id = self.cliente.get(chaves.indice_nome_jogo(nome))
        if jogo_id is None:
            raise RecursoNaoEncontrado("Jogo não encontrado.")
        return self.buscar_por_id(int(jogo_id))

    def listar(self) -> list[dict[str, Any]]:
        ids = self.cliente.scan_iter(match="jogo:*")
        jogos = []
        for chave in ids:
            if chave.count(":") == 1:
                jogos.append(converter_hash(self.cliente.hgetall(chave)))
        return sorted(jogos, key=lambda item: item["nome"].lower())

    def atualizar(self, jogo_id: int, **campos: Any) -> dict[str, Any]:
        atual = self.buscar_por_id(jogo_id)
        permitidos = {"nome", "descricao", "categoria", "data_lancamento", "publicadora", "desenvolvedora"}
        alteracoes = {chave: valor for chave, valor in campos.items() if chave in permitidos}
        if "nome" in alteracoes:
            novo_nome = normalizar_texto(str(alteracoes["nome"]))
            dono = self.cliente.get(chaves.indice_nome_jogo(novo_nome))
            if dono and int(dono) != jogo_id:
                raise RecursoDuplicado("O jogo já está cadastrado.")
            self.cliente.delete(chaves.indice_nome_jogo(atual["nome"]))
            self.cliente.set(chaves.indice_nome_jogo(novo_nome), jogo_id)
            alteracoes["nome"] = novo_nome
        if alteracoes:
            alteracoes["atualizado_em"] = agora_iso()
            self.cliente.hset(chaves.jogo(jogo_id), mapping=alteracoes)
        return self.buscar_por_id(jogo_id)

    def excluir(self, jogo_id: int) -> None:
        jogo = self.buscar_por_id(jogo_id)
        self.cliente.delete(
            chaves.jogo(jogo_id),
            chaves.indice_nome_jogo(jogo["nome"]),
            chaves.registros_do_jogo(jogo_id),
        )

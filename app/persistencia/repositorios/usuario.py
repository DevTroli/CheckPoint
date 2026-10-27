from __future__ import annotations

from typing import Any

from redis import Redis

from app.persistencia import chaves
from app.persistencia.excecoes import RecursoDuplicado, RecursoNaoEncontrado
from app.persistencia.repositorios.base import agora_iso, converter_hash, normalizar_texto


class RepositorioUsuario:
    def __init__(self, cliente: Redis):
        self.cliente = cliente

    def criar(self, *, nome_usuario: str, email: str, senha_hash: str) -> dict[str, Any]:
        nome_usuario = normalizar_texto(nome_usuario)
        email = email.strip().lower()
        if self.cliente.exists(chaves.indice_email(email)):
            raise RecursoDuplicado("O e-mail já está cadastrado.")
        if self.cliente.exists(chaves.indice_nome_usuario(nome_usuario)):
            raise RecursoDuplicado("O nome de usuário já está cadastrado.")

        usuario_id = int(self.cliente.incr(chaves.sequencia("usuario")))
        agora = agora_iso()
        dados = {
            "id": usuario_id,
            "nome_usuario": nome_usuario,
            "email": email,
            "senha_hash": senha_hash,
            "criado_em": agora,
            "atualizado_em": agora,
        }
        self.cliente.hset(chaves.usuario(usuario_id), mapping=dados)
        self.cliente.set(chaves.indice_email(email), usuario_id)
        self.cliente.set(chaves.indice_nome_usuario(nome_usuario), usuario_id)
        return dados

    def buscar_por_id(self, usuario_id: int) -> dict[str, Any]:
        dados = self.cliente.hgetall(chaves.usuario(usuario_id))
        if not dados:
            raise RecursoNaoEncontrado("Usuário não encontrado.")
        return converter_hash(dados)

    def buscar_por_email(self, email: str) -> dict[str, Any]:
        usuario_id = self.cliente.get(chaves.indice_email(email.strip().lower()))
        if usuario_id is None:
            raise RecursoNaoEncontrado("Usuário não encontrado.")
        return self.buscar_por_id(int(usuario_id))

    def atualizar(self, usuario_id: int, **campos: Any) -> dict[str, Any]:
        atual = self.buscar_por_id(usuario_id)
        permitidos = {"nome_usuario", "email", "senha_hash"}
        alteracoes = {chave: valor for chave, valor in campos.items() if chave in permitidos}
        if "email" in alteracoes:
            novo_email = str(alteracoes["email"]).strip().lower()
            dono = self.cliente.get(chaves.indice_email(novo_email))
            if dono and int(dono) != usuario_id:
                raise RecursoDuplicado("O e-mail já está cadastrado.")
            self.cliente.delete(chaves.indice_email(atual["email"]))
            self.cliente.set(chaves.indice_email(novo_email), usuario_id)
            alteracoes["email"] = novo_email
        if "nome_usuario" in alteracoes:
            novo_nome = normalizar_texto(str(alteracoes["nome_usuario"]))
            dono = self.cliente.get(chaves.indice_nome_usuario(novo_nome))
            if dono and int(dono) != usuario_id:
                raise RecursoDuplicado("O nome de usuário já está cadastrado.")
            self.cliente.delete(chaves.indice_nome_usuario(atual["nome_usuario"]))
            self.cliente.set(chaves.indice_nome_usuario(novo_nome), usuario_id)
            alteracoes["nome_usuario"] = novo_nome
        if alteracoes:
            alteracoes["atualizado_em"] = agora_iso()
            self.cliente.hset(chaves.usuario(usuario_id), mapping=alteracoes)
        return self.buscar_por_id(usuario_id)

    def excluir(self, usuario_id: int) -> None:
        usuario = self.buscar_por_id(usuario_id)
        self.cliente.delete(
            chaves.usuario(usuario_id),
            chaves.indice_email(usuario["email"]),
            chaves.indice_nome_usuario(usuario["nome_usuario"]),
            chaves.registros_do_usuario(usuario_id),
        )

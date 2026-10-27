from __future__ import annotations

import fakeredis
import pytest

from app.persistencia import chaves
from app.persistencia.conexao_redis import ConfiguracaoRedis, criar_cliente, verificar_conexao
from app.persistencia.excecoes import RecursoDuplicado, RecursoNaoEncontrado, RelacaoInvalida
from app.persistencia.repositorios.jogo import RepositorioJogo
from app.persistencia.repositorios.registro import RepositorioRegistro
from app.persistencia.repositorios.usuario import RepositorioUsuario


@pytest.fixture
def cliente():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def repositorios(cliente):
    return {
        "cliente": cliente,
        "usuarios": RepositorioUsuario(cliente),
        "jogos": RepositorioJogo(cliente),
        "registros": RepositorioRegistro(cliente),
    }


def criar_usuario_e_jogo(repositorios):
    usuario = repositorios["usuarios"].criar(
        nome_usuario="ana",
        email="ana@example.com",
        senha_hash="hash-seguro",
    )
    jogo = repositorios["jogos"].criar(
        nome="Hollow Knight",
        categoria="Metroidvania",
        data_lancamento="2017-02-24",
        publicadora="Team Cherry",
        desenvolvedora="Team Cherry",
    )
    return usuario, jogo


def test_cliente_redis_responde_ping():
    cliente = fakeredis.FakeRedis(decode_responses=True)
    assert verificar_conexao(cliente) is True


def test_configuracao_possui_padrao_local():
    config = ConfiguracaoRedis()
    assert config.host == "localhost"
    assert config.porta == 6379
    assert config.banco == 0


def test_usuario_cria_consulta_atualiza_e_exclui(repositorios):
    repo = repositorios["usuarios"]
    usuario = repo.criar(nome_usuario=" Ana ", email="ANA@EXAMPLE.COM ", senha_hash="hash")

    assert usuario["id"] == 1
    assert repo.buscar_por_email("ana@example.com")["nome_usuario"] == "Ana"

    atualizado = repo.atualizar(usuario["id"], nome_usuario="Ana Silva")
    assert atualizado["nome_usuario"] == "Ana Silva"
    assert repositorios["cliente"].get(chaves.indice_nome_usuario("Ana")) is None

    repo.excluir(usuario["id"])
    with pytest.raises(RecursoNaoEncontrado):
        repo.buscar_por_id(usuario["id"])


def test_usuario_impede_email_e_nome_duplicados(repositorios):
    repo = repositorios["usuarios"]
    repo.criar(nome_usuario="ana", email="ana@example.com", senha_hash="hash")
    with pytest.raises(RecursoDuplicado):
        repo.criar(nome_usuario="outra", email="ana@example.com", senha_hash="hash")
    with pytest.raises(RecursoDuplicado):
        repo.criar(nome_usuario="ana", email="outra@example.com", senha_hash="hash")


def test_jogo_cria_lista_atualiza_e_exclui(repositorios):
    repo = repositorios["jogos"]
    jogo = repo.criar(nome=" Celeste ", categoria="Plataforma", data_lancamento="2018-01-25")

    assert repo.buscar_por_nome("celeste")["nome"] == "Celeste"
    assert len(repo.listar()) == 1
    atualizado = repo.atualizar(jogo["id"], categoria="Aventura")
    assert atualizado["categoria"] == "Aventura"

    repo.excluir(jogo["id"])
    with pytest.raises(RecursoNaoEncontrado):
        repo.buscar_por_id(jogo["id"])


def test_jogo_impede_nome_duplicado(repositorios):
    repo = repositorios["jogos"]
    repo.criar(nome="Celeste", categoria="Plataforma", data_lancamento="2018-01-25")
    with pytest.raises(RecursoDuplicado):
        repo.criar(nome="Celeste", categoria="Aventura", data_lancamento="2018-01-25")


def test_registro_exige_relacoes_existentes(repositorios):
    repo = repositorios["registros"]
    with pytest.raises(RelacaoInvalida):
        repo.criar(usuario_id=1, jogo_id=1)


def test_registro_cria_consulta_atualiza_lista_e_exclui(repositorios):
    usuario, jogo = criar_usuario_e_jogo(repositorios)
    repo = repositorios["registros"]
    registro = repo.criar(
        usuario_id=usuario["id"],
        jogo_id=jogo["id"],
        progresso=25,
        tempo_jogado_minutos=120,
        nota=8.5,
        status="jogando",
        avaliacao="Muito bom",
    )

    assert repo.buscar_do_usuario_e_jogo(usuario["id"], jogo["id"])["progresso"] == 25
    assert len(repo.listar_do_usuario(usuario["id"])) == 1
    atualizado = repo.atualizar(registro["id"], progresso=100, status="concluido")
    assert atualizado["progresso"] == 100
    assert atualizado["status"] == "concluido"

    assert repositorios["cliente"].sismember(chaves.registros_do_usuario(usuario["id"]), registro["id"])
    assert repositorios["cliente"].sismember(chaves.registros_do_jogo(jogo["id"]), registro["id"])

    repo.excluir(registro["id"])
    with pytest.raises(RecursoNaoEncontrado):
        repo.buscar_por_id(registro["id"])
    assert not repositorios["cliente"].sismember(chaves.registros_do_usuario(usuario["id"]), registro["id"])
    assert not repositorios["cliente"].exists(chaves.indice_registro(usuario["id"], jogo["id"]))


def test_registro_unico_por_usuario_e_jogo(repositorios):
    usuario, jogo = criar_usuario_e_jogo(repositorios)
    repo = repositorios["registros"]
    repo.criar(usuario_id=usuario["id"], jogo_id=jogo["id"])
    with pytest.raises(RecursoDuplicado):
        repo.criar(usuario_id=usuario["id"], jogo_id=jogo["id"])


def test_excluir_jogo_remove_registros_e_indices_relacionados(repositorios):
    usuario, jogo = criar_usuario_e_jogo(repositorios)
    registro = repositorios["registros"].criar(usuario_id=usuario["id"], jogo_id=jogo["id"])

    repositorios["jogos"].excluir(jogo["id"])

    assert not repositorios["cliente"].exists(chaves.registro(registro["id"]))
    assert not repositorios["cliente"].exists(chaves.indice_registro(usuario["id"], jogo["id"]))
    assert not repositorios["cliente"].sismember(
        chaves.registros_do_usuario(usuario["id"]), registro["id"]
    )


def test_excluir_usuario_remove_registros_e_indices_relacionados(repositorios):
    usuario, jogo = criar_usuario_e_jogo(repositorios)
    registro = repositorios["registros"].criar(usuario_id=usuario["id"], jogo_id=jogo["id"])

    repositorios["usuarios"].excluir(usuario["id"])

    assert not repositorios["cliente"].exists(chaves.registro(registro["id"]))
    assert not repositorios["cliente"].exists(chaves.indice_registro(usuario["id"], jogo["id"]))
    assert not repositorios["cliente"].sismember(
        chaves.registros_do_jogo(jogo["id"]), registro["id"]
    )

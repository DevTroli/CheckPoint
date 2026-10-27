import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

import fakeredis
import pytest
from django.test import Client

from app.api import dependencias, views
from app.persistencia import chaves


@pytest.fixture
def api(monkeypatch):
    cliente = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(dependencias, "cliente_redis", cliente)
    monkeypatch.setattr(views, "cliente_redis", cliente)
    return cliente


def cadastrar(client, nome, email):
    resposta = client.post(
        "/api/usuarios/",
        {"nome_usuario": nome, "email": email, "senha": "senha123"},
        content_type="application/json",
    )
    assert resposta.status_code == 201
    return resposta.json()


def login(client, email):
    resposta = client.post(
        "/api/auth/login/",
        {"email": email, "senha": "senha123"},
        content_type="application/json",
    )
    assert resposta.status_code == 200
    return resposta.json()


def test_fluxo_de_usuario_jogo_registro_e_gamificacao(api):
    admin_client = Client()
    admin = cadastrar(admin_client, "admin", "admin@example.com")
    assert admin["papel"] == "admin"
    login(admin_client, "admin@example.com")

    jogo_resposta = admin_client.post(
        "/api/jogos/",
        {
            "nome": "Celeste",
            "categoria": "Plataforma",
            "data_lancamento": "2018-01-25",
            "publicadora": "Matt Makes Games",
            "desenvolvedora": "Maddy Makes Games",
        },
        content_type="application/json",
    )
    assert jogo_resposta.status_code == 201
    jogo_id = jogo_resposta.json()["id"]

    usuario_client = Client()
    usuario = cadastrar(usuario_client, "jogador", "jogador@example.com")
    login(usuario_client, "jogador@example.com")

    registro_resposta = usuario_client.post(
        "/api/registros/",
        {"jogo_id": jogo_id, "progresso": 50, "nota": 9, "status": "jogando"},
        content_type="application/json",
    )
    assert registro_resposta.status_code == 201
    assert registro_resposta.json()["gamificacao"]["xp"] == 30

    meu_xp = usuario_client.get("/api/gamificacao/me/")
    assert meu_xp.status_code == 200
    assert meu_xp.json()["streak"] == 1

    ranking = usuario_client.get("/api/gamificacao/ranking/")
    assert ranking.status_code == 200
    assert ranking.json()[0]["usuario_id"] == usuario["id"]
    assert api.zscore("ranking:xp", f"usuario:{usuario['id']}") == 30


def test_permissoes_e_validacoes_basicas(api):
    anonimo = Client()
    assert anonimo.get("/api/registros/").status_code == 401
    assert anonimo.post("/api/jogos/", {}, content_type="application/json").status_code == 401

    cliente = Client()
    cadastrar(cliente, "primeiro", "primeiro@example.com")
    login(cliente, "primeiro@example.com")
    resposta = cliente.post(
        "/api/jogos/",
        {"nome": "Jogo", "categoria": "RPG", "data_lancamento": "2020-01-01"},
        content_type="application/json",
    )
    assert resposta.status_code == 201
    assert api.hget(chaves.jogo(resposta.json()["id"]), "data_lancamento") == "2020-01-01"


def test_streak_nao_concede_xp_duas_vezes_no_mesmo_dia(api):
    client = Client()
    usuario = cadastrar(client, "streak", "streak@example.com")
    login(client, "streak@example.com")
    primeira = client.get("/api/gamificacao/me/").json()
    segunda = client.get("/api/gamificacao/me/").json()
    assert primeira["xp"] == segunda["xp"]
    assert primeira["streak"] == segunda["streak"] == 1

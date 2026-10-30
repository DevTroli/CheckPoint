import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

import fakeredis
import pytest
from django.test import Client

from app.api import dependencias, views

JOGO = {"nome": "Celeste", "categoria": "Plataforma", "data_lancamento": "2018-01-25"}


@pytest.fixture
def api(monkeypatch):
    cliente = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(dependencias, "cliente_redis", cliente)
    monkeypatch.setattr(views, "cliente_redis", cliente)
    return cliente


def entrar(nome):
    client = Client()
    email = f"{nome}@example.com"
    dados = client.post(
        "/api/usuarios/",
        {"nome_usuario": nome, "email": email, "senha": "senha123"},
        content_type="application/json",
    ).json()
    resposta = client.post(
        "/api/auth/login/", {"email": email, "senha": "senha123"}, content_type="application/json"
    )
    assert resposta.status_code == 200
    return client, dados


def criar_jogo(client, **extra):
    return client.post("/api/jogos/", {**JOGO, **extra}, content_type="application/json")


@pytest.fixture
def cenario(api):
    admin, admin_dados = entrar("admin")
    ana, ana_dados = entrar("ana")
    bia, bia_dados = entrar("bia")
    return {"admin": admin, "ana": ana, "bia": bia, "ana_dados": ana_dados}


def test_usuario_comum_cria_jogo_e_vira_dono(cenario):
    resposta = criar_jogo(cenario["ana"])

    assert resposta.status_code == 201
    assert resposta.json()["dono_id"] == cenario["ana_dados"]["id"]


def test_jogo_so_aparece_para_o_dono(cenario):
    jogo_id = criar_jogo(cenario["ana"]).json()["id"]

    assert [j["id"] for j in cenario["ana"].get("/api/jogos/").json()] == [jogo_id]
    assert cenario["bia"].get("/api/jogos/").json() == []
    assert cenario["bia"].get(f"/api/jogos/{jogo_id}/").status_code == 404


def test_admin_enxerga_todos_os_jogos(cenario):
    criar_jogo(cenario["ana"])
    criar_jogo(cenario["bia"], nome="Hades")

    nomes = {j["nome"] for j in cenario["admin"].get("/api/jogos/").json()}

    assert nomes == {"Celeste", "Hades"}


def test_outro_usuario_nao_edita_nem_exclui(cenario):
    jogo_id = criar_jogo(cenario["ana"]).json()["id"]
    corpo = {"nome": "Outro nome"}

    assert cenario["bia"].put(f"/api/jogos/{jogo_id}/", corpo, content_type="application/json").status_code == 404
    assert cenario["bia"].delete(f"/api/jogos/{jogo_id}/").status_code == 404
    assert cenario["ana"].put(f"/api/jogos/{jogo_id}/", corpo, content_type="application/json").status_code == 200
    assert cenario["ana"].delete(f"/api/jogos/{jogo_id}/").status_code == 204


def test_nome_pode_repetir_entre_usuarios_mas_nao_para_o_mesmo(cenario):
    assert criar_jogo(cenario["ana"]).status_code == 201
    assert criar_jogo(cenario["bia"]).status_code == 201
    assert criar_jogo(cenario["ana"]).status_code == 409


def test_renomear_respeita_unicidade_por_dono(cenario):
    criar_jogo(cenario["ana"], nome="Hades")
    celeste = criar_jogo(cenario["ana"]).json()["id"]

    resposta = cenario["ana"].put(
        f"/api/jogos/{celeste}/", {"nome": "Hades"}, content_type="application/json"
    )

    assert resposta.status_code == 409


def test_nao_avalia_jogo_de_outro_usuario(cenario):
    jogo_id = criar_jogo(cenario["ana"]).json()["id"]

    resposta = cenario["bia"].post(
        "/api/registros/", {"jogo_id": jogo_id, "nota": 8}, content_type="application/json"
    )

    assert resposta.status_code == 404


def test_listagem_exige_login(api):
    assert Client().get("/api/jogos/").status_code == 401

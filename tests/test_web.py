import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

import pytest
from django.test import Client


@pytest.mark.parametrize(
    "caminho, acao",
    [
        ("/entrar/", 'data-acao="login"'),
        ("/cadastrar/", 'data-acao="cadastro"'),
    ],
)
def test_paginas_de_autenticacao_respondem(caminho, acao):
    resposta = Client().get(caminho)

    assert resposta.status_code == 200
    assert acao in resposta.content.decode()

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from pathlib import Path

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


@pytest.mark.parametrize(
    "caminho, marcador",
    [
        ("/jogos/", 'id="lista-jogos"'),
        ("/jogos/7/", 'data-jogo-id="7"'),
        ("/jogos/novo/", 'data-acao="jogo"'),
        ("/jogos/7/editar/", 'data-jogo-id="7"'),
    ],
)
def test_paginas_do_catalogo_respondem(caminho, marcador):
    resposta = Client().get(caminho)

    assert resposta.status_code == 200
    assert marcador in resposta.content.decode()


@pytest.mark.parametrize(
    "caminho, marcador",
    [
        ("/jogos/7/", 'id="minha-avaliacao"'),
        ("/jogos/7/", 'id="form-avaliacao"'),
    ],
)
def test_paginas_trazem_a_avaliacao_pessoal(caminho, marcador):
    assert marcador in Client().get(caminho).content.decode()


def test_pagina_inicial_tem_tela_de_loading_travada_em_75():
    html = Client().get("/").content.decode()
    css = Path("app/web/static/web/estilo.css").read_text(encoding="utf-8")

    assert 'class="abertura"' in html
    assert 'role="progressbar"' in html and 'aria-valuenow="75"' in html
    assert "LOADING" in html
    assert "@keyframes flutuar" in css and "width: 75%" in css


def test_pagina_inicial_tem_seta_para_o_catalogo():
    html = Client().get("/").content.decode()

    assert '<a class="seta" href="/jogos/"' in html


def test_login_e_cadastro_redirecionam_para_a_pagina_inicial():
    # Sem runner de JS no projeto: garante, ao menos, o destino do redirecionamento.
    js = Path("app/web/static/web/auth.js").read_text(encoding="utf-8")

    assert 'window.location.href = "/";' in js
    assert 'window.location.href = "/jogos/"' not in js


def test_loading_tem_pontos_animados():
    html = Client().get("/").content.decode()
    css = Path("app/web/static/web/estilo.css").read_text(encoding="utf-8")

    assert 'class="pontos"' in html
    assert "@keyframes pontos" in css


def test_catalogo_nao_tem_filtro_exibir():
    # Todo jogo visível já é do usuário, então não há o que alternar.
    html = Client().get("/jogos/").content.decode()

    assert 'id="visao"' not in html
    assert 'id="busca"' in html


def test_novo_jogo_tem_duas_etapas():
    html = Client().get("/jogos/novo/").content.decode()

    assert 'id="etapa-jogo"' in html
    assert 'id="etapa-avaliacao"' in html


def test_editar_jogo_tem_so_a_etapa_do_jogo():
    html = Client().get("/jogos/7/editar/").content.decode()

    assert 'id="etapa-jogo"' in html
    assert 'id="etapa-avaliacao"' not in html


def test_pagina_do_ranking_responde():
    resposta = Client().get("/ranking/")

    assert resposta.status_code == 200
    assert 'id="tabela-ranking"' in resposta.content.decode()


def test_placar_usa_estilo_de_fliperama_em_caixa_alta():
    html = Client().get("/ranking/").content.decode()
    css = Path("app/web/static/web/estilo.css").read_text(encoding="utf-8")

    assert 'class="pagina placar"' in html
    assert ".placar" in css and "text-transform: uppercase" in css


def test_menu_tem_link_para_o_ranking():
    assert 'href="/ranking/"' in Client().get("/").content.decode()


def test_css_respeita_o_atributo_hidden():
    # Regressão: .form/.acoes (display próprio) deixavam elementos hidden visíveis.
    from pathlib import Path

    css = Path("app/web/static/web/estilo.css").read_text(encoding="utf-8")

    assert "[hidden]" in css and "display: none !important" in css


def test_detalhe_com_id_invalido_nao_existe():
    assert Client().get("/jogos/abc/").status_code == 404

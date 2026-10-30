from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("entrar/", views.entrar, name="entrar"),
    path("cadastrar/", views.cadastrar, name="cadastrar"),
    path("ranking/", views.ranking, name="ranking"),
    path("jogos/", views.jogos, name="jogos"),
    path("jogos/novo/", views.jogo_novo, name="jogo_novo"),
    path("jogos/<int:jogo_id>/", views.jogo_detalhe, name="jogo_detalhe"),
    path("jogos/<int:jogo_id>/editar/", views.jogo_editar, name="jogo_editar"),
]

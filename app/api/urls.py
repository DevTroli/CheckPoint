from django.urls import path

from app.api import views

urlpatterns = [
    path("usuarios/", views.UsuariosView.as_view()),
    path("usuarios/me/", views.UsuarioAtualView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("auth/logout/", views.LogoutView.as_view()),
    path("jogos/", views.JogosView.as_view()),
    path("jogos/<int:jogo_id>/", views.JogoDetalheView.as_view()),
    path("registros/", views.RegistrosView.as_view()),
    path("registros/<int:registro_id>/", views.RegistroDetalheView.as_view()),
    path("gamificacao/me/", views.MinhaGamificacaoView.as_view()),
    path("gamificacao/ranking/", views.RankingView.as_view()),
]

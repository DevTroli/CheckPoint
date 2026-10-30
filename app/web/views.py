from django.shortcuts import render


def inicio(request):
    return render(request, "web/inicio.html")


def entrar(request):
    return render(request, "web/entrar.html")


def cadastrar(request):
    return render(request, "web/cadastrar.html")


def jogos(request):
    return render(request, "web/jogos.html")


def jogo_detalhe(request, jogo_id):
    return render(request, "web/jogo_detalhe.html", {"jogo_id": jogo_id})


def ranking(request):
    return render(request, "web/ranking.html")


def jogo_novo(request):
    return render(request, "web/jogo_form.html", {"jogo_id": ""})


def jogo_editar(request, jogo_id):
    return render(request, "web/jogo_form.html", {"jogo_id": jogo_id})

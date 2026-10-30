from django.shortcuts import render


def inicio(request):
    return render(request, "web/inicio.html")


def entrar(request):
    return render(request, "web/entrar.html")


def cadastrar(request):
    return render(request, "web/cadastrar.html")

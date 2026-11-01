from __future__ import annotations

from functools import wraps

from django.contrib.auth.hashers import check_password, make_password
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from app.api import gamificacao
from app.api.dependencias import cliente_redis, repositorios
from app.api.serializers import (
    AtualizacaoRegistroSerializer,
    AtualizacaoUsuarioSerializer,
    CadastroUsuarioSerializer,
    JogoSerializer,
    LoginSerializer,
    RegistroSerializer,
)
from app.persistencia.excecoes import ErroDePersistencia, RecursoDuplicado, RecursoNaoEncontrado, RelacaoInvalida


def resposta_erro(mensagem: str, codigo: str, status_code: int):
    return Response({"erro": codigo, "mensagem": mensagem}, status=status_code)


def tratar_erro(erro: Exception):
    if isinstance(erro, RecursoDuplicado):
        return resposta_erro(str(erro), "conflito", status.HTTP_409_CONFLICT)
    if isinstance(erro, (RecursoNaoEncontrado, RelacaoInvalida)):
        return resposta_erro(str(erro), "nao_encontrado", status.HTTP_404_NOT_FOUND)
    if isinstance(erro, ErroDePersistencia):
        return resposta_erro(str(erro), "erro_de_persistencia", status.HTTP_400_BAD_REQUEST)
    raise erro


def dados_publicos_usuario(usuario: dict) -> dict:
    return {
        "id": usuario["id"],
        "nome_usuario": usuario["nome_usuario"],
        "email": usuario["email"],
        "papel": usuario.get("papel", "usuario"),
        "criado_em": usuario["criado_em"],
    }


def usuario_da_sessao(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return None
    try:
        return repositorios()[0].buscar_por_id(int(usuario_id))
    except RecursoNaoEncontrado:
        request.session.flush()
        return None


def jogo_acessivel(usuario: dict, jogo_id: int) -> dict:
    """Devolve o jogo se for do usuário (inclusive admin); senão, 'não encontrado'."""
    jogo = repositorios()[1].buscar_por_id(jogo_id)
    if jogo.get("dono_id") != usuario["id"]:
        raise RecursoNaoEncontrado("Jogo não encontrado.")
    return jogo


def exigir_login(view):
    @wraps(view)
    def wrapper(self, request, *args, **kwargs):
        usuario = usuario_da_sessao(request)
        if not usuario:
            return resposta_erro("Faça login para continuar.", "nao_autenticado", status.HTTP_401_UNAUTHORIZED)
        request.usuario_atual = usuario
        return view(self, request, *args, **kwargs)
    return wrapper


def exigir_admin(view):
    @wraps(view)
    @exigir_login
    def wrapper(self, request, *args, **kwargs):
        if request.usuario_atual.get("papel") != "admin":
            return resposta_erro("Apenas administradores podem alterar o catálogo.", "sem_permissao", status.HTTP_403_FORBIDDEN)
        return view(self, request, *args, **kwargs)
    return wrapper


class UsuariosView(APIView):
    def post(self, request):
        serializer = CadastroUsuarioSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        dados = serializer.validated_data
        usuarios, _, _ = repositorios()
        primeiro_usuario = not cliente_redis.exists("sequencia:usuario")
        try:
            usuario = usuarios.criar(
                nome_usuario=dados["nome_usuario"],
                email=dados["email"],
                senha_hash=make_password(dados["senha"]),
                papel="admin" if primeiro_usuario else "usuario",
            )
            return Response(dados_publicos_usuario(usuario), status=status.HTTP_201_CREATED)
        except Exception as erro:
            return tratar_erro(erro)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            usuario = repositorios()[0].buscar_por_email(serializer.validated_data["email"])
            if not check_password(serializer.validated_data["senha"], usuario["senha_hash"]):
                return resposta_erro("E-mail ou senha inválidos.", "credenciais_invalidas", status.HTTP_401_UNAUTHORIZED)
            request.session.cycle_key()
            request.session["usuario_id"] = usuario["id"]
            gamificacao.registrar_atividade(cliente_redis, usuario["id"])
            return Response({"usuario": dados_publicos_usuario(usuario), "gamificacao": gamificacao.consultar_gamificacao(cliente_redis, usuario["id"])})
        except RecursoNaoEncontrado:
            return resposta_erro("E-mail ou senha inválidos.", "credenciais_invalidas", status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    def post(self, request):
        request.session.flush()
        return Response({"mensagem": "Logout realizado com sucesso."})


class UsuarioAtualView(APIView):
    @exigir_login
    def get(self, request):
        return Response(dados_publicos_usuario(request.usuario_atual))

    @exigir_login
    def patch(self, request):
        serializer = AtualizacaoUsuarioSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        dados = serializer.validated_data.copy()
        if "senha" in dados:
            dados["senha_hash"] = make_password(dados.pop("senha"))
        try:
            usuario = repositorios()[0].atualizar(request.usuario_atual["id"], **dados)
            return Response(dados_publicos_usuario(usuario))
        except Exception as erro:
            return tratar_erro(erro)


class JogosView(APIView):
    @exigir_login
    def get(self, request):
        jogos = repositorios()[1].listar(dono_id=request.usuario_atual["id"])
        busca = request.query_params.get("busca", "").strip().lower()
        categoria = request.query_params.get("categoria", "").strip().lower()
        if busca:
            jogos = [jogo for jogo in jogos if busca in jogo["nome"].lower()]
        if categoria:
            jogos = [jogo for jogo in jogos if jogo["categoria"].lower() == categoria]
        ordenacao = request.query_params.get("ordenar", "nome")
        if ordenacao in {"nome", "categoria", "data_lancamento"}:
            jogos.sort(key=lambda jogo: jogo[ordenacao].lower())
        return Response(jogos)

    @exigir_login
    def post(self, request):
        serializer = JogoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            jogo = repositorios()[1].criar(dono_id=request.usuario_atual["id"], **serializer.validated_data)
            return Response(jogo, status=status.HTTP_201_CREATED)
        except Exception as erro:
            return tratar_erro(erro)


class JogoDetalheView(APIView):
    @exigir_login
    def get(self, request, jogo_id):
        try:
            return Response(jogo_acessivel(request.usuario_atual, jogo_id))
        except Exception as erro:
            return tratar_erro(erro)

    @exigir_login
    def put(self, request, jogo_id):
        serializer = JogoSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            jogo_acessivel(request.usuario_atual, jogo_id)
            return Response(repositorios()[1].atualizar(jogo_id, **serializer.validated_data))
        except Exception as erro:
            return tratar_erro(erro)

    @exigir_login
    def delete(self, request, jogo_id):
        try:
            jogo_acessivel(request.usuario_atual, jogo_id)
            repositorios()[1].excluir(jogo_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as erro:
            return tratar_erro(erro)


class RegistrosView(APIView):
    @exigir_login
    def get(self, request):
        registros = repositorios()[2].listar_do_usuario(request.usuario_atual["id"])
        return Response(registros)

    @exigir_login
    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            jogo_acessivel(request.usuario_atual, serializer.validated_data["jogo_id"])
            registro = repositorios()[2].criar(usuario_id=request.usuario_atual["id"], **serializer.validated_data)
            gamificacao.registrar_atividade(cliente_redis, request.usuario_atual["id"])
            dados_gamificacao = gamificacao.conceder_xp(cliente_redis, request.usuario_atual["id"], gamificacao.XP_REGISTRO_CRIADO)
            return Response({"registro": registro, "gamificacao": dados_gamificacao}, status=status.HTTP_201_CREATED)
        except Exception as erro:
            return tratar_erro(erro)


class RegistroDetalheView(APIView):
    @exigir_login
    def get(self, request, registro_id):
        try:
            registro = repositorios()[2].buscar_por_id(registro_id)
            if registro["usuario_id"] != request.usuario_atual["id"]:
                return resposta_erro("Você não pode acessar este registro.", "sem_permissao", status.HTTP_403_FORBIDDEN)
            return Response(registro)
        except Exception as erro:
            return tratar_erro(erro)

    @exigir_login
    def patch(self, request, registro_id):
        serializer = AtualizacaoRegistroSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            registros = repositorios()[2]
            registro = registros.buscar_por_id(registro_id)
            if registro["usuario_id"] != request.usuario_atual["id"]:
                return resposta_erro("Você não pode alterar este registro.", "sem_permissao", status.HTTP_403_FORBIDDEN)
            atualizado = registros.atualizar(registro_id, **serializer.validated_data)
            gamificacao.registrar_atividade(cliente_redis, request.usuario_atual["id"])
            dados_gamificacao = gamificacao.conceder_xp(cliente_redis, request.usuario_atual["id"], gamificacao.XP_REGISTRO_ATUALIZADO)
            return Response({"registro": atualizado, "gamificacao": dados_gamificacao})
        except Exception as erro:
            return tratar_erro(erro)

    @exigir_login
    def delete(self, request, registro_id):
        try:
            registros = repositorios()[2]
            registro = registros.buscar_por_id(registro_id)
            if registro["usuario_id"] != request.usuario_atual["id"]:
                return resposta_erro("Você não pode excluir este registro.", "sem_permissao", status.HTTP_403_FORBIDDEN)
            registros.excluir(registro_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as erro:
            return tratar_erro(erro)


class MinhaGamificacaoView(APIView):
    @exigir_login
    def get(self, request):
        return Response(gamificacao.consultar_gamificacao(cliente_redis, request.usuario_atual["id"]))


class RankingView(APIView):
    def get(self, request):
        limite = min(max(int(request.query_params.get("limite", 10)), 1), 50)
        return Response(gamificacao.listar_ranking(cliente_redis, limite))

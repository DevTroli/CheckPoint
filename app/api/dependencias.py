from app.persistencia.conexao_redis import criar_cliente
from app.persistencia.repositorios.jogo import RepositorioJogo
from app.persistencia.repositorios.registro import RepositorioRegistro
from app.persistencia.repositorios.usuario import RepositorioUsuario


cliente_redis = criar_cliente()


def repositorios():
    return (
        RepositorioUsuario(cliente_redis),
        RepositorioJogo(cliente_redis),
        RepositorioRegistro(cliente_redis),
    )

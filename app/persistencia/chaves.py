def usuario(usuario_id: int) -> str:
    return f"usuario:{usuario_id}"


def jogo(jogo_id: int) -> str:
    return f"jogo:{jogo_id}"


def registro(registro_id: int) -> str:
    return f"registro:{registro_id}"


def indice_email(email: str) -> str:
    return f"indice:usuario:email:{email.strip().lower()}"


def indice_nome_usuario(nome: str) -> str:
    return f"indice:usuario:nome:{nome.strip().lower()}"


def indice_nome_jogo(nome: str) -> str:
    return f"indice:jogo:nome:{nome.strip().lower()}"


def registros_do_usuario(usuario_id: int) -> str:
    return f"usuario:{usuario_id}:registros"


def registros_do_jogo(jogo_id: int) -> str:
    return f"jogo:{jogo_id}:registros"


def indice_registro(usuario_id: int, jogo_id: int) -> str:
    return f"indice:registro:{usuario_id}:{jogo_id}"


def sequencia(entidade: str) -> str:
    return f"sequencia:{entidade}"

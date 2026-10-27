class ErroDePersistencia(Exception):
    """Erro base da camada de persistência."""


class RecursoNaoEncontrado(ErroDePersistencia):
    """Quando o item solicitado não existe."""


class RecursoDuplicado(ErroDePersistencia):
    """Quando uma regra de unicidade é violada."""


class RelacaoInvalida(ErroDePersistencia):
    """Quando uma relação aponta para um item inexistente."""

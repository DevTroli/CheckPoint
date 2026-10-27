# Checkpoint

Backend do Checkpoint, um catálogo pessoal de jogos com registros de progresso e avaliação.

Esta primeira etapa implementa a milestone **Banco** usando Redis como banco NoSQL principal.

## Requisitos

- Python 3.11+
- Docker e Docker Compose, para executar o Redis local

## Executar o Redis

```bash
docker compose up -d redis
```

O Redis ficará disponível em `localhost:6379`.

## Configuração

As variáveis abaixo possuem valores locais padrão:

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=
```

## Instalar dependências

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Testar

```bash
pytest -q
```

Os testes usam `fakeredis`, uma implementação de teste compatível com o cliente Redis. Assim, o comportamento dos repositórios pode ser validado sem depender de um servidor externo.

## Modelagem NoSQL

O Redis usa estruturas simples e explícitas:

| Entidade | Chave principal | Tipo | Uso |
| --- | --- | --- | --- |
| Usuário | `usuario:{id}` | Hash | Guarda dados da conta |
| Jogo | `jogo:{id}` | Hash | Guarda dados do catálogo |
| Registro | `registro:{id}` | Hash | Relaciona um usuário a um jogo |
| IDs de registros do usuário | `usuario:{id}:registros` | Set | Lista registros daquele usuário |
| IDs de registros do jogo | `jogo:{id}:registros` | Set | Lista usuários que registraram aquele jogo |
| Índice de e-mail | `indice:usuario:email:{email}` | String | Encontra usuário pelo e-mail |
| Índice de nome de usuário | `indice:usuario:nome:{nome}` | String | Encontra usuário pelo nome |
| Índice de nome de jogo | `indice:jogo:nome:{nome}` | String | Evita jogos duplicados pelo nome |
| Índice usuário-jogo | `indice:registro:{usuario_id}:{jogo_id}` | String | Garante um registro por usuário e jogo |
| Sequências | `sequencia:{entidade}` | String | Gera IDs incrementais |

Os nomes de campos seguem o domínio em português:

### Usuário

```text
id, nome_usuario, email, senha_hash, criado_em, atualizado_em
```

### Jogo

```text
id, nome, descricao, categoria, data_lancamento, publicadora,
desenvolvedora, criado_em, atualizado_em
```

### Registro

```text
id, usuario_id, jogo_id, progresso, tempo_jogado_minutos, nota,
status, avaliacao, criado_em, atualizado_em
```

## Regras de consistência

1. O e-mail e o nome de usuário são únicos.
2. O nome do jogo é único no catálogo nesta primeira versão.
3. Um usuário não pode ter dois registros para o mesmo jogo.
4. Um registro só pode apontar para usuário e jogo existentes.
5. Ao excluir um registro, seus índices e referências nos Sets são removidos.
6. A camada de serviço/backend será responsável por autenticação e permissões; esta milestone cuida da persistência.

## Estrutura

```text
checkpoint/
├── app/
│   └── persistencia/
│       ├── conexao_redis.py
│       ├── excecoes.py
│       ├── chaves.py
│       └── repositorios/
│           ├── usuario.py
│           ├── jogo.py
│           └── registro.py
├── tests/
│   └── test_repositorios.py
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

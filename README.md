# Checkpoint

Backend do Checkpoint, um catálogo pessoal de jogos com registros de progresso e avaliação.

O projeto usa **Django + Django REST Framework** para as rotas e serializers, mas mantém o **Redis como banco NoSQL principal**. O Django ORM não é usado para as entidades do domínio.

## Stack atual

- Django 5
- Django REST Framework
- Redis 7
- `redis-py`
- Argon2 para hash de senha
- `fakeredis` nos testes

O SQLite em memória aparece somente como configuração interna exigida por componentes do Django. Usuários, jogos, registros e gamificação ficam no Redis.

## Executar o Redis

```bash
docker compose up -d redis
```

O Redis ficará disponível em `localhost:6379`.

## Instalar dependências e executar a API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python manage.py runserver
```

A API ficará disponível em `http://127.0.0.1:8000`.

Variáveis de ambiente disponíveis:

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=
export DJANGO_SECRET_KEY=uma-chave-local
```

## Testar o projeto

```bash
pytest -q
python manage.py check
```

Os testes usam `fakeredis`, uma implementação compatível com o cliente Redis. Isso permite testar os repositórios e a API sem depender de um Redis externo. Para validar a integração com um Redis real, execute o Docker Compose antes de iniciar a API.

## Testar diretamente no Redis

Com o container em execução, abra o terminal do Redis:

```bash
docker exec -it checkpoint-redis redis-cli
```

Verifique se o servidor está respondendo:

```redis
PING
```

A resposta esperada é:

```text
PONG
```

Depois de cadastrar dados pela API, consulte os Hashes e índices:

```redis
SCAN 0 MATCH usuario:* COUNT 100
HGETALL usuario:1
GET indice:usuario:email:admin@example.com

SCAN 0 MATCH jogo:* COUNT 100
HGETALL jogo:1

SMEMBERS usuario:1:registros
HGETALL registro:1
GET indice:registro:1:1
```

Para verificar a gamificação:

```redis
ZSCORE ranking:xp usuario:1
ZRANGE ranking:xp 0 -1 REV WITHSCORES
HGETALL gamificacao:1
SCAN 0 MATCH atividade:1:* COUNT 100
```

O `ZRANGE ... REV WITHSCORES` mostra o ranking do maior XP para o menor. O backend usa `ZINCRBY` para somar XP e `ZRANGE` para consultar o ranking.

Para limpar somente o banco local de desenvolvimento, use com cuidado:

```redis
FLUSHDB
```

## Como testar a API com curl

Cadastre o primeiro usuário. Nesta versão, o primeiro usuário recebe o papel `admin` para permitir o cadastro inicial do catálogo:

```bash
curl -i -c cookies.txt -X POST http://127.0.0.1:8000/api/usuarios/ \
  -H 'Content-Type: application/json' \
  -d '{"nome_usuario":"admin","email":"admin@example.com","senha":"senha123"}'
```

Faça login e guarde o cookie de sessão:

```bash
curl -i -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","senha":"senha123"}'
```

Cadastre um jogo:

```bash
curl -i -b cookies.txt -X POST http://127.0.0.1:8000/api/jogos/ \
  -H 'Content-Type: application/json' \
  -d '{"nome":"Celeste","categoria":"Plataforma","data_lancamento":"2018-01-25"}'
```

Consulte o catálogo:

```bash
curl 'http://127.0.0.1:8000/api/jogos/?busca=celeste'
```

## Endpoints implementados

### Autenticação e usuário

```text
POST  /api/usuarios/
POST  /api/auth/login/
POST  /api/auth/logout/
GET   /api/usuarios/me/
PATCH /api/usuarios/me/
```

### Jogos

```text
GET    /api/jogos/
POST   /api/jogos/                 # admin
GET    /api/jogos/{id}/
PUT    /api/jogos/{id}/             # admin
DELETE /api/jogos/{id}/             # admin
```

A listagem aceita `busca`, `categoria` e `ordenar`.

### Registros pessoais

```text
GET    /api/registros/
POST   /api/registros/
GET    /api/registros/{id}/
PATCH  /api/registros/{id}/
DELETE /api/registros/{id}/
```

Cada usuário acessa somente seus próprios registros.

### Gamificação

```text
GET /api/gamificacao/me/
GET /api/gamificacao/ranking/?limite=10
```

Regras mínimas:

- criar um registro: `+25 XP`;
- atualizar um registro: `+5 XP`;
- primeira atividade do dia: `+5 XP`;
- a atividade diária repetida não gera XP novamente;
- dias consecutivos aumentam o streak;
- uma quebra de sequência reinicia o streak em `1`.

## Modelagem NoSQL

| Entidade | Chave principal | Tipo | Uso |
| --- | --- | --- | --- |
| Usuário | `usuario:{id}` | Hash | Dados da conta |
| Jogo | `jogo:{id}` | Hash | Dados do catálogo |
| Registro | `registro:{id}` | Hash | Relação entre usuário e jogo |
| Registros do usuário | `usuario:{id}:registros` | Set | Lista de registros do usuário |
| Registros do jogo | `jogo:{id}:registros` | Set | Registros associados ao jogo |
| Índice de e-mail | `indice:usuario:email:{email}` | String | Busca rápida por e-mail |
| Índice de nome de usuário | `indice:usuario:nome:{nome}` | String | Busca rápida por nome |
| Índice de nome de jogo | `indice:jogo:nome:{nome}` | String | Evita jogos repetidos |
| Índice usuário-jogo | `indice:registro:{usuario_id}:{jogo_id}` | String | Garante um registro único |
| Ranking de XP | `ranking:xp` | Sorted Set | Ordena usuários por XP |
| Perfil de gamificação | `gamificacao:{id}` | Hash | Streak e última atividade |
| Atividade do dia | `atividade:{id}:{data}` | String com expiração | Evita recompensa duplicada |

## Regras de consistência

1. E-mail e nome de usuário são únicos.
2. O nome do jogo é único nesta primeira versão.
3. Um usuário não pode registrar o mesmo jogo duas vezes.
4. Um registro só aponta para usuário e jogo existentes.
5. Exclusões removem registros relacionados e índices conhecidos.
6. Senhas nunca são armazenadas em texto puro.
7. O primeiro usuário cadastrado recebe `admin` para inicializar o catálogo.
8. As alterações de jogos exigem papel `admin`.

## Estrutura atual

```text
checkpoint/
├── app/
│   ├── api/
│   │   ├── dependencias.py
│   │   ├── gamificacao.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   └── persistencia/
│       ├── conexao_redis.py
│       ├── excecoes.py
│       ├── chaves.py
│       └── repositorios/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tests/
│   ├── test_api.py
│   └── test_repositorios.py
├── manage.py
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

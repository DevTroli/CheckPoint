# Checkpoint

O **Checkpoint** é um catálogo pessoal de jogos. Cada usuário pode registrar os jogos que jogou, acompanhar seu progresso, informar uma nota e escrever uma avaliação.

O projeto foi desenvolvido como um backend acadêmico usando **Django**, **Django REST Framework** e **Redis como banco NoSQL principal**.

## Stack e decisões

- **Django + DRF:** rotas, views, serializers e sessões.
- **Redis:** usuários, jogos, registros e gamificação.
- **redis-py:** comunicação com o Redis.
- **Argon2:** proteção das senhas.
- **fakeredis:** testes automatizados sem depender de um servidor externo.

O Django ORM não é usado para os dados do sistema. As entidades são armazenadas diretamente em Hashes, Sets, Strings e Sorted Sets do Redis.

## Executando o projeto

É necessário ter Python 3.11+ e Docker instalados.

```bash
git clone https://github.com/DevTroli/CheckPoint.git
cd CheckPoint
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Inicie o Redis:

```bash
docker compose up -d redis
```

Depois, execute o Django:

```bash
python manage.py runserver
```

A API ficará disponível em:

```text
http://127.0.0.1:8000
```

As principais variáveis de ambiente são:

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
DJANGO_SECRET_KEY=uma-chave-local
```

## Fluxo principal da API

O primeiro usuário cadastrado recebe o papel `admin`. Isso permite criar o catálogo inicial de jogos.

### Cadastro e login

```http
POST /api/usuarios/
POST /api/auth/login/
POST /api/auth/logout/
GET  /api/usuarios/me/
PATCH /api/usuarios/me/
```

Exemplo de cadastro:

```bash
curl -c cookies.txt -X POST http://127.0.0.1:8000/api/usuarios/ \
  -H 'Content-Type: application/json' \
  -d '{"nome_usuario":"admin","email":"admin@example.com","senha":"senha123"}'
```

Exemplo de login:

```bash
curl -b cookies.txt -c cookies.txt -X POST \
  http://127.0.0.1:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","senha":"senha123"}'
```

### Catálogo de jogos

```http
GET    /api/jogos/
POST   /api/jogos/
GET    /api/jogos/{id}/
PUT    /api/jogos/{id}/
DELETE /api/jogos/{id}/
```

As operações de escrita exigem um usuário administrador. A listagem aceita filtros simples:

```text
/api/jogos/?busca=zelda
/api/jogos/?categoria=RPG
/api/jogos/?ordenar=nome
```

### Registros pessoais

```http
GET    /api/registros/
POST   /api/registros/
GET    /api/registros/{id}/
PATCH  /api/registros/{id}/
DELETE /api/registros/{id}/
```

Cada registro guarda o progresso, o tempo jogado, a nota, o status e a avaliação do usuário. Um usuário não pode registrar o mesmo jogo duas vezes e só pode alterar os próprios registros.

### Gamificação

```http
GET /api/gamificacao/me/
GET /api/gamificacao/ranking/?limite=10
```

A gamificação foi mantida intencionalmente simples:

- criar um registro concede `25 XP`;
- atualizar um registro concede `5 XP`;
- a primeira atividade do dia concede `5 XP`;
- dias consecutivos aumentam o streak;
- a mesma atividade não concede XP duas vezes no mesmo dia.

O XP é acumulado com `ZINCRBY` e o ranking é consultado com `ZRANGE` em ordem decrescente.

## Conferindo os dados no Redis

Com o Redis em execução, abra o cliente:

```bash
docker exec -it checkpoint-redis redis-cli
```

Verifique a conexão:

```redis
PING
```

Consulte usuários, jogos e registros:

```redis
SCAN 0 MATCH usuario:* COUNT 100
HGETALL usuario:1

SCAN 0 MATCH jogo:* COUNT 100
HGETALL jogo:1

HGETALL registro:1
SMEMBERS usuario:1:registros
```

Consulte a gamificação:

```redis
ZSCORE ranking:xp usuario:1
ZRANGE ranking:xp 0 -1 REV WITHSCORES
HGETALL gamificacao:1
SCAN 0 MATCH atividade:1:* COUNT 100
```

Para limpar o banco local de desenvolvimento, use com cuidado:

```redis
FLUSHDB
```

## Modelagem Redis

As entidades principais usam Hashes:

```text
usuario:{id}
jogo:{id}
registro:{id}
```

Os Sets mantêm os índices de relacionamento:

```text
usuario:{id}:registros
jogo:{id}:registros
```

Strings são usadas para buscas rápidas e unicidade:

```text
indice:usuario:email:{email}
indice:usuario:nome:{nome}
indice:jogo:nome:{nome}
indice:registro:{usuario_id}:{jogo_id}
```

A gamificação usa:

```text
ranking:xp                  Sorted Set
gamificacao:{id}            Hash
atividade:{id}:{data}       String com expiração
```

## Testes

Execute a checagem do Django e os testes automatizados com:

```bash
python manage.py check
pytest -q
```

A suíte cobre persistência, CRUD, validações, autenticação, permissões, XP, ranking e streak.

## Estrutura do projeto

```text
app/
├── api/
│   ├── gamificacao.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
└── persistencia/
    ├── conexao_redis.py
    ├── chaves.py
    └── repositorios/

config/
├── settings.py
└── urls.py

tests/
├── test_api.py
└── test_repositorios.py
```

## Status

As milestones **Banco** e **BackEnd** estão concluídas. A próxima etapa é implementar o **FrontEnd**, consumindo os endpoints já definidos.

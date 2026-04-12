# 03 - Cach cai dat

## Dieu kien can

- Docker Desktop dang chay
- Docker Compose v2

## Chay Backend Microservices

Tu thu muc Day4-Day7:

```bash
docker compose -f docker-compose.microservices.yml up -d --build
```

Kiem tra:

```bash
docker compose -f docker-compose.microservices.yml ps
```

Dung va xoa volume:

```bash
docker compose -f docker-compose.microservices.yml down
docker compose -f docker-compose.microservices.yml down -v
```

## URL mac dinh

- http://localhost:8000
- http://localhost:8000/docs

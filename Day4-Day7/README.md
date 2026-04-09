# Day4-Day7 - Blog API (2 Kien Truc: Monolith va Microservices)

Project nay co 2 cach trien khai:

- Kien truc 1: Monolith (app FastAPI duy nhat)
- Kien truc 2: Microservices (auth/content/gateway tach rieng)

README nay mo ta ro ca 2 mo hinh de ban chon cach chay phu hop.

## 1. Kien truc Monolith (app/)

Mo ta:

- 1 service backend FastAPI trong thu muc app/
- 1 database PostgreSQL blogdb
- Frontend static duoc phuc vu cung backend

Luong request:

Client -> FastAPI app (localhost:8000 hoac localhost:3000) -> PostgreSQL (blogdb)

Compose file:

- docker-compose.yml

Chay monolith (tai thu muc Day4-Day7):

```bash
docker compose -f docker-compose.yml up -d --build
```

Dung monolith:

```bash
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml down
docker compose -f docker-compose.yml down -v
```

## 2. Kien truc Microservices (microservices/)

Mo ta:

- auth-service: dang ky, dang nhap, xac thuc token
- content-service: CRUD post, comment, upload image
- api-gateway: route request tu client sang auth/content
- 2 database rieng: auth-db (authdb), content-db (contentdb)

Luong request:

Client -> API Gateway (localhost:8000 hoac localhost:3000)
-> Auth Service (internal:8001) + Content Service (internal:8002)
-> PostgreSQL (authdb, contentdb)

Compose file:

- docker-compose.microservices.yml

Chay microservices (tai thu muc Day4-Day7):

```bash
docker compose -f docker-compose.microservices.yml up -d --build
```

Dung microservices:

```bash
docker compose -f docker-compose.microservices.yml ps
docker compose -f docker-compose.microservices.yml down
docker compose -f docker-compose.microservices.yml down -v
```

## URL truy cap (ca 2 mo hinh)

- Frontend: http://localhost:8000
- Alias frontend: http://localhost:3000
- Swagger docs: http://localhost:8000/docs

## Ket qua test thuc te

Da test thanh cong voi kien truc microservices:

- Build va start full stack thanh cong
- Tat ca container len trang thai Up/Healthy
- Gateway /docs tra ve HTTP 200
- Luong E2E qua gateway:
  - Dang ky user
  - Dang nhap lay access token
  - Goi /api/auth/me voi Bearer token
  - Tao bai viet qua /api/posts/
  - Lay danh sach bai viet qua /api/posts/

## API chinh (goi qua gateway hoac monolith)

Auth:

- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me

Posts:

- GET /api/posts/
- POST /api/posts/
- PUT /api/posts/{post_id}
- DELETE /api/posts/{post_id}
- POST /api/posts/upload-image

Comments:

- GET /api/posts/{post_id}/comments
- POST /api/posts/{post_id}/comments
- DELETE /api/posts/{post_id}/comments/{comment_id}

## Auth flow

1. Dang ky: POST /api/auth/register
2. Dang nhap: POST /api/auth/login
3. Truyen token cho API can dang nhap:

```http
Authorization: Bearer <access_token>
```

## Luu y quan trong

- Endpoint noi bo /api/auth/internal/* chi dung trong microservices va bi chan o gateway.
- Health endpoint cua auth/content chi dung noi bo cho Docker healthcheck.
- Upload file duoc luu qua volume (microservices) hoac thu muc uploads (monolith).

## Troubleshooting nhanh

Neu build fail gateway voi loi khong tim thay requirements.txt:

- Kiem tra microservices/gateway/Dockerfile copy dung duong dan theo build context.

Xem log microservices:

```bash
docker compose -f docker-compose.microservices.yml logs -f api-gateway
docker compose -f docker-compose.microservices.yml logs -f auth-service
docker compose -f docker-compose.microservices.yml logs -f content-service
```

Xem log monolith:

```bash
docker compose -f docker-compose.yml logs -f web
```

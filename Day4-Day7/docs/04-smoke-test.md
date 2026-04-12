# 04 - Smoke test

Tai lieu nay su dung curl de test nhanh luong chinh.

## 1) Kiem tra docs

```bash
curl -i http://localhost:8000/docs
```

Ky vong: HTTP 200.

## 2) Dang ky tai khoan

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "email": "demo_user@example.com",
    "full_name": "Demo User",
    "password": "123456"
  }'
```

## 3) Dang nhap lay token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo_user&password=123456"
```

Luu access_token tra ve.

## 4) Goi /me

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## 5) Tao post

```bash
curl -X POST http://localhost:8000/api/posts/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Smoke Test Post",
    "content": "Noi dung test",
    "is_published": true
  }'
```

## 6) Lay danh sach post

```bash
curl -X GET "http://localhost:8000/api/posts/?skip=0&limit=10"
```

Neu 6 buoc deu pass, smoke test co ban da dat.

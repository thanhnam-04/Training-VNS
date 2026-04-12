# Auth API

Base path: /api/auth

## POST /register

Mo ta:

- Tao tai khoan moi
- Neu la tai khoan dau tien, role duoc gan admin

Request body:

```json
{
  "username": "string",
  "email": "string",
  "full_name": "string",
  "password": "string"
}
```

## POST /login

Mo ta:

- Dang nhap bang username/password
- Tra ve access_token (Bearer)

Request form:

- username
- password

Response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

## GET /me

Mo ta:

- Lay thong tin user hien tai tu token

Header:

- Authorization: Bearer <access_token>

## GET /users

Mo ta:

- Admin lay danh sach tat ca user

Header:

- Authorization: Bearer <access_token_admin>

## PATCH /users/{user_id}/role

Mo ta:

- Admin cap role cho user
- Role hop le: admin, user

Header:

- Authorization: Bearer <access_token_admin>

Request body:

```json
{
  "role": "admin"
}
```

# Day4 - Personal Blog API (FastAPI + PostgreSQL + JWT)

Mini project blog ca nhan voi backend FastAPI, database PostgreSQL, xac thuc JWT, phan quyen role, va frontend HTML/Bootstrap.

## Features

- Dang ky / Dang nhap (JWT Bearer token)
- Hash mat khau bang `pbkdf2_sha256` (khong luu plain text)
- CRUD bai viet
- Upload anh cho bai viet
- Comment bai viet
- Xoa comment (admin hoac chinh chu comment)
- Sua / xoa bai viet (admin hoac chinh chu bai viet)
- Hien role ngay tren giao dien (`ADMIN` / `USER`)

## Tech Stack

- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- JWT (PyJWT)
- Passlib
- Docker Compose
- Bootstrap 5 + Vanilla JS

## Project Structure

```text
Day4/
	app/
		main.py
		api/
			routers/
				auth.py
				posts.py
		core/
			database.py
			security.py
		services/
			auth_service.py
			post_service.py
			comment_service.py
		models/
			user.py
			post.py
			comment.py
		schemas/
			user.py
			auth.py
			post.py
			comment.py
	frontend/
		index.html
	docker-compose.yml
	Dockerfile
	uploads/
	pyproject.toml
	README.md
```

## Run With Docker

Tu thu muc `Day4`:

```bash
docker-compose up -d --build
```

Mo app tai:

- Frontend + API docs host: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

Dung app:

1. Dang ky tai khoan
2. Dang nhap de nhan token
3. Tao bai viet, upload anh, comment

## Reset Database

Xoa toan bo du lieu Postgres:

```bash
docker-compose down -v
```

Khoi dong lai:

```bash
docker-compose up -d --build
```

## Authentication Flow

1. `POST /api/auth/register` de tao tai khoan
2. `POST /api/auth/login` de lay `access_token`
3. Goi API can auth voi header:

```http
Authorization: Bearer <access_token>
```

## Main API Endpoints

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Posts

- `GET /api/posts/`
- `POST /api/posts/`
- `PUT /api/posts/{post_id}`
- `DELETE /api/posts/{post_id}`
- `POST /api/posts/upload-image`

### Comments

- `GET /api/posts/{post_id}/comments`
- `POST /api/posts/{post_id}/comments`
- `DELETE /api/posts/{post_id}/comments/{comment_id}`

## Roles And Permissions

- `user`
	- Tao bai viet
	- Sua/xoa bai viet cua chinh minh
	- Comment
	- Xoa comment cua chinh minh

- `admin`
	- Toan bo quyen cua user
	- Sua/xoa bai viet cua user khac
	- Xoa comment cua user khac

## Troubleshooting

### Khong vao duoc `localhost:3000`

Frontend dang duoc mount chung voi FastAPI, truy cap:

- `http://localhost:8000`

### Loi `email-validator is not installed`

Da khai bao dependency trong `pyproject.toml`. Neu gap lai, rebuild image:

```bash
docker-compose build --no-cache web
docker-compose up -d
```

## Notes

- Du lieu anh duoc luu trong thu muc `uploads/`, DB chi luu `image_url`.
- Mat khau luu duoi dang hash trong cot `password_hash`.

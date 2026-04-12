# Day4-Day7 - Blog Backend API (Microservices)

README này tập trung vào backend microservices và 5 phần chính để học, triển khai, kiểm thử API.

## 1. Kiến trúc hệ thống

Project triển khai theo kiến trúc backend microservices:

- auth-service + content-service + api-gateway + 2 PostgreSQL riêng.

Sơ đồ nhanh:

- Microservices: Client -> Gateway -> Auth/Content services -> PostgreSQL

Tài liệu chi tiết:

- [docs/01-kien-truc-he-thong.md](docs/01-kien-truc-he-thong.md)

## 2. Cấu trúc thư mục

Thư mục quan trọng trong Day4-Day7:

- microservices/: source auth-service, content-service, gateway
- frontend/: giao diện static, được gateway phục vụ tại /
- uploads/: nơi lưu file upload
- docker-compose.microservices.yml: chạy microservices

Tài liệu chi tiết:

- [docs/02-cau-truc-thu-muc.md](docs/02-cau-truc-thu-muc.md)

## 3. Cách cài đặt

Yêu cầu:

- Docker Desktop
- Docker Compose v2

Khởi động microservices:

- Lệnh chạy: docker compose -f docker-compose.microservices.yml up -d --build

Tài liệu cài đặt đầy đủ:

- [docs/03-cai-dat.md](docs/03-cai-dat.md)

## Tài khoản mẫu (admin và user)

Hệ thống đang dùng quy tắc bootstrap role:

- Tài khoản đăng ký đầu tiên sẽ là admin.
- Các tài khoản đăng ký sau sẽ là user.

Tài khoản mẫu đề xuất để test:

- Admin:
	- username: admin_demo
	- email: admin_demo@example.com
	- password: Admin@123
- User:
	- username: user_demo
	- email: user_demo@example.com
	- password: User@123

Luồng tạo mẫu nhanh:

1. Đăng ký admin_demo trước.
2. Đăng ký user_demo sau.
3. Đăng nhập từng tài khoản qua API login để lấy token kiểm thử.

Lưu ý:

- Nếu bạn đã có dữ liệu cũ trong database thì admin có thể không phải tài khoản admin_demo.
- Muốn tạo lại đúng cặp mẫu admin/user, cần reset volume database rồi đăng ký lại theo đúng thứ tự trên.

Nâng quyền nhanh lên admin (không cần reset DB):

```bash
docker compose -f docker-compose.microservices.yml exec -T auth-db psql -U postgres -d authdb -c "UPDATE users SET role='admin' WHERE username='admin_demo';"
```

Kiểm tra lại role qua API:

1. Đăng nhập bằng `admin_demo`.
2. Gọi `GET /api/auth/me` với Bearer token vừa nhận.
3. Xác nhận trường `role` là `admin`.

## 4. Cách chạy smoke test

Smoke test tối thiểu cần xác nhận:

- Container lên trạng thái healthy/up
- /docs trả về HTTP 200
- Đăng ký -> Đăng nhập -> Lấy profile me
- Tạo post -> Lấy danh sách post

Tài liệu và lệnh test mẫu:

- [docs/04-smoke-test.md](docs/04-smoke-test.md)

## 5. Tài liệu chức năng và API endpoint

Quyền admin hiện có thể:

- Xem danh sách user
- Cấp role admin/user cho user khác

Auth:

- [docs/features/auth-api.md](docs/features/auth-api.md)

Posts:

- [docs/features/posts-api.md](docs/features/posts-api.md)

Comments:

- [docs/features/comments-api.md](docs/features/comments-api.md)

## URL mặc định

- API Gateway: http://localhost:8000
- Alias frontend: http://localhost:3000
- Swagger docs (qua gateway): http://localhost:8000/docs

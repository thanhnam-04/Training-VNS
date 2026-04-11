# ecommerce-microservices

README này được viết thuần tiếng Việt để dễ đọc và dễ bàn giao.

## 1. Kiến trúc hệ thống

Hệ thống theo mô hình microservices, gồm các thành phần:

- frontend: giao diện web (Nginx, cổng 3000)
- api-gateway: định tuyến API (Nginx, cổng 8000)
- user-service: xác thực, người dùng, JWT, cổng quản trị
- product-service: kho hàng, sản phẩm, danh mục
- cart-service: giỏ hàng
- order-service: thanh toán và đơn hàng
- notification-service: API thông báo và tra cứu trạng thái tác vụ
- notification-worker, notification-beat: Celery worker/scheduler
- db: PostgreSQL
- redis: message broker/cache

Tài liệu chi tiết: [docs/01-kien-truc-he-thong.md](docs/01-kien-truc-he-thong.md)

## 2. Cấu trúc thư mục

```text
ecommerce-microservices/
├── api-gateway/
├── frontend/
├── services/
│   ├── user-service/
│   ├── product-service/
│   ├── cart-service/
│   ├── order-service/
│   └── notification-service/
├── docs/
├── docker-compose.yml
├── .env.example
└── README.md
```

Tài liệu chi tiết: [docs/02-cau-truc-thu-muc.md](docs/02-cau-truc-thu-muc.md)

## 3. Cách cài đặt

1. Tạo file .env từ .env.example.
2. Build và chạy hệ thống:

```bash
docker compose up -d --build
```

3. Kiểm tra trạng thái:

```bash
docker compose ps
```

Tài liệu chi tiết: [docs/03-cai-dat.md](docs/03-cai-dat.md)

## 4. Cách chạy smoke test

Smoke test gồm 5 nhóm: health check, auth, inventory, cart, checkout.

Tài liệu chi tiết: [docs/04-smoke-test.md](docs/04-smoke-test.md)

## 5. Link tài liệu md cho chức năng và API endpoint

- Auth/User API: [docs/features/auth-api.md](docs/features/auth-api.md)
- Inventory API: [docs/features/inventory-api.md](docs/features/inventory-api.md)
- Cart API: [docs/features/cart-api.md](docs/features/cart-api.md)
- Order/Checkout API: [docs/features/order-api.md](docs/features/order-api.md)
- Notification API: [docs/features/notification-api.md](docs/features/notification-api.md)

## URL nhanh

- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- Admin: http://localhost:8000/admin/
- Flower: http://localhost:5555

## Tài khoản demo

- Admin: admin@shopvns.com / Admin@123
- User: user@shopvns.com / User@123

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

Chạy smoke test tự động:

```bash
docker compose exec user-service sh -lc "pip install -r requirements-dev.txt"
docker compose exec user-service sh -lc "SMOKE_BASE_URL=http://api-gateway pytest tests/smoke -q"
```

## 5. Cách chạy unit test, coverage, lint

Luu y: khong chay `pytest` o thu muc goc repo vi moi service co cau hinh test rieng.

1. Chay unit test + lint cho tung service:

```bash
docker compose exec user-service sh -lc "pip install -r requirements-dev.txt; pytest; ruff check tests"
docker compose exec order-service sh -lc "pip install -r requirements-dev.txt; pytest; ruff check tests"
docker compose exec cart-service sh -lc "pip install -r requirements-dev.txt; pytest; ruff check tests"
docker compose exec product-service sh -lc "pip install -r requirements-dev.txt; pytest; ruff check tests"
docker compose exec notification-service sh -lc "pip install -r requirements-dev.txt; pytest; ruff check tests"
```

2. Do coverage module notifications tasks:

```bash
docker compose exec user-service sh -lc "pytest --cov=apps.notifications.tasks --cov-report=term-missing"
docker compose exec order-service sh -lc "pytest --cov=apps.notifications.tasks --cov-report=term-missing"
docker compose exec cart-service sh -lc "pytest --cov=apps.notifications.tasks --cov-report=term-missing"
docker compose exec product-service sh -lc "pytest --cov=apps.notifications.tasks --cov-report=term-missing"
docker compose exec notification-service sh -lc "pytest --cov=apps.notifications.tasks --cov-report=term-missing"
```

3. Do coverage module core service_clients:

```bash
docker compose exec user-service sh -lc "pytest tests/test_service_clients.py --cov=apps.orders.service_clients --cov-report=term-missing"
docker compose exec order-service sh -lc "pytest tests/test_service_clients.py --cov=apps.orders.service_clients --cov-report=term-missing"
docker compose exec cart-service sh -lc "pytest tests/test_service_clients.py --cov=apps.orders.service_clients --cov-report=term-missing"
docker compose exec product-service sh -lc "pytest tests/test_service_clients.py --cov=apps.orders.service_clients --cov-report=term-missing"
docker compose exec notification-service sh -lc "pytest tests/test_service_clients.py --cov=apps.orders.service_clients --cov-report=term-missing"
```

4. Chay nhanh smoke test xuyen 5 service qua API gateway:

```bash
docker compose exec user-service sh -lc "SMOKE_BASE_URL=http://api-gateway pytest tests/smoke -o addopts=''"
```

## 6. Link tài liệu md cho chức năng và API endpoint

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

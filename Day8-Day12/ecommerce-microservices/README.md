# ecommerce-microservices

Kien truc duoc tach theo huong microservices:

```text
ecommerce-microservices/
├── services/
│   ├── user-service/
│   ├── product-service/
│   ├── cart-service/
│   ├── order-service/
│   └── notification-service/
├── api-gateway/
├── frontend/
├── docker-compose.yml
├── .env
└── README.md
```

## Mapping domain

- user-service: Auth, User, JWT, admin portal
- product-service: Inventory, Product, Category
- cart-service: Cart
- order-service: Order, OrderItem, checkout orchestration
- notification-service: Notification API
- notification-worker/notification-beat: async jobs va scheduler cho notification

## Luu y implementation

- Tat ca service da co codebase rieng trong `services/*-service` va duoc build truc tiep tu folder service.
- `order-service` goi service-to-service sang `cart-service` va `product-service` qua HTTP cho checkout.
- API Gateway tiep nhan toan bo request tai cong `8000`.

## Chay he thong

```bash
cd N:\Training-VNS\Day8-Day12\ecommerce-microservices

# Build + start
docker compose up -d --build

# Logs
docker compose logs -f api-gateway
docker compose logs -f order-service
docker compose logs -f notification-worker
```

## URL

- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- Django Admin: http://localhost:8000/admin/
- Flower: http://localhost:5555

## Health checks

- http://localhost:8000/health/user
- http://localhost:8000/health/product
- http://localhost:8000/health/cart
- http://localhost:8000/health/order
- http://localhost:8000/health/notification

## Tai khoan demo

- Admin: admin@shopvns.com / Admin@123
- User: user@shopvns.com / User@123

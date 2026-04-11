# Cấu trúc thư mục

```text
ecommerce-microservices/
├── api-gateway/
│   └── nginx.conf
├── frontend/
│   ├── index.html
│   ├── nginx.conf
│   ├── css/
│   └── js/
├── services/
│   ├── user-service/
│   ├── product-service/
│   ├── cart-service/
│   ├── order-service/
│   └── notification-service/
├── docs/
│   ├── 01-kien-truc-he-thong.md
│   ├── 02-cau-truc-thu-muc.md
│   ├── 03-cai-dat.md
│   ├── 04-smoke-test.md
│   └── features/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quy ước
- Mỗi service có codebase riêng trong services/*-service.
- Mỗi service có config URL riêng (urls_*_service.py).
- Frontend chỉ gọi qua /api/* trên gateway, không gọi trực tiếp service.

# Smoke test

## 1) Health check
```bash
curl http://localhost:8000/health/user
curl http://localhost:8000/health/product
curl http://localhost:8000/health/cart
curl http://localhost:8000/health/order
curl http://localhost:8000/health/notification
```

## 2) Auth flow
```bash
curl -X POST http://localhost:8000/api/auth/login/ \\
  -H "Content-Type: application/json" \\
  -d '{"email":"admin@shopvns.com","password":"Admin@123"}'
```
Kiểm tra response có access và refresh token.

## 3) Inventory read
```bash
curl http://localhost:8000/api/inventory/products/
```

## 4) Cart flow
```bash
# Lấy giỏ hàng
curl http://localhost:8000/api/cart/ -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## 5) Checkout flow
```bash
curl -X POST http://localhost:8000/api/orders/checkout/ \\
  -H "Authorization: Bearer <ACCESS_TOKEN>" \\
  -H "Content-Type: application/json" \\
  -d '{"shipping_name":"Smoke Test","shipping_phone":"0900000000","shipping_address":"HCM","payment_method":"cod"}'
```
Kỳ vọng: trả về đơn hàng mới và worker gửi email.

## 6) Notification email task
- Kiểm tra log worker:
```bash
docker compose logs --tail=200 notification-worker
```
- Tìm dòng log gửi email đơn mới cho admin.

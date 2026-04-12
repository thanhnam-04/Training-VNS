# Kiến trúc hệ thống

## Tổng quan
Hệ thống được tách thành 5 microservice, 1 API Gateway, 1 frontend Nginx, và các thành phần hạ tầng (PostgreSQL, Redis, Celery worker/beat).

## Thành phần chính
- frontend: giao diện web, chạy qua Nginx tại cổng 3000.
- api-gateway: định tuyến request vào từng service backend tại cổng 8000.
- user-service: auth, user, JWT, admin portal.
- product-service: category, product, stock movement, reserve/release stock.
- cart-service: giỏ hàng của user.
- order-service: checkout, tạo đơn, lịch sử đơn, admin order CRUD.
- notification-service: endpoint task status, test email, chạy Celery worker/beat.

## Luồng checkout
1. Frontend gọi POST /api/orders/checkout/ qua gateway.
2. order-service đọc giỏ hàng từ cart-service.
3. order-service reserve stock qua product-service.
4. order-service tạo Order và OrderItem.
5. order-service clear cart.
6. notification tasks gửi email xác nhận cho user và email đơn mới cho admin.

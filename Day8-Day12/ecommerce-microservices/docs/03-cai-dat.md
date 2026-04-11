# Cài đặt

## Điều kiện
- Docker Desktop
- Docker Compose v2

## Bước cài đặt
1. Tạo file .env từ .env.example và cập nhật giá trị cần thiết.
2. Build và khởi động hệ thống:

```bash
docker compose up -d --build
```

3. Kiểm tra service đang chạy:

```bash
docker compose ps
```

## URL mặc định
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- Admin: http://localhost:8000/admin/
- Flower: http://localhost:5555

## Lưu ý email
Nếu muốn gửi thông báo đơn mới cho nhiều admin, thêm biến sau vào .env:

```env
ADMIN_ORDER_ALERT_EMAILS=admin1@domain.com,admin2@domain.com
```

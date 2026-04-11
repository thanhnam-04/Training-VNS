# Chức năng Notification

Base path: /api/notifications/

## Endpoint
- GET /api/notifications/task/{task_id}/
- POST /api/notifications/test-email/

## Background tasks
- send_order_confirmation_email
- send_new_order_admin_email
- send_order_status_email
- send_low_stock_alert

## Mục đích
- Theo dõi task async và gửi email hệ thống.

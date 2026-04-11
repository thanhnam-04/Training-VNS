# Chức năng Inventory

Base path: /api/inventory/

## Endpoint
- GET /api/inventory/categories/
- GET /api/inventory/tags/
- GET /api/inventory/suppliers/
- GET /api/inventory/products/
- GET /api/inventory/products/{id}/
- GET /api/inventory/stock-movements/
- GET /api/inventory/stats/

## Internal endpoint (service-to-service)
- POST /api/inventory/internal/reserve-stock/
- POST /api/inventory/internal/release-stock/

## Mục đích
- Quản lý danh mục, sản phẩm, tồn kho và cập nhật kho trong checkout.

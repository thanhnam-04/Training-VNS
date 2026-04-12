# 01 - Kien truc he thong

Day4-Day7 duoc trien khai theo mo hinh backend microservices.

## Backend microservices

Thanh phan:

- api-gateway (Nginx)
- auth-service (dang ky, dang nhap, validate token)
- content-service (posts, comments, upload image)
- auth-db + content-db

Luong request:

Client -> Gateway -> Auth/Content -> PostgreSQL

Diem manh:

- Tach domain ro rang
- De scale theo service

## RBAC

He thong su dung RBAC dua tren role cua user.

- role admin: co quyen thao tac moi tai nguyen
- role user: thao tac tai nguyen cua chinh minh

Kiem tra quyen da duoc dong goi thanh class dependency de tai su dung va tranh hard-code role trong business logic.

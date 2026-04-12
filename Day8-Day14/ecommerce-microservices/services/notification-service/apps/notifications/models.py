from django.db import models


# Notifications app sử dụng Celery tasks và Django signals
# Không có models riêng — signals lắng nghe từ apps khác

import os
import django
from django.core.files.base import ContentFile
import urllib.request

# Setup Django standalone
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from apps.inventory.models import Product

print("Tiến hành tải ảnh chất lượng cao cho các sản phẩm...")

# Unsplash Premium Tech Images
image_map = {
    "Máy tính bảng": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?q=80&w=800&auto=format&fit=crop", 
    "Smartwatch": "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?q=80&w=800&auto=format&fit=crop", 
    "Phụ kiện": "https://images.unsplash.com/photo-1606220588913-b3aecb4b2609?q=80&w=800&auto=format&fit=crop", 
    "Laptop": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=800&auto=format&fit=crop", 
    "Điện thoại": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?q=80&w=800&auto=format&fit=crop", 
}

default_img = "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?q=80&w=800&auto=format&fit=crop"

products = Product.objects.all()

for p in products:
    cat_name = p.category.name if p.category else ""
    url = image_map.get(cat_name, default_img)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            if p.image:
                p.image.delete(save=False)
            file_name = f"{p.sku.lower()}_mock.jpg"
            p.image.save(file_name, ContentFile(response.read()), save=True)
            print(f"✅ Đã tải và thêm ảnh siêu đẹp cho: {p.name}")
    except Exception as e:
        print(f"❌ Lỗi tải ảnh cho {p.name}: {e}")

print("✨ Hoàn tất cập nhật ảnh!")

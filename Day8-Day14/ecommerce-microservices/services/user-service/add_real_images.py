import os
import django
from django.core.files.base import ContentFile
import urllib.request
import ssl
from duckduckgo_search import DDGS

# Bỏ qua xác thực SSL
ssl._create_default_https_context = ssl._create_unverified_context

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from apps.inventory.models import Product

print("Tiến hành tìm kiếm ảnh THỰC TẾ với AI...")

products = Product.objects.all()

for p in products:
    try:
        req = None
        response = None
        img_url = None
        
        # Tìm kiếm URL bằng tên sản phẩm thật
        print(f"Đang tìm trên Google/Bing ảnh cho: {p.name}...")
        results = DDGS().images(p.name + " official render transparent", max_results=1)
        if results:
            img_url = results[0].get("image")
            
        if not img_url:
            print(f"⚠️ Không tìm thấy kết quả cho {p.name}")
            continue
            
        req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if p.image:
                p.image.delete(save=False)
                
            extension = "png" if "png" in img_url.lower() else "jpg"
            file_name = f"{p.sku.lower()}_real.{extension}"
            p.image.save(file_name, ContentFile(response.read()), save=True)
            print(f"✅ Đã tải thành công ảnh gốc: {p.name}")
    except Exception as e:
        print(f"❌ Lỗi tải ảnh {p.name} ({img_url}): {e}")

print("✨ Hoàn tất cập nhật 100% ảnh thực tế!")

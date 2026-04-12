"""
Management Command: seed_data
Tạo dữ liệu mẫu để demo ngay sau khi chạy project
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu cho ShopVNS"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("🚀 Bắt đầu seed dữ liệu..."))
        self._create_users()
        self._create_categories()
        self._create_tags()
        self._create_suppliers()
        self._create_products()
        self.stdout.write(self.style.SUCCESS("✅ Seed dữ liệu hoàn thành!"))

    def _create_users(self):
        # Admin
        if not User.objects.filter(email="admin@shopvns.com").exists():
            User.objects.create_superuser(
                username="admin", email="admin@shopvns.com",
                password="Admin@123", first_name="Admin", last_name="ShopVNS"
            )
            self.stdout.write("  👤 Tạo admin@shopvns.com / Admin@123")

        # Customer
        if not User.objects.filter(email="user@shopvns.com").exists():
            User.objects.create_user(
                username="customer1", email="user@shopvns.com",
                password="User@123", first_name="Nguyễn", last_name="Văn A",
                phone="0901234567"
            )
            self.stdout.write("  👤 Tạo user@shopvns.com / User@123")

    def _create_categories(self):
        from apps.inventory.models import Category
        categories = [
            ("Điện thoại", "📱"), ("Laptop", "💻"), ("Phụ kiện", "🎧"),
            ("Máy tính bảng", "📟"), ("Smartwatch", "⌚"), ("Loa & Âm thanh", "🔊"),
        ]
        for name, icon in categories:
            Category.objects.get_or_create(name=name, defaults={"icon": icon})
        self.stdout.write(f"  📂 Tạo {len(categories)} danh mục")

    def _create_tags(self):
        from apps.inventory.models import Tag
        tags = ["Hot", "Sale", "Mới", "Bestseller", "Pin lâu", "Flagship", "Gaming", "Chính hãng"]
        for tag in tags:
            Tag.objects.get_or_create(name=tag)
        self.stdout.write(f"  🏷️ Tạo {len(tags)} tags")

    def _create_suppliers(self):
        from apps.inventory.models import Supplier
        suppliers = [
            ("Apple Vietnam", "Nguyễn Minh", "apple@vn.com", "0281234567"),
            ("Samsung Electronics", "Trần Hoa", "samsung@vn.com", "0289876543"),
            ("Xiaomi Vietnam", "Lê Nam", "xiaomi@vn.com", "0287654321"),
            ("Dell Technologies", "Phạm Linh", "dell@vn.com", "0285432109"),
        ]
        for name, contact, email, phone in suppliers:
            Supplier.objects.get_or_create(name=name, defaults={
                "contact_name": contact, "email": email, "phone": phone
            })
        self.stdout.write(f"  🏭 Tạo {len(suppliers)} nhà cung cấp")

    def _create_products(self):
        from apps.inventory.models import Category, Supplier, Tag, Product

        products_data = [
            {"name": "iPhone 15 Pro Max 256GB", "sku": "IP15PM-256", "price": 34_990_000, "cost_price": 28_000_000, "stock": 25, "cat": "Điện thoại", "sup": "Apple Vietnam", "featured": True, "tags": ["Hot", "Flagship", "Chính hãng"]},
            {"name": "iPhone 15 128GB", "sku": "IP15-128", "price": 22_990_000, "cost_price": 18_000_000, "stock": 40, "cat": "Điện thoại", "sup": "Apple Vietnam", "featured": False, "tags": ["Chính hãng", "Mới"]},
            {"name": "Samsung Galaxy S24 Ultra", "sku": "SS-S24U", "price": 31_990_000, "cost_price": 25_000_000, "stock": 30, "cat": "Điện thoại", "sup": "Samsung Electronics", "featured": True, "tags": ["Hot", "Flagship"]},
            {"name": "Samsung Galaxy A55 5G", "sku": "SS-A55", "price": 10_990_000, "cost_price": 8_500_000, "stock": 50, "cat": "Điện thoại", "sup": "Samsung Electronics", "featured": False, "tags": ["Sale", "Mới"]},
            {"name": "Xiaomi 14 Pro", "sku": "XM-14P", "price": 18_990_000, "cost_price": 15_000_000, "stock": 20, "cat": "Điện thoại", "sup": "Xiaomi Vietnam", "featured": True, "tags": ["Hot", "Chính hãng"]},
            {"name": "Xiaomi Redmi Note 13 Pro", "sku": "XM-RN13P", "price": 8_490_000, "cost_price": 6_500_000, "stock": 3, "cat": "Điện thoại", "sup": "Xiaomi Vietnam", "featured": False, "tags": ["Sale", "Bestseller"]},
            {"name": "MacBook Pro M3 14 inch", "sku": "MBP-M3-14", "price": 49_990_000, "cost_price": 42_000_000, "stock": 10, "cat": "Laptop", "sup": "Apple Vietnam", "featured": True, "tags": ["Flagship", "Hot"]},
            {"name": "MacBook Air M2 13 inch", "sku": "MBA-M2-13", "price": 28_990_000, "cost_price": 23_000_000, "stock": 15, "cat": "Laptop", "sup": "Apple Vietnam", "featured": False, "tags": ["Bestseller", "Chính hãng"]},
            {"name": "Dell XPS 15 OLED", "sku": "DELL-XPS15", "price": 45_990_000, "cost_price": 38_000_000, "stock": 8, "cat": "Laptop", "sup": "Dell Technologies", "featured": True, "tags": ["Hot", "Gaming"]},
            {"name": "AirPods Pro 2nd Gen", "sku": "APP-2G", "price": 6_290_000, "cost_price": 4_800_000, "stock": 60, "cat": "Phụ kiện", "sup": "Apple Vietnam", "featured": True, "tags": ["Bestseller", "Hot"]},
            {"name": "Samsung Galaxy Watch 6", "sku": "SS-GW6", "price": 7_990_000, "cost_price": 6_000_000, "stock": 25, "cat": "Smartwatch", "sup": "Samsung Electronics", "featured": False, "tags": ["Mới", "Chính hãng"]},
            {"name": "iPad Pro M4 11 inch", "sku": "IPAD-PRO-M4", "price": 26_990_000, "cost_price": 21_000_000, "stock": 2, "cat": "Máy tính bảng", "sup": "Apple Vietnam", "featured": True, "tags": ["Flagship", "Hot", "Mới"]},
        ]

        created = 0
        for data in products_data:
            cat = Category.objects.get(name=data["cat"])
            sup = Supplier.objects.get(name=data["sup"])

            product, is_new = Product.objects.get_or_create(
                sku=data["sku"],
                defaults={
                    "name": data["name"],
                    "price": Decimal(data["price"]),
                    "cost_price": Decimal(data["cost_price"]),
                    "stock": data["stock"],
                    "min_stock": 5,
                    "category": cat,
                    "supplier": sup,
                    "is_featured": data["featured"],
                    "description": f"Sản phẩm chính hãng {data['name']} - {data['cat']}. Bảo hành 12 tháng.",
                }
            )
            if is_new:
                tags = Tag.objects.filter(name__in=data["tags"])
                product.tags.set(tags)
                created += 1

        self.stdout.write(f"  📦 Tạo {created} sản phẩm mới ({len(products_data)} tổng)")

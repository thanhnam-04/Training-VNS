"""
Notifications Tasks — Day 11: Celery Tasks
Demo: gửi email async, xử lý ảnh, cập nhật stock
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id: int):
    """
    Task: Gửi email xác nhận đơn hàng
    Trigger: Sau khi tạo Order thành công (từ checkout view)
    """
    from apps.orders.models import Order

    try:
        order = Order.objects.select_related("user").prefetch_related("items").get(pk=order_id)

        items_text = "\n".join([
            f"  - {item.product_name} x{item.quantity}: {item.subtotal:,.0f} ₫"
            for item in order.items.all()
        ])

        message = f"""
Xin chào {order.user.full_name}!

Đơn hàng #{order.order_number} của bạn đã được đặt thành công.

📦 CHI TIẾT ĐƠN HÀNG:
{items_text}

💰 Tạm tính:     {order.subtotal:,.0f} ₫
🚚 Phí giao:     {order.shipping_fee:,.0f} ₫
✅ Tổng cộng:    {order.total_amount:,.0f} ₫

📍 Giao đến: {order.shipping_address}
👤 Người nhận: {order.shipping_name} — {order.shipping_phone}
💳 Thanh toán: {order.get_payment_method_display()}

Chúng tôi sẽ xử lý đơn hàng của bạn sớm nhất có thể!

Trân trọng,
Đội ngũ ShopVNS 🛒
        """.strip()

        send_mail(
            subject=f"[ShopVNS] Xác nhận đơn hàng #{order.order_number}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )
        logger.info(f"✅ Đã gửi email xác nhận đơn #{order.order_number} tới {order.user.email}")
        return {"status": "sent", "order_number": order.order_number, "email": order.user.email}

    except Order.DoesNotExist:
        logger.warning(f"⚠️ Bỏ qua gửi email: đơn #{order_id} không tồn tại")
        return {"status": "order_not_found", "order_id": order_id}

    except Exception as exc:
        logger.error(f"❌ Lỗi gửi email đơn #{order_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_status_email(self, order_id: int):
    """
    Task: Gửi email thông báo khi đơn hàng thay đổi trạng thái
    """
    from apps.orders.models import Order

    try:
        order = Order.objects.select_related("user").get(pk=order_id)
        status_label = order.get_status_display().upper()

        message = f"""
Xin chào {order.user.full_name}!

Đơn hàng #{order.order_number} của bạn vừa được cập nhật trạng thái mới.
Trạng thái hiện tại: {status_label}

Bạn có thể đăng nhập vào tài khoản trên ShopVNS để kiểm tra lịch sử đơn hàng.

Trân trọng,
Đội ngũ ShopVNS 🛒
        """.strip()

        send_mail(
            subject=f"[ShopVNS] Cập nhật: Đơn hàng #{order.order_number} -> {status_label}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )
        logger.info(f"✅ Đã gửi email cập nhật trạng thái đơn #{order.order_number} tới {order.user.email}")
        return {"status": "sent", "order_number": order.order_number}

    except Order.DoesNotExist:
        logger.warning(f"⚠️ Bỏ qua gửi email status: đơn #{order_id} không tồn tại")
        return {"status": "order_not_found"}
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2)
def send_low_stock_alert(self, product_id: int):
    """Task: Cảnh báo tồn kho thấp gửi tới admin"""
    try:
        from apps.inventory.models import Product
        from django.contrib.auth import get_user_model
        User = get_user_model()

        product = Product.objects.get(pk=product_id)
        admin_emails = list(User.objects.filter(is_staff=True).values_list("email", flat=True))

        if not admin_emails:
            return {"status": "no_admins"}

        send_mail(
            subject=f"⚠️ [ShopVNS] Cảnh báo tồn kho thấp: {product.name}",
            message=f"Sản phẩm [{product.sku}] {product.name} chỉ còn {product.stock} trong kho.\nTồn kho tối thiểu: {product.min_stock}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )
        logger.info(f"⚠️ Đã gửi cảnh báo tồn kho thấp: {product.name}")
        return {"status": "sent", "product": product.name}

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def generate_inventory_report():
    """Periodic task: Báo cáo hàng ngày (demo Celery Beat)"""
    from apps.inventory.models import Product
    from django.db.models import Count, Q

    stats = Product.objects.aggregate(
        total_products=Count("id"),
        out_of_stock=Count("id", filter=Q(stock=0)),
        low_stock=Count("id", filter=Q(stock__gt=0, stock__lte=5)),
    )
    logger.info(f"📊 Báo cáo kho: {stats}")
    return stats


@shared_task(bind=True)
def resize_product_image(self, product_id: int):
    """Task: Resize ảnh sản phẩm sau khi upload"""
    try:
        from apps.inventory.models import Product
        from PIL import Image
        import os

        product = Product.objects.get(pk=product_id)
        if not product.image:
            return {"status": "no_image"}

        img_path = product.image.path
        with Image.open(img_path) as img:
            img.thumbnail((800, 800), Image.LANCZOS)
            img.save(img_path, optimize=True, quality=85)

        logger.info(f"🖼️ Đã resize ảnh sản phẩm {product.name}")
        return {"status": "resized", "product": product.name}

    except Exception as exc:
        logger.error(f"❌ Lỗi resize ảnh: {exc}")
        raise self.retry(exc=exc)

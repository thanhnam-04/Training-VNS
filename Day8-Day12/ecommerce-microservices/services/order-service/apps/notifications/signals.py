"""
Notifications Signals — Day 11: Django Signals
Demo: post_save, pre_delete, các signal pattern thực tế
"""
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender="orders.Order")
def order_created_signal(sender, instance, created, **kwargs):
    """
    Signal: Khi tạo Order mới
    → Gọi Celery task gửi email xác nhận (async)
    """
    if created:
        logger.info(f"📦 [Signal] Đơn hàng mới: #{instance.order_number}")
        try:
            from .tasks import send_order_confirmation_email, send_new_order_admin_email
            transaction.on_commit(lambda: send_order_confirmation_email.delay(instance.id))
            transaction.on_commit(lambda: send_new_order_admin_email.delay(instance.id))
        except Exception as e:
            logger.warning(f"Celery chưa sẵn sàng: {e}")


@receiver(post_save, sender="inventory.Product")
def check_low_stock_signal(sender, instance, **kwargs):
    """
    Signal: Khi lưu Product
    → Kiểm tra tồn kho thấp → gửi alert
    """
    if instance.is_low_stock:
        logger.warning(f"⚠️ [Signal] Tồn kho thấp: {instance.name} ({instance.stock}/{instance.min_stock})")
        try:
            from .tasks import send_low_stock_alert
            send_low_stock_alert.delay(instance.id)
        except Exception as e:
            logger.warning(f"Celery chưa sẵn sàng: {e}")


@receiver(post_save, sender="inventory.Product")
def auto_resize_image_signal(sender, instance, created, **kwargs):
    """
    Signal: Khi upload ảnh cho Product
    → Trigger task resize ảnh async
    """
    if instance.image and created:
        try:
            from .tasks import resize_product_image
            resize_product_image.delay(instance.id)
        except Exception:
            pass


@receiver(post_save, sender="users.User")
def create_user_cart_signal(sender, instance, created, **kwargs):
    """
    Signal: Khi tạo User mới
    → Tự động tạo Cart cho user
    """
    if created:
        try:
            from apps.cart.models import Cart
            Cart.objects.get_or_create(user=instance)
            logger.info(f"🛒 [Signal] Đã tạo giỏ hàng cho user: {instance.email}")
        except Exception as e:
            logger.error(f"Lỗi tạo cart: {e}")


@receiver(pre_delete, sender="orders.Order")
def order_pre_delete_signal(sender, instance, **kwargs):
    """Signal: Trước khi xóa Order → log"""
    logger.info(f"🗑️ [Signal] Xóa đơn hàng: #{instance.order_number}")

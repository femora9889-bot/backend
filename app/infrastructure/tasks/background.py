from fastapi import BackgroundTasks

from app.infrastructure.notifications.fcm import send_push
from app.models.order import OrderStatus


async def notify_order_confirmed(background: BackgroundTasks, fcm_token: str | None, order_id: str):
    if fcm_token:
        background.add_task(send_push, fcm_token, "تم تأكيد طلبك ✓", "طلبك في طريقه للمتجر", {"order_id": order_id})


async def notify_order_status(background: BackgroundTasks, fcm_token: str | None, order_id: str, status: OrderStatus):
    messages = {
        OrderStatus.accepted: ("قبل المتجر طلبك 🎉", "جاري تجهيز طلبك"),
        OrderStatus.preparing: ("طلبك قيد التجهيز 📦", "المتجر يجهز طلبك الآن"),
        OrderStatus.out_for_delivery: ("طلبك في الطريق 🚗", "المندوب في طريقه إليك"),
        OrderStatus.delivered: ("تم توصيل طلبك ✓", "نتمنى أن تعجبك القطعة!"),
        OrderStatus.cancelled: ("تم إلغاء الطلب", "تم إلغاء طلبك"),
    }
    title, body = messages.get(status, ("تحديث الطلب", "تم تحديث حالة طلبك"))
    if fcm_token:
        background.add_task(send_push, fcm_token, title, body, {"order_id": order_id})

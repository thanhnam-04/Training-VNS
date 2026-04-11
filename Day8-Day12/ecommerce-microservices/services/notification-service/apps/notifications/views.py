from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from celery.result import AsyncResult


class TaskStatusView(APIView):
    """GET /api/notifications/task/{task_id}/ — Kiểm tra trạng thái Celery task"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id):
        result = AsyncResult(task_id)
        return Response({
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
        })


class TriggerTestEmailView(APIView):
    """POST /api/notifications/test-email/ — Demo trigger email task thủ công"""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from .tasks import send_order_confirmation_email
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"error": "Cần truyền order_id"}, status=400)
        task = send_order_confirmation_email.delay(order_id)
        return Response({"task_id": task.id, "status": "queued"})

from django.urls import path
from . import views

urlpatterns = [
    path("task/<str:task_id>/", views.TaskStatusView.as_view(), name="task-status"),
    path("test-email/", views.TriggerTestEmailView.as_view(), name="test-email"),
]

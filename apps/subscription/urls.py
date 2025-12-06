from django.urls import path

from .views import CreateSubView, GetUserSubView, GetChildSubView, MarkAttendance, DeleteSubView

urlpatterns = [
    path('create_subscription/', CreateSubView.as_view()), 
    path('get_user_sub/<int:telegram_id>/', GetUserSubView.as_view()),
    path('get_child_sub/<int:telegram_id>/', GetChildSubView.as_view()),
    path('mark_attendance/<int:subscription_id>/', MarkAttendance.as_view()),
    path('delete_sub/<int:sub_id>/', DeleteSubView.as_view())
]
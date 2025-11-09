from django.urls import path

from .views import CreateSubView, GetUserSubView, GetChildSubView

urlpatterns = [
    path('create_subscription/', CreateSubView.as_view()), 
    path('get_user_sub/<int:telegram_id>/', GetUserSubView.as_view()),
    path('get_child_sub/<int:telegram_id>/', GetChildSubView.as_view())
]
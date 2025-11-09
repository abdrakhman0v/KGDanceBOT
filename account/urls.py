from django.urls import path

from .views import TelegramRegisterView, ChildRegisterView, TelegramLoginView, CheckRoleView, GetChildsView, GetUserView

urlpatterns = [
    path('tg_register/', TelegramRegisterView.as_view()),
    path('tg_login/', TelegramLoginView.as_view()),
    path('child_register/', ChildRegisterView.as_view()),
    path('role/', CheckRoleView.as_view()),
    path('get_user/', GetUserView.as_view()),
    path('get_childs/', GetChildsView.as_view())
]
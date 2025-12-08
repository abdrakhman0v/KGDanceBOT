from django.urls import path

from .views import TelegramRegisterView, ChildRegisterView, TelegramLoginView, CheckRoleView, GetChildsView, GetChildDataView ,GetUserByPhoneView, GetAdminsView, GetUsersDataView, UpdateUserView, DeleteChildView

urlpatterns = [
    path('tg_register/', TelegramRegisterView.as_view()),
    path('tg_login/', TelegramLoginView.as_view()),
    path('child_register/', ChildRegisterView.as_view()),
    path('role/', CheckRoleView.as_view()),
    path('get_user_by_phone/', GetUserByPhoneView.as_view()),
    path('get_childs/', GetChildsView.as_view()),
    path('get_child_data/<int:pk>/', GetChildDataView.as_view()),
    path('get_admins/', GetAdminsView.as_view()),
    path('get_users_data/', GetUsersDataView.as_view()),
    path('update_user/', UpdateUserView.as_view()),
    path('delete_child/<int:pk>/',DeleteChildView.as_view()),
]
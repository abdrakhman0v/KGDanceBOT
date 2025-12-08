from django.urls import path, include

from .views import GroupCreateView, GroupListView, GroupDetailView, GetGroupUsersView, GroupDeleteAPIView, AddUserToGroup, DeleteUserFromGroup

urlpatterns = [
    path('create/', GroupCreateView.as_view()),
    path('list/', GroupListView.as_view()),
    path('detail/<int:pk>/', GroupDetailView.as_view()),
    path('delete/<int:pk>/', GroupDeleteAPIView.as_view()),
    path('get_group_users/<int:group_id>/', GetGroupUsersView.as_view()),
    path('add_user/', AddUserToGroup.as_view()),
    path('delete_user/', DeleteUserFromGroup.as_view())
]
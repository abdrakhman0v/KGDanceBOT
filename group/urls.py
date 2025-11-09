from django.urls import path, include

from .views import GroupCreateView, GroupListView, GroupDetailView, GroupDeleteAPIView

urlpatterns = [
    path('create/', GroupCreateView.as_view()),
    path('list/', GroupListView.as_view()),
    path('detail/<int:pk>/', GroupDetailView.as_view()),
    path('delete/<int:pk>/', GroupDeleteAPIView.as_view())
]
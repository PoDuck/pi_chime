from django.urls import path
from . import views

urlpatterns = [
    path('', views.ClipsList.as_view(), name='clip_list'),
    path('<int:pk>/', views.ClipsList.as_view(), name='play_clip'),
    path("create/", views.ClipUploadView.as_view(), name="add_clip")
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ClipsList.as_view(), name='clip_list'),
    path('<int:pk>/', views.ClipsList.as_view(), name='play_clip'),
    path("create/", views.ClipUploadView.as_view(), name="add_clip"),
    path("update/<int:pk>/", views.ClipUpdateView.as_view(), name="update_clip"),
    path("delete/<int:pk>/", views.ClipDeleteView.as_view(), name="delete_clip"),
    path("trigger/", views.TriggerChime.as_view(), name="trigger_chime"),
]
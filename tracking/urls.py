from django.urls import path
from . import views

urlpatterns = [
    path('', views.TrackingView.as_view(), name='tracking'),
]

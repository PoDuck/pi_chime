from django.urls import path
from . import views

urlpatterns = [
    path('', views.DayTrackingView.as_view(), name='day_tracking'),
    path('<int:pk>/<str:start_date>/<str:end_date>/', views.HourTrackingView.as_view(), name='hour_tracking'),
    path('data/<str:start_date>/<str:end_date>/', views.DayTrackingDataView.as_view(), name='data'),
    path('data/<int:pk>/<str:start_date>/<str:end_date>/', views.HourTrackingDataView.as_view(), name='hour_data'),
]

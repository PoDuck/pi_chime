from django.urls import path
from .views import DownloaderView, JobView, JobStatusView, ConvertView, RawFileView, DownloadFileView

urlpatterns = [
    path('', DownloaderView.as_view(), name='downloader'),
    path('job/<int:pk>/', JobView.as_view(), name='downloader_job'),
    path('job/<int:pk>/status/', JobStatusView.as_view(), name='downloader_job_status'),
    path('job/<int:pk>/raw/', RawFileView.as_view(), name='downloader_raw'),
    path('job/<int:pk>/convert/', ConvertView.as_view(), name='downloader_convert'),
    path('job/<int:pk>/download/', DownloadFileView.as_view(), name='downloader_download'),
]

"""
URL configuration for chime project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from clips.views import ClipsList
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path('', ClipsList.as_view(), name='index'),
    # path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('clips/', include('clips.urls')),
    path('tracking/', include('tracking.urls')),
    path('admin/', admin.site.urls),
] + debug_toolbar_urls()

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

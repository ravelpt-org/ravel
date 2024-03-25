"""
URL configuration for ravel project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

urlpatterns = [
    path('__debug__/', include('debug_toolbar.urls')),
    path('', include('contests.urls')),
    path('', include('homesite.urls')),
    path('admin/', admin.site.urls),
    path("favicon.ico", RedirectView.as_view(url=staticfiles_storage.url("favicon.ico")))
]

handler403 = "homesite.views.return_error"
handler404 = "homesite.views.return_error"
handler500 = "homesite.views.return_error"

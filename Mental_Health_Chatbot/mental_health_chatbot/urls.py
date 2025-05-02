"""
URL configuration for mental_health_chatbot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path , include
from main import views
from django.shortcuts import redirect

def redirect_to_login(request):
    return redirect("login")

urlpatterns = [
    path('admin/', admin.site.urls),
    # path("", redirect_to_login),  # Redirect root URL to login page
    path('', views.home, name='home'),  # Public homepage
    path('dashboard/', views.dashboard, name='dashboard'),
    path("", include("main.urls")), 
    
]

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include

urlpatterns += [
    path('', include('main.urls')),
    path('blogs/', include('blog.urls')),
    

    
] 
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
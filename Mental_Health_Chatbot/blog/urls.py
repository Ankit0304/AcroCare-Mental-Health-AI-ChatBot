from django.urls import path
from . import views

urlpatterns = [
    path('', views.blog_list, name='blog_list'),
    path('create/', views.blog_create, name='blog_create'),
    path('sync-feeds/', views.sync_web_blogs, name='sync_web_blogs'),
    path('<int:blog_id>/', views.blog_detail, name='blog_detail'),
    path('redirect/', views.blog_redirect, name='blog_redirect'),
]

from django.urls import path
from . import views
from .views import blog_list
from .views import blog_view

urlpatterns = [
    path('', blog_list, name='blog_list'),
    path('external-blogs/', views.blog_list_external, name='external_blogs'),
    path('blog/', blog_view, name='blog'),
    path("blog-redirect/", views.blog_redirect, name="blog_redirect"),

]
    

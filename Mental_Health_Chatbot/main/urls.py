from django.urls import path
from . import views
from .views import chatbot_response
from django.contrib.auth import views as auth_views

urlpatterns = [
#    path("", views.index, name="base"),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chat/', views.chat, name='chat'),
    path("chat/", views.chat_page, name="chat_page"),
    path('profile/', views.profile, name='profile'),
    path("chatbot/", chatbot_response, name="chatbot_response"),
    path("journal/", views.journal_page, name="journal_page"),
    path('therapy/', views.therapy_view, name='therapy'),
    # path('', views.therapy_home, name='therapy_home'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
    path('password/change/', auth_views.PasswordChangeView.as_view(
        template_name='auth/password_change.html',
        success_url='/password/change/done/'
    ), name='password_change'),

    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='auth/password_change_done.html'
    ), name='password_change_done'),
   path('psychiatrists/', views.psychiatrist_list, name='psychiatrist_list'),

]

from django.urls import path
from . import views
from django.contrib.auth import logout
from django.shortcuts import redirect

# Logout function
def logout_view(request):
    logout(request)
    return redirect("login")



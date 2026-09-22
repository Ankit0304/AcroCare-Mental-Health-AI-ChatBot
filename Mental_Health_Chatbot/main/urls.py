from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chat/', views.chat_page, name='chat'),
    path('chatbot/', views.chatbot_response, name='chatbot_response'),
    path('chat/clear/', views.clear_chat_history, name='clear_chat_history'),
    path('profile/', views.profile, name='profile'),
    path("journal/", views.journal_page, name="journal_page"),
    path('therapy/', views.therapy_view, name='therapy'),
    path('contact/', views.contact_view, name='contact'),

    # Mood tracker API
    path('api/mood/save/', views.save_mood, name='save_mood'),
    path('api/mood/history/', views.mood_history, name='mood_history'),

    # Assessment
    path('assessment/', views.assessment_view, name='assessment'),

    # Password management
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset.html'
    ), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('password/change/', auth_views.PasswordChangeView.as_view(
        template_name='auth/password_change.html',
        success_url='/password/change/done/'
    ), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='auth/password_change_done.html'
    ), name='password_change_done'),
]

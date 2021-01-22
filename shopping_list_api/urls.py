from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from rest_framework.authtoken import views
from .views import IndexView, LoginView, LogoutView, FirstLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-token-auth/', views.obtain_auth_token, name='api-token-auth'),
    path('api/', include('api.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('transmission/', include('transmission.urls')),
    path('', IndexView.as_view(), name='home-index'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='home-logout'),
    path('first-login/', FirstLoginView.as_view(), name='home-first-login'),
    path(
        'password-reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='home/password-reset.html',
            extra_context= {'main_selected': 'login'},
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='home/password-reset-done.html',
            extra_context= {'main_selected': 'login'},
        ),
        name='password_reset_done'
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='home/password-reset-confirm.html',
            extra_context= {'main_selected': 'login'},
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset-complete/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='home/password-reset-complete.html',
            extra_context= {'main_selected': 'login'},
        ),
        name='password_reset_complete'
    ),
]

from django.urls import path

from . import views


app_name = 'account'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterPage.as_view(), name='register'),
    path('logout/', views.Logout, name='logout'),
    path('notify/<str:alert_key>/', views.alert_box, name='alert'),

    path('profile/', views.ProfileView.as_view(), name='profile'),
    path(
        'profile/update/',
        views.ProfileUpdate.as_view(), name='profile_update'),

    path(
        'change-password/',
        views.ChangePassword.as_view(), name='change_password'),
    path("activate/<slug:uidb64>/<slug:token>/",
         views.activate_email, name="activate"),

    path('forget-password/', views.ForgetPasswordView.as_view(),
         name='forget_password'),
    path('reset/<slug:uidb64>/<slug:token>/',
         views.ResetPasswordVerify.as_view(), name='password_reset_confirm'),
    path('resend-email-verification/',
         views.ResendEmailVerificationLink.as_view(),
         name='resend_verification'),
]

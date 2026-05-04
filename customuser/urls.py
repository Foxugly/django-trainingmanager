from django.urls import path

from .views import ConfirmEmailView, MeView, RegisterView, ResendEmailView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path("auth/email/confirm/", ConfirmEmailView.as_view(), name="auth_email_confirm"),
    path("auth/email/resend/", ResendEmailView.as_view(), name="auth_email_resend"),
]

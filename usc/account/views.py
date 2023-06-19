from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls.base import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.generic import FormView, TemplateView, UpdateView

from .forms import (ChangePasswordForm, ForgetPasswordForm, LoginForm,
                    ProfileForm, RegisterForm, ResetPasswordValidateEmailForm)
from .models import User
from .tokens import account_token
from .utils import verification_message


def activate_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user: User = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.warning(request, 'Invalid verification link.')
        return redirect('account:login')

    # Check if the user is already verified
    if user.verified_email:
        account_token.mark_used(user, token)
        messages.success(request, 'Account is already verified')
        return redirect('account:login')

    # Check if the token is valid
    if account_token.check_token(user, token):
        user.verified_email = True
        user.save()
        account_token.mark_used(user, token)
        messages.success(
            request, 'Your account is verified successfully.')
        return redirect('account:login')

    # Send another verification email
    subject = f"{settings.APP_NAME} Account Verification"
    message = verification_message(
        request, user, "account/email/activation_email.html")
    user.email_user(subject, message)

    messages.success(
        request, 'Email verification link is expired \
or invalid, another email verification link has been sent to you.')

    return redirect('account:login')


class CookieBlockMixin:
    def dispatch(self, request, *args, **kwargs):
        # check if user has accepted cookies
        if request.session.get(settings.DISABLE_COOKIES):
            messages.warning(
                request,
                'Please enable cookies to get the best \
experience using this site. You can disable cookies later.')
            return redirect(reverse('main:index'))

        return super().dispatch(request, *args, **kwargs)


class LoginView(CookieBlockMixin, TemplateView):
    template_name = 'account/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LoginForm()
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, 'You are already logged in.')
            return redirect(reverse('main:index'))

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Initialize data
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=email, password=password)

            if user:
                if user.verified_email:
                    # if user.verified_email:
                    login(request, user)
                    messages.success(request, 'Login successful.')
                    return redirect(reverse('main:index'))

                # Flush sessions
                request.session.flush()
                request.session['resend_email_uid'] = user.pk
                return redirect(
                    'account:alert', alert_key='unverified-email')

            messages.error(request, 'Account has been deactivated.')
            return redirect('account:login')

        return render(
            request, self.template_name, {'form': form})


class RegisterPage(CookieBlockMixin, TemplateView):
    template_name = 'account/register.html'
    extra_context = {
        'title': f'Create {settings.APP_NAME} account'
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = RegisterForm()
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()

        form = RegisterForm(data=request.POST, files=request.FILES)

        if form.is_valid():
            user = form.save()

            subject = f"{settings.APP_NAME} Email Verification"
            message = verification_message(
                request, user, "account/email/activation_email.html")

            user.email_user(subject, message)

            messages.success(
                request,
                f'Your account is successfully created. A \
link was sent to your email {user.email}, use the link to verify you account.')

            return redirect('account:login')

        context['form'] = form

        return render(request, self.template_name, context)


class ChangePassword(LoginRequiredMixin, UpdateView):
    template_name = 'account/change_password.html'
    extra_context = {
        'title': 'Change Password'
    }
    form_class = ChangePasswordForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class()
        return context

    def post(self, request, *args, **kwargs):
        request = self.request
        context = self.get_context_data()

        form = self.form_class(
            instance=request.user,
            data=request.POST
        )
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Your password is successfully changed, \
please login with your new password')
            return redirect('account:logout')

        context['form'] = form
        return render(request, self.template_name, context)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'account/profile.html'
    extra_context = {
        'title': 'Account',
    }


class ProfileUpdate(LoginRequiredMixin, TemplateView):
    template_name = 'account/profile_update.html'
    extra_context = {
        'title': 'Update Profile',
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ProfileForm(instance=self.request.user.profile)
        return context

    def post(self, request, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        form = ProfileForm(
            instance=self.request.user.profile,
            data=request.POST,
            files=request.FILES
        )

        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile is successfully updated')
            return redirect('account:profile')

        context['form'] = form
        return render(request, self.template_name, context)


class ForgetPasswordView(FormView):
    template_name = 'account/forget_password.html'
    extra_context = {
        'title': 'Forgot password',
    }
    form_class = ResetPasswordValidateEmailForm

    def post(self, *args, **kwargs):
        request = self.request

        form = self.get_form_class()
        form = form(request.POST)

        if form.is_valid():
            # Get the user if the email is correct and send email
            email = form.cleaned_data.get('email')
            try:
                user: User = User.objects.get(email=email)

                # Send password reset link
                subject = f"{settings.APP_NAME} Account Password Reset"
                message = verification_message(
                    request, user, "account/email/password_reset.html")

                user.email_user(subject, message)
            except User.DoesNotExist:
                pass

            return redirect('account:alert', alert_key='password-reset')

        context = self.get_context_data()
        context['form'] = form

        return render(request, self.template_name, context)


class ResendEmailVerificationLink(TemplateView):
    def get(self, *args, **kwargs):
        resend_email_uid = self.request.session.get('resend_email_uid')
        if resend_email_uid:
            try:
                user: User = User.objects.get(pk=resend_email_uid)
                subject = f"{settings.APP_NAME} Email Verification"
                message = verification_message(
                    self.request, user, "account/email/activation_email.html")

                user.email_user(subject, message)
            except User.DoesNotExist:
                pass

        self.request.session.pop('resend_email_uid', None)
        return redirect(
            'account:alert', alert_key='email-verification-link-sent')


class ResetPasswordVerify(FormView):
    template_name = 'account/reset_password.html'
    extra_context = {
        'title': 'Reset your password',
    }
    form_class = ForgetPasswordForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the user from the uidb64
        try:
            uidb64 = self.kwargs.get('uidb64')
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            context["user"] = user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context['form'] = self.form_class()

        # Get token from kwargs
        token = self.kwargs.get('token')
        user = context['user']

        if user and account_token.check_token(user, token):
            messages.success(request, 'You can now set a new password')
            return render(request, self.template_name, context)

        messages.warning(
            request, 'This password reset link is already invalid.')
        return redirect('account:login')

    def post(self, *args, **kwargs):
        request = self.request
        context = self.get_context_data()

        user: User = context['user']

        form = self.form_class(instance=user, data=request.POST)

        if form.is_valid():
            form.save()

            token = self.kwargs.get('token')
            account_token.mark_used(user, token)

            messages.success(
                request, 'You can now login with your new password')
            return redirect('account:login')

        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


ALERTS = {
    'registration-success': {
        'title': 'Registration Successful',
        'message': 'You have successfully registered, \
please login to continue',
        'type': 'success',
        'action': 'Login',
        'action_url': 'account:login',
    },
    'unverified-email': {
        'title': 'Email Verification Required',
        'message': 'You have not verified your email, \
please check your email for the verification link',
        'type': 'warning',
        'action': 'Resend Verification Link',
        'action_url': 'account:resend_verification',
    },
    'email-verification-link-sent': {
        'title': 'Verification Link Sent',
        'message': 'A verification link has been sent to your email, \
please check your email for the verification link',
        'type': 'success',
    },
    'password-reset': {
        'title': 'Password Reset Link Sent',
        'message': 'A password reset link has been sent to your email, \
please check your email for the password reset link',
        'type': 'success',
    },
}


ALERT_TYPES = {
    'success': 'check-circle',
    'warning': 'alert-triangle',
    'danger': 'x-circle',
}


def alert_box(request, alert_key):
    context = ALERTS.get(alert_key)
    if context:
        # Get the alert type
        alert_type = context.get('type')
        context['icon'] = ALERT_TYPES.get(alert_type)
        return render(request, 'account/alert_box.html', context)
    raise Http404()


def Logout(request):
    logout(request)
    return redirect('account:login')

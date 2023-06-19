from django import forms
from django.contrib.auth import password_validation
from django.core.validators import validate_email
from django.urls import reverse

from .models import Profile, User


class GlobalClassMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            if field.__class__ == forms.fields.TypedChoiceField:
                field.widget.attrs['class'] = 'form-select'
            elif field.__class__ == forms.fields.BooleanField:
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class ProfileForm(GlobalClassMixin, forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('user',)


class ResetPasswordValidateEmailForm(forms.Form):
    email = forms.CharField(
        help_text="Enter your account email")

    def clean_email(self):
        email = self.data.get('email')
        validate_email(email)
        return email


class RegisterForm(GlobalClassMixin, forms.ModelForm):
    email = forms.EmailField()
    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text=password_validation.password_validators_help_text_html()
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text='Confirm your password'
    )
    terms_of_service = forms.BooleanField(
        required=True,
    )
    terms_of_use = forms.BooleanField(
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set help text for terms_of_service and terms_of_use
        self.fields['terms_of_service'].help_text = (
            'I agree to the <a href="{}" target="_blank">Terms of Service</a>'
        ).format(reverse('main:terms_of_service'))
        self.fields['terms_of_use'].help_text = (
            'I agree to the <a href="{}" target="_blank">Terms of Use</a>'
        ).format(reverse('main:terms_of_use'))

    class Meta:
        model = Profile
        exclude = ('user',)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('Email is not available')
        return email

    def clean_password(self):
        ps1 = self.cleaned_data.get("password")
        password_validation.validate_password(ps1, None)
        return ps1

    def clean_confirm_password(self):
        ps1 = self.cleaned_data.get("password")
        ps2 = self.cleaned_data.get("confirm_password")
        if (ps1 and ps2) and (ps1 != ps2):
            raise forms.ValidationError("The passwords does not match")
        return ps2

    def save(self, commit=True):
        profile = super().save(commit=False)

        if commit:
            email = self.cleaned_data.get('email')
            password = self.cleaned_data.get('password')
            user = User.objects.create_user(
                email=email, password=password
            )
            for field in self.fields:
                if field not in ['email', 'password', 'confirm_password']:
                    setattr(user.profile, field, self.cleaned_data.get(field))
            return user

        return profile


class ForgetPasswordForm(GlobalClassMixin, forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text=password_validation.password_validators_help_text_html()
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text='Confirm your password'
    )

    class Meta:
        model = User
        fields = ('password', 'confirm_password')

    def clean_password(self):
        ps1 = self.cleaned_data.get("password")
        password_validation.validate_password(ps1, None)
        return ps1

    def clean_confirm_password(self):
        ps1 = self.cleaned_data.get("password")
        ps2 = self.cleaned_data.get("confirm_password")
        if (ps1 and ps2) and (ps1 != ps2):
            raise forms.ValidationError("The passwords does not match")
        return ps2

    def save(self, commit=True):
        self.instance.set_password(self.cleaned_data.get("password"))
        if commit:
            self.instance.save()
        return self.instance


class ChangePasswordForm(GlobalClassMixin, forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form__input'}),
        help_text='Enter your current password here'
    )
    new_password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form__input'}),
        help_text=password_validation.password_validators_help_text_html()
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text='Confirm your password'
    )

    class Meta:
        model = User
        fields = ('password', 'new_password', 'confirm_password')

    instance: User = None

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.instance.check_password(password):
            raise forms.ValidationError('Your password is not correct')
        return password

    def clean_new_password(self):
        ps1 = self.cleaned_data.get("new_password")
        password_validation.validate_password(ps1, None)
        return ps1

    def clean_confirm_password(self):
        ps1 = self.cleaned_data.get("new_password")
        ps2 = self.cleaned_data.get("confirm_password")
        if (ps1 and ps2) and (ps1 != ps2):
            raise forms.ValidationError("The passwords does not match")
        return ps2

    def save(self, commit=True):
        self.instance.set_password(self.cleaned_data.get("new_password"))
        if commit:
            self.instance.save()
        return self.instance


class LoginForm(GlobalClassMixin, forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        data = super(LoginForm, self).clean()
        email = data.get('email')
        password = data.get('password')
        try:
            user: User = User.objects.get(email=email)
            if not user.check_password(password):
                raise forms.ValidationError(
                    {'email': 'Email and Password does not match'})
        except User.DoesNotExist:
            raise forms.ValidationError(
                {'email': 'Email and Password does not match'})
        return data


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

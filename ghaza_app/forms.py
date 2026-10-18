from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class SignUpForm(UserCreationForm):
    """Registration form: username, email, phone, password + confirm."""

    first_name = forms.CharField(
        label="نام", max_length=30, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'نام'}))
    last_name = forms.CharField(
        label="نام خانوادگی", max_length=30, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'نام خانوادگی'}))
    email = forms.EmailField(
        label="ایمیل",
        widget=forms.EmailInput(attrs={'placeholder': 'ایمیل *'}))
    phone = forms.CharField(
        label="شماره تماس", max_length=15, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'شماره تماس'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'نام کاربری *'
        self.fields['username'].help_text = ''
        self.fields['password1'].widget.attrs['placeholder'] = 'رمز عبور *'
        self.fields['password1'].help_text = ''
        self.fields['password2'].widget.attrs['placeholder'] = 'تکرار رمز عبور *'
        self.fields['password2'].help_text = ''

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('این ایمیل قبلاً ثبت شده است.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and not phone.replace('+', '').isdigit():
            raise forms.ValidationError('شماره تماس فقط باید شامل رقم باشد.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        if commit:
            user.save()
            Profile.objects.update_or_create(
                user=user,
                defaults={'phone': self.cleaned_data.get('phone', '')})
        return user


class SignInForm(AuthenticationForm):
    """Login form accepting the username (or email) + password."""

    username = forms.CharField(
        label="نام کاربری یا ایمیل",
        widget=forms.TextInput(attrs={'placeholder': 'نام کاربری یا ایمیل *'}))
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={'placeholder': 'رمز عبور *'}))

    def clean_username(self):
        value = self.cleaned_data.get('username', '').strip()
        # allow signing in with the e-mail address
        if '@' in value:
            qs = User.objects.filter(email__iexact=value)
            if qs.exists():
                return qs.first().username
        return value


class ProfileEditForm(forms.ModelForm):
    """Edit name / e-mail / phone on the profile page."""

    phone = forms.CharField(
        label="شماره تماس", max_length=15, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'شماره تماس'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'ایمیل',
        }

    _PLACEHOLDERS = {
        'first_name': 'نام',
        'last_name': 'نام خانوادگی',
        'email': 'ایمیل',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            css = f.widget.attrs.get('class', '')
            f.widget.attrs['class'] = (css + ' form-control').strip()
            if name in self._PLACEHOLDERS:
                f.widget.attrs.setdefault('placeholder', self._PLACEHOLDERS[name])

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('این ایمیل قبلاً ثبت شده است.')
        return email


class AvatarForm(forms.ModelForm):
    """Upload / replace the profile picture."""

    class Meta:
        model = Profile
        fields = ('avatar',)
        labels = {'avatar': 'عکس پروفایل'}
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class PasswordChangeSimpleForm(forms.Form):
    """Change password with old + new + confirm."""

    old_password = forms.CharField(
        label="رمز فعلی",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'رمز فعلی *',
            'class': 'form-control',
            'autocomplete': 'current-password',
        }))
    new_password1 = forms.CharField(
        label="رمز جدید",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'رمز جدید *',
            'class': 'form-control',
            'autocomplete': 'new-password',
        }))
    new_password2 = forms.CharField(
        label="تکرار رمز جدید",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'تکرار رمز جدید *',
            'class': 'form-control',
            'autocomplete': 'new-password',
        }))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old = self.cleaned_data.get('old_password', '')
        if not self.user.check_password(old):
            raise forms.ValidationError('رمز فعلی درست نیست.')
        return old

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1', '')
        p2 = cleaned.get('new_password2', '')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('رمز جدید و تکرارش یکسان نیستند.')
        if p1 and len(p1) < 8:
            raise forms.ValidationError('رمز جدید باید حداقل ۸ کاراکتر باشد.')
        return cleaned

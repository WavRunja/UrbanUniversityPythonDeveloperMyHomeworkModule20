from django import forms
from .models import ImageFeed
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


# class ImageUploadForm(forms.ModelForm):
#     class Meta:
#         model = ImageFeed
#         fields = ['image']


# class CustomUserCreationForm(UserCreationForm):
#     email = forms.EmailField(required=True, label="Email")
#     first_name = forms.CharField(required=True, label="Имя")
#     last_name = forms.CharField(required=True, label="Фамилия")
#
#     class Meta:
#         model = User
#         fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
#
#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.email = self.cleaned_data['email']
#         user.first_name = self.cleaned_data['first_name']
#         user.last_name = self.cleaned_data['last_name']
#         if commit:
#             user.save()
#         return user


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = ImageFeed  # Используем модель ImageFeed
        fields = ['image']  # Поле для загрузки изображений
        labels = {  # Определяем текст меток
            'image': 'Изображение:',  # Заменяем "Image:" на "Изображение:"
        }


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Электронная почта")
    first_name = forms.CharField(required=True, label="Имя")
    last_name = forms.CharField(required=True, label="Фамилия")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        labels = {
            'username': 'Имя пользователя',
            'email': 'Электронная почта',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }
        help_texts = {
            'username': 'Обязательно. Не более 150 символов. Только буквы, цифры и символы @/./+/-/_.',
            'password1': (
                'Ваш пароль не должен быть слишком похож на вашу личную информацию.\n'
                'Ваш пароль должен содержать как минимум 8 символов.\n'
                'Ваш пароль не должен быть слишком простым.\n'
                'Ваш пароль не должен состоять только из цифр.'
            ),
            'password2': 'Введите тот же пароль, что и ранее, для проверки.',
        }
        error_messages = {
            'username': {
                'required': 'Имя пользователя обязательно.',
                'unique': 'Пользователь с таким именем уже существует.',
            },
            'password2': {
                'password_mismatch': 'Пароли не совпадают.',
            },
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

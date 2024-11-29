from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext as _

from .forms import CustomUserCreationForm
from .forms import ImageUploadForm
from .models import ImageFeed
from .utils import process_image

# Модуль для работы с файловой системой
import os
# Импорт для настройки MEDIA_ROOT
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import ImageFeed

# Create your views here.


def home(request):
    return render(request, 'modify_objects/home.html')


def dashboard(request): # Добавить ограничение. Довести до рабочего состояния код функции.
    if not request.user.is_authenticated:
        return redirect('login')

    user_images = ImageFeed.objects.filter(user=request.user)

    if request.method == 'POST':
        if user_images.count() >= 9:
            messages.error(request, "Вы не можете загрузить более 9 изображений.")
        else:
            form = ImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                image_instance = form.save(commit=False)
                image_instance.user = request.user
                image_instance.save()
                return redirect('dashboard')  # Перезагрузка dashboard
    else:
        form = ImageUploadForm()

    return render(request, 'modify_objects/dashboard.html', {'form': form, 'images': user_images})



def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Переход к dashboard после успешного входа
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'modify_objects/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Создаём пользователя
            login(request, user)  # Входим после успешной регистрации
            messages.success(request, f'Пользователь {user.username} успешно зарегистрирован!')
            return redirect('dashboard')  # Перенаправляем на dashboard
        else:
            messages.error(request, 'Ошибка при регистрации. Проверьте введённые данные.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'modify_objects/register.html', {'form': form})


def logout_view(request):
    logout(request)  # Завершение сессии пользователя
    messages.info(request, _("Вы вышли из системы."))
    return redirect('home')  # Перенаправление на главную страницу

def delete_image(request, image_id):
    image = get_object_or_404(ImageFeed, id=image_id)

    # Проверяем, принадлежит ли изображение текущему пользователю
    if image.user != request.user:
        messages.error(request, "У вас нет прав для удаления этого изображения.")
        return redirect("dashboard")

    # Удаляем исходное изображение
    if image.image and os.path.isfile(image.image.path):
        os.remove(image.image.path)

    # Удаляем обработанное изображение (по имени из базы данных)
    if image.processed_image and os.path.isfile(image.processed_image.path):
        os.remove(image.processed_image.path)

    # Удаляем дублированные файлы, если они остались
    duplicate_path = os.path.join(
        settings.MEDIA_ROOT, "processed_images", f"processed_{image.id}.jpg"
    )
    if os.path.exists(duplicate_path):
        os.remove(duplicate_path)

    # Удаляем запись из базы данных
    image.delete()

    messages.success(request, "Изображение успешно удалено.")
    return redirect("dashboard")


def add_image_feed(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image_instance = form.save(commit=False)
            image_instance.user = request.user
            image_instance.save()
            return redirect('dashboard')  # После добавления изображения вернуться на dashboard
    else:
        form = ImageUploadForm()

    return render(request, 'modify_objects/add_image_feed.html', {'form': form})


def view_processed_image(request, image_id):
    """
    Возвращает обработанное изображение для просмотра в полном размере.
    """
    image = get_object_or_404(ImageFeed, id=image_id)
    if not image.processed_image:
        return HttpResponse("Обработанное изображение отсутствует.", status=404)
    return render(request, 'modify_objects/view_processed_image.html', {'image': image})

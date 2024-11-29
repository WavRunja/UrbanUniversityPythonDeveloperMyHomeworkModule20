import os
from django.conf import settings
from django.core.files.base import ContentFile
import torch
from torchvision import transforms, models
from PIL import Image
from django.shortcuts import get_object_or_404, redirect
from .models import ImageFeed


# Загрузка предобученной модели VGG-19
def load_vgg_model():
    """
    Загружаем предобученную модель VGG-19 для преобразования стиля.
    """
    model = models.vgg19(pretrained=True).features.eval()  # Используем только сверточные слои
    for param in model.parameters():
        param.requires_grad = False  # Отключаем обучение
    return model


# Предобработка изображения
def preprocess_image(image_path, image_size=256):
    img = Image.open(image_path).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])
    return transform(img).unsqueeze(0)


# Постобработка изображения
def postprocess_image(tensor):
    unloader = transforms.ToPILImage()
    image = tensor.cpu().squeeze(0)
    image = unloader(image)
    return image


# Функция преобразования стиля
def style_transfer(content_image, style_image, model, num_steps=300, style_weight=1e6, content_weight=1):
    """
    Преобразует стиль `style_image` на содержимое `content_image` с использованием модели VGG-19.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Загрузка изображений
    content_image = content_image.to(device)
    style_image = style_image.to(device)

    # Генерируемое изображение (копия content_image)
    generated_image = content_image.clone().requires_grad_(True)

    optimizer = torch.optim.Adam([generated_image], lr=0.01)

    # Определяем слои для извлечения признаков стиля и содержимого
    content_layers = ['conv_4']  # Пример: выбираем только один слой для содержимого
    style_layers = ['conv_1', 'conv_2', 'conv_3', 'conv_4', 'conv_5']  # Слои для стиля
    content_features = extract_features(content_image, model, content_layers)
    style_features = extract_features(style_image, model, style_layers)
    style_gram_matrices = {layer: gram_matrix(style_features[layer]) for layer in style_features}

    # Обучение
    for step in range(num_steps):
        generated_features = extract_features(generated_image, model, content_layers + style_layers)
        content_loss = torch.mean((generated_features['conv_4'] - content_features['conv_4']) ** 2)

        style_loss = 0
        for layer in style_layers:
            gen_gram = gram_matrix(generated_features[layer])
            style_gram = style_gram_matrices[layer]
            style_loss += torch.mean((gen_gram - style_gram) ** 2)

        total_loss = content_weight * content_loss + style_weight * style_loss
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        if step % 50 == 0:
            print(f"Step {step}/{num_steps}, Total Loss: {total_loss.item()}")

    return generated_image


def extract_features(image, model, layers):
    """
    Извлекает признаки из указанных слоев модели.
    """
    features = {}
    x = image
    for name, layer in model._modules.items():
        x = layer(x)
        if f"conv_{name}" in layers:
            features[f"conv_{name}"] = x
    return features


def gram_matrix(tensor):
    """
    Вычисляет грам-матрицу для заданного тензора.
    """
    _, d, h, w = tensor.size()
    tensor = tensor.view(d, h * w)
    gram = torch.mm(tensor, tensor.t())
    return gram


# Основная функция обработки
def process_image(request, image_id):
    """
    Обработка изображения с использованием нейронного переноса стиля.
    """
    image_instance = get_object_or_404(ImageFeed, id=image_id)
    content_path = image_instance.image.path
    processed_path = os.path.join(settings.MEDIA_ROOT, "processed_images", f"processed_{image_instance.id}.jpg")

    try:
        # Загружаем предобученную модель VGG-19
        model = load_vgg_model()

        # Предобработка изображения
        content_image = preprocess_image(content_path)
        style_image = preprocess_image("static/images/style.jpg")  # Указываем путь к стилю

        # Перенос стиля
        output_image = style_transfer(content_image, style_image, model)

        # Сохранение результата
        result_image = postprocess_image(output_image)
        result_image.save(processed_path)

        # Сохраняем обработанное изображение в записи модели
        with open(processed_path, "rb") as f:
            image_instance.processed_image.save(f"processed_{image_instance.id}.jpg", ContentFile(f.read()), save=True)

        return redirect("dashboard")
    except Exception as e:
        print(f"Ошибка обработки изображения: {e}")
        return redirect("dashboard")

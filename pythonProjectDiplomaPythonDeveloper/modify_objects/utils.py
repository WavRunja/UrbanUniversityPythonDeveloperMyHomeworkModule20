import torch
from torchvision import transforms
from PIL import Image
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect
from .models import ImageFeed
from .gan_models.animegan import AnimeGAN

# Путь к модели
MODEL_PATH = os.path.join(settings.BASE_DIR, "modify_objects/gan_models/animegan.pth")


# Загрузка модели
def load_model():
    """
    Загружаем модель AnimeGAN и её веса.
    """
    # Создаём модель
    model = AnimeGAN()
    # Загружаем веса
    state_dict = torch.load(MODEL_PATH, map_location=torch.device('cpu'))
    # Загружаем веса в модель
    model.load_state_dict(state_dict)
    # Устанавливаем режим оценки
    model.eval()
    return model


# Предобработка изображения
def preprocess_image(image_path):
    img = Image.open(image_path).convert("RGB")
    max_dim = max(img.size)
    square_img = Image.new("RGB", (max_dim, max_dim), (255, 255, 255))
    square_img.paste(img, ((max_dim - img.width) // 2, (max_dim - img.height) // 2))

    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])
    return transform(square_img).unsqueeze(0)


# Сохранение изображения
def save_image(tensor, path):
    unloader = transforms.ToPILImage()
    image = tensor.squeeze(0)
    image = unloader(image)
    image.save(path)


def split_image_to_tiles(image, tile_size):
    """
    Разделяет изображение на квадраты.
    """
    width, height = image.size
    tiles = []
    for top in range(0, height, tile_size):
        for left in range(0, width, tile_size):
            box = (left, top, left + tile_size, top + tile_size)
            tile = image.crop(box)

            # Если квадрат меньше tile_size, заполняем недостающие части белым
            if tile.size != (tile_size, tile_size):
                new_tile = Image.new("RGB", (tile_size, tile_size), (255, 255, 255))
                new_tile.paste(tile, (0, 0))
                tile = new_tile

            tiles.append((tile, box))  # Сохраняем квадрат и его координаты
    return tiles


def process_tiles_with_model(tiles, model, transform, device):
    """
    Пропускает каждый квадрат через модель.
    """
    processed_tiles = []
    for tile, box in tiles:
        # Преобразуем изображение в тензор
        input_tensor = transform(tile).unsqueeze(0).to(device)

        # Прогоняем через модель
        with torch.no_grad():
            output_tensor = model(input_tensor).cpu().squeeze(0)

        # Конвертируем результат в изображение
        unloader = transforms.ToPILImage()
        processed_tile = unloader(output_tensor)
        processed_tiles.append((processed_tile, box))
    return processed_tiles


def combine_tiles_to_image(processed_tiles, original_size):
    """
    Собирает квадраты обратно в исходное изображение.
    """
    output_image = Image.new("RGB", original_size)
    for tile, box in processed_tiles:
        output_image.paste(tile, box[:2])  # Используем только верхний левый угол
    return output_image


def process_image(request, image_id, tile_size=256):
    """
    Преобразует изображение в аниме-стиль, используя обработку по квадратам.
    """
    from .models import ImageFeed
    from django.shortcuts import get_object_or_404, redirect

    # Получаем изображение
    image_instance = get_object_or_404(ImageFeed, id=image_id)
    input_path = image_instance.image.path
    processed_path = os.path.join(
        settings.MEDIA_ROOT, "processed_images", f"processed_{image_instance.id}.jpg"
    )

    try:
        # Загрузка изображения
        original_image = Image.open(input_path).convert("RGB")

        # Разделение изображения на квадраты
        tiles = split_image_to_tiles(original_image, tile_size)

        # Загрузка модели
        model = load_model()
        device = torch.device("cpu")  # Можно заменить на "cuda" при наличии GPU
        model.to(device)

        # Преобразования для модели
        transform = transforms.Compose([
            transforms.Resize((tile_size, tile_size)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ])

        # Обработка каждого квадрата
        processed_tiles = process_tiles_with_model(tiles, model, transform, device)

        # Сборка обработанного изображения
        output_image = combine_tiles_to_image(processed_tiles, original_image.size)

        # Сохранение результата
        output_image.save(processed_path)

        # Сохраняем обработанное изображение в записи модели
        with open(processed_path, "rb") as processed_file:
            image_instance.processed_image.save(
                f"processed_{image_instance.id}.jpg",
                ContentFile(processed_file.read()),
                save=True,
            )

        return redirect("dashboard")
    except Exception as e:
        print(f"Ошибка обработки изображения: {e}")
        return redirect("dashboard")

import tensorflow as tf
import torch
import numpy as np

# Подключение архитектуры AnimeGAN
from animegan import AnimeGAN

# Путь к весам TensorFlow
tf_checkpoint_path = "modify_objects/gan_models/anime_gan/Shinkai-33/Shinkai-33.ckpt"
# Путь для сохранения весов PyTorch
pytorch_model_path = "modify_objects/gan_models/animegan.pth"


def convert_to_pth(tf_checkpoint_path, pytorch_model_path):
    # Загрузка весов из TensorFlow
    reader = tf.train.load_checkpoint(tf_checkpoint_path)
    weights = {k: reader.get_tensor(k) for k in reader.get_variable_to_dtype_map()}

    # Создание модели AnimeGAN
    model = AnimeGAN()

    # Конвертирование весов из TensorFlow в PyTorch
    state_dict = model.state_dict()
    for name, param in state_dict.items():
        tf_name = name.replace('.', '/')
        if tf_name in weights:
            state_dict[name] = torch.tensor(weights[tf_name], dtype=param.dtype)

    # Сохранение весов в формате PyTorch
    torch.save(state_dict, pytorch_model_path)
    print(f"Веса конвертированы и сохранены в: {pytorch_model_path}")

convert_to_pth(tf_checkpoint_path, pytorch_model_path)

from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class ImageFeed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images/')
    # processed_image = models.ImageField(upload_to='processed_images/', blank=True, null=True, )
    processed_image = models.ImageField(
        upload_to='processed_images/',
        blank=True,
        null=True,
        default='default/default.png'
    )

    label = models.CharField(max_length=50, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

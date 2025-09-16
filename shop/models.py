from django.db import models
from cloudinary.models import CloudinaryField

class Product(models.Model):
    no = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    origin = models.CharField(max_length=100, help_text='例: ニカラグア、エチオピアなど')
    logo = CloudinaryField('logo', folder="products/", blank=True, null=True)
    image = CloudinaryField('image', folder='products/', blank=True, null=True)
    map = CloudinaryField('map', folder='products/', blank=True, null=True)
    title = models.CharField(max_length=200, blank=True)
    roast_level = models.CharField(max_length=50, blank=True, help_text='例: 生豆、ライトロースト')
    price = models.DecimalField(max_digits=6, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
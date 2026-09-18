from django.conf import settings
from django.db import models
from cloudinary.models import CloudinaryField

class Product(models.Model):
    class ProductType(models.TextChoices):
        COFFEE = 'coffee', 'コーヒー'
        CACAO = 'cacao', 'カカオ'

    no = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    origin = models.CharField(max_length=100, help_text='例: ニカラグア、エチオピアなど')
    product_type = models.CharField(max_length=20, choices=ProductType.choices, default=ProductType.COFFEE)
    logo = CloudinaryField('logo', folder="products/", blank=True, null=True)
    image = CloudinaryField('image', folder='products/', blank=True, null=True)
    map = CloudinaryField('map', folder='products/', blank=True, null=True)
    title = models.CharField(max_length=200, blank=True)
    roast_level = models.CharField(max_length=50, blank=True, help_text='例: 生豆、ライトロースト')
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text='産地マップに表示する緯度(例: 12.865416)。Googleマップで場所を右クリック→座標をコピーして入力'
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text='産地マップに表示する経度(例: -85.207229)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def starting_price(self):
        cheapest = self.variants.order_by('price').first()
        return cheapest.price if cheapest else None

    @property
    def in_stock(self):
        return self.variants.filter(stock__gt=0).exists()


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, help_text='例: 1, 5, 10, 30')
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text='この重量での販売価格(円)')
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['weight_kg']
        unique_together = ('product', 'weight_kg')

    def __str__(self):
        return f"{self.product.name} - {self.weight_kg}kg"

    @property
    def label(self):
        weight = self.weight_kg
        if weight == weight.to_integral_value():
            weight = int(weight)
        return f"{weight}kg"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('image', folder='products/gallery/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product.name} - image {self.pk}"


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart({self.user})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'variant')

    def __str__(self):
        return f"{self.variant} x{self.quantity}"

    @property
    def product(self):
        return self.variant.product

    @property
    def line_total(self):
        return self.variant.price * self.quantity


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    prefecture = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20)
    is_default = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.user})"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', '支払い待ち'
        PAID = 'paid', '支払い完了'
        FAILED = 'failed', '決済失敗'
        FULFILLED = 'fulfilled', '発送済み'
        CANCELED = 'canceled', 'キャンセル'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    subtotal = models.DecimalField(max_digits=8, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=8, decimal_places=2)

    contact_email = models.EmailField()
    shipping_name = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=10)
    shipping_prefecture = models.CharField(max_length=10)
    shipping_city = models.CharField(max_length=100)
    shipping_address_line1 = models.CharField(max_length=200)
    shipping_address_line2 = models.CharField(max_length=200, blank=True)
    shipping_phone = models.CharField(max_length=20)

    stripe_checkout_session_id = models.CharField(max_length=200, blank=True, db_index=True)
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product_name} ({self.weight_kg}kg) x{self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
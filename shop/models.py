from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from cloudinary.models import CloudinaryField

class Product(models.Model):
    class ProductType(models.TextChoices):
        COFFEE = 'coffee', _('コーヒー')
        CACAO = 'cacao', _('カカオ')

    no = models.PositiveIntegerField(_('表示順'), default=1)
    name = models.CharField(_('商品名'), max_length=100)
    description = models.TextField(_('紹介文'), blank=True)
    notes = models.TextField(
        _("ご購入時の注意"), blank=True, default="", db_default="",
        help_text=_('送料・関税など購入前に知っておいてほしい注意書き。商品ページで紹介文とは別枠に表示されます'),
    )
    origin = models.CharField(_('産地'), max_length=100, help_text=_('例: ニカラグア、エチオピアなど'))
    product_type = models.CharField(_('種類'), max_length=20, choices=ProductType.choices, default=ProductType.COFFEE)
    logo = CloudinaryField(_('ロゴ'), folder="products/", blank=True, null=True)
    image = CloudinaryField(_('トップ画像'), folder='products/', blank=True, null=True)
    map = CloudinaryField(_('地図画像'), folder='products/', blank=True, null=True)
    title = models.CharField(_('キャッチコピー'), max_length=200, blank=True)
    roast_level = models.CharField(_('焙煎度'), max_length=50, blank=True, help_text=_('例: 生豆、ライトロースト'))
    latitude = models.DecimalField(
        _('緯度'), max_digits=9, decimal_places=6, null=True, blank=True,
        help_text=_('産地マップに表示する緯度(例: 12.865416)。Googleマップで場所を右クリック→座標をコピーして入力')
    )
    longitude = models.DecimalField(
        _('経度'), max_digits=9, decimal_places=6, null=True, blank=True,
        help_text=_('産地マップに表示する経度(例: -85.207229)')
    )
    created_at = models.DateTimeField(_('登録日時'), auto_now_add=True)

    class Meta:
        verbose_name = _('商品')
        verbose_name_plural = _('商品')

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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name=_('商品'))
    weight_kg = models.DecimalField(_('重量(kg)'), max_digits=6, decimal_places=2, help_text=_('例: 1, 5, 10, 30'))
    price = models.DecimalField(_('価格(円)'), max_digits=8, decimal_places=2, help_text=_('この重量での販売価格(円)'))
    stock = models.PositiveIntegerField(_('在庫'), default=0)

    class Meta:
        ordering = ['weight_kg']
        unique_together = ('product', 'weight_kg')
        verbose_name = _('重量・価格')
        verbose_name_plural = _('重量・価格')

    def __str__(self):
        return f"{self.product.name} - {self.weight_kg}kg"

    @property
    def label(self):
        weight = self.weight_kg
        if weight == weight.to_integral_value():
            weight = int(weight)
        return f"{weight}kg"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name=_('商品'))
    image = CloudinaryField(_('画像'), folder='products/gallery/')
    order = models.PositiveIntegerField(_('並び順'), default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = _('ギャラリー画像')
        verbose_name_plural = _('ギャラリー画像')

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses', verbose_name=_('会員'))
    full_name = models.CharField(_('お名前'), max_length=100)
    postal_code = models.CharField(_('郵便番号'), max_length=10)
    prefecture = models.CharField(_('都道府県'), max_length=10)
    city = models.CharField(_('市区町村'), max_length=100)
    address_line1 = models.CharField(_('番地'), max_length=200)
    address_line2 = models.CharField(_('建物名など'), max_length=200, blank=True)
    phone = models.CharField(_('電話番号'), max_length=20)
    is_default = models.BooleanField(_('いつもの住所'), default=True)
    created_at = models.DateTimeField(_('登録日時'), auto_now_add=True)

    class Meta:
        verbose_name = _('住所')
        verbose_name_plural = _('住所')

    def __str__(self):
        return f"{self.full_name} ({self.user})"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('支払い待ち')
        PAID = 'paid', _('支払い完了')
        PREPARING = 'preparing', _('発送準備中')
        FAILED = 'failed', _('決済失敗')
        FULFILLED = 'fulfilled', _('発送済み')
        CANCELED = 'canceled', _('キャンセル')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='orders', verbose_name=_('会員'))
    status = models.CharField(_('状態'), max_length=20, choices=Status.choices, default=Status.PENDING)

    subtotal = models.DecimalField(_('小計'), max_digits=8, decimal_places=2)
    shipping_fee = models.DecimalField(_('送料'), max_digits=6, decimal_places=2, default=0)
    total = models.DecimalField(_('合計'), max_digits=8, decimal_places=2)

    contact_email = models.EmailField(_('メールアドレス'))
    shipping_name = models.CharField(_('お名前'), max_length=100)
    shipping_postal_code = models.CharField(_('郵便番号'), max_length=10)
    shipping_prefecture = models.CharField(_('都道府県'), max_length=10)
    shipping_city = models.CharField(_('市区町村'), max_length=100)
    shipping_address_line1 = models.CharField(_('番地'), max_length=200)
    shipping_address_line2 = models.CharField(_('建物名など'), max_length=200, blank=True)
    shipping_phone = models.CharField(_('電話番号'), max_length=20)

    stripe_checkout_session_id = models.CharField(_('Stripe決済セッションID'), max_length=200, blank=True, db_index=True)
    stripe_payment_intent_id = models.CharField(_('Stripe支払いID'), max_length=200, blank=True, db_index=True)

    created_at = models.DateTimeField(_('注文日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    paid_at = models.DateTimeField(_('支払日時'), null=True, blank=True)

    tracking_number = models.CharField(_("追跡番号(DHL)"), max_length=100, blank=True, default="", db_default="", help_text=_('DHLの送り状番号(Waybill No.)。入力するとお客様の注文ページに追跡リンクが表示されます'))
    shipped_at = models.DateTimeField(_("発送日時"), null=True, blank=True)
    admin_note = models.TextField(_("社内メモ"), blank=True, default="", db_default="", help_text=_('お客様には表示されません'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("受注")
        verbose_name_plural = _("受注")

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"

    @property
    def tracking_url(self):
        """Shipments go out with DHL Express (coffee bean plan), so link to DHL's tracker."""
        if not self.tracking_number:
            return ""
        number = self.tracking_number.replace(" ", "").replace("-", "")
        return f"https://www.dhl.com/jp-ja/home/tracking/tracking-express.html?submit=1&tracking-id={number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_('受注'))
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name=_('商品'))
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, verbose_name=_('重量・価格'))
    product_name = models.CharField(_('商品名'), max_length=200)
    weight_kg = models.DecimalField(_('重量(kg)'), max_digits=6, decimal_places=2, default=1)
    unit_price = models.DecimalField(_('単価'), max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(_('数量'))

    class Meta:
        verbose_name = _('注文商品')
        verbose_name_plural = _('注文商品')

    def __str__(self):
        return f"{self.product_name} ({self.weight_kg}kg) x{self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity

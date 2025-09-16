from django.db import models
from cloudinary.models import CloudinaryField

class CompanyInfo(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    logo = CloudinaryField('logo', folder='company/', blank=True, null=True)
    favicon = CloudinaryField('favicon', folder='company/', blank=True, null=True)
    title = CloudinaryField('title', folder='company/', blank=True, null=True)
    map = CloudinaryField('map', folder='company/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "会社概要"
        verbose_name_plural = "会社概要"

    def __str__(self):
        return self.name

class ShippingStep(models.Model):
    no = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = CloudinaryField('image', folder='shipping/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "送付"
        verbose_name_plural = "送付"

    def __str__(self):
        return self.title
    
class PrivacyPolicy(models.Model):
    no = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "プライバシーポリシー"
        verbose_name_plural = "プライバシーポリシー"

    def __str__(self):
        return self.title
    
class TermsOfService(models.Model):
    no = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=100)
    content = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "利用規約"
        verbose_name_plural = "利用規約"

    def __str__(self):
        return self.title
    
class OrderPolicy(models.Model):
    company_name = models.CharField("販売業者", max_length=200, default='KiMame')
    manager = models.CharField("運営責任者", max_length=100, default='未設定')
    address = models.CharField("所在地", max_length=300, default='Nicaragua')
    phone = models.CharField("電話番号", max_length=50, default='未設定')
    email = models.EmailField("メールアドレス", default='未設定')

    shipping_fee = models.CharField("商品代金以外の必要料金", max_length=300, blank=True, default='未設定')
    delivery_time = models.CharField("引渡し時期ついて", max_length=200, blank=True, default='未設定')
    delivery_cost = models.CharField("送料について", max_length=200, blank=True, default='未設定')
    payment_method = models.CharField("支払方法に", max_length=200, blank=True, default='未設定')
    return_policy = models.TextField("返品・交換・キャンセルについて", blank=True, default='未設定')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "特定商取引法に基づく表記"
        verbose_name_plural = "特定商取引法に基づく表記"

    def __str__(self):
        return f"{self.company_name} - {self.manager}"
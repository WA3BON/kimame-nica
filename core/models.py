from django.conf import settings
from django.db import models
from cloudinary.models import CloudinaryField


class Inquiry(models.Model):
    class Kind(models.TextChoices):
        CONTACT = 'contact', 'お問い合わせ'
        ESTIMATE = 'estimate', 'お見積り'

    class Status(models.TextChoices):
        NEW = 'new', '未対応'
        REPLIED = 'replied', '返信済み'
        CLOSED = 'closed', '完了'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='inquiries'
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    product = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    prefecture = models.CharField(max_length=10, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        "対応状況", max_length=20, choices=Status.choices, default=Status.NEW, db_default=Status.NEW
    )
    admin_note = models.TextField("社内メモ", blank=True, default="", db_default="")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "お問い合わせ"
        verbose_name_plural = "お問い合わせ"

    def __str__(self):
        return f"{self.get_kind_display()} - {self.name} ({self.created_at:%Y-%m-%d})"


class InquiryReply(models.Model):
    """A reply mail sent to the customer from the admin screen (kept as a sent-mail log)."""
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='replies')
    subject = models.CharField("件名", max_length=200)
    body = models.TextField("本文")
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    sent_at = models.DateTimeField("送信日時", auto_now_add=True)

    class Meta:
        ordering = ['sent_at']
        verbose_name = "返信"
        verbose_name_plural = "返信履歴"

    def __str__(self):
        return self.subject


class CompanyInfo(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    logo = CloudinaryField('logo', folder='company/', blank=True, null=True)
    favicon = CloudinaryField('favicon', folder='company/', blank=True, null=True)
    ogp_image = CloudinaryField('ogp_image', folder='company/ogp/', blank=True, null=True)
    ogp_title = models.CharField(max_length=200, blank=True)
    ogp_description = models.TextField(blank=True)
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
    duration = models.CharField(
        "目安期間", max_length=100, blank=True, help_text='例: 約3〜5営業日'
    )
    detail = models.TextField(
        "補足説明", blank=True, help_text='もう少し詳しい説明(任意、一覧には小さめに表示)'
    )
    image = CloudinaryField('image', folder='shipping/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "送付"
        verbose_name_plural = "送付"
        ordering = ["no"]

    def __str__(self):
        return self.title


class WhyChooseUs(models.Model):
    no = models.PositiveIntegerField(default=1)
    title = models.CharField(
        "見出し", max_length=100, help_text='例: 現地農家との直接取引'
    )
    story = models.TextField(
        "ストーリー本文", help_text='選ばれる理由をストーリー形式で記述'
    )
    image = CloudinaryField('image', folder='why_choose_us/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "選ばれる理由"
        verbose_name_plural = "選ばれる理由"
        ordering = ["no"]

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
    phone = models.CharField("電話番号", max_length=50, blank=True, default='未設定')
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
    
class AppPolicy(models.Model):
    no = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "アプリ規約"
        verbose_name_plural = "アプリ規約"
        ordering = ["no"]

    def __str__(self):
        return self.title

class Faq(models.Model):
    class Category(models.TextChoices):
        PRODUCT = 'product', '商品について'
        ORDER = 'order', 'ご注文・お支払い'
        SHIPPING = 'shipping', '配送について'
        OTHER = 'other', 'その他'

    no = models.PositiveIntegerField("並び順", default=1)
    category = models.CharField("カテゴリ", max_length=20, choices=Category.choices, default=Category.OTHER)
    question = models.CharField("質問", max_length=200)
    answer = models.TextField("回答", help_text='改行はそのまま反映されます')
    is_published = models.BooleanField("公開", default=True)
    show_on_top = models.BooleanField("トップページに表示", default=False, help_text='トップページのFAQ欄に表示します(最大6件)')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "よくある質問"
        verbose_name_plural = "よくある質問"
        ordering = ["no", "id"]

    def __str__(self):
        return self.question

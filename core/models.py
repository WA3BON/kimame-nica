from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from cloudinary.models import CloudinaryField


class Inquiry(models.Model):
    class Kind(models.TextChoices):
        CONTACT = 'contact', _('お問い合わせ')
        ESTIMATE = 'estimate', _('お見積り')

    class Status(models.TextChoices):
        NEW = 'new', _('未対応')
        REPLIED = 'replied', _('返信済み')
        CLOSED = 'closed', _('完了')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='inquiries',
        verbose_name=_('会員'),
    )
    kind = models.CharField(_('種類'), max_length=20, choices=Kind.choices)
    name = models.CharField(_('お名前'), max_length=100)
    email = models.EmailField(_('メールアドレス'))
    product = models.CharField(_('商品名'), max_length=100, blank=True)
    quantity = models.PositiveIntegerField(_('予定数量'), null=True, blank=True)
    prefecture = models.CharField(_('都道府県'), max_length=10, blank=True)
    message = models.TextField(_('内容'))
    created_at = models.DateTimeField(_('受付日時'), auto_now_add=True)

    status = models.CharField(
        _("対応状況"), max_length=20, choices=Status.choices, default=Status.NEW, db_default=Status.NEW
    )
    admin_note = models.TextField(_("社内メモ"), blank=True, default="", db_default="")

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("お問い合わせ")
        verbose_name_plural = _("お問い合わせ")

    def __str__(self):
        return f"{self.get_kind_display()} - {self.name} ({self.created_at:%Y-%m-%d})"


class InquiryReply(models.Model):
    """A reply mail sent to the customer from the admin screen (kept as a sent-mail log)."""
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='replies', verbose_name=_('お問い合わせ'))
    subject = models.CharField(_("件名"), max_length=200)
    body = models.TextField(_("本文"))
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('送信者'))
    sent_at = models.DateTimeField(_("送信日時"), auto_now_add=True)

    class Meta:
        ordering = ['sent_at']
        verbose_name = _("返信")
        verbose_name_plural = _("返信履歴")

    def __str__(self):
        return self.subject


class CompanyInfo(models.Model):
    name = models.CharField(_('会社名'), max_length=100)
    description = models.TextField(_('紹介文'), blank=True)
    address = models.CharField(_('住所'), max_length=200)
    phone = models.CharField(_('電話番号'), max_length=50)
    email = models.EmailField(_('メールアドレス'))
    logo = CloudinaryField(_('ロゴ'), folder='company/', blank=True, null=True)
    favicon = CloudinaryField(_('ファビコン(アイコン)'), folder='company/', blank=True, null=True)
    ogp_image = CloudinaryField(_('OGP画像(SNS共有用)'), folder='company/ogp/', blank=True, null=True)
    ogp_title = models.CharField(_('OGPタイトル'), max_length=200, blank=True)
    ogp_description = models.TextField(_('OGP説明文'), blank=True)
    title = CloudinaryField(_('ロゴ文字画像'), folder='company/', blank=True, null=True)
    map = CloudinaryField(_('産地マップ画像'), folder='company/', blank=True, null=True)
    hero_image = CloudinaryField(_('トップ画像(ヒーロー背景)'), folder='company/hero/', blank=True, null=True)
    about_image = CloudinaryField(_('会社紹介の写真'), folder='company/', blank=True, null=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        verbose_name = _("会社概要")
        verbose_name_plural = _("会社概要")

    def __str__(self):
        return self.name


class ShippingStep(models.Model):
    no = models.PositiveIntegerField(_('番号'), default=1)
    title = models.CharField(_('見出し'), max_length=100)
    description = models.TextField(_('説明'), blank=True)
    duration = models.CharField(
        _("目安期間"), max_length=100, blank=True, help_text=_('例: 約3〜5営業日')
    )
    detail = models.TextField(
        _("補足説明"), blank=True, help_text=_('もう少し詳しい説明(任意、一覧には小さめに表示)')
    )
    image = CloudinaryField(_('画像'), folder='shipping/', blank=True, null=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        verbose_name = _("お届けまでの流れ")
        verbose_name_plural = _("お届けまでの流れ")
        ordering = ["no"]

    def __str__(self):
        return self.title


class WhyChooseUs(models.Model):
    no = models.PositiveIntegerField(_('番号'), default=1)
    title = models.CharField(
        _("見出し"), max_length=100, help_text=_('例: 現地農家との直接取引')
    )
    story = models.TextField(
        _("ストーリー本文"), help_text=_('選ばれる理由をストーリー形式で記述')
    )
    image = CloudinaryField(_('画像'), folder='why_choose_us/', blank=True, null=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        verbose_name = _("選ばれる理由")
        verbose_name_plural = _("選ばれる理由")
        ordering = ["no"]

    def __str__(self):
        return self.title


class PrivacyPolicy(models.Model):
    no = models.PositiveIntegerField(_('番号'), default=1)
    title = models.CharField(_('見出し'), max_length=100)
    description = models.TextField(_('本文'), blank=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        verbose_name = _("プライバシーポリシー")
        verbose_name_plural = _("プライバシーポリシー")

    def __str__(self):
        return self.title


class TermsOfService(models.Model):
    no = models.PositiveIntegerField(_('番号'), default=1)
    title = models.CharField(_('見出し'), max_length=100)
    content = models.TextField(_('本文'), blank=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        verbose_name = _("利用規約")
        verbose_name_plural = _("利用規約")

    def __str__(self):
        return self.title


class OrderPolicy(models.Model):
    company_name = models.CharField(_("販売業者"), max_length=200, default='KiMame')
    manager = models.CharField(_("運営責任者"), max_length=100, default='未設定')
    address = models.CharField(_("所在地"), max_length=300, default='Nicaragua')
    phone = models.CharField(_("電話番号"), max_length=50, blank=True, default='未設定')
    email = models.EmailField(_("メールアドレス"), default='未設定')

    shipping_fee = models.CharField(_("商品代金以外の必要料金"), max_length=300, blank=True, default='未設定')
    delivery_time = models.CharField(_("引渡し時期について"), max_length=200, blank=True, default='未設定')
    delivery_cost = models.CharField(_("送料について"), max_length=200, blank=True, default='未設定')
    payment_method = models.CharField(_("支払方法"), max_length=200, blank=True, default='未設定')
    return_policy = models.TextField(_("返品・交換・キャンセルについて"), blank=True, default='未設定')

    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        verbose_name = _("特定商取引法に基づく表記")
        verbose_name_plural = _("特定商取引法に基づく表記")

    def __str__(self):
        return f"{self.company_name} - {self.manager}"


class AppPolicy(models.Model):
    no = models.PositiveIntegerField(_('番号'), default=1)
    title = models.CharField(_('見出し'), max_length=200)
    content = models.TextField(_('本文'), blank=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        verbose_name = _("アプリ規約")
        verbose_name_plural = _("アプリ規約")
        ordering = ["no"]

    def __str__(self):
        return self.title


class Faq(models.Model):
    class Category(models.TextChoices):
        PRODUCT = 'product', _('商品について')
        ORDER = 'order', _('ご注文・お支払い')
        SHIPPING = 'shipping', _('配送について')
        OTHER = 'other', _('その他')

    no = models.PositiveIntegerField(_("並び順"), default=1)
    category = models.CharField(_("カテゴリ"), max_length=20, choices=Category.choices, default=Category.OTHER)
    question = models.CharField(_("質問"), max_length=200)
    answer = models.TextField(_("回答"), help_text=_('改行はそのまま反映されます'))
    is_published = models.BooleanField(_("公開"), default=True)
    show_on_top = models.BooleanField(_("トップページに表示"), default=False, help_text=_('トップページのFAQ欄に表示します(最大6件)'))
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        verbose_name = _("よくある質問")
        verbose_name_plural = _("よくある質問")
        ordering = ["no", "id"]

    def __str__(self):
        return self.question

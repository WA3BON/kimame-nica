import requests
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class TurnstileFormMixin:
    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        if request is not None and request.user.is_authenticated:
            user = request.user
            for field_name, value in (("name", user.first_name), ("email", user.email)):
                if field_name in self.fields and value:
                    self.initial[field_name] = value
                    self.fields[field_name].widget.attrs.update({
                        "readonly": "readonly",
                        "class": "opacity-60 cursor-not-allowed",
                    })

    def clean(self):
        cleaned_data = super().clean()
        token = self.data.get("cf-turnstile-response")
        if not self._verify_turnstile(token):
            raise forms.ValidationError(
                "ロボットではないことの確認に失敗しました。もう一度お試しください。"
            )
        if self.request is not None and self.request.user.is_authenticated:
            user = self.request.user
            if "name" in cleaned_data and user.first_name:
                cleaned_data["name"] = user.first_name
            if "email" in cleaned_data and user.email:
                cleaned_data["email"] = user.email
        return cleaned_data

    def _verify_turnstile(self, token):
        if not token:
            return False
        payload = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
        if self.request is not None:
            payload["remoteip"] = self.request.META.get("REMOTE_ADDR")
        try:
            resp = requests.post(TURNSTILE_VERIFY_URL, data=payload, timeout=5)
            resp.raise_for_status()
            return resp.json().get("success", False)
        except requests.RequestException:
            return False


class ContactForm(TurnstileFormMixin, forms.Form):
    name = forms.CharField(label='お名前', max_length=100)
    email = forms.EmailField(label='メールアドレス')
    message = forms.CharField(label='メッセージ', widget=forms.Textarea)
    privacy_agree = forms.BooleanField(
        label='プライバシーポリシーに同意する',
        required=True,
        error_messages={'required': 'プライバシーポリシーへの同意が必要です。'},
    )

class ProfileForm(forms.Form):
    name = forms.CharField(label='お名前', max_length=150)
    email = forms.EmailField(label='メールアドレス')


class SignupForm(forms.Form):
    privacy_agree = forms.BooleanField(
        label=mark_safe('<a href="/privacy-policy/" target="_blank" class="underline">プライバシーポリシー</a>に同意する'),
        required=True,
        error_messages={'required': 'プライバシーポリシーへの同意が必要です。'},
    )
    terms_agree = forms.BooleanField(
        label=mark_safe('<a href="/terms/" target="_blank" class="underline">利用規約</a>に同意する'),
        required=True,
        error_messages={'required': '利用規約への同意が必要です。'},
    )

    def signup(self, request, user):
        pass


class EstimateForm(TurnstileFormMixin, forms.Form):
    name = forms.CharField(label='お名前', max_length=100)
    email = forms.EmailField(label='メールアドレス')
    product = forms.CharField(label='商品名', max_length=100)
    quantity = forms.IntegerField(label='予定数量', min_value=1)

    PREFECTURE_CHOICES = [
        ('北海道', '北海道'), ('青森県', '青森県'), ('岩手県', '岩手県'), ('宮城県', '宮城県'),
        ('秋田県', '秋田県'), ('山形県', '山形県'), ('福島県', '福島県'), ('茨城県', '茨城県'),
        ('栃木県', '栃木県'), ('群馬県', '群馬県'), ('埼玉県', '埼玉県'), ('千葉県', '千葉県'),
        ('東京都', '東京都'), ('神奈川県', '神奈川県'), ('新潟県', '新潟県'), ('富山県', '富山県'),
        ('石川県', '石川県'), ('福井県', '福井県'), ('山梨県', '山梨県'), ('長野県', '長野県'),
        ('岐阜県', '岐阜県'), ('静岡県', '静岡県'), ('愛知県', '愛知県'), ('三重県', '三重県'),
        ('滋賀県', '滋賀県'), ('京都府', '京都府'), ('大阪府', '大阪府'), ('兵庫県', '兵庫県'),
        ('奈良県', '奈良県'), ('和歌山県', '和歌山県'), ('鳥取県', '鳥取県'), ('島根県', '島根県'),
        ('岡山県', '岡山県'), ('広島県', '広島県'), ('山口県', '山口県'), ('徳島県', '徳島県'),
        ('香川県', '香川県'), ('愛媛県', '愛媛県'), ('高知県', '高知県'), ('福岡県', '福岡県'),
        ('佐賀県', '佐賀県'), ('長崎県', '長崎県'), ('熊本県', '熊本県'), ('大分県', '大分県'),
        ('宮崎県', '宮崎県'), ('鹿児島県', '鹿児島県'), ('沖縄県', '沖縄県'),
    ]
    prefecture = forms.ChoiceField(label='お届け先都道府県', choices=PREFECTURE_CHOICES)
    message = forms.CharField(label='メッセージ', widget=forms.Textarea)
    privacy_agree = forms.BooleanField(
        label='プライバシーポリシーに同意する',
        required=True,
        error_messages={'required': 'プライバシーポリシーへの同意が必要です。'},
    )
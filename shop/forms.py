from django import forms

from core.forms import EstimateForm


class CheckoutForm(forms.Form):
    full_name = forms.CharField(label='お名前', max_length=100)
    postal_code = forms.CharField(label='郵便番号', max_length=10)
    prefecture = forms.ChoiceField(label='都道府県', choices=EstimateForm.PREFECTURE_CHOICES)
    city = forms.CharField(label='市区町村', max_length=100)
    address_line1 = forms.CharField(label='番地', max_length=200)
    address_line2 = forms.CharField(label='建物名など', max_length=200, required=False)
    phone = forms.CharField(label='電話番号', max_length=20)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._locked_name = None
        if user is not None and user.is_authenticated and user.first_name:
            self._locked_name = user.first_name
            self.initial['full_name'] = user.first_name
            self.fields['full_name'].widget.attrs.update({
                'readonly': 'readonly',
                'class': 'opacity-60 cursor-not-allowed',
            })

    def clean_full_name(self):
        if self._locked_name:
            return self._locked_name
        return self.cleaned_data['full_name']

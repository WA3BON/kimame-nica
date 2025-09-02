from django.urls import path
from .views import IndexView, ContactView, EstimateView, PrivacyPolicyView, OrderPolicyView, TermsOfServiceView

app_name = 'core'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('estimate/', EstimateView.as_view(), name='estimate'),
    path("privacy-policy/", PrivacyPolicyView.as_view(), name="privacy_policy"),
    path("order-policy/", OrderPolicyView.as_view(), name="order_policy"),
    path('terms/', TermsOfServiceView.as_view(), name='terms_of_service'),
]
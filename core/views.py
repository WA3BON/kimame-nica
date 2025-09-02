from django.contrib import messages 
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.shortcuts import render
from config import settings

from .models import CompanyInfo, ShippingStep, PrivacyPolicy, OrderPolicy, TermsOfService
from shop.models import Product
from .forms import ContactForm, EstimateForm
from django.urls import reverse_lazy
from django.core.mail import send_mail


class IndexView(TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shipping_steps'] = ShippingStep.objects.all()
        context['products'] = Product.objects.all()
        return context
    
class ContactView(FormView):
    template_name = 'core/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('core:contact') 

    def form_valid(self, form):
        send_mail(
            subject='【KiMame】お問合せ',
            message=f"お名前: {form.cleaned_data['name']}\nメール: {form.cleaned_data['email']}\n\n{form.cleaned_data['message']}",
            from_email=form.cleaned_data['email'],
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
        )
        # メッセージ追加
        messages.success(self.request, "お問い合わせを受け付けました。ありがとうございます！")
        return super().form_valid(form)
    
class EstimateView(FormView):
    template_name = 'core/estimate.html'
    form_class = EstimateForm
    success_url = reverse_lazy('core:estimate')

    def form_valid(self, form):
        send_mail(
            subject='【KiMame】見積り依頼',
            message=f"""
            お名前: {form.cleaned_data['name']}
            メール: {form.cleaned_data['email']}
            商品名: {form.cleaned_data['product']}
            予定数量: {form.cleaned_data['quantity']}
            お届け先都道府県: {form.cleaned_data['prefecture']}
            メッセージ: {form.cleaned_data['message']}""",
            from_email=form.cleaned_data['email'],
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
        )
        messages.success(self.request, "見積り依頼を受け付けました。ありがとうございます！")
        return super().form_valid(form)
    
class PrivacyPolicyView(ListView):
    model = PrivacyPolicy
    template_name = 'core/privacy_policy.html'
    context_object_name = 'policies'
    ordering = ['no']  # 1から順に表示

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 注文ポリシー情報（責任者・メール）を渡す
        context['order_policy'] = OrderPolicy.objects.last()
        # 最終更新日用
        context['last_policy'] = self.get_queryset().last()
        return context

class TermsOfServiceView(ListView):
    model = TermsOfService
    template_name = 'core/terms_of_service.html'
    context_object_name = 'terms'
    ordering = ['no']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 注文ポリシー情報（責任者・メール）を渡す
        context['order_policy'] = OrderPolicy.objects.last()
        # 最終更新日用
        context['last_term'] = self.get_queryset().last()
        return context

class OrderPolicyView(TemplateView):
    template_name = "core/order_policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 最新の1件を取得（存在しない場合は None）
        context["policy"] = OrderPolicy.objects.last()
        return context

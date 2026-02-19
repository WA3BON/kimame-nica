import os
from django.contrib import messages
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.shortcuts import render
from django.conf import settings

from .models import (
    AppPolicy,
    ShippingStep,
    PrivacyPolicy,
    OrderPolicy,
    TermsOfService,
)
from shop.models import Product
from .forms import ContactForm, EstimateForm
from django.urls import reverse_lazy
from .google.gmail import send_mail_with_gmail


class IndexView(TemplateView):
    template_name = "core/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["shipping_steps"] = ShippingStep.objects.all().order_by("no")
        context["products"] = Product.objects.all()
        return context


class ContactView(FormView):
    template_name = "core/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("core:contact")

    def form_valid(self, form):
        name = form.cleaned_data["name"]
        email = form.cleaned_data["email"]
        message = form.cleaned_data["message"]

        # ① 管理者へ通知（Gmail API）
        try:
            send_mail_with_gmail(
                to_email=settings.ADMIN_EMAIL,
                subject="【KiMame】新しいお問い合わせ",
                body=f"お名前: {name}\nメール: {email}\n\n{message}",
            )

        except Exception as e:
            print("Gmail送信エラー:", e)

        # ② 問い合わせ者へ自動返信
        send_mail_with_gmail(
            to_email=email,
            subject="【KiMame】お問い合わせありがとうございます",
            body=(
                f"{name} 様\n\n"
                "お問い合わせありがとうございます。\n"
                "以下の内容で受け付けました。\n\n"
                f"{message}\n\n"
                "担当者より折り返しご連絡いたします。"
            ),
        )
        messages.success(
            self.request, "お問い合わせを受け付けました。ありがとうございます！"
        )
        return super().form_valid(form)


class EstimateView(FormView):
    template_name = "core/estimate.html"
    form_class = EstimateForm
    success_url = reverse_lazy("core:estimate")

    def form_valid(self, form):
        name = form.cleaned_data["name"]
        email = form.cleaned_data["email"]
        product = form.cleaned_data["product"]
        quantity = form.cleaned_data["quantity"]
        prefecture = form.cleaned_data["prefecture"]
        message = form.cleaned_data["message"]

        # ① 管理者へ見積り通知（Gmail API）
        admin_body = f"""【見積り依頼】
        お名前: {name}
        メール: {email}
        商品名: {product}予定数量: {quantity}
        お届け先都道府県: {prefecture}
        
        メッセージ:{message}"""

        send_mail_with_gmail(
            to_email=settings.ADMIN_EMAIL,
            subject="【KiMame】見積り依頼",
            body=admin_body,
        )

        # ② 依頼者へ自動返信
        user_body = f"""{name} 様
        
        この度は見積りのご依頼ありがとうございます。
        以下の内容で受け付けました。
        
        商品名: {product}
        予定数量: {quantity}
        お届け先都道府県: {prefecture}
        メッセージ:
        {message}
        
        担当者より折り返しご連絡いたします
        どうぞよろしくお願いいたします。
        
        KiMame"""

        send_mail_with_gmail(
            to_email=email,
            subject="【KiMame】見積り依頼ありがとうございます",
            body=user_body,
        )

        messages.success(
            self.request, "見積り依頼を受け付けました。ありがとうございます！"
        )

        return super().form_valid(form)


class PrivacyPolicyView(ListView):
    model = PrivacyPolicy
    template_name = "core/privacy_policy.html"
    context_object_name = "policies"
    ordering = ["no"]  # 1から順に表示

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 注文ポリシー情報（責任者・メール）を渡す
        context["order_policy"] = OrderPolicy.objects.last()
        # 最終更新日用
        context["last_policy"] = self.get_queryset().last()
        return context


class TermsOfServiceView(ListView):
    model = TermsOfService
    template_name = "core/terms_of_service.html"
    context_object_name = "terms"
    ordering = ["no"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 注文ポリシー情報（責任者・メール）を渡す
        context["order_policy"] = OrderPolicy.objects.last()
        # 最終更新日用
        context["last_term"] = self.get_queryset().last()
        return context


class OrderPolicyView(TemplateView):
    template_name = "core/order_policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 最新の1件を取得（存在しない場合は None）
        context["policy"] = OrderPolicy.objects.last()
        return context

class AppPolicyView(ListView):
    model = AppPolicy
    template_name = "core/app_policy.html"
    context_object_name = "policies"
    ordering = ["no"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 注文ポリシー情報（責任者・メール）を渡す
        context["order_policy"] = OrderPolicy.objects.last()
        # 最終更新日用
        context["last_policy"] = self.get_queryset().last()
        return context
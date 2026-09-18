import os
import json
import math
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from .models import CompanyInfo, Inquiry

from .models import (
    AppPolicy,
    ShippingStep,
    PrivacyPolicy,
    OrderPolicy,
    TermsOfService,
)
from shop.models import Product, Order
from .forms import ContactForm, EstimateForm, ProfileForm
from django.urls import reverse_lazy
from .google.gmail import send_mail_with_gmail


# Nicaragua's approximate bounding box, used to place origin labels on the
# hand-illustrated map image at roughly the right spot (not a real projection).
NICARAGUA_BOUNDS = {"north": 15.0, "south": 10.7, "west": -87.7, "east": -83.0}

# Well-known Nicaraguan places shown as plain reference labels on the origin
# map, so viewers have geographic context for where the product pins sit.
NICARAGUA_LANDMARKS = [
    {"name": "マナグア", "lat": 12.1150, "lng": -86.2362},
    {"name": "レオン", "lat": 12.4340, "lng": -86.8780},
    {"name": "グラナダ", "lat": 11.9297, "lng": -85.9560},
    {"name": "エステリ", "lat": 13.0908, "lng": -86.3540},
    {"name": "マタガルパ", "lat": 12.9250, "lng": -85.9170},
    {"name": "ヒノテガ", "lat": 13.0920, "lng": -85.9990},
    {"name": "チナンデガ", "lat": 12.6280, "lng": -87.1310},
    {"name": "リバス", "lat": 11.4380, "lng": -85.8280},
    {"name": "オメテペ島", "lat": 11.5280, "lng": -85.5150},
    {"name": "ブルーフィールズ", "lat": 12.0080, "lng": -83.7620},
]


def _map_label_position(lat, lng):
    x = (float(lng) - NICARAGUA_BOUNDS["west"]) / (NICARAGUA_BOUNDS["east"] - NICARAGUA_BOUNDS["west"]) * 100
    y = (NICARAGUA_BOUNDS["north"] - float(lat)) / (NICARAGUA_BOUNDS["north"] - NICARAGUA_BOUNDS["south"]) * 100
    return round(max(4, min(96, x)), 1), round(max(4, min(96, y)), 1)


def _spread_pins(points, min_gap=7.0, iterations=8):
    """Nudge pins apart that sit too close together (e.g. two products from
    the same town) so their number badges don't overlap on the map."""
    n = len(points)
    for _ in range(iterations):
        moved = False
        for i in range(n):
            for j in range(i + 1, n):
                dx = points[i]["x"] - points[j]["x"]
                dy = points[i]["y"] - points[j]["y"]
                dist = math.hypot(dx, dy)
                if dist < min_gap:
                    moved = True
                    if dist == 0:
                        dx, dy = 1, 0
                        dist = 1
                    push = (min_gap - dist) / 2
                    ux, uy = dx / dist, dy / dist
                    points[i]["x"] = round(max(4, min(96, points[i]["x"] + ux * push)), 1)
                    points[i]["y"] = round(max(4, min(96, points[i]["y"] + uy * push)), 1)
                    points[j]["x"] = round(max(4, min(96, points[j]["x"] - ux * push)), 1)
                    points[j]["y"] = round(max(4, min(96, points[j]["y"] - uy * push)), 1)
        if not moved:
            break
    return points


def _avoid_landmarks(points, landmarks, min_gap=9.0, iterations=6):
    """Push pins away from nearby landmark labels so the number badge and
    the place-name tag don't sit on top of each other."""
    for _ in range(iterations):
        moved = False
        for p in points:
            for lm in landmarks:
                dx = p["x"] - lm["x"]
                dy = p["y"] - lm["y"]
                dist = math.hypot(dx, dy)
                if dist < min_gap:
                    moved = True
                    if dist == 0:
                        dx, dy = 0, -1
                        dist = 1
                    ux, uy = dx / dist, dy / dist
                    push = min_gap - dist
                    p["x"] = round(max(4, min(96, p["x"] + ux * push)), 1)
                    p["y"] = round(max(4, min(96, p["y"] + uy * push)), 1)
        if not moved:
            break
    return points


class IndexView(TemplateView):
    template_name = "core/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["shipping_steps"] = ShippingStep.objects.all().order_by("no")
        products = Product.objects.all()
        context["products"] = products
        context["featured_products"] = (
            Product.objects.order_by("-created_at").prefetch_related("variants")[:5]
        )

        origin_labels = []
        for p in products:
            if p.latitude is None or p.longitude is None:
                continue
            x, y = _map_label_position(p.latitude, p.longitude)
            origin_labels.append({
                "no": len(origin_labels) + 1,
                "name": p.name,
                "origin": p.origin,
                "x": x,
                "y": y,
                "logo": p.logo.url if p.logo else "",
                "url": reverse("shop:product_detail", args=[p.pk]),
            })
        landmarks = []
        for city in NICARAGUA_LANDMARKS:
            x, y = _map_label_position(city["lat"], city["lng"])
            landmarks.append({"name": city["name"], "x": x, "y": y})
        context["nicaragua_landmarks"] = landmarks

        origin_labels = _spread_pins(origin_labels)
        origin_labels = _avoid_landmarks(origin_labels, landmarks)
        origin_labels = _spread_pins(origin_labels)
        context["origin_labels"] = origin_labels
        return context


class MyPageView(LoginRequiredMixin, FormView):
    template_name = "core/mypage.html"
    form_class = ProfileForm
    success_url = reverse_lazy("core:mypage")

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        initial.update({
            "name": user.first_name,
            "email": user.email,
        })
        return initial

    def form_valid(self, form):
        user = self.request.user
        user.first_name = form.cleaned_data["name"]
        user.email = form.cleaned_data["email"]
        user.save(update_fields=["first_name", "email"])
        messages.success(self.request, "個人情報を更新しました。")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_orders"] = Order.objects.filter(user=self.request.user)[:5]
        context["inquiries"] = Inquiry.objects.filter(user=self.request.user)[:10]
        return context


class TurnstileFormViewMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class ContactView(TurnstileFormViewMixin, FormView):
    template_name = "core/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("core:contact")

    def form_valid(self, form):
        name = form.cleaned_data["name"]
        email = form.cleaned_data["email"]
        message = form.cleaned_data["message"]
        company = CompanyInfo.objects.first()

        Inquiry.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            kind=Inquiry.Kind.CONTACT,
            name=name,
            email=email,
            message=message,
        )

        # ① 管理者へ通知（Gmail API）
        try:
            send_mail_with_gmail(
                to_email=settings.ADMIN_EMAIL,
                subject="【KiMame】新しいお問い合わせ",
                body=f"お名前: {name}\nメール: {email}\n\n{message}",
                sender_name=company.name,
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
            sender_name=company.name,
        )
        messages.success(
            self.request, "お問い合わせを受け付けました。ありがとうございます！"
        )
        return super().form_valid(form)


class EstimateView(TurnstileFormViewMixin, FormView):
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
        company = CompanyInfo.objects.first()

        Inquiry.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            kind=Inquiry.Kind.ESTIMATE,
            name=name,
            email=email,
            product=product,
            quantity=quantity,
            prefecture=prefecture,
            message=message,
        )

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
            sender_name=company.name,
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
            sender_name=company.name,
        )

        messages.success(
            self.request, "見積り依頼を受け付けました。ありがとうございます！"
        )

        return super().form_valid(form)


class PrivacyPolicyView(ListView):
    model = PrivacyPolicy
    template_name = "core/privacy_policy.html"
    context_object_name = "policies"
    ordering = ["no"]  

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
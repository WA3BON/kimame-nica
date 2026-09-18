import json
import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, TemplateView, FormView

from .cart import Cart
from .forms import CheckoutForm
from .models import Address, CartItem, Order, OrderItem, Product, ProductVariant
from core.google.gmail import send_mail_with_gmail
from core.models import CompanyInfo


class ProductListView(ListView):
    model = Product
    template_name = "shop/product_list.html"
    context_object_name = "products"
    ordering = ["no"]

    def get_queryset(self):
        queryset = super().get_queryset()
        product_type = self.request.GET.get("product_type")
        origin = self.request.GET.get("origin")
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        if origin:
            queryset = queryset.filter(origin=origin)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product_types"] = Product.ProductType.choices
        context["origins"] = (
            Product.objects.order_by("origin").values_list("origin", flat=True).distinct()
        )
        context["selected_product_type"] = self.request.GET.get("product_type", "")
        context["selected_origin"] = self.request.GET.get("origin", "")
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "shop/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        variants = list(self.object.variants.all())
        context["variants_json"] = json.dumps([
            {"id": v.pk, "label": v.label, "price": str(v.price), "stock": v.stock}
            for v in variants
        ])
        in_stock = [v for v in variants if v.stock > 0]
        context["default_variant_id"] = (in_stock[0].pk if in_stock else (variants[0].pk if variants else "null"))
        return context


class CartView(TemplateView):
    template_name = "shop/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = Cart(self.request)
        context["cart_items"] = cart.items()
        context["cart_total"] = cart.total()
        return context


class AddToCartView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        variant_id = request.POST.get("variant")
        variant = get_object_or_404(ProductVariant, pk=variant_id, product=product)
        try:
            quantity = int(request.POST.get("quantity", 1))
        except ValueError:
            quantity = 1
        quantity = max(1, quantity)
        Cart(request).add(variant, quantity)
        messages.success(request, f"{product.name}({variant.label})をカートに追加しました。")
        return redirect("shop:cart")


class UpdateCartItemView(View):
    def post(self, request, pk):
        variant = get_object_or_404(ProductVariant, pk=pk)
        try:
            quantity = int(request.POST.get("quantity", 1))
        except ValueError:
            quantity = 1
        Cart(request).set_quantity(variant, quantity)
        return redirect("shop:cart")


class RemoveFromCartView(View):
    def post(self, request, pk):
        variant = get_object_or_404(ProductVariant, pk=pk)
        Cart(request).remove(variant)
        messages.success(request, f"{variant.product.name}({variant.label})をカートから削除しました。")
        return redirect("shop:cart")


class CheckoutView(LoginRequiredMixin, FormView):
    template_name = "shop/checkout.html"
    form_class = CheckoutForm

    def get(self, request, *args, **kwargs):
        if not Cart(request).items():
            messages.error(request, "カートが空です。")
            return redirect("shop:cart")
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        address = Address.objects.filter(user=self.request.user, is_default=True).first()
        if address:
            initial.update({
                "full_name": address.full_name,
                "postal_code": address.postal_code,
                "prefecture": address.prefecture,
                "city": address.city,
                "address_line1": address.address_line1,
                "address_line2": address.address_line2,
                "phone": address.phone,
            })
        return initial

    def form_valid(self, form):
        cart = Cart(self.request)
        cart_items = cart.items()
        if not cart_items:
            messages.error(self.request, "カートが空です。")
            return redirect("shop:cart")

        if not settings.STRIPE_SECRET_KEY:
            messages.error(self.request, "現在お支払い機能は準備中です。しばらくお待ちください。")
            return redirect("shop:cart")

        data = form.cleaned_data
        subtotal = cart.total()

        Address.objects.update_or_create(
            user=self.request.user,
            is_default=True,
            defaults={
                "full_name": data["full_name"],
                "postal_code": data["postal_code"],
                "prefecture": data["prefecture"],
                "city": data["city"],
                "address_line1": data["address_line1"],
                "address_line2": data["address_line2"],
                "phone": data["phone"],
            },
        )

        order = Order.objects.create(
            user=self.request.user,
            subtotal=subtotal,
            total=subtotal,
            contact_email=self.request.user.email,
            shipping_name=data["full_name"],
            shipping_postal_code=data["postal_code"],
            shipping_prefecture=data["prefecture"],
            shipping_city=data["city"],
            shipping_address_line1=data["address_line1"],
            shipping_address_line2=data["address_line2"],
            shipping_phone=data["phone"],
        )
        for entry in cart_items:
            OrderItem.objects.create(
                order=order,
                product=entry["product"],
                variant=entry["variant"],
                product_name=entry["product"].name,
                weight_kg=entry["variant"].weight_kg,
                unit_price=entry["variant"].price,
                quantity=entry["quantity"],
            )

        line_items = [
            {
                "price_data": {
                    "currency": "jpy",
                    "product_data": {"name": f"{entry['product'].name}({entry['variant'].label})"},
                    "unit_amount": int(entry["variant"].price),
                },
                "quantity": entry["quantity"],
            }
            for entry in cart_items
        ]

        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=line_items,
            customer_email=self.request.user.email,
            client_reference_id=str(order.pk),
            success_url=self.request.build_absolute_uri(reverse("shop:checkout_success")),
            cancel_url=self.request.build_absolute_uri(reverse("shop:checkout_cancel")),
        )
        order.stripe_checkout_session_id = session.id
        order.save(update_fields=["stripe_checkout_session_id"])

        return redirect(session.url)


class CheckoutSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "shop/checkout_success.html"


class CheckoutCancelView(LoginRequiredMixin, TemplateView):
    template_name = "shop/checkout_cancel.html"


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            return HttpResponseBadRequest("invalid payload")

        event_type = event["type"]
        session = event["data"]["object"]

        if event_type == "checkout.session.completed":
            self._mark_paid(session)
        elif event_type in ("payment_intent.payment_failed", "checkout.session.async_payment_failed"):
            self._mark_failed(session)

        return HttpResponse(status=200)

    def _mark_paid(self, session):
        order = Order.objects.filter(stripe_checkout_session_id=session.get("id")).first()
        if not order or order.status != Order.Status.PENDING:
            return

        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.stripe_payment_intent_id = session.get("payment_intent", "") or ""
        order.save(update_fields=["status", "paid_at", "stripe_payment_intent_id"])

        for item in order.items.select_related("variant").all():
            if item.variant:
                ProductVariant.objects.filter(pk=item.variant_id).update(
                    stock=max(0, item.variant.stock - item.quantity)
                )

        if order.user:
            CartItem.objects.filter(cart__user=order.user).delete()

        company = CompanyInfo.objects.first()
        body = "\n".join(
            [f"{item.product_name} x{item.quantity} = {item.line_total}円" for item in order.items.all()]
        )
        send_mail_with_gmail(
            to_email=order.contact_email,
            subject="【KiMame】ご注文ありがとうございます",
            body=f"ご注文ありがとうございます。\n\n{body}\n\n合計: {order.total}円",
            sender_name=company.name if company else "KiMame",
        )

    def _mark_failed(self, session):
        order = Order.objects.filter(stripe_checkout_session_id=session.get("id")).first()
        if order and order.status == Order.Status.PENDING:
            order.status = Order.Status.FAILED
            order.save(update_fields=["status"])


class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "shop/order_history.html"
    context_object_name = "orders"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "shop/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderPayView(LoginRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        if order.status != Order.Status.PENDING:
            messages.error(request, "この注文はすでに支払い待ちではありません。")
            return redirect("shop:order_detail", pk=pk)

        if not settings.STRIPE_SECRET_KEY:
            messages.error(request, "現在お支払い機能は準備中です。しばらくお待ちください。")
            return redirect("shop:order_detail", pk=pk)

        line_items = [
            {
                "price_data": {
                    "currency": "jpy",
                    "product_data": {"name": f"{item.product_name}({item.weight_kg}kg)"},
                    "unit_amount": int(item.unit_price),
                },
                "quantity": item.quantity,
            }
            for item in order.items.all()
        ]

        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=line_items,
            customer_email=order.contact_email,
            client_reference_id=str(order.pk),
            success_url=request.build_absolute_uri(reverse("shop:checkout_success")),
            cancel_url=request.build_absolute_uri(reverse("shop:checkout_cancel")),
        )
        order.stripe_checkout_session_id = session.id
        order.save(update_fields=["stripe_checkout_session_id"])
        return redirect(session.url)


class OrderShippingUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        if order.status == Order.Status.FULFILLED:
            messages.error(request, "発送済みの注文はお届け先を変更できません。")
            return redirect("shop:order_detail", pk=pk)

        form = CheckoutForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            order.shipping_name = data["full_name"]
            order.shipping_postal_code = data["postal_code"]
            order.shipping_prefecture = data["prefecture"]
            order.shipping_city = data["city"]
            order.shipping_address_line1 = data["address_line1"]
            order.shipping_address_line2 = data["address_line2"]
            order.shipping_phone = data["phone"]
            order.save(update_fields=[
                "shipping_name", "shipping_postal_code", "shipping_prefecture",
                "shipping_city", "shipping_address_line1", "shipping_address_line2",
                "shipping_phone",
            ])
            messages.success(request, "お届け先を更新しました。")
        else:
            messages.error(request, "入力内容に誤りがあります。もう一度ご確認ください。")
        return redirect("shop:order_detail", pk=pk)

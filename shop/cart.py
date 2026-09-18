from decimal import Decimal

from .models import CartItem, ProductVariant
from .models import Cart as CartModel


class Cart:
    """Cart abstraction: DB-backed for authenticated users, session-backed for guests.

    Items are keyed by ProductVariant (a product + weight combination), not Product,
    since each weight tier has its own price/stock.
    """

    SESSION_KEY = 'cart'

    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None

    # -- internal helpers -------------------------------------------------

    def _session_cart(self):
        return self.request.session.setdefault(self.SESSION_KEY, {})

    def _save_session(self):
        self.request.session.modified = True

    def _db_cart(self, create=False):
        if create:
            cart, _ = CartModel.objects.get_or_create(user=self.user)
            return cart
        return CartModel.objects.filter(user=self.user).first()

    # -- public API ---------------------------------------------------------

    def add(self, variant, quantity=1):
        quantity = max(1, quantity)
        if self.user:
            cart = self._db_cart(create=True)
            item, created = CartItem.objects.get_or_create(
                cart=cart, variant=variant, defaults={'quantity': quantity}
            )
            if not created:
                item.quantity += quantity
                item.save()
        else:
            session_cart = self._session_cart()
            key = str(variant.pk)
            session_cart[key] = session_cart.get(key, 0) + quantity
            self._save_session()

    def set_quantity(self, variant, quantity):
        if self.user:
            cart = self._db_cart(create=True)
            if quantity <= 0:
                CartItem.objects.filter(cart=cart, variant=variant).delete()
            else:
                CartItem.objects.update_or_create(
                    cart=cart, variant=variant, defaults={'quantity': quantity}
                )
        else:
            session_cart = self._session_cart()
            key = str(variant.pk)
            if quantity <= 0:
                session_cart.pop(key, None)
            else:
                session_cart[key] = quantity
            self._save_session()

    def remove(self, variant):
        self.set_quantity(variant, 0)

    def items(self):
        if self.user:
            cart = self._db_cart()
            if not cart:
                return []
            return [
                {
                    'variant': item.variant,
                    'product': item.variant.product,
                    'quantity': item.quantity,
                    'line_total': item.line_total,
                }
                for item in cart.items.select_related('variant__product').all()
            ]
        session_cart = self._session_cart()
        if not session_cart:
            return []
        variants = ProductVariant.objects.select_related('product').in_bulk(session_cart.keys())
        result = []
        for variant_id, quantity in session_cart.items():
            variant = variants.get(int(variant_id))
            if not variant:
                continue
            result.append({
                'variant': variant,
                'product': variant.product,
                'quantity': quantity,
                'line_total': variant.price * quantity,
            })
        return result

    def total(self):
        return sum((entry['line_total'] for entry in self.items()), Decimal('0'))

    def count(self):
        return sum(entry['quantity'] for entry in self.items())

    def clear(self):
        if self.user:
            cart = self._db_cart()
            if cart:
                cart.items.all().delete()
        else:
            self.request.session.pop(self.SESSION_KEY, None)
            self._save_session()

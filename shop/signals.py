from .cart import Cart
from .models import Cart as CartModel, CartItem


def merge_session_cart(sender, request, user, **kwargs):
    session_cart = request.session.pop(Cart.SESSION_KEY, None)
    if not session_cart:
        return
    request.session.modified = True

    db_cart, _ = CartModel.objects.get_or_create(user=user)
    for variant_id, quantity in session_cart.items():
        item, created = CartItem.objects.get_or_create(
            cart=db_cart, variant_id=variant_id, defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()

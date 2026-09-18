from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'

    def ready(self):
        import stripe
        from django.conf import settings
        from django.contrib.auth.signals import user_logged_in
        from . import signals

        stripe.api_key = settings.STRIPE_SECRET_KEY
        user_logged_in.connect(signals.merge_session_cart)

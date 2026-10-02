from django import template
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils import timezone

from blog.models import Post
from core.models import CompanyInfo, Faq, Inquiry, OrderPolicy, ShippingStep, WhyChooseUs
from shop.admin import SOLD_STATUSES, STATUS_STYLES, status_badge_html
from shop.models import Order, ProductVariant

register = template.Library()

LOW_STOCK_THRESHOLD = 3


@register.inclusion_tag('admin/shop/dashboard.html', takes_context=True)
def admin_dashboard(context):
    now = timezone.localtime()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    changelist = reverse('admin:shop_order_changelist')

    counts = dict(Order.objects.values_list('status').annotate(n=Count('id')))
    status_cards = [
        {
            'label': status.label,
            'count': counts.get(status.value, 0),
            'color': STATUS_STYLES[status][0],
            'url': f"{changelist}?status__exact={status.value}",
        }
        for status in Order.Status
    ]

    todo_qs = Order.objects.filter(status__in=[Order.Status.PAID, Order.Status.PREPARING])
    todo_orders = list(
        todo_qs.order_by('created_at')
        .prefetch_related('items')[:20]
    )
    for order in todo_orders:
        order.badge = status_badge_html(order)

    recent_orders = list(Order.objects.prefetch_related('items')[:15])
    for order in recent_orders:
        order.badge = status_badge_html(order)

    sold_this_month = Order.objects.filter(status__in=SOLD_STATUSES, paid_at__gte=month_start)
    month = sold_this_month.aggregate(total=Sum('total'), n=Count('id'))

    return {
        'status_cards': status_cards,
        'todo_orders': todo_orders,
        'todo_count': todo_qs.count(),
        'todo_url': f"{changelist}?status__in={Order.Status.PAID},{Order.Status.PREPARING}",
        'today_count': Order.objects.filter(status__in=SOLD_STATUSES, paid_at__date=now.date()).count(),
        'month_sales': month['total'] or 0,
        'month_count': month['n'],
        'low_stock': ProductVariant.objects.filter(stock__lte=LOW_STOCK_THRESHOLD)
                     .select_related('product').order_by('stock')[:10],
        'recent_orders': recent_orders,
        'recent_inquiries': Inquiry.objects.all()[:5],
        'new_inquiries': Inquiry.objects.filter(status=Inquiry.Status.NEW).count(),
        'draft_posts': Post.objects.filter(is_published=False).count(),
        'company': CompanyInfo.objects.first(),
        'order_policy': OrderPolicy.objects.order_by('-updated_at').first(),
        'shipping_steps': ShippingStep.objects.all(),
        'why_count': WhyChooseUs.objects.count(),
        'faq_count': Faq.objects.filter(is_published=True).count(),
        'faq_top_count': Faq.objects.filter(is_published=True, show_on_top=True).count(),
    }

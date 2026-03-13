from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('no', 'name', 'origin', 'roast_level', 'price', 'stock', 'created_at')
    list_filter = ('origin', 'roast_level')
    search_fields = ('name', 'origin')
    readonly_fields = ('created_at',)
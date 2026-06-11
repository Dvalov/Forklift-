# warehouse/admin.py
from django.contrib import admin
from .models import Warehouse, Cell

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name']

@admin.register(Cell)
class CellAdmin(admin.ModelAdmin):
    list_display = ['id', 'warehouse', 'x', 'y', 'z', 'available']
    list_filter = ['warehouse', 'available']
    search_fields = ['warehouse__name']
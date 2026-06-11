from django.contrib import admin
from .models import Size


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['warehouse_id', 'name', 'row_size', 'shelf_size', 'cell_size', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['warehouse_id', 'name']
    list_editable = ['row_size', 'shelf_size', 'cell_size', 'is_active']

    fieldsets = (
        ('Основная информация', {
            'fields': ('warehouse_id', 'name', 'description', 'is_active')
        }),
        ('Размеры ячейки (в метрах)', {
            'fields': ('row_size', 'shelf_size', 'cell_size'),
            'description': 'Настройте размеры для конвертации адресов ячеек в реальные координаты'
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

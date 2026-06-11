from django.db import models


class Size(models.Model):
    """
    Модель для хранения размеров ячеек склада
    """
    warehouse_id = models.IntegerField(
        'ID склада',
        unique=True,
        db_index=True
    )

    # Размеры ячейки в метрах
    row_size = models.FloatField(
        'Размер ряда (м)',
        default=3.0,
        help_text='Расстояние между рядами стеллажей в метрах'
    )

    shelf_size = models.FloatField(
        'Размер полки (м)',
        default=0.8,
        help_text='Глубина полки в метрах'
    )

    cell_size = models.FloatField(
        'Размер ячейки (м)',
        default=1.2,
        help_text='Высота ячейки в метрах'
    )

    # Дополнительные поля
    name = models.CharField(
        'Название склада',
        max_length=100,
        blank=True,
        null=True
    )

    description = models.TextField(
        'Описание',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        'Активен',
        default=True
    )

    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )

    class Meta:
        app_label = 'Converter_app'
        verbose_name = 'Размер ячейки склада'
        verbose_name_plural = 'Размеры ячеек складов'
        ordering = ['warehouse_id']

    def __str__(self):
        return f"Склад {self.warehouse_id}: {self.row_size}x{self.shelf_size}x{self.cell_size} м"

    def get_dimensions(self):
        """Вернуть размеры в виде словаря"""
        return {
            'row_size': self.row_size,
            'shelf_size': self.shelf_size,
            'cell_size': self.cell_size
        }
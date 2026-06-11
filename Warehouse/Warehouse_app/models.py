
from django.db import models

class Warehouse(models.Model):
    """Модель склада"""
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Cell(models.Model):
    """Модель ячейки склада"""
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='cells')
    x = models.IntegerField()
    y = models.IntegerField()
    z = models.IntegerField()
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['warehouse', 'x', 'y', 'z']
        ordering = ['x', 'y', 'z']

    def __str__(self):
        return f"Cell {self.x}-{self.y}-{self.z} (Warehouse {self.warehouse_id})"
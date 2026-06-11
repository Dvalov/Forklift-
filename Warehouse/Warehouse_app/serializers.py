# warehouse/serializers.py
from rest_framework import serializers
from .models import Cell

class CellSerializer(serializers.ModelSerializer):
    """Сериализатор для ячейки"""
    class Meta:
        model = Cell
        fields = ['id', 'x', 'y', 'z', 'available', 'warehouse_id']
        read_only_fields = ['id', 'warehouse_id']

class CellListSerializer(serializers.Serializer):
    """Сериализатор для списка ячеек"""
    x = serializers.FloatField()
    y = serializers.FloatField()
    z = serializers.FloatField()
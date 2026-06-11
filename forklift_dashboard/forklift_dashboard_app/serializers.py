from rest_framework import serializers
from .models import Forklift, Task


class ForkliftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forklift
        fields = ['id', 'name', 'status', 'position_x', 'position_y', 'position_z', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class ForkliftUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forklift
        fields = ['id', 'name', 'status', 'position_x', 'position_y', 'position_z', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class PositionUpdateSerializer(serializers.Serializer):
    position_x = serializers.FloatField()
    position_y = serializers.FloatField()
    position_z = serializers.FloatField()


class TaskSerializer(serializers.ModelSerializer):
    forklift_id = serializers.IntegerField(source='forklift.id', read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'forklift_id', 'status', 'origin_x', 'origin_y', 'origin_z',
                  'dest_x', 'dest_y', 'dest_z', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskCreateSerializer(serializers.Serializer):
    cell_address = serializers.DictField(child=serializers.IntegerField())

    def validate_cell_address(self, value):
        required_fields = ['row', 'height', 'depth']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing field: {field}")
        return value


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['dest_x', 'dest_y', 'dest_z', 'origin_x', 'origin_y', 'origin_z']
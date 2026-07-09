from rest_framework import serializers
from .models import Forklift, Task


class ForkliftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forklift
        fields = ['id', 'name', 'charge_level', 'status', 'position_x', 'position_y', 'position_z', 'speed', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class ForkliftUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forklift
        fields = ['id', 'name', 'charge_level', 'status', 'position_x', 'position_y', 'position_z', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class PositionUpdateSerializer(serializers.Serializer):
    position_x = serializers.FloatField()
    position_y = serializers.FloatField()
    position_z = serializers.FloatField()


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'forklift_id', 'status', 'origin_x', 'origin_y', 'origin_z',
                  'dest_x', 'dest_y', 'dest_z', 'dest_cell_x', 'dest_cell_y', 'dest_cell_z',
                  'path_waypoints', 'created_at', 'updated_at']
        read_only_fields = ['id', 'forklift_id', 'path_waypoints', 'created_at', 'updated_at']


class TaskCreateSerializer(serializers.Serializer):
    forklift_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    dest_x = serializers.FloatField()
    dest_y = serializers.FloatField()
    dest_z = serializers.FloatField()
    dest_cell_x = serializers.IntegerField()
    dest_cell_y = serializers.IntegerField()
    dest_cell_z = serializers.IntegerField()
    origin_x = serializers.FloatField(required=False, default=0)
    origin_y = serializers.FloatField(required=False, default=0)
    origin_z = serializers.FloatField(required=False, default=0)


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['dest_x', 'dest_y', 'dest_z', 'origin_x', 'origin_y', 'origin_z']
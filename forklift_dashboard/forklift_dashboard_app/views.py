from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django.shortcuts import get_object_or_404
from .models import Forklift, Task
from .serializers import (
    ForkliftSerializer, ForkliftUpdateSerializer, PositionUpdateSerializer,
    TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer
)



class ForkliftViewSet(viewsets.ModelViewSet):
    queryset = Forklift.objects.all()
    serializer_class = ForkliftSerializer

    def get_serializer_class(self):
        if self.action == 'update' or self.action == 'partial_update':
            return ForkliftUpdateSerializer
        return ForkliftSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception:
            return Response({"error": "Forklift not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['put'], url_path='(?P<position>[xyz])')
    def update_position(self, request, id=None, position=None):
        """Обновление позиции погрузчика"""
        try:
            forklift = self.get_object()

            serializer = PositionUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            x = serializer.validated_data.get('position_x', forklift.position_x)
            y = serializer.validated_data.get('position_y', forklift.position_y)
            z = serializer.validated_data.get('position_z', forklift.position_z)

            forklift.update_position(x, y, z)

            return Response({
                'message': 'Position updated successfully',
                'id': forklift.id,
                'name': forklift.name,
                'status': forklift.status,
                'position_x': forklift.position_x,
                'position_y': forklift.position_y,
                'position_z': forklift.position_z,
                'updated_at': forklift.updated_at
            })
        except Exception:
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='status')
    def get_status(self, request, pk=None):
        """Получение телеметрии в реальном времени"""
        try:
            forklift = self.get_object()
            return Response({'status': forklift.status})
        except Exception:
            return Response({"error": "Forklift not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='stop')
    def emergency_stop(self, request, pk=None):
        """Экстренная остановка"""
        try:
            forklift = self.get_object()
            forklift.emergency_stop()
            return Response({
                'message': 'Emergency stop activated',
                'forklift_id': forklift.id,
                'status': forklift.status
            })
        except Exception:
            return Response({"error": "Forklift not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='task/(?P<task_id>[^/.]+)/execute')
    def execute_task(self, request, pk=None, task_id=None):
        """Выполнение задания"""
        try:
            forklift = self.get_object()
            task = get_object_or_404(Task, id=task_id)

            # Обновляем статус задачи
            if task.status != 'pending':
                return Response({"error": "Task is not pending"}, status=status.HTTP_400_BAD_REQUEST)

            task.status = 'in_progress'
            task.forklift = forklift
            task.save()

            # Отправляем погрузчик к точке
            forklift.status = 'moving'
            forklift.save()

            return Response({
                'message': 'Task execution started',
                'forklift_id': forklift.id,
                'task_id': task.id,
                'dest_x': task.dest_x,
                'dest_y': task.dest_y,
                'dest_z': task.dest_z,
                'status': task.status
            })
        except Exception:
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.all()
        status_filter = self.request.query_params.get('status')
        forklift_filter = self.request.query_params.get('forklift')

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if forklift_filter:
            queryset = queryset.filter(forklift_id=forklift_filter)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = TaskCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        forklift = None
        if data.get('forklift_id'):
            try:
                forklift = Forklift.objects.get(pk=data['forklift_id'])
            except Forklift.DoesNotExist:
                return Response({"error": "Forklift not found"}, status=status.HTTP_400_BAD_REQUEST)

        if forklift is None:
            from django.conf import settings as _s
            fallback_id = getattr(_s, 'FORKLIFT_ID', None)
            if fallback_id:
                try:
                    forklift = Forklift.objects.get(pk=fallback_id)
                except Forklift.DoesNotExist:
                    pass  # leave forklift=None; task saved unassigned

        task = Task.objects.create(
            forklift=forklift,
            dest_x=data['dest_x'],
            dest_y=data['dest_y'],
            dest_z=data['dest_z'],
            dest_cell_x=data['dest_cell_x'],
            dest_cell_y=data['dest_cell_y'],
            dest_cell_z=data['dest_cell_z'],
            origin_x=data['origin_x'],
            origin_y=data['origin_y'],
            origin_z=data['origin_z'],
        )

        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Обновление задания (только если pending)"""
        try:
            task = self.get_object()

            if task.status != 'pending':
                return Response({"error": "Can only update pending tasks"},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = TaskUpdateSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Task updated successfully',
                    'id': task.id,
                    'forklift_id': task.forklift.id if task.forklift else None,
                    'status': task.status,
                    'created_at': task.created_at,
                    'updated_at': task.updated_at
                })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, *args, **kwargs):
        """Удаление задания (только pending или cancelled)"""
        try:
            task = self.get_object()

            if not task.can_modify():
                return Response({"error": "Can only delete pending or cancelled tasks"},
                                status=status.HTTP_400_BAD_REQUEST)

            task.delete()
            return Response({'message': 'Task deleted successfully', 'id': kwargs['pk']})

        except Exception:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='restore')
    def restore_task(self, request, pk=None):
        """Восстановление отменённого задания"""
        try:
            task = self.get_object()
            if task.restore():
                return Response({
                    'message': 'Task restored successfully',
                    'id': task.id,
                    'status': task.status,
                })
            return Response({"error": "Can only restore cancelled tasks"},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_task(self, request, pk=None):
        """Отмена задания"""
        try:
            task = self.get_object()

            if task.cancel():
                return Response({
                    'message': 'Task cancelled successfully',
                    'id': task.id,
                    'status': task.status
                })
            return Response({"error": "Can only cancel pending tasks"},
                            status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
# Create your views here.

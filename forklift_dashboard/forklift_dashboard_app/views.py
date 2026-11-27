import logging

from django.conf import settings
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django.shortcuts import get_object_or_404
from .models import Forklift, Task
from .scheduler import (
    anylogic_dispatch_state, dispatch_next_task, dispatch_task, recover_missing_anylogic_orders,
    remove_anylogic_order,
)
from .serializers import (
    ForkliftSerializer, ForkliftUpdateSerializer, PositionUpdateSerializer,
    TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer
)

logger = logging.getLogger(__name__)

class ForkliftViewSet(viewsets.ModelViewSet):
    queryset = Forklift.objects.all()
    serializer_class = ForkliftSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            route = Task.objects.filter(forklift_id=OuterRef('pk'), status='in_progress')
            queryset = queryset.annotate(remaining_waypoints=Subquery(route.values('path_waypoints')[:1]))
        return queryset

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
            logger.info("Task %s status: pending -> in_progress (forklift=%s api=execute)",
                        task.pk, forklift.pk)

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
        if self.action in {'update', 'partial_update', 'destroy', 'cancel_task'}:
            queryset = queryset.select_for_update()
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
            fallback_id = getattr(settings, 'FORKLIFT_ID', None)
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
            source_cell_x=data['source_cell_x'],
            source_cell_y=data['source_cell_y'],
            source_cell_z=data['source_cell_z'],
            source_cell_name=data['source_cell_name'],
            dest_cell_name=data['dest_cell_name'],
        )
        if (
            forklift is not None
            and forklift.pk == settings.FORKLIFT_ID
            and task.source_cell_name
            and task.dest_cell_name
        ):
            with anylogic_dispatch_state() as anylogic_state:
                if anylogic_state is not None:
                    if recover_missing_anylogic_orders(forklift.pk, anylogic_state):
                        dispatch_next_task(anylogic_state, forklift)
                    else:
                        logger.info("Dispatching new task %s to AnyLogic", task.pk)
                        dispatch_task(task.pk, anylogic_state)
                    task.refresh_from_db()
        logger.info("Task %s queued: forklift=%s status=%s", task.pk, task.forklift_id, task.status)

        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Обновление задания (только если pending)"""
        try:
            task = self.get_object()

            if task.status != 'pending' or not task.can_modify():
                return Response({"error": "Can only update unsent pending tasks"},
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
        with anylogic_dispatch_state() as anylogic_state, transaction.atomic():
            task = self.get_object()
            if task.status not in {'pending', 'cancelled'}:
                return Response({"error": "Can only delete pending or cancelled tasks"},
                                status=status.HTTP_409_CONFLICT)

            if task.anylogic_order_number is not None:
                error = remove_anylogic_order(task, anylogic_state)
                if error:
                    status_code, message = error
                    return Response({'error': message}, status=status_code)

            task.delete()
            return Response({'message': 'Task deleted successfully', 'id': kwargs['pk']})

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
    @transaction.atomic
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
            return Response({"error": "Can only cancel unsent pending tasks"},
                            status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
# Create your views here.

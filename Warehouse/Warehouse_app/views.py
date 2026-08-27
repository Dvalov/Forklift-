# warehouse/views.py
import os
import requests as http_requests
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Warehouse, Cell
from .serializers import CellSerializer, CellListSerializer


class CellListView(APIView):
    """GET /api/warehouse/<id>/cells/"""

    def get(self, request, id):
        try:
            # Проверяем существование склада
            warehouse = get_object_or_404(Warehouse, id=id)

            # Получаем ячейки склада
            cells_queryset = warehouse.cells.all()

            # Фильтрация по параметру available
            available_param = request.query_params.get('available')
            if available_param is not None:
                if available_param.lower() == 'true':
                    cells_queryset = cells_queryset.filter(available=True)
                elif available_param.lower() == 'false':
                    cells_queryset = cells_queryset.filter(available=False)
                else:
                    return Response(
                        {"error": "Parameter 'available' must be 'true' or 'false'"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Формируем ответ в указанном формате
            result = [
                {"id": cell.id, "x": cell.x, "y": cell.y, "z": cell.z, "available": cell.available}
                for cell in cells_queryset
            ]

            return Response(result, status=status.HTTP_200_OK)

        except Warehouse.DoesNotExist:
            return Response(
                {"error": f"Warehouse with id={id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CellDetailView(APIView):
    """GET и PUT /api/warehouse/<id>/cell/"""

    def get_cell(self, warehouse_id, x, y, z):
        """Вспомогательный метод для получения ячейки"""
        return get_object_or_404(
            Cell,
            warehouse_id=warehouse_id,
            x=x,
            y=y,
            z=z
        )

    def get(self, request, id):
        """GET /api/warehouse/id/cell/"""
        try:
            # Получаем параметры из query
            x = request.query_params.get('x')
            y = request.query_params.get('y')
            z = request.query_params.get('z')

            # Валидация обязательных параметров
            if x is None or y is None or z is None:
                return Response(
                    {"error": "Parameters 'x', 'y', 'z' are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Преобразуем в int
            try:
                x = int(x)
                y = int(y)
                z = int(z)
            except ValueError:
                return Response(
                    {"error": "Parameters 'x', 'y', 'z' must be integers"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Получаем ячейку
            cell = self.get_cell(id, x, y, z)
            serializer = CellSerializer(cell)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Cell.DoesNotExist:
            return Response(
                {"error": f"Cell with coordinates ({x}, {y}, {z}) not found in warehouse {id}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, id):
        """PUT /api/warehouse/id/cell/"""
        try:
            # Получаем параметры из query
            available = request.query_params.get('available')
            x = request.query_params.get('x')
            y = request.query_params.get('y')
            z = request.query_params.get('z')

            # Валидация обязательных параметров
            if available is None:
                return Response(
                    {"error": "Parameter 'available' is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if x is None or y is None or z is None:
                return Response(
                    {"error": "Parameters 'x', 'y', 'z' are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Преобразуем параметры
            try:
                x = int(x)
                y = int(y)
                z = int(z)
                available = available.lower() == 'true'
            except ValueError:
                return Response(
                    {"error": "Parameters 'x', 'y', 'z' must be integers"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Получаем и обновляем ячейку
            cell = self.get_cell(id, x, y, z)
            cell.available = available
            cell.save()

            return Response({"success": True}, status=status.HTTP_200_OK)

        except Cell.DoesNotExist:
            return Response(
                {"error": f"Cell with coordinates ({x}, {y}, {z}) not found in warehouse {id}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SyncFromOneCView(APIView):
    """POST /api/warehouse/<warehouse_id>/sync-from-1c/
    Calls a 1C HTTP service, normalizes its JSON response through a configurable
    field adapter, and performs an atomic upsert+delete of cells.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, warehouse_id):
        # STEP 1 — look up warehouse
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)

        # STEP 2 — read all env vars inline (NOT at module level)
        onec_url       = os.getenv('ONEC_API_URL')
        onec_user      = os.getenv('ONEC_API_USER', '')
        onec_password  = os.getenv('ONEC_API_PASSWORD', '')
        onec_warehouse = os.getenv('ONEC_WAREHOUSE', '')
        field_x       = os.getenv('ONEC_FIELD_X', 'x')
        field_y       = os.getenv('ONEC_FIELD_Y', 'y')
        field_z       = os.getenv('ONEC_FIELD_Z', 'z')
        field_avail   = os.getenv('ONEC_FIELD_AVAILABLE', 'available')
        root_key      = os.getenv('ONEC_ROOT_KEY', '')

        # STEP 3 — guard: ONEC_API_URL not configured
        if not onec_url:
            return Response({"error": "onec_unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # STEP 4 — call 1C with Basic Auth, timeout=10
        params = {'warehouse': onec_warehouse} if onec_warehouse else {}
        try:
            resp = http_requests.get(onec_url, params=params, auth=(onec_user, onec_password), timeout=10)
            resp.raise_for_status()
            raw = resp.json()
        except Exception:
            return Response({"error": "onec_unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # STEP 5 — normalize to flat list of items
        if root_key:
            items = raw.get(root_key, []) if isinstance(raw, dict) else []
        elif isinstance(raw, dict):
            items = raw.get('value', raw.get('data', []))
        else:
            items = raw  # flat array — Shape A

        # STEP 6 — empty response guard
        if not items:
            return Response(
                {"error": "empty_response", "message": "1C returned 0 cells — sync aborted to prevent accidental deletion of all cells"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # STEP 7 — atomic upsert + delete
        try:
            with transaction.atomic():
                synced = 0
                seen_ids = []
                for item in items:
                    cell, _ = Cell.objects.update_or_create(
                        warehouse=warehouse,
                        x=int(item[field_x]),
                        y=int(item[field_y]),
                        z=int(item[field_z]),
                        defaults={'available': bool(item.get(field_avail, True))},
                    )
                    seen_ids.append(cell.pk)
                    synced += 1
                deleted_count, _ = (
                    Cell.objects.filter(warehouse=warehouse)
                    .exclude(pk__in=seen_ids)
                    .delete()
                )
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # STEP 8 — success response
        return Response({"synced": synced, "deleted": deleted_count}, status=status.HTTP_200_OK)

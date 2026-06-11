# warehouse/views.py
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
                {"x": float(cell.x), "y": float(cell.y), "z": float(cell.z)}
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

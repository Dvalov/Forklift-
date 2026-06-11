from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
import json
import math

from .models import Size


def get_warehouse_size(warehouse_id):
    """
    Получить размеры ячейки для склада из БД или кэша
    """
    cache_key = f'warehouse_size_{warehouse_id}'
    size_data = cache.get(cache_key)

    if size_data is None:
        try:
            size_obj = Size.objects.get(warehouse_id=warehouse_id, is_active=True)
            size_data = {
                'row_size': size_obj.row_size,
                'shelf_size': size_obj.shelf_size,
                'cell_size': size_obj.cell_size,
                'name': size_obj.name or f'Warehouse {warehouse_id}'
            }
            # Кэшируем на 1 час
            cache.set(cache_key, size_data, 3600)
        except Size.DoesNotExist:
            # Возвращаем значения по умолчанию
            size_data = {
                'row_size': 3.0,
                'shelf_size': 0.8,
                'cell_size': 1.2,
                'name': f'Warehouse {warehouse_id} (default)'
            }

    return size_data


def validate_cell_coordinates(x, y, z):
    """
    Валидация координат ячейки
    """
    errors = []

    try:
        x_int = int(x)
        y_int = int(y)
        z_int = int(z)

        if x_int < 1:
            errors.append("x должен быть больше 0")
        if y_int < 1:
            errors.append("y должен быть больше 0")
        if z_int < 1:
            errors.append("z должен быть больше 0")

        return x_int, y_int, z_int, errors
    except (ValueError, TypeError):
        errors.append("x, y, z должны быть целыми числами")
        return None, None, None, errors


@csrf_exempt
@require_http_methods(["GET"])
def convert_cell_address(request, warehouse_id):
    """
    Конвертировать адрес ячейки 1С в реальные координаты (x, y, z)

    GET параметры:
        x (int) — номер ряда стеллажа
        y (int) — уровень полки
        z (int) — глубина ячейки
    """
    try:
        # Получаем параметры
        x_param = request.GET.get('x')
        y_param = request.GET.get('y')
        z_param = request.GET.get('z')

        # Проверяем наличие всех параметров
        if x_param is None or y_param is None or z_param is None:
            return JsonResponse({
                'error': 'Missing required parameters',
                'required': ['x', 'y', 'z']
            }, status=400)

        # Валидация координат ячейки
        x_val, y_val, z_val, errors = validate_cell_coordinates(x_param, y_param, z_param)

        if errors:
            return JsonResponse({
                'error': 'Validation failed',
                'details': errors
            }, status=400)

        # Получаем размеры для склада
        size_data = get_warehouse_size(warehouse_id)

        # Конвертируем в реальные координаты
        real_x = x_val * size_data['row_size']  # ряд × размер ряда
        real_y = y_val * size_data['shelf_size']  # уровень × размер полки
        real_z = z_val * size_data['cell_size']  # глубина × размер ячейки

        response_data = {
            'x': float(real_x),
            'y': float(real_y),
            'z': float(real_z),
            'warehouse': size_data['name'],
            'dimensions_used': {
                'row_size': size_data['row_size'],
                'shelf_size': size_data['shelf_size'],
                'cell_size': size_data['cell_size']
            }
        }

        return JsonResponse(response_data, status=200)

    except Exception as e:
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def get_cell_path(request, warehouse_id):
    """
    Возвращает путь для перемещения между ячейками

    Параметры:
        from_x, from_y, from_z - начальные координаты
        dest_x, dest_y, dest_z - конечные координаты
    """
    try:
        # Получаем данные запроса
        if request.method == "GET":
            data = request.GET
        else:
            data = json.loads(request.body) if request.body else {}

        # Проверяем обязательные параметры
        required_params = ['from_x', 'from_y', 'from_z', 'dest_x', 'dest_y', 'dest_z']
        missing_params = [p for p in required_params if p not in data]

        if missing_params:
            return JsonResponse({
                'error': 'Missing required parameters',
                'missing': missing_params
            }, status=400)

        # Конвертируем координаты
        try:
            from_x = float(data['from_x'])
            from_y = float(data['from_y'])
            from_z = float(data['from_z'])
            dest_x = float(data['dest_x'])
            dest_y = float(data['dest_y'])
            dest_z = float(data['dest_z'])
        except (ValueError, TypeError):
            return JsonResponse({
                'error': 'All coordinates must be valid numbers'
            }, status=400)

        # Получаем параметры пути
        num_points = int(data.get('num_points', 20))
        strategy = data.get('strategy', 'linear')

        # Вычисляем путь
        if strategy == 'linear':
            # Линейная интерполяция
            path = []
            for i in range(num_points + 1):
                t = i / num_points
                point = {
                    'x': round(from_x + (dest_x - from_x) * t, 3),
                    'y': round(from_y + (dest_y - from_y) * t, 3),
                    'z': round(from_z + (dest_z - from_z) * t, 3)
                }
                path.append(point)
        else:
            # Стратегия по умолчанию - линейная
            path = []
            for i in range(num_points + 1):
                t = i / num_points
                point = {
                    'x': round(from_x + (dest_x - from_x) * t, 3),
                    'y': round(from_y + (dest_y - from_y) * t, 3),
                    'z': round(from_z + (dest_z - from_z) * t, 3)
                }
                path.append(point)

        # Вычисляем общую длину пути
        distance = math.sqrt(
            (dest_x - from_x) ** 2 +
            (dest_y - from_y) ** 2 +
            (dest_z - from_z) ** 2
        )

        response_data = {
            'path': path,
            'total_distance': round(distance, 3),
            'start_point': {'x': from_x, 'y': from_y, 'z': from_z},
            'end_point': {'x': dest_x, 'y': dest_y, 'z': dest_z},
            'num_points': len(path),
            'strategy_used': strategy
        }

        return JsonResponse(response_data, status=200)

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT"])
def manage_warehouse_size(request, warehouse_id):
    """
    Управление размерами ячеек склада

    GET - получить размеры
    POST - создать новые размеры
    PUT - обновить существующие размеры
    """
    try:
        if request.method == "GET":
            # Получить размеры
            size_data = get_warehouse_size(warehouse_id)

            # Проверяем, есть ли запись в БД
            try:
                size_obj = Size.objects.get(warehouse_id=warehouse_id)
                exists_in_db = True
            except Size.DoesNotExist:
                exists_in_db = False

            return JsonResponse({
                'warehouse_id': warehouse_id,
                'dimensions': size_data,
                'is_custom': exists_in_db,
                'units': {
                    'row_size': 'meters',
                    'shelf_size': 'meters',
                    'cell_size': 'meters'
                }
            }, status=200)

        elif request.method == "POST":
            # Создать новые размеры
            data = json.loads(request.body) if request.body else {}

            # Проверяем, не существует ли уже запись
            if Size.objects.filter(warehouse_id=warehouse_id).exists():
                return JsonResponse({
                    'error': f'Warehouse {warehouse_id} already exists. Use PUT to update.'
                }, status=400)

            # Создаем новую запись
            size_obj = Size.objects.create(
                warehouse_id=warehouse_id,
                row_size=data.get('row_size', 3.0),
                shelf_size=data.get('shelf_size', 0.8),
                cell_size=data.get('cell_size', 1.2),
                name=data.get('name', ''),
                description=data.get('description', ''),
                is_active=data.get('is_active', True)
            )

            # Очищаем кэш
            cache.delete(f'warehouse_size_{warehouse_id}')

            return JsonResponse({
                'message': 'Warehouse size created successfully',
                'warehouse_id': warehouse_id,
                'dimensions': size_obj.get_dimensions()
            }, status=201)

        elif request.method == "PUT":
            # Обновить существующие размеры
            data = json.loads(request.body) if request.body else {}

            try:
                size_obj = Size.objects.get(warehouse_id=warehouse_id)

                # Обновляем поля
                size_obj.row_size = data.get('row_size', size_obj.row_size)
                size_obj.shelf_size = data.get('shelf_size', size_obj.shelf_size)
                size_obj.cell_size = data.get('cell_size', size_obj.cell_size)
                size_obj.name = data.get('name', size_obj.name)
                size_obj.description = data.get('description', size_obj.description)
                size_obj.is_active = data.get('is_active', size_obj.is_active)
                size_obj.save()

                # Очищаем кэш
                cache.delete(f'warehouse_size_{warehouse_id}')

                return JsonResponse({
                    'message': 'Warehouse size updated successfully',
                    'warehouse_id': warehouse_id,
                    'dimensions': size_obj.get_dimensions()
                }, status=200)

            except Size.DoesNotExist:
                return JsonResponse({
                    'error': f'Warehouse {warehouse_id} not found. Use POST to create.'
                }, status=404)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def list_warehouses(request):
    """
    Список всех складов с их размерами
    """
    try:
        warehouses = Size.objects.filter(is_active=True).values(
            'warehouse_id', 'name', 'row_size', 'shelf_size', 'cell_size', 'description'
        )

        return JsonResponse({
            'total': warehouses.count(),
            'warehouses': list(warehouses)
        }, status=200)

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
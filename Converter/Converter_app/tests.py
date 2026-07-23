from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
import json


class ConverterAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.warehouse_id = 1

    def test_convert_cell_success(self):
        """Тест успешной конвертации ячейки"""
        response = self.client.get(
            reverse('converter_app:convert_cell', args=[self.warehouse_id]),
            {'x': 3, 'y': 2, 'z': 1}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['x'], 9.0)  # 3 × 3.0
        self.assertEqual(data['y'], 1.6)  # 2 × 0.8
        self.assertEqual(data['z'], 1.2)  # 1 × 1.2

    def test_convert_cell_zero_values(self):
        """Тест с нулевыми значениями"""
        response = self.client.get(
            reverse('converter_app:convert_cell', args=[self.warehouse_id]),
            {'x': 0, 'y': 0, 'z': 0}
        )
        self.assertEqual(response.status_code, 400)

    def test_convert_cell_missing_params(self):
        """Тест отсутствующих параметров"""
        response = self.client.get(
            reverse('converter_app:convert_cell', args=[self.warehouse_id]),
            {'x': 3, 'y': 2}
        )
        self.assertEqual(response.status_code, 400)

    def test_convert_cell_invalid_params(self):
        """Тест с невалидными параметрами"""
        response = self.client.get(
            reverse('converter_app:convert_cell', args=[self.warehouse_id]),
            {'x': 'abc', 'y': 2, 'z': 1}
        )
        self.assertEqual(response.status_code, 400)


class AStarPathTestCase(TestCase):
    """
    Все ячейки склада — шкафы (препятствия). Погрузчик едет до ближайшей
    свободной ячейки прохода рядом с целевым шкафом.
    """
    def setUp(self):
        self.client = Client()
        self.warehouse_id = 1
        self.path_url = reverse('converter_app:get_cell_path', args=[self.warehouse_id])

    def _mock_shelves(self, mock_get, shelf_coords):
        """shelf_coords: список (x, z) — позиции шкафов."""
        mock_get.return_value.json.return_value = [
            {"x": x, "y": 1, "z": z, "available": True} for x, z in shelf_coords
        ]
        mock_get.return_value.raise_for_status = lambda: None

    @patch('Converter_app.views.http_requests.get')
    def test_simple_path(self, mock_get):
        # Шкаф на (3,1). Погрузчик с (1,1). Подъезжает к (2,1) — ячейка прохода слева от шкафа.
        self._mock_shelves(mock_get, [(3, 1)])
        response = self.client.get(self.path_url, {
            'from_x': 1, 'from_y': 1, 'from_z': 1,
            'dest_x': 3, 'dest_y': 1, 'dest_z': 1,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('path', data)
        path = data['path']
        self.assertEqual(len(path), 1)
        self.assertEqual(path[0], {'x': 2, 'z': 1})

    @patch('Converter_app.views.http_requests.get')
    def test_integer_waypoints(self, mock_get):
        # Шкаф на (4,1). Все waypoints должны быть целыми.
        self._mock_shelves(mock_get, [(4, 1)])
        response = self.client.get(self.path_url, {
            'from_x': 1, 'from_y': 1, 'from_z': 1,
            'dest_x': 4, 'dest_y': 1, 'dest_z': 1,
        })
        self.assertEqual(response.status_code, 200)
        path = response.json()['path']
        self.assertTrue(len(path) > 0)
        for wp in path:
            self.assertIsInstance(wp['x'], int, f"x not int: {wp}")
            self.assertIsInstance(wp['z'], int, f"z not int: {wp}")

    @patch('Converter_app.views.http_requests.get')
    def test_no_diagonals(self, mock_get):
        # Шкаф на (3,3). Путь до ближайшего прохода должен содержать только ортогональные шаги.
        self._mock_shelves(mock_get, [(3, 3)])
        response = self.client.get(self.path_url, {
            'from_x': 1, 'from_y': 1, 'from_z': 1,
            'dest_x': 3, 'dest_y': 1, 'dest_z': 3,
        })
        self.assertEqual(response.status_code, 200)
        path = response.json()['path']
        full = [{'x': 1, 'z': 1}] + path
        for a, b in zip(full, full[1:]):
            step = abs(a['x'] - b['x']) + abs(a['z'] - b['z'])
            self.assertEqual(step, 1, f"diagonal step between {a} and {b}")

    @patch('Converter_app.views.http_requests.get')
    def test_obstacle_avoidance(self, mock_get):
        # Шкафы: (3,1) — цель, (2,1) — блокирует прямой проход слева.
        # Погрузчик должен найти обход и не заезжать ни в один шкаф.
        self._mock_shelves(mock_get, [(3, 1), (2, 1)])
        response = self.client.get(self.path_url, {
            'from_x': 1, 'from_y': 1, 'from_z': 1,
            'dest_x': 3, 'dest_y': 1, 'dest_z': 1,
        })
        self.assertEqual(response.status_code, 200)
        path = response.json()['path']
        self.assertTrue(len(path) > 0, "path should exist (detour via z row)")
        shelf_positions = {(3, 1), (2, 1)}
        for wp in path:
            self.assertNotIn((wp['x'], wp['z']), shelf_positions, f"shelf in path: {wp}")

    @patch('Converter_app.views.http_requests.get')
    def test_already_at_approach(self, mock_get):
        # Погрузчик уже стоит в ячейке прохода рядом со шкафом — путь пустой.
        self._mock_shelves(mock_get, [(3, 1)])
        response = self.client.get(self.path_url, {
            'from_x': 2, 'from_y': 1, 'from_z': 1,
            'dest_x': 3, 'dest_y': 1, 'dest_z': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"path": []})

    @patch('Converter_app.views.http_requests.get')
    def test_no_path(self, mock_get):
        # Шкаф на (3,3), все 4 соседа тоже шкафы — нет прохода к нему.
        self._mock_shelves(mock_get, [(3, 3), (4, 3), (2, 3), (3, 4), (3, 2)])
        response = self.client.get(self.path_url, {
            'from_x': 1, 'from_y': 1, 'from_z': 1,
            'dest_x': 3, 'dest_y': 1, 'dest_z': 3,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['path'], [])
        self.assertEqual(data.get('error'), 'no_path')

    def test_missing_params(self):
        response = self.client.get(self.path_url, {'from_x': 1})
        self.assertEqual(response.status_code, 400)

    @patch('Converter_app.views.http_requests.get')
    def test_warehouse_unavailable(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        response = self.client.get(self.path_url, {
            'from_x': 1, 'from_y': 1, 'from_z': 1,
            'dest_x': 3, 'dest_y': 1, 'dest_z': 1,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['path'], [])
        self.assertEqual(data.get('error'), 'warehouse_unavailable')

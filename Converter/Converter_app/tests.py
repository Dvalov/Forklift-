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
    def setUp(self):
        self.client = Client()
        self.warehouse_id = 1
        self.path_url = reverse('converter_app:get_cell_path', args=[self.warehouse_id])

    def _no_obstacles(self, mock_get):
        mock_get.return_value.json.return_value = []
        mock_get.return_value.raise_for_status = lambda: None

    @patch('Converter_app.views.http_requests.get')
    def test_simple_path(self, mock_get):
        self._no_obstacles(mock_get)
        response = self.client.get(self.path_url, {
            'from_x': 1, 'from_y': 1, 'from_z': 1,
            'dest_x': 3, 'dest_y': 1, 'dest_z': 1,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('path', data)
        path = data['path']
        self.assertEqual(len(path), 2)
        self.assertEqual(path[0], {'x': 2, 'z': 1})
        self.assertEqual(path[1], {'x': 3, 'z': 1})

    @patch('Converter_app.views.http_requests.get')
    def test_integer_waypoints(self, mock_get):
        self._no_obstacles(mock_get)
        response = self.client.get(self.path_url, {
            'from_x': 1, 'from_y': 1, 'from_z': 1,
            'dest_x': 4, 'dest_y': 1, 'dest_z': 1,
        })
        self.assertEqual(response.status_code, 200)
        path = response.json()['path']
        for wp in path:
            self.assertIsInstance(wp['x'], int, f"x not int: {wp}")
            self.assertIsInstance(wp['z'], int, f"z not int: {wp}")

    @patch('Converter_app.views.http_requests.get')
    def test_no_diagonals(self, mock_get):
        self._no_obstacles(mock_get)
        response = self.client.get(self.path_url, {
            'from_x': 1, 'from_y': 1, 'from_z': 1,
            'dest_x': 3, 'dest_y': 1, 'dest_z': 3,
        })
        self.assertEqual(response.status_code, 200)
        path = response.json()['path']
        # prepend start for pairwise check
        full = [{'x': 1, 'z': 1}] + path
        for a, b in zip(full, full[1:]):
            step = abs(a['x'] - b['x']) + abs(a['z'] - b['z'])
            self.assertEqual(step, 1, f"diagonal step between {a} and {b}")

    @patch('Converter_app.views.http_requests.get')
    def test_obstacle_avoidance(self, mock_get):
        mock_get.return_value.json.return_value = [{"x": 2, "y": 1, "z": 1, "available": False}]
        mock_get.return_value.raise_for_status = lambda: None
        response = self.client.get(self.path_url, {
            'from_x': 1, 'from_y': 1, 'from_z': 1,
            'dest_x': 3, 'dest_y': 1, 'dest_z': 1,
        })
        self.assertEqual(response.status_code, 200)
        path = response.json()['path']
        for wp in path:
            self.assertFalse(wp['x'] == 2 and wp['z'] == 1, f"obstacle in path: {wp}")

    @patch('Converter_app.views.http_requests.get')
    def test_same_cell(self, mock_get):
        self._no_obstacles(mock_get)
        response = self.client.get(self.path_url, {
            'from_x': 2, 'from_y': 1, 'from_z': 2,
            'dest_x': 2, 'dest_y': 1, 'dest_z': 2,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"path": []})

    @patch('Converter_app.views.http_requests.get')
    def test_no_path(self, mock_get):
        mock_get.return_value.json.return_value = [
            {"x": 2, "y": 1, "z": 1, "available": False},
            {"x": 0, "y": 1, "z": 1, "available": False},
            {"x": 1, "y": 1, "z": 2, "available": False},
            {"x": 1, "y": 1, "z": 0, "available": False},
        ]
        mock_get.return_value.raise_for_status = lambda: None
        response = self.client.get(self.path_url, {
            'from_x': 1, 'from_y': 1, 'from_z': 1,
            'dest_x': 5, 'dest_y': 1, 'dest_z': 5,
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

from django.test import TestCase, Client
from django.urls import reverse
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

    def test_get_path_success_get(self):
        """Тест получения пути через GET"""
        response = self.client.get(
            reverse('converter_app:get_cell_path', args=[self.warehouse_id]),
            {
                'from_x': 0, 'from_y': 0, 'from_z': 0,
                'dest_x': 3, 'dest_y': 4, 'dest_z': 5
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('path', data)
        self.assertIn('total_distance', data)
        self.assertIn('start_point', data)
        self.assertIn('end_point', data)

    def test_get_path_success_post(self):
        """Тест получения пути через POST с JSON"""
        response = self.client.post(
            reverse('converter_app:get_cell_path', args=[self.warehouse_id]),
            data=json.dumps({
                'from_x': 0, 'from_y': 0, 'from_z': 0,
                'dest_x': 3, 'dest_y': 4, 'dest_z': 5
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('path', data)

    def test_get_path_missing_params(self):
        """Тест отсутствующих параметров в запросе пути"""
        response = self.client.get(
            reverse('converter_app:get_cell_path', args=[self.warehouse_id]),
            {'from_x': 0, 'from_y': 0}
        )
        self.assertEqual(response.status_code, 400)
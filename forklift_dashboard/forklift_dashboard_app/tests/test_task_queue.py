from unittest.mock import call, patch

from django.test import TestCase
from rest_framework.test import APIClient
from django.conf import settings
from django.utils import timezone
from forklift_dashboard_app.models import Forklift, Task
from forklift_dashboard_app.scheduler import ROUTE_PREVIEW_DURATION, _tick_django_mode


class TestTaskAutoAssign(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.forklift = Forklift.objects.create(
            pk=settings.FORKLIFT_ID,
            name='Test Forklift',
            status='idle',
        )

    def test_create_without_forklift_id_assigns_default(self):
        response = self.client.post('/api/tasks/', {
            'dest_x': 1.0,
            'dest_y': 0.0,
            'dest_z': 1.0,
            'dest_cell_x': 1,
            'dest_cell_y': 1,
            'dest_cell_z': 1,
            'origin_x': 0.0,
            'origin_y': 0.0,
            'origin_z': 0.0,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['forklift_id'], settings.FORKLIFT_ID)

    def test_create_with_explicit_forklift_id_uses_it(self):
        response = self.client.post('/api/tasks/', {
            'forklift_id': self.forklift.pk,
            'dest_x': 2.0,
            'dest_y': 0.0,
            'dest_z': 2.0,
            'dest_cell_x': 2,
            'dest_cell_y': 1,
            'dest_cell_z': 2,
            'origin_x': 0.0,
            'origin_y': 0.0,
            'origin_z': 0.0,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['forklift_id'], self.forklift.pk)


class TestTaskOrdering(TestCase):

    def setUp(self):
        self.forklift = Forklift.objects.create(name='Test Forklift', status='idle')

    def test_pending_sorted_oldest_first(self):
        t1 = Task.objects.create(
            forklift=self.forklift,
            status='pending',
            dest_x=1, dest_y=0, dest_z=1,
            dest_cell_x=1, dest_cell_y=1, dest_cell_z=1,
        )
        t2 = Task.objects.create(
            forklift=self.forklift,
            status='pending',
            dest_x=2, dest_y=0, dest_z=2,
            dest_cell_x=2, dest_cell_y=1, dest_cell_z=2,
        )
        oldest = Task.objects.filter(status='pending').first()
        self.assertEqual(oldest.pk, t1.pk)


class TestLocalTaskRoute(TestCase):
    def setUp(self):
        self.forklift = Forklift.objects.create(name='Test Forklift')
        self.task = Task.objects.create(
            forklift=self.forklift,
            source_cell_x=1, source_cell_y=1, source_cell_z=2,
            dest_cell_x=2, dest_cell_y=1, dest_cell_z=3,
            dest_x=6, dest_y=0.8, dest_z=3.6,
        )

    @patch('forklift_dashboard_app.scheduler._fetch_real_coords', return_value=None)
    @patch('forklift_dashboard_app.scheduler._fetch_path')
    def test_drives_to_pickup_before_delivering(self, fetch_path, _fetch_coords):
        self.task.frontend_advanced_at = timezone.now()
        self.task.save(update_fields=['frontend_advanced_at'])
        pickup = [{'x': 0, 'z': 1}, {'x': 0, 'z': 2}]
        delivery = [{'x': 0, 'z': 3}, {'x': 1, 'z': 3}, {'x': 2, 'z': 3}]
        fetch_path.side_effect = [pickup, delivery]

        _tick_django_mode(self.forklift, self.forklift.pk, 1)
        self.task.refresh_from_db()
        with patch('forklift_dashboard_app.scheduler.timezone.now', return_value=self.task.updated_at):
            _tick_django_mode(self.forklift, self.forklift.pk, 1)
        snapshot = self.client.get(f'/api/forklifts/{self.forklift.pk}/').json()
        self.assertEqual(snapshot['remaining_waypoints'], pickup + delivery)
        self.assertEqual((snapshot['cell_x'], snapshot['cell_z']), (0, 0))
        self.assertEqual(snapshot['status'], 'idle')

        Task.objects.filter(pk=self.task.pk).update(updated_at=timezone.now() - ROUTE_PREVIEW_DURATION)

        for index, expected_cell in enumerate(((0, 1), (0, 2), (0, 3), (1, 3), (2, 3))):
            _tick_django_mode(self.forklift, self.forklift.pk, 1)
            self.forklift.refresh_from_db()
            self.task.refresh_from_db()
            self.assertEqual((self.forklift.cell_x, self.forklift.cell_z), expected_cell)
            self.assertEqual(self.task.status, 'completed' if index == 4 else 'in_progress')
            self.assertEqual(len(self.task.path_waypoints), 4 - index)

        snapshot = self.client.get(f'/api/forklifts/{self.forklift.pk}/').json()
        self.assertIsNone(snapshot['remaining_waypoints'])

        self.assertEqual(fetch_path.call_args_list, [
            call(self.forklift.pk, 1, 0, 1, 0, 1, 1, 2),
            call(self.forklift.pk, 1, 0, 1, 2, 3, 1, 3),
        ])

    @patch('forklift_dashboard_app.scheduler.http_requests.get')
    def test_failed_delivery_route_leaves_task_pending(self, get):
        get.return_value.json.side_effect = [
            {'path': []},
            {'path': [], 'error': 'no_path'},
        ]

        _tick_django_mode(self.forklift, self.forklift.pk, 1)

        self.task.refresh_from_db()
        self.assertEqual(get.call_count, 2)
        self.assertEqual(self.task.status, 'pending')
        self.assertEqual(self.task.path_waypoints, [])

    def test_legacy_advance_endpoint_cannot_consume_a_waypoint(self):
        self.task.status = 'in_progress'
        self.task.path_waypoints = [{'x': 0, 'z': 1}]
        self.task.save()

        response = self.client.post(f'/api/tasks/{self.task.pk}/advance/')

        self.assertEqual(response.status_code, 404)
        self.task.refresh_from_db()
        self.assertEqual(self.task.path_waypoints, [{'x': 0, 'z': 1}])

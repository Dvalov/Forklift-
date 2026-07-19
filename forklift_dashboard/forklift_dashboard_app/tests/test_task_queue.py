from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.conf import settings
from forklift_dashboard_app.models import Forklift, Task


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

from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient
from requests import ReadTimeout
from unittest.mock import patch
from forklift_dashboard_app.models import Forklift, Task
from forklift_dashboard_app.scheduler import _tick_anylogic_mode


class AnyLogicSchedulerTests(TestCase):

    def setUp(self):
        self.forklift = Forklift.objects.create(
            pk=settings.FORKLIFT_ID,
            name='Test Forklift',
            status='idle',
            charge_level=20.0,
        )

    def test_charging_state_does_not_affect_pending_task(self):
        task = Task.objects.create(
            forklift=self.forklift,
            status='pending',
            dest_x=1, dest_y=0, dest_z=1,
            dest_cell_name='Cell_1',
            source_cell_name='Cell_0',
        )
        state = {'forklifts': [{'state': 'Charging', 'charge': 25.0}]}
        _tick_anylogic_mode(self.forklift, state)

        self.forklift.refresh_from_db()
        task.refresh_from_db()
        self.assertEqual(self.forklift.status, 'charging')
        self.assertEqual(self.forklift.charge_level, 25.0)
        self.assertEqual(task.status, 'pending')

    def test_return_to_base_after_charging_leaves_task_pending(self):
        task = Task.objects.create(
            forklift=self.forklift,
            status='pending',
            dest_x=1, dest_y=0, dest_z=1,
            dest_cell_name='Cell_1',
            source_cell_name='Cell_0',
        )
        # Forklift exits charging and is returning to base
        state = {'forklifts': [{'state': 'ReturnToBase', 'charge': 100.0}]}
        _tick_anylogic_mode(self.forklift, state)

        self.forklift.refresh_from_db()
        task.refresh_from_db()
        self.assertEqual(self.forklift.status, 'moving')
        self.assertEqual(task.status, 'pending')  # Still pending until AnyLogic actually starts order

    def test_arrival_at_idle_does_not_complete_task(self):
        task = Task.objects.create(
            forklift=self.forklift,
            status='pending',
            dest_x=1, dest_y=0, dest_z=1,
            dest_cell_name='Cell_1',
            source_cell_name='Cell_0',
        )
        # Forklift arrives at base (Idle) after ReturnToBase
        state = {'forklifts': [{'state': 'Idle', 'busy': False, 'charge': 100.0}]}
        _tick_anylogic_mode(self.forklift, state)

        self.forklift.refresh_from_db()
        task.refresh_from_db()
        self.assertEqual(self.forklift.status, 'idle')
        self.assertEqual(task.status, 'pending')  # NOT completed!

    def test_task_remains_pending_on_working_states(self):
        for working_state in ('GoToSource', 'PickUp', 'GoToDest', 'PutDown'):
            task = Task.objects.create(
                forklift=self.forklift,
                status='pending',
                dest_x=1, dest_y=0, dest_z=1,
                dest_cell_name='Cell_1',
                source_cell_name='Cell_0',
            )
            state = {'forklifts': [{'state': working_state, 'charge': 99.0}]}
            _tick_anylogic_mode(self.forklift, state)

            task.refresh_from_db()
            self.assertEqual(task.status, 'pending')
            task.delete()

    def _order_payload(self):
        return {
            'forklift_id': self.forklift.pk,
            'dest_x': 1, 'dest_y': 0, 'dest_z': 1,
            'dest_cell_x': 1, 'dest_cell_y': 1, 'dest_cell_z': 1,
            'source_cell_name': 'Cell_0', 'dest_cell_name': 'Cell_1',
        }

    def _state(self, state, pending, done):
        return {
            'cells': [{'name': 'Cell_0', 'id': 10}, {'name': 'Cell_1', 'id': 20}],
            'forklifts': [{'state': state, 'busy': state != 'Idle'}],
            'pending': pending,
            'done': done,
        }

    @patch('forklift_dashboard_app.scheduler._fetch_anylogic_state')
    @patch('forklift_dashboard_app.scheduler.http_requests.post')
    def test_create_sends_while_busy_and_syncs_each_order(self, post, fetch_state):
        post.return_value.json.return_value = {'ok': True}
        fetch_state.side_effect = [
            self._state('GoToDest', pending=0, done=4),
            self._state('GoToDest', pending=1, done=4),
        ]
        client = APIClient()

        responses = [client.post('/api/tasks/', self._order_payload(), format='json') for _ in range(2)]
        for response in responses:
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data['status'], 'pending')
            self.assertFalse(response.data['can_modify'])

        first, second = [Task.objects.get(pk=response.data['id']) for response in responses]
        self.assertEqual((first.anylogic_order_number, second.anylogic_order_number), (6, 7))
        self.assertEqual(post.call_count, 2)
        self.assertEqual(post.call_args.kwargs['json'], {'sourceCellId': 10, 'destCellId': 20})
        self.assertEqual(client.post(f'/api/tasks/{second.pk}/cancel/').status_code, 400)

        for state, pending, done, expected in (
            ('GoToDest', 2, 4, ('pending', 'pending')),
            ('GoToSource', 1, 5, ('in_progress', 'pending')),
            ('GoToSource', 0, 6, ('completed', 'in_progress')),
            ('Idle', 0, 7, ('completed', 'completed')),
        ):
            with self.subTest(done=done):
                _tick_anylogic_mode(self.forklift, self._state(state, pending, done))
                first.refresh_from_db()
                second.refresh_from_db()
                self.assertEqual((first.status, second.status), expected)
                self.assertEqual(post.call_count, 2)

    @patch('forklift_dashboard_app.scheduler._fetch_anylogic_state', return_value=None)
    @patch('forklift_dashboard_app.scheduler.http_requests.post')
    def test_offline_task_retries_while_charging_and_accepts_only_ok_true(self, post, fetch_state):
        post.return_value.json.side_effect = [{'ok': False}, {'ok': True}]
        response = APIClient().post('/api/tasks/', self._order_payload(), format='json')
        self.assertEqual(response.status_code, 201)
        task = Task.objects.get(pk=response.data['id'])
        self.assertIsNone(task.anylogic_order_number)

        state = self._state('Charging', pending=0, done=4)
        _tick_anylogic_mode(self.forklift, state)
        task.refresh_from_db()
        self.assertIsNone(task.anylogic_order_number)

        _tick_anylogic_mode(self.forklift, state)
        task.refresh_from_db()
        self.assertEqual(task.anylogic_order_number, 5)
        self.assertEqual(task.status, 'pending')

    @patch('forklift_dashboard_app.scheduler._fetch_anylogic_state')
    @patch('forklift_dashboard_app.scheduler.http_requests.post', side_effect=ReadTimeout)
    def test_timeout_after_sending_does_not_resend(self, post, fetch_state):
        fetch_state.return_value = self._state('Idle', pending=0, done=0)
        response = APIClient().post('/api/tasks/', self._order_payload(), format='json')
        task = Task.objects.get(pk=response.data['id'])
        self.assertEqual(task.status, 'pending')
        self.assertEqual(task.anylogic_order_number, 0)
        _tick_anylogic_mode(self.forklift, fetch_state.return_value)
        post.assert_called_once()

    @patch('forklift_dashboard_app.scheduler._fetch_anylogic_state', return_value=None)
    @patch('forklift_dashboard_app.scheduler.http_requests.delete')
    def test_delete_unsent_pending_task_without_anylogic(self, delete, fetch_state):
        task = Task.objects.create(**self._order_payload())

        response = APIClient().delete(f'/api/tasks/{task.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
        delete.assert_not_called()

    @patch('forklift_dashboard_app.scheduler._fetch_anylogic_state')
    @patch('forklift_dashboard_app.scheduler.http_requests.delete')
    def test_delete_waiting_order_without_shifting_following_task_statuses(self, delete, fetch_state):
        waiting = Task.objects.create(**self._order_payload(), anylogic_order_number=2)
        following = Task.objects.create(**self._order_payload(), anylogic_order_number=3)
        fetch_state.return_value = self._state('GoToDest', pending=2, done=0)
        delete.return_value.json.return_value = {'ok': True}

        response = APIClient().delete(f'/api/tasks/{waiting.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(pk=waiting.pk).exists())
        self.assertTrue(delete.call_args.args[0].endswith(f'/order/{waiting.pk}'))
        self.assertEqual(delete.call_args.kwargs['params']['orderNumber'], 2)

        for state, done, expected in (('GoToSource', 1, 'in_progress'), ('Idle', 2, 'completed')):
            snapshot = self._state(state, pending=0, done=done)
            snapshot['cancelledOrders'] = [2]
            _tick_anylogic_mode(self.forklift, snapshot)
            following.refresh_from_db()
            self.assertEqual(following.status, expected)

    @patch('forklift_dashboard_app.scheduler._fetch_anylogic_state')
    @patch('forklift_dashboard_app.scheduler.http_requests.delete')
    def test_delete_retains_task_if_anylogic_has_already_started_it(self, delete, fetch_state):
        task = Task.objects.create(**self._order_payload(), anylogic_order_number=1)
        fetch_state.return_value = self._state('GoToSource', pending=0, done=0)
        delete.return_value.json.return_value = {'ok': False, 'error': 'not_pending'}

        response = APIClient().delete(f'/api/tasks/{task.pk}/')

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())

    @patch('forklift_dashboard_app.scheduler._fetch_anylogic_state')
    @patch('forklift_dashboard_app.scheduler.http_requests.post')
    def test_empty_queue_after_restart_restores_pending_orders_in_order(self, post, fetch_state):
        payload = self._order_payload()
        pending_first = Task.objects.create(**payload, anylogic_order_number=6)
        pending_second = Task.objects.create(
            **{**payload, 'source_cell_name': 'Cell_1', 'dest_cell_name': 'Cell_0'},
            anylogic_order_number=7,
        )
        finished = Task.objects.create(**payload, status='completed', anylogic_order_number=5)
        post.return_value.json.return_value = {'ok': True}
        fresh_state = self._state('Idle', pending=0, done=0)
        fetch_state.return_value = fresh_state

        _tick_anylogic_mode(self.forklift, fresh_state)
        pending_first.refresh_from_db()
        pending_second.refresh_from_db()
        self.assertEqual(pending_first.anylogic_order_number, 1)
        self.assertIsNone(pending_second.anylogic_order_number)
        self.assertEqual(post.call_args.kwargs['json'], {'sourceCellId': 10, 'destCellId': 20})

        state_with_first_order = self._state('GoToSource', pending=0, done=0)
        _tick_anylogic_mode(self.forklift, state_with_first_order)
        pending_first.refresh_from_db()
        pending_second.refresh_from_db()
        finished.refresh_from_db()
        self.assertEqual(pending_first.status, 'in_progress')
        self.assertEqual((pending_second.status, pending_second.anylogic_order_number), ('pending', 2))
        self.assertEqual((finished.status, finished.anylogic_order_number), ('completed', 5))
        self.assertEqual(post.call_args.kwargs['json'], {'sourceCellId': 20, 'destCellId': 10})

        _tick_anylogic_mode(self.forklift, self._state('GoToSource', pending=1, done=0))
        self.assertEqual(post.call_count, 2)
        fetch_state.assert_called_once()

    @patch('forklift_dashboard_app.scheduler._fetch_anylogic_state')
    @patch('forklift_dashboard_app.scheduler.http_requests.post')
    def test_recovery_does_not_resend_if_confirmation_shows_an_existing_order(self, post, fetch_state):
        task = Task.objects.create(**self._order_payload(), anylogic_order_number=1)
        fetch_state.return_value = self._state('GoToSource', pending=0, done=0)

        _tick_anylogic_mode(self.forklift, self._state('Idle', pending=0, done=0))
        task.refresh_from_db()
        self.assertEqual(task.anylogic_order_number, 1)
        post.assert_not_called()

    def test_task_completes_when_anylogic_complete_or_idle(self):
        task = Task.objects.create(
            forklift=self.forklift,
            status='in_progress',
            dest_x=1, dest_y=0, dest_z=1,
            dest_cell_name='Cell_1',
            source_cell_name='Cell_0',
        )
        # Order finishes, state is Complete
        state = {'forklifts': [{'state': 'Complete', 'charge': 95.0}]}
        _tick_anylogic_mode(self.forklift, state)

        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')

    def test_goto_charger_does_not_affect_tasks(self):
        task = Task.objects.create(
            forklift=self.forklift,
            status='pending',
            dest_x=1, dest_y=0, dest_z=1,
            dest_cell_name='Cell_1',
            source_cell_name='Cell_0',
        )
        state = {'forklifts': [{'state': 'GoToCharger', 'charge': 15.0}]}
        _tick_anylogic_mode(self.forklift, state)

        self.forklift.refresh_from_db()
        task.refresh_from_db()
        self.assertEqual(self.forklift.status, 'moving')
        self.assertEqual(task.status, 'pending')

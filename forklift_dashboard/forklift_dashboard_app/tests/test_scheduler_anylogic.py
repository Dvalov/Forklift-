from django.test import TestCase
from unittest.mock import patch
from forklift_dashboard_app.models import Forklift, Task
from forklift_dashboard_app.scheduler import _tick_anylogic_mode


class AnyLogicSchedulerTests(TestCase):

    def setUp(self):
        self.enterContext(patch('forklift_dashboard_app.scheduler._last_dispatched_task_id', None))
        self.forklift = Forklift.objects.create(
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

    @patch('forklift_dashboard_app.scheduler._dispatch_next_task')
    def test_return_to_base_after_charging_leaves_task_pending(self, mock_dispatch):
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
        mock_dispatch.assert_not_called()

    @patch('forklift_dashboard_app.scheduler._dispatch_next_task')
    def test_arrival_at_idle_does_not_complete_task_and_triggers_dispatch(self, mock_dispatch):
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
        mock_dispatch.assert_called_once()

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

    @patch('forklift_dashboard_app.scheduler._dispatch_next_task')
    def test_in_progress_task_completes_before_next_dispatch(self, mock_dispatch):
        for start_state in ('Complete', 'Idle', 'ReturnToBase'):
            mock_dispatch.reset_mock()
            in_prog = Task.objects.create(
                forklift=self.forklift,
                status='in_progress',
                dest_x=1, dest_y=0, dest_z=1,
                dest_cell_name='Cell_1',
                source_cell_name='Cell_0',
            )
            pending = Task.objects.create(
                forklift=self.forklift,
                status='pending',
                dest_x=2, dest_y=0, dest_z=2,
                dest_cell_name='Cell_2',
                source_cell_name='Cell_1',
            )
            state = {'forklifts': [{'state': start_state, 'busy': False, 'charge': 80.0}]}
            _tick_anylogic_mode(self.forklift, state)

            in_prog.refresh_from_db()
            self.assertEqual(in_prog.status, 'completed')
            if start_state != 'Idle':
                mock_dispatch.assert_not_called()
                _tick_anylogic_mode(self.forklift, {'forklifts': [{'state': 'Idle', 'busy': True}]})
                mock_dispatch.assert_not_called()
                _tick_anylogic_mode(self.forklift, {'forklifts': [{'state': 'Idle', 'busy': False}]})
            mock_dispatch.assert_called_once()

            in_prog.delete()
            pending.delete()

    @patch('forklift_dashboard_app.scheduler._dispatch_next_task')
    def test_just_dispatched_task_not_immediately_completed_on_subsequent_ticks(self, mock_dispatch):
        import forklift_dashboard_app.scheduler as sched
        task = Task.objects.create(
            forklift=self.forklift,
            status='in_progress',
            dest_x=1, dest_y=0, dest_z=1,
            dest_cell_name='Cell_1',
            source_cell_name='Cell_0',
        )
        # Simulate that task was just dispatched in current or previous tick
        sched._last_dispatched_task_id = task.pk

        for start_state in ('ReturnToBase', 'Idle'):
            mock_dispatch.reset_mock()
            state = {'forklifts': [{'state': start_state, 'busy': False, 'charge': 80.0}]}
            _tick_anylogic_mode(self.forklift, state)

            task.refresh_from_db()
            self.assertEqual(task.status, 'in_progress')
            mock_dispatch.assert_not_called()

        sched._last_dispatched_task_id = None
        task.delete()

    @patch('forklift_dashboard_app.scheduler.http_requests.post')
    def test_dispatch_next_task_sets_in_progress_on_success(self, mock_post):
        mock_resp = mock_post.return_value
        mock_resp.ok = True
        mock_resp.status_code = 200

        task = Task.objects.create(
            forklift=self.forklift,
            status='pending',
            dest_x=1, dest_y=0, dest_z=1,
            dest_cell_name='Cell_1',
            source_cell_name='Cell_0',
        )
        state = {
            'cells': [
                {'name': 'Cell_0', 'id': 10},
                {'name': 'Cell_1', 'id': 20},
            ],
            'forklifts': [{'state': 'Idle', 'busy': False, 'charge': 100.0}],
        }
        _tick_anylogic_mode(self.forklift, state)

        task.refresh_from_db()
        self.assertEqual(task.status, 'in_progress')
        mock_post.assert_called_once()

    @patch('forklift_dashboard_app.scheduler._dispatch_next_task')
    def test_dispatch_requires_explicit_idle_and_not_busy(self, mock_dispatch):
        for forklifts in (
            [],
            [{'busy': False}],
            [{'state': 'Idle'}],
            [{'state': 'Idle', 'busy': True}],
            [{'state': 'Complete', 'busy': False}],
            [{'state': 'ReturnToBase', 'busy': False}],
        ):
            with self.subTest(forklifts=forklifts):
                _tick_anylogic_mode(self.forklift, {'forklifts': forklifts})
                mock_dispatch.assert_not_called()

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

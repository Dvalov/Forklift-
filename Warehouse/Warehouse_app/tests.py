from django.test import TestCase
from unittest.mock import patch, MagicMock
from Warehouse_app.models import Warehouse, Cell
import requests


class SyncViewTests(TestCase):
    """Test suite for SyncFromOneCView — POST /api/warehouse/<id>/sync-from-1c/"""

    def setUp(self):
        self.warehouse = Warehouse.objects.create(name='Test Warehouse')
        self.url = f'/api/warehouse/{self.warehouse.id}/sync-from-1c/'

    def _make_getenv(self, overrides):
        """Return a side_effect function that uses overrides for known keys,
        falling back to os.environ.get() (not os.getenv) to avoid infinite
        recursion when os.getenv itself is patched."""
        import os as _os

        def _getenv(key, default=None):
            if key in overrides:
                return overrides[key]
            # Use os.environ.get directly — avoids calling os.getenv which is mocked
            return _os.environ.get(key, default)

        return _getenv

    def _base_overrides(self):
        """Default env overrides: 1C URL set, default field names."""
        return {
            'ONEC_API_URL': 'http://fake-1c/',
            'ONEC_API_USER': '',
            'ONEC_API_PASSWORD': '',
            'ONEC_FIELD_X': 'x',
            'ONEC_FIELD_Y': 'y',
            'ONEC_FIELD_Z': 'z',
            'ONEC_FIELD_AVAILABLE': 'available',
            'ONEC_ROOT_KEY': '',
        }

    # ------------------------------------------------------------------
    # Case 1 — success upsert (SYNC-01, SYNC-04, SYNC-06)
    # ------------------------------------------------------------------
    @patch('Warehouse_app.views.os.getenv')
    @patch('Warehouse_app.views.http_requests.get')
    def test_success_upsert(self, mock_get, mock_getenv):
        """1C returns two cells → synced=2, deleted=0, two Cell rows created."""
        mock_getenv.side_effect = self._make_getenv(self._base_overrides())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = [
            {'x': 1, 'y': 1, 'z': 1, 'available': True},
            {'x': 2, 'y': 1, 'z': 1, 'available': False},
        ]
        mock_get.return_value = mock_resp

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'synced': 2, 'deleted': 0})
        self.assertEqual(Cell.objects.filter(warehouse=self.warehouse).count(), 2)

    # ------------------------------------------------------------------
    # Case 2 — stale cells deleted (SYNC-05)
    # ------------------------------------------------------------------
    @patch('Warehouse_app.views.os.getenv')
    @patch('Warehouse_app.views.http_requests.get')
    def test_stale_cells_deleted(self, mock_get, mock_getenv):
        """Existing stale cell at (9,9,9) is deleted when 1C omits it."""
        mock_getenv.side_effect = self._make_getenv(self._base_overrides())

        # Pre-seed a stale cell
        Cell.objects.create(warehouse=self.warehouse, x=9, y=9, z=9, available=True)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = [
            {'x': 1, 'y': 1, 'z': 1, 'available': True},
        ]
        mock_get.return_value = mock_resp

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['deleted'], 1)
        self.assertFalse(
            Cell.objects.filter(warehouse=self.warehouse, x=9, y=9, z=9).exists()
        )

    # ------------------------------------------------------------------
    # Case 3 — 1C unreachable → 503 (SYNC-06)
    # ------------------------------------------------------------------
    @patch('Warehouse_app.views.os.getenv')
    @patch('Warehouse_app.views.http_requests.get')
    def test_1c_unavailable_503(self, mock_get, mock_getenv):
        """ConnectionError from requests → 503 onec_unavailable, no DB changes."""
        mock_getenv.side_effect = self._make_getenv(self._base_overrides())

        # Pre-seed a cell; it must survive the failed sync
        Cell.objects.create(warehouse=self.warehouse, x=1, y=1, z=1, available=True)

        mock_get.side_effect = requests.ConnectionError('refused')

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'error': 'onec_unavailable'})
        # Cell count unchanged
        self.assertEqual(Cell.objects.filter(warehouse=self.warehouse).count(), 1)

    # ------------------------------------------------------------------
    # Case 4 — empty response guard → 400
    # ------------------------------------------------------------------
    @patch('Warehouse_app.views.os.getenv')
    @patch('Warehouse_app.views.http_requests.get')
    def test_empty_response_400(self, mock_get, mock_getenv):
        """1C returns [] → 400 empty_response, no cells created or deleted."""
        mock_getenv.side_effect = self._make_getenv(self._base_overrides())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = []
        mock_get.return_value = mock_resp

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'empty_response')
        self.assertEqual(Cell.objects.filter(warehouse=self.warehouse).count(), 0)

    # ------------------------------------------------------------------
    # Case 5 — custom field mapping (SYNC-02, SYNC-03)
    # ------------------------------------------------------------------
    @patch('Warehouse_app.views.os.getenv')
    @patch('Warehouse_app.views.http_requests.get')
    def test_custom_field_mapping(self, mock_get, mock_getenv):
        """Custom ONEC_FIELD_* env vars map non-standard 1C keys to cell coords."""
        overrides = {
            'ONEC_API_URL': 'http://fake-1c/',
            'ONEC_API_USER': '',
            'ONEC_API_PASSWORD': '',
            'ONEC_FIELD_X': 'col_x',
            'ONEC_FIELD_Y': 'col_y',
            'ONEC_FIELD_Z': 'col_z',
            'ONEC_FIELD_AVAILABLE': 'avail',
            'ONEC_ROOT_KEY': '',
        }
        mock_getenv.side_effect = self._make_getenv(overrides)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = [
            {'col_x': 3, 'col_y': 2, 'col_z': 1, 'avail': True},
        ]
        mock_get.return_value = mock_resp

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        cell = Cell.objects.get(warehouse=self.warehouse, x=3, y=2, z=1)
        self.assertTrue(cell.available)

    # ------------------------------------------------------------------
    # Case 6 — nested root key (SYNC-03)
    # ------------------------------------------------------------------
    @patch('Warehouse_app.views.os.getenv')
    @patch('Warehouse_app.views.http_requests.get')
    def test_nested_root_key(self, mock_get, mock_getenv):
        """ONEC_ROOT_KEY='value' unwraps nested dict before processing."""
        overrides = {
            'ONEC_API_URL': 'http://fake-1c/',
            'ONEC_API_USER': '',
            'ONEC_API_PASSWORD': '',
            'ONEC_FIELD_X': 'x',
            'ONEC_FIELD_Y': 'y',
            'ONEC_FIELD_Z': 'z',
            'ONEC_FIELD_AVAILABLE': 'available',
            'ONEC_ROOT_KEY': 'value',
        }
        mock_getenv.side_effect = self._make_getenv(overrides)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {'value': [{'x': 5, 'y': 1, 'z': 1, 'available': True}]}
        mock_get.return_value = mock_resp

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['synced'], 1)
        self.assertTrue(
            Cell.objects.filter(warehouse=self.warehouse, x=5, y=1, z=1).exists()
        )

#!/bin/sh
set -e

echo "[Converter] Applying migrations..."
n=0
until [ "$n" -ge 10 ]
do
    python manage.py migrate --noinput && break
    n=$((n+1))
    echo "[Converter] Migration failed (attempt $n/10), retrying in 2s..."
    sleep 2
done

if [ "${SEED_INITIAL_DATA:-false}" = "true" ]; then
    echo "[Converter] Ensuring default warehouse size configuration exists..."
    python manage.py shell -c "from Converter_app.models import Size; Size.objects.get_or_create(warehouse_id=1, defaults={'row_size': 3.0, 'shelf_size': 0.8, 'cell_size': 1.2, 'name': 'Main Warehouse', 'is_active': True}); print('Converter size ready')" || true
fi

echo "[Converter] Starting server..."
exec "$@"

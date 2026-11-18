#!/bin/sh
set -e

echo "[Warehouse] Applying migrations..."
n=0
until [ "$n" -ge 10 ]
do
    python manage.py migrate --noinput && break
    n=$((n+1))
    echo "[Warehouse] Migration failed (attempt $n/10), retrying in 2s..."
    sleep 2
done

if [ "${SEED_INITIAL_DATA:-false}" = "true" ]; then
    echo "[Warehouse] Ensuring default warehouse and cells exist..."
    python manage.py shell -c "from Warehouse_app.models import Warehouse, Cell; w, created = Warehouse.objects.get_or_create(id=1, defaults={'name': 'Main Warehouse'}); [Cell.objects.get_or_create(warehouse=w, x=x, y=y, z=z, defaults={'available': True}) for x in range(1, 4) for y in range(1, 4) for z in range(1, 3)] if (created or not w.cells.exists()) else None; print(f'Warehouse 1 ready with {w.cells.count()} cells')" || true
fi

echo "[Warehouse] Starting server..."
exec "$@"

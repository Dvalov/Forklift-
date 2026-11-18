#!/bin/sh
set -e

echo "[forklift_dashboard] Applying migrations..."
n=0
until [ "$n" -ge 10 ]
do
    python manage.py migrate --noinput && break
    n=$((n+1))
    echo "[forklift_dashboard] Migration failed (attempt $n/10), retrying in 2s..."
    sleep 2
done

if [ "${SEED_INITIAL_DATA:-false}" = "true" ]; then
    echo "[forklift_dashboard] Ensuring initial forklift exists..."
    python manage.py create_forklift --name "${FORKLIFT_NAME:-Forklift-01}"
fi

if [ "${ENABLE_SCHEDULER:-true}" = "true" ]; then
    export RUN_MAIN="true"
fi

echo "[forklift_dashboard] Starting server..."
exec "$@"

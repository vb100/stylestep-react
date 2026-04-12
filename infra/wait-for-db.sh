#!/bin/sh
set -e

if [ "${USE_SQLITE:-True}" = "True" ]; then
  exec "$@"
fi

until python manage.py shell -c "from django.db import connections; connections['default'].ensure_connection()"; do
  echo "Waiting for database..."
  sleep 2
done

exec "$@"

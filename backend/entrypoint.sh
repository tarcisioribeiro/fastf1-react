#!/bin/bash

# Entrypoint script for Django backend

set -e

echo "Waiting for MySQL to be ready..."
while ! nc -z mysql 3306; do
  sleep 1
done
echo "MySQL is ready!"

echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Creating superuser if it doesn't exist..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@f1data.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Django server..."
exec "$@"

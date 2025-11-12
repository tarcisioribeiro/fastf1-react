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

echo "Triggering initial data collection tasks..."
python manage.py shell <<EOF
from data_collector.tasks import start_all_data_collection, collect_all_race_data, collect_all_qualifying_data, collect_all_sprint_data
from data_collector.historical_tasks import incremental_historical_update
import logging

logger = logging.getLogger('data_collector')
logger.info("=" * 80)
logger.info("STARTING INITIAL DATA COLLECTION")
logger.info("This will collect all F1 data from 2018 to current year")
logger.info("Tasks will run in background via Celery")
logger.info("=" * 80)

# Trigger complete data collection
try:
    # Start metadata and current season data
    start_all_data_collection.delay()
    logger.info("✓ Triggered: Metadata and current season collection")

    # Start complete historical data collection
    collect_all_race_data.delay()
    logger.info("✓ Triggered: Complete race data collection (2018-present)")

    collect_all_qualifying_data.delay()
    logger.info("✓ Triggered: Complete qualifying data collection (2018-present)")

    collect_all_sprint_data.delay()
    logger.info("✓ Triggered: Complete sprint data collection (2021-present)")

    # Start historical data ingestion (pre-2018)
    incremental_historical_update.delay()
    logger.info("✓ Triggered: Historical data ingestion (1950-2017)")

    print("✓ All initial data collection tasks have been queued successfully!")
    print("  Monitor progress at: http://localhost:8000/api/tasks/status/")
except Exception as e:
    logger.error(f"Error triggering initial tasks: {e}")
    print(f"✗ Error triggering tasks: {e}")
EOF

echo "Starting Django server..."
exec "$@"

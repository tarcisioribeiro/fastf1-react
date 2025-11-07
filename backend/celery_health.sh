#!/bin/bash
# Health check script for Celery worker

# Check if Celery can be inspected
celery -A config inspect ping -t 5 > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Celery worker is healthy"
    exit 0
else
    echo "Celery worker is not responding"
    exit 1
fi

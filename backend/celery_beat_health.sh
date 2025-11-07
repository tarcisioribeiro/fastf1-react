#!/bin/bash
# Health check script for Celery beat

# Simple health check: verify Redis connectivity
# Celery beat doesn't expose a good health endpoint, so we check if dependencies are available
python3 -c "
import redis
import sys
try:
    r = redis.from_url('redis://redis:6379/0', socket_connect_timeout=2)
    r.ping()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "Celery beat is healthy (Redis accessible)"
    exit 0
else
    echo "Celery beat is unhealthy (Redis not accessible)"
    exit 1
fi

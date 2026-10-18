#!/bin/sh
set -eu
: "${PORT:=8080}"
export PORT
flask --app wsgi:app db upgrade
if [ -n "${ADMIN_USERNAME:-}" ] && [ -n "${ADMIN_PASSWORD:-}" ]; then
  flask --app wsgi:app create-admin --if-not-exists
fi
exec gunicorn --bind "0.0.0.0:${PORT}" --workers "${WEB_CONCURRENCY:-2}" --access-logfile - --error-logfile - --timeout 60 wsgi:app

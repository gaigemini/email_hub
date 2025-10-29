#!/bin/sh

# This script runs database migrations and then starts the main application.

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting 5 seconds for DB to be ready..."
sleep 5

echo "Applying Alembic database migrations..."
# This is the correct command to run Alembic migrations
alembic upgrade head

echo "Migrations applied."

# 'exec' replaces the shell process with the command that follows.
# This ensures that Gunicorn becomes the main process (PID 1) and
# receives signals (like SIGTERM) from Kubernetes correctly.
exec "$@"

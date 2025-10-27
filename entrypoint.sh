#!/bin/sh

# This script runs database migrations and then starts the main application.

# Exit immediately if a command exits with a non-zero status
set -e

echo "Applying database migrations..."
# Set FLASK_APP environment variable if not already set
export FLASK_APP=${FLASK_APP:-app.py}
flask db upgrade

echo "Migrations applied."

# 'exec' replaces the shell process with the command that follows.
# This ensures that Gunicorn becomes the main process (PID 1) and
# receives signals (like SIGTERM) from Kubernetes correctly.
exec "$@"

#!/bin/bash
set -e

# Pull the latest changes from the repository
git pull origin main

# Initialize or update the virtual environment using uv
uv venv

# Install project dependencies in editable mode
uv pip install -e .

# Run database migrations (assumes your manage.py is in the golfbackend directory)
cd golfbackend && uv run manage.py migrate

# Collect static files without user interaction
cd golfbackend && uv run manage.py collectstatic --noinput

# Restart the uWSGI service (ensure the service name matches your systemd unit, e.g. "golf_server")
sudo systemctl restart golf_server
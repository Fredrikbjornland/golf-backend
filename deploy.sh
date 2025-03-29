# Pull latest changes
git pull origin main

# Install dependencies using uv
uv venv
uv pip install -e .

# Run migrations
cd golfbackend && uv manage.py migrate

# Collect static files
cd golfbackend && uv manage.py collectstatic --noinput

# Restart uwsgi service
sudo systemctl restart golf_server
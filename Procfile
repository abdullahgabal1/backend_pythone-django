web: gunicorn daary_backend.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A daary_backend worker -l info
beat: celery -A daary_backend beat -l info

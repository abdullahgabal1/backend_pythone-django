"""
Daary AI Backend — Celery Application
=======================================
Configures Celery for the project using Redis as broker.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daary_backend.settings")

app = Celery("daary_backend")

# Load Celery config from Django settings, namespace CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.beat_schedule = {
	"refresh-price-medians-daily": {
		"task": "apps.search.tasks.refresh_price_medians",
		"schedule": crontab(minute=0, hour=0),
	},
}

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

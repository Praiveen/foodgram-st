"""Configuration for the API app."""
from django.apps import AppConfig


class ApiConfig(AppConfig):
    """API app config."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

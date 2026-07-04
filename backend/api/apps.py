from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        from django.db.backends.signals import connection_created

        from .db_schema import configure_search_path, qualify_model_tables

        qualify_model_tables()
        connection_created.connect(
            configure_search_path,
            dispatch_uid='api.configure_search_path',
        )

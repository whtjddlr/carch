from django.conf import settings
from django.apps import apps


def _is_postgres_database():
    return settings.DATABASES.get('default', {}).get('ENGINE') == 'django.db.backends.postgresql'


def _qualified_table_name(schema, table_name):
    if not schema or not table_name or table_name.startswith('"') or '.' in table_name:
        return table_name
    return f'"{schema}"."{table_name}"'


def qualify_model_tables():
    if not _is_postgres_database():
        return

    schema = getattr(settings, 'DATABASE_SCHEMA', '')
    if not schema:
        return

    for model in apps.get_models(include_auto_created=True):
        model._meta.db_table = _qualified_table_name(schema, model._meta.db_table)


def configure_search_path(sender, connection, **kwargs):
    if connection.vendor != 'postgresql':
        return

    schema_names = [
        schema
        for schema in getattr(settings, 'DATABASE_SEARCH_PATH', [])
        if schema
    ]
    if not schema_names:
        return

    quoted_names = ', '.join(connection.ops.quote_name(schema) for schema in schema_names)
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO {quoted_names}')

import json
import os
import sqlite3
from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


APP_TABLES = [
    'django_migrations',
    'django_content_type',
    'auth_permission',
    'auth_group',
    'auth_group_permissions',
    'auth_user',
    'auth_user_groups',
    'auth_user_user_permissions',
    'django_admin_log',
    'django_session',
    'api_aianalysisrecord',
    'api_transaction',
    'api_ownedcard',
    'api_authsession',
    'api_socialaccount',
    'api_purchaseplan',
    'api_communitypost',
    'api_communitycomment',
    'api_communitypostlike',
    'api_budget',
]

JSON_COLUMNS = {
    'api_aianalysisrecord': {'input_payload', 'result_payload'},
    'api_socialaccount': {'raw_profile'},
    'api_purchaseplan': {'items', 'scenarios'},
    'api_communitypost': {'tags'},
    'api_budget': {'category_budgets'},
}

BOOLEAN_COLUMNS = {
    'auth_user': {'is_superuser', 'is_staff', 'is_active'},
    'api_transaction': {'is_cancelled', 'is_interest_free_installment'},
    'api_communitypost': {'liked'},
}


def quote_identifier(name):
    return '"' + name.replace('"', '""') + '"'


class Command(BaseCommand):
    help = 'Sync the local Django SQLite demo database into Supabase via PostgREST.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            default=str(settings.BASE_DIR / 'db.sqlite3'),
            help='Path to the local Django SQLite database.',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Rows per Supabase REST upsert batch.',
        )

    def handle(self, *args, **options):
        source = Path(options['source'])
        if not source.exists() or source.stat().st_size == 0:
            raise CommandError(f'Django SQLite database is missing or empty: {source}')

        supabase_url = os.environ.get('SUPABASE_URL', '').rstrip('/')
        supabase_key = (
            os.environ.get('SUPABASE_SECRET_KEY')
            or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
            or ''
        )
        if not supabase_url or not supabase_key:
            raise CommandError('SUPABASE_URL and SUPABASE_SECRET_KEY are required.')

        self.session = requests.Session()
        self.session.headers.update({
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'resolution=merge-duplicates,return=minimal',
        })
        self.rest_base_url = f'{supabase_url}/rest/v1'

        with sqlite3.connect(source) as sqlite_conn:
            sqlite_conn.row_factory = sqlite3.Row
            for table in APP_TABLES:
                columns, primary_keys = self._table_columns(sqlite_conn, table)
                if not columns:
                    raise CommandError(f'Missing source table: {table}')
                total = self._upsert_table(sqlite_conn, table, columns, primary_keys, options['batch_size'])
                self.stdout.write(f'{table}: {total} rows')

        self.stdout.write(self.style.SUCCESS('Supabase app data sync complete.'))

    def _table_columns(self, sqlite_conn, table):
        rows = sqlite_conn.execute(f'pragma table_info({quote_identifier(table)})').fetchall()
        columns = [row['name'] for row in rows]
        primary_keys = [
            row['name']
            for row in sorted(rows, key=lambda item: item['pk'])
            if row['pk']
        ]
        return columns, primary_keys

    def _upsert_table(self, sqlite_conn, table, columns, primary_keys, batch_size):
        quoted_columns = ', '.join(quote_identifier(column) for column in columns)
        select_sql = f'SELECT {quoted_columns} FROM {quote_identifier(table)}'
        url = f'{self.rest_base_url}/{table}'
        params = {'on_conflict': ','.join(primary_keys)} if primary_keys else {}

        batch = []
        total = 0
        for row in sqlite_conn.execute(select_sql):
            batch.append(self._serialize_row(table, columns, row))
            if len(batch) >= batch_size:
                self._send_batch(url, params, batch, table)
                total += len(batch)
                batch = []
        if batch:
            self._send_batch(url, params, batch, table)
            total += len(batch)
        return total

    def _serialize_row(self, table, columns, row):
        payload = {}
        json_columns = JSON_COLUMNS.get(table, set())
        boolean_columns = BOOLEAN_COLUMNS.get(table, set())
        for column in columns:
            value = row[column]
            if column in json_columns:
                payload[column] = self._parse_json(value)
            elif column in boolean_columns and value is not None:
                payload[column] = bool(value)
            else:
                payload[column] = value
        return payload

    def _parse_json(self, value):
        if value in (None, ''):
            return None
        if isinstance(value, (dict, list)):
            return value
        return json.loads(value)

    def _send_batch(self, url, params, batch, table):
        response = self.session.post(url, params=params, json=batch, timeout=60)
        if response.status_code not in {200, 201, 204}:
            body = response.text[:1000]
            raise CommandError(f'Supabase upsert failed for {table}: {response.status_code} {body}')

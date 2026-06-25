import os
import sqlite3
from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


CATALOG_TABLES = [
    'issuers',
    'benefit_category_codes',
    'merchants',
    'cards',
    'card_benefits',
    'benefit_categories',
    'benefit_channel_flags',
    'benefit_condition_lines',
    'benefit_exclusion_keywords',
    'benefit_merchants',
    'benefit_source_rules',
    'merchant_rules',
    'merchant_rule_categories',
    'merchant_rule_exclusion_keywords',
    'merchant_rule_review_reasons',
    'discontinued_card_candidates',
    'issuer_policy_notes',
]


def quote_identifier(name):
    return '"' + name.replace('"', '""') + '"'


class Command(BaseCommand):
    help = 'Sync the card catalog SQLite bundle into Supabase via PostgREST.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            default=str(settings.CARD_MASTER_DB),
            help='Path to card_master_api.sqlite.',
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
            raise CommandError(f'Card catalog SQLite is missing or empty: {source}')

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
            for table in CATALOG_TABLES:
                columns, primary_keys = self._table_columns(sqlite_conn, table)
                if not columns:
                    raise CommandError(f'Missing source table: {table}')
                if not primary_keys:
                    raise CommandError(f'Source table has no primary key: {table}')
                total = self._upsert_table(sqlite_conn, table, columns, primary_keys, options['batch_size'])
                self.stdout.write(f'{table}: {total} rows')

        self.stdout.write(self.style.SUCCESS('Supabase card catalog sync complete.'))

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
        params = {'on_conflict': ','.join(primary_keys)}

        batch = []
        total = 0
        for row in sqlite_conn.execute(select_sql):
            batch.append({column: row[column] for column in columns})
            if len(batch) >= batch_size:
                self._send_batch(url, params, batch, table)
                total += len(batch)
                batch = []
        if batch:
            self._send_batch(url, params, batch, table)
            total += len(batch)
        return total

    def _send_batch(self, url, params, batch, table):
        response = self.session.post(url, params=params, json=batch, timeout=60)
        if response.status_code not in {200, 201, 204}:
            body = response.text[:1000]
            raise CommandError(f'Supabase upsert failed for {table}: {response.status_code} {body}')

import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


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


def normalize_sqlite_ddl(sql):
    sql = sql.strip().rstrip(';')
    sql = sql.replace('AUTOINCREMENT', '')
    sql = sql.replace('integer primary key', 'integer primary key')
    sql = sql.replace('INTEGER PRIMARY KEY', 'integer primary key')
    return sql


class Command(BaseCommand):
    help = 'Import the external card catalog SQLite bundle into the configured Django database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            default=str(settings.CARD_MASTER_DB),
            help='Path to card_master_api.sqlite.',
        )
        parser.add_argument(
            '--drop',
            action='store_true',
            help='Drop existing card catalog tables before importing.',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Rows per bulk insert batch.',
        )

    def handle(self, *args, **options):
        source = Path(options['source'])
        if not source.exists():
            raise CommandError(f'Card catalog SQLite not found: {source}')

        if connection.vendor == 'sqlite':
            raise CommandError(
                'Refusing to import the card catalog into the local app SQLite DB. '
                'Set DATABASE_URL to Supabase/Postgres first.'
            )

        self.stdout.write(f'Importing card catalog from {source}')
        with sqlite3.connect(source) as sqlite_conn:
            sqlite_conn.row_factory = sqlite3.Row
            with connection.cursor() as cursor:
                if options['drop']:
                    self._drop_tables(cursor)
                self._create_tables(cursor, sqlite_conn)
                self._copy_rows(cursor, sqlite_conn, options['batch_size'])
                self._create_indexes(cursor, sqlite_conn)

        self.stdout.write(self.style.SUCCESS('Card catalog import complete.'))

    def _drop_tables(self, cursor):
        for table in reversed(CATALOG_TABLES):
            cursor.execute(f'DROP TABLE IF EXISTS {quote_identifier(table)} CASCADE')

    def _create_tables(self, cursor, sqlite_conn):
        for table in CATALOG_TABLES:
            row = sqlite_conn.execute(
                "select sql from sqlite_master where type = 'table' and name = ?",
                (table,),
            ).fetchone()
            if not row:
                raise CommandError(f'Missing source table: {table}')
            cursor.execute(normalize_sqlite_ddl(row['sql']))
            self.stdout.write(f'- table {table}')

    def _copy_rows(self, cursor, sqlite_conn, batch_size):
        for table in CATALOG_TABLES:
            columns = [row['name'] for row in sqlite_conn.execute(f'pragma table_info({quote_identifier(table)})')]
            if not columns:
                continue
            quoted_columns = ', '.join(quote_identifier(column) for column in columns)
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f'INSERT INTO {quote_identifier(table)} ({quoted_columns}) VALUES ({placeholders})'
            select_sql = f'SELECT {quoted_columns} FROM {quote_identifier(table)}'

            batch = []
            total = 0
            for row in sqlite_conn.execute(select_sql):
                batch.append(tuple(row[column] for column in columns))
                if len(batch) >= batch_size:
                    cursor.executemany(insert_sql, batch)
                    total += len(batch)
                    batch = []
            if batch:
                cursor.executemany(insert_sql, batch)
                total += len(batch)
            self.stdout.write(f'  copied {total} rows from {table}')

    def _create_indexes(self, cursor, sqlite_conn):
        rows = sqlite_conn.execute(
            "select name, sql from sqlite_master where type = 'index' and sql is not null order by name"
        ).fetchall()
        for row in rows:
            cursor.execute(row['sql'])
        self.stdout.write(f'- indexes {len(rows)}')

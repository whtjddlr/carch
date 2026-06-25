import mimetypes
import os
from pathlib import Path
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}


class Command(BaseCommand):
    help = 'Upload card image assets to a public Supabase Storage bucket.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            action='append',
            default=[],
            help='Image directory to upload. Can be passed multiple times.',
        )
        parser.add_argument(
            '--bucket',
            default='card-images',
            help='Supabase Storage bucket name.',
        )

    def handle(self, *args, **options):
        supabase_url = os.environ.get('SUPABASE_URL', '').rstrip('/')
        supabase_key = (
            os.environ.get('SUPABASE_SECRET_KEY')
            or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
            or ''
        )
        if not supabase_url or not supabase_key:
            raise CommandError('SUPABASE_URL and SUPABASE_SECRET_KEY are required.')

        sources = options['source'] or [str(settings.CARD_IMAGE_DIR)]
        directories = [Path(source) for source in sources]
        missing = [str(directory) for directory in directories if not directory.exists()]
        if missing:
            missing_paths = ', '.join(missing)
            raise CommandError(f'Image directory not found: {missing_paths}')

        session = requests.Session()
        session.headers.update({
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'x-upsert': 'true',
        })

        bucket = options['bucket']
        total = 0
        for directory in directories:
            files = sorted(
                path for path in directory.iterdir()
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
            )
            for path in files:
                self._upload_file(session, supabase_url, bucket, path)
                total += 1
            self.stdout.write(f'{directory}: {len(files)} files')

        self.stdout.write(self.style.SUCCESS(f'Supabase image upload complete: {total} files.'))

    def _upload_file(self, session, supabase_url, bucket, path):
        object_name = quote(path.name)
        url = f'{supabase_url}/storage/v1/object/{bucket}/{object_name}'
        content_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        with path.open('rb') as handle:
            response = session.put(
                url,
                data=handle,
                headers={'Content-Type': content_type},
                timeout=60,
            )
        if response.status_code not in {200, 201}:
            body = response.text[:1000]
            raise CommandError(f'Image upload failed for {path.name}: {response.status_code} {body}')

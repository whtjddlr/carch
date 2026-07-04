from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Import card catalog data. Disabled in the App Store deployment branch.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Card catalog import is not configured in this build.'))

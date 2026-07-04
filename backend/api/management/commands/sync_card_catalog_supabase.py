from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Sync card catalog data to Supabase. Disabled in the App Store deployment branch.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Card catalog Supabase sync is not configured in this build.'))

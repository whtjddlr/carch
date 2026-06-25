import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from api.models import CommunityComment, CommunityPost, OwnedCard, PurchasePlan, Transaction
from api.views import (
    ensure_community_seeded,
    ensure_owned_cards_seeded,
    ensure_purchase_plans_seeded,
    ensure_transactions_seeded,
    get_demo_user,
    get_dev_admin_user,
)


class Command(BaseCommand):
    help = 'Prepare the reproducible CARCH demo scenario for local presentation.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--demo-password',
            default=os.environ.get('DEMO_USER_PASSWORD', 'skawngus'),
            help='Password to set for the Nam Ju Hyun demo account. Use an empty value to keep the current password.',
        )
        parser.add_argument(
            '--skip-dev-admin',
            action='store_true',
            help='Do not create or seed the DEV_ADMIN_EMAIL account.',
        )
        parser.add_argument(
            '--strict-card-bundle',
            action='store_true',
            help='Fail when the full card catalog database or image directory is missing.',
        )

    def handle(self, *args, **options):
        self._check_card_bundle(strict=options['strict_card_bundle'])

        demo_user = get_demo_user()
        demo_password = options.get('demo_password')
        if demo_password:
            demo_user.set_password(demo_password)
            demo_user.save(update_fields=['password'])

        self._seed_user(demo_user)
        self.stdout.write(self.style.SUCCESS(f'Demo user ready: {demo_user.email}'))
        if demo_password:
            self.stdout.write(f'Demo password: {demo_password}')

        if not options['skip_dev_admin']:
            admin_user = get_dev_admin_user()
            self._seed_user(admin_user)
            self.stdout.write(self.style.SUCCESS(f'Dev admin ready: {admin_user.email}'))

        ensure_community_seeded()
        self._print_counts(demo_user)

    def _seed_user(self, user):
        ensure_owned_cards_seeded(user)
        ensure_transactions_seeded(user)
        ensure_purchase_plans_seeded(user)

    def _check_card_bundle(self, strict=False):
        missing = []
        if not settings.CARD_MASTER_DB.exists():
            missing.append(f'CARD_MASTER_DB not found: {settings.CARD_MASTER_DB}')
        if not settings.CARD_IMAGE_DIR.exists():
            missing.append(f'CARD_IMAGE_DIR not found: {settings.CARD_IMAGE_DIR}')

        if not missing:
            self.stdout.write(self.style.SUCCESS('Card catalog bundle detected.'))
            return

        message = '\n'.join(missing)
        if strict:
            raise CommandError(message)
        self.stdout.write(self.style.WARNING(message))
        self.stdout.write(
            self.style.WARNING(
                'Seed data will still be created, but full card search/images need the card bundle.'
            )
        )

    def _print_counts(self, demo_user):
        self.stdout.write('Seed summary')
        self.stdout.write(f'- owned cards: {OwnedCard.objects.filter(user=demo_user).count()}')
        self.stdout.write(f'- transactions: {Transaction.objects.filter(user=demo_user).count()}')
        self.stdout.write(f'- purchase plans: {PurchasePlan.objects.filter(user=demo_user).count()}')
        self.stdout.write(f'- community posts: {CommunityPost.objects.count()}')
        self.stdout.write(f'- community comments: {CommunityComment.objects.count()}')

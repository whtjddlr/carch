from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def attach_existing_community_rows_to_demo_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    CommunityPost = apps.get_model('api', 'CommunityPost')
    CommunityComment = apps.get_model('api', 'CommunityComment')

    user = User.objects.filter(email__iexact='demo@carch.local').first()
    if not user:
        username = 'demo'
        if User.objects.filter(username=username).exclude(email='demo@carch.local').exists():
            suffix = 2
            while User.objects.filter(username=f'demo{suffix}').exists():
                suffix += 1
            username = f'demo{suffix}'
        user = User.objects.create(username=username, email='demo@carch.local', first_name='남주현')
        user.set_unusable_password()
        user.save(update_fields=['password'])

    CommunityPost.objects.filter(user__isnull=True).update(user=user)
    CommunityComment.objects.filter(user__isnull=True).update(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_aianalysisrecord_user_ownedcard_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='communitypost',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='community_posts',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='communitycomment',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='community_comments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddIndex(
            model_name='communitypost',
            index=models.Index(fields=['user', '-created_at'], name='api_communi_user_id_529041_idx'),
        ),
        migrations.AddIndex(
            model_name='communitycomment',
            index=models.Index(fields=['user', 'created_at'], name='api_communi_user_id_e50661_idx'),
        ),
        migrations.RunPython(attach_existing_community_rows_to_demo_user, migrations.RunPython.noop),
    ]

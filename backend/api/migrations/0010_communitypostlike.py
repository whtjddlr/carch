from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def attach_existing_likes_to_demo_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    CommunityPost = apps.get_model('api', 'CommunityPost')
    CommunityPostLike = apps.get_model('api', 'CommunityPostLike')

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

    for post in CommunityPost.objects.filter(liked=True):
        CommunityPostLike.objects.get_or_create(post=post, user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_community_ownership'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunityPostLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'post',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='like_set',
                        to='api.communitypost',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='community_likes',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name='communitypostlike',
            constraint=models.UniqueConstraint(fields=('post', 'user'), name='unique_community_post_like'),
        ),
        migrations.AddIndex(
            model_name='communitypostlike',
            index=models.Index(fields=['user', '-created_at'], name='api_communi_user_id_db2f54_idx'),
        ),
        migrations.AddIndex(
            model_name='communitypostlike',
            index=models.Index(fields=['post', '-created_at'], name='api_communi_post_id_f81cfa_idx'),
        ),
        migrations.RunPython(attach_existing_likes_to_demo_user, migrations.RunPython.noop),
    ]

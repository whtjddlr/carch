from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_merge_demo_author_ownedcard'),
    ]

    operations = [
        migrations.AddField(
            model_name='aianalysisrecord',
            name='cache_key',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddIndex(
            model_name='aianalysisrecord',
            index=models.Index(
                fields=['analysis_type', 'cache_key', '-created_at'],
                name='api_ai_cache_idx',
            ),
        ),
    ]

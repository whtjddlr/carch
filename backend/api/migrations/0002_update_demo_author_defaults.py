from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communitycomment',
            name='author',
            field=models.CharField(default='남주현', max_length=30),
        ),
        migrations.AlterField(
            model_name='communitycomment',
            name='avatar',
            field=models.CharField(default='남', max_length=2),
        ),
        migrations.AlterField(
            model_name='communitypost',
            name='author',
            field=models.CharField(default='남주현', max_length=30),
        ),
        migrations.AlterField(
            model_name='communitypost',
            name='avatar',
            field=models.CharField(default='남', max_length=2),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_communitypostlike'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='payment_type',
            field=models.CharField(default='lump_sum', max_length=20),
        ),
        migrations.AddField(
            model_name='transaction',
            name='installment_months',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='transaction',
            name='is_interest_free_installment',
            field=models.BooleanField(default=False),
        ),
    ]

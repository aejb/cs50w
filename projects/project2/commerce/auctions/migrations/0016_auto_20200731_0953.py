# Generated by Django 3.0.8 on 2020-07-31 09:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0015_auto_20200731_0948'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='watch',
            name='item',
        ),
        migrations.AddField(
            model_name='watch',
            name='item',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='watchers', to='auctions.Listing'),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='watch',
            name='user',
        ),
        migrations.AddField(
            model_name='watch',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='watchlist', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0006_wiehrglobemodel_bpm'),
    ]

    operations = [
        migrations.AddField(
            model_name='cvexperience',
            name='overview',
            field=models.CharField(blank=True, help_text="One-line company overview, e.g. 'Global tech consultancy with 3,000+ engineers'", max_length=300, default=''),
            preserve_default=False,
        ),
    ]

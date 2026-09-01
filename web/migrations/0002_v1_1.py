from django.db import migrations, models


SEPARATOR = '•'


def split_titles(apps, schema_editor):
    """Move the part after the separator out of `title` and into `project_type`.

    Every Lab row was authored as "NAME <sep> QUALIFIER" because there was
    nowhere else to put the qualifier. Now that `project_type` exists, /lab
    rebuilds that string via `title_with_type` while /archive can show the name
    on its own.

    Only rows that actually contain the separator and have no type set are
    touched, so re-running this is a no-op.
    """
    Lab = apps.get_model('web', 'WiehrLabModel')
    for item in Lab.objects.all():
        if item.project_type or SEPARATOR not in item.title:
            continue
        name, _, qualifier = item.title.partition(SEPARATOR)
        name, qualifier = name.strip(), qualifier.strip()
        if not name or not qualifier:
            continue
        item.title = name
        item.project_type = qualifier
        item.save(update_fields=['title', 'project_type'])


def rejoin_titles(apps, schema_editor):
    """Put the qualifier back into `title` so the migration is reversible."""
    Lab = apps.get_model('web', 'WiehrLabModel')
    for item in Lab.objects.exclude(project_type=''):
        item.title = f'{item.title} {SEPARATOR} {item.project_type}'
        item.project_type = ''
        item.save(update_fields=['title', 'project_type'])


class Migration(migrations.Migration):
    """Everything between the V1.0 and V1.1 releases, as one migration.

    Squashed from the six migrations listed in `replaces`. Those added the
    `<field>_ru` translation columns and then dropped them again when the site
    went English-only, so 24 of their 31 operations cancelled out; Django's
    optimiser could not see that because the data migration below sits between
    the add and the remove. They are left out by hand here, which means an
    install coming from V1.0 never creates the twelve columns just to drop
    them.

    What remains is the real shape of the release: a Lab project type, storage
    pricing, the Lab description becoming a plain TextField when CKEditor was
    removed, and the Lab media poster frame.
    """

    replaces = [
        ('web', '0002_licensetype_description_ru_licensetype_name_ru_and_more'),
        ('web', '0003_split_lab_title_type'),
        ('web', '0004_wiehrstoragemodel_currency_wiehrstoragemodel_price_and_more'),
        ('web', '0005_alter_wiehrlabmodel_description'),
        ('web', '0006_wiehrlabmodel_media_poster'),
        ('web', '0007_remove_licensetype_description_ru_and_more'),
    ]

    dependencies = [
        ('web', '0001_v1_0'),
    ]

    operations = [
        migrations.AddField(
            model_name='wiehrlabmodel',
            name='project_type',
            field=models.CharField(blank=True, db_index=True, default='', help_text='What the project is — e.g. "Chrome Extension", "Telegram Bot". Shown after the title on /lab as "Wanda • Chrome Extension"; /archive lists the title on its own.', max_length=140, verbose_name='Type'),
        ),
        migrations.RunPython(split_titles, rejoin_titles),
        migrations.AddField(
            model_name='wiehrstoragemodel',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Leave empty for a free download. 29 shows as $29, 29.50 as $29.50. Setting a price does not lock the file on its own — pair it with Access Type "license_key" and a Purchase URL to actually sell it.', max_digits=8, null=True, verbose_name='Price'),
        ),
        migrations.AddField(
            model_name='wiehrstoragemodel',
            name='currency',
            field=models.CharField(choices=[('USD', 'USD'), ('EUR', 'EUR')], default='USD', help_text='Only read when a Price is set', max_length=3, verbose_name='Currency'),
        ),
        migrations.AddField(
            model_name='wiehrstoragemodel',
            name='purchase_url',
            field=models.URLField(blank=True, default='', help_text='Where a visitor buys this — Ko-fi, Gumroad, Boosty, anything. Shown as the BUY button next to a locked download.', max_length=500, verbose_name='Purchase URL'),
        ),
        migrations.AlterField(
            model_name='wiehrlabmodel',
            name='description',
            field=models.TextField(help_text='HTML. Wrap paragraphs in <p>...</p>.', verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='wiehrlabmodel',
            name='media_poster',
            field=models.ImageField(blank=True, editable=False, help_text='Auto-generated first frame, used for the page backdrop when Media is a GIF.', null=True, upload_to='lab_media/posters/', verbose_name='Media Poster'),
        ),
    ]

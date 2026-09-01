import ckeditor.fields
import django.core.validators
from django.db import migrations, models


def clear_dropped_preview_types(apps, schema_editor):
    Storage = apps.get_model('web', 'WiehrStorageModel')
    Storage.objects.filter(preview_type__in=['audio', 'image']).update(preview_type='')
import django.db.migrations.operations.special
import django.db.models.deletion
import django.utils.timezone



class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CVEducation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('date', models.CharField(help_text='e.g. 09/2023 — Present', max_length=50)),
                ('url', models.URLField(blank=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'CV Education',
                'verbose_name_plural': 'CV Education',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='CVExperience',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=200)),
                ('company', models.CharField(max_length=200)),
                ('company_url', models.URLField(blank=True)),
                ('date', models.CharField(help_text='e.g. 03/2022 — Present', max_length=50)),
                ('location', models.CharField(blank=True, max_length=100)),
                ('bullets', models.TextField(help_text='One bullet point per line')),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'CV Experience',
                'verbose_name_plural': 'CV Experiences',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='CVLanguage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(max_length=50)),
                ('level', models.CharField(help_text='e.g. C2 Proficient · EF SET Certified', max_length=100)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'CV Language',
                'verbose_name_plural': 'CV Languages',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='CVProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(choices=[('engineer', 'ENGINEER'), ('composer', 'COMPOSER')], max_length=20, unique=True)),
                ('name', models.CharField(help_text='Full name', max_length=100)),
                ('title', models.CharField(help_text='Job title / headline', max_length=200)),
                ('bio', models.TextField(blank=True, help_text='Short professional summary')),
                ('email', models.EmailField(help_text='Contact email for CV', max_length=254)),
                ('location', models.CharField(blank=True, max_length=100)),
                ('linkedin', models.CharField(blank=True, help_text='Display text, e.g. linkedin.com/in/wiehrcc', max_length=100)),
                ('linkedin_url', models.URLField(blank=True)),
                ('website', models.URLField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Wiehr CV Profile',
                'verbose_name_plural': 'Wiehr CV Profiles',
                'ordering': ['version'],
            },
        ),
        migrations.CreateModel(
            name='CVProject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section', models.CharField(choices=[('commercial', 'Commercial'), ('personal', 'Personal')], default='personal', max_length=20)),
                ('name', models.CharField(max_length=200)),
                ('project_type', models.CharField(help_text='e.g. Portfolio, Record Label', max_length=100)),
                ('date', models.CharField(help_text='e.g. 01/2026 — Present', max_length=50)),
                ('description', models.TextField()),
                ('bullets', models.TextField(blank=True, help_text='One bullet point per line (optional, mainly for commercial projects)')),
                ('link_text', models.CharField(blank=True, help_text='Display text for link', max_length=200)),
                ('link_url', models.URLField(blank=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'CV Project',
                'verbose_name_plural': 'CV Projects',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='CVSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(help_text='e.g. Backend, Frontend, DevOps', max_length=100)),
                ('items', models.TextField(help_text='Comma-separated skills, e.g. Python, Django, Flask')),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'CV Skill',
                'verbose_name_plural': 'CV Skills',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_id', models.CharField(blank=True, help_text='Auto-generated on save (C001, C002, ...) if left blank', max_length=10, unique=True, verbose_name='Internal ID')),
                ('license_key', models.CharField(blank=True, db_index=True, help_text='Auto-generated on save if left blank', max_length=64, unique=True, verbose_name='License ID')),
                ('product_text', models.CharField(blank=True, help_text='Used instead of the field above when the licensed product has no Storage item — e.g. "Wiehr Font Family"', max_length=200, verbose_name='Product (custom text)')),
                ('licensee_name', models.CharField(max_length=200, verbose_name='Licensee Name')),
                ('licensee_email', models.EmailField(max_length=254, verbose_name='Licensee Email')),
                ('effective_date', models.DateField(default=django.utils.timezone.now, verbose_name='Effective Date')),
                ('is_active', models.BooleanField(default=True, help_text='Uncheck to revoke — the license will no longer verify or unlock downloads', verbose_name='Active')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modified At')),
            ],
            options={
                'verbose_name': 'Wiehr License',
                'verbose_name_plural': 'Wiehr Licenses',
                'db_table': 'web_license',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='LicenseType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='e.g. Exclusive Personal License, Non-Exclusive Commercial License', max_length=100, unique=True, verbose_name='Name')),
                ('description', models.TextField(blank=True, help_text='Optional internal note about what this license type covers', verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Wiehr License Type',
                'verbose_name_plural': 'Wiehr License Types',
                'db_table': 'web_license_type',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='QrCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.CharField(max_length=100, verbose_name='Object ID')),
                ('tag', models.CharField(blank=True, max_length=100, verbose_name='Tag')),
                ('link', models.URLField(verbose_name='Link')),
                ('wid', models.CharField(blank=True, help_text='Release WID (e.g., W000, W001) to auto-set colors from Release', max_length=10, null=True, verbose_name='WID')),
                ('error_correction', models.CharField(choices=[('L', 'L'), ('M', 'M'), ('Q', 'Q'), ('H', 'H')], default='H', max_length=1, verbose_name='Error Correction')),
                ('version', models.PositiveIntegerField(default=10, verbose_name='Version')),
                ('border', models.PositiveIntegerField(default=8, verbose_name='Border')),
                ('fg_color', models.CharField(default='#151617', max_length=7, verbose_name='Foreground Color')),
                ('bg_color', models.CharField(default='#f4f4f4', max_length=7, verbose_name='Background Color')),
                ('logo_size', models.FloatField(default=0.2, verbose_name='Logo Size')),
                ('svg_size', models.PositiveIntegerField(default=320, verbose_name='SVG Size')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, null=True, verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'Wiehr QR Code',
                'verbose_name_plural': 'Wiehr QR Codes',
                'db_table': 'web_qr_code',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Shortener',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('long_url', models.URLField(max_length=2000, verbose_name='Long URL')),
                ('short_url', models.CharField(blank=True, max_length=15, unique=True, verbose_name='Short URL')),
                ('full_url', models.CharField(blank=True, max_length=2000, verbose_name='Full URL')),
                ('times_followed', models.PositiveIntegerField(default=0, verbose_name='Times Followed')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, null=True, verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'Wiehr Shortener',
                'verbose_name_plural': 'Wiehr Shortener',
                'db_table': 'web_shortener',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ShortenerSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(default='W1', help_text='Required on /s to create a short link. Change it here.', max_length=100, verbose_name='Password')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modified At')),
            ],
            options={
                'verbose_name': 'Wiehr Shortener Settings',
                'verbose_name_plural': 'Wiehr Shortener Settings',
                'db_table': 'web_shortener_settings',
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(help_text='Subscriber email address', max_length=254, unique=True, verbose_name='Email')),
                ('city', models.CharField(blank=True, help_text='Subscriber city (optional)', max_length=100, null=True, verbose_name='City')),
                ('country', models.CharField(blank=True, help_text='Subscriber country (optional)', max_length=100, null=True, verbose_name='Country')),
                ('country_code', models.CharField(blank=True, help_text='ISO 3166-1 alpha-2 country code', max_length=2, null=True, verbose_name='Country Code')),
                ('disconnect_token', models.CharField(blank=True, help_text='Token for disconnect link', max_length=64, null=True, unique=True, verbose_name='Disconnect Token')),
                ('is_blacklist', models.BooleanField(default=False, help_text='Exclude from email campaigns for other reasons', verbose_name='Blacklisted')),
                ('is_disconnected', models.BooleanField(default=False, help_text='User has disconnected from emails', verbose_name='Disconnected')),
                ('disconnected_at', models.DateTimeField(blank=True, help_text='Date and time when the user disconnected', null=True, verbose_name='Disconnected At')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Subscribed At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Wiehr Network',
                'verbose_name_plural': 'Wiehr Network',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='WiehrArchiveModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_id', models.CharField(help_text='Unique archive identifier (e.g., 2025, 2026)', max_length=10, unique=True, verbose_name='Internal ID')),
                ('year', models.IntegerField(db_index=True, help_text='Archive year', unique=True, verbose_name='Year')),
                ('is_visible', models.BooleanField(db_index=True, default=True, help_text='Show in public view', verbose_name='Visible')),
                ('globe_count', models.IntegerField(default=0, help_text='Cached count of globe items', verbose_name='Globe Count')),
                ('atlas_count', models.IntegerField(default=0, help_text='Cached count of atlas items', verbose_name='Atlas Count')),
                ('lab_count', models.IntegerField(default=0, help_text='Cached count of lab items', verbose_name='Lab Count')),
                ('storage_count', models.IntegerField(default=0, help_text='Cached count of storage items', verbose_name='Storage Count')),
                ('total_count', models.IntegerField(default=0, help_text='Cached total count of all items', verbose_name='Total Count')),
                ('globe_ids', models.JSONField(blank=True, default=list, help_text='Cached list of globe internal_ids', verbose_name='Globe IDs')),
                ('atlas_ids', models.JSONField(blank=True, default=list, help_text='Cached list of atlas internal_ids', verbose_name='Atlas IDs')),
                ('lab_ids', models.JSONField(blank=True, default=list, help_text='Cached list of lab internal_ids', verbose_name='Lab IDs')),
                ('storage_ids', models.JSONField(blank=True, default=list, help_text='Cached list of storage internal_ids', verbose_name='Storage IDs')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created At')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modified At')),
            ],
            options={
                'verbose_name': 'Wiehr Archive',
                'verbose_name_plural': 'Wiehr Archives',
                'db_table': 'web_wiehr_archive',
                'ordering': ['-year'],
            },
        ),
        migrations.CreateModel(
            name='WiehrAtlasModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_id', models.CharField(help_text='Interal ID for history', max_length=10, verbose_name='Internal ID')),
                ('country_code', models.CharField(help_text='ISO 3166-1 alpha-2 country code (e.g., ge, by, ru)', max_length=2, verbose_name='Country Code')),
                ('country_title', models.CharField(help_text='Full country name (e.g., Georgia, Belarus, Russia)', max_length=100, verbose_name='Country Title')),
                ('coordinates', models.CharField(help_text='Geographic coordinates (e.g., 41° 41\' 49.5672" N 44° 46\' 25.2264" E)', max_length=200, verbose_name='Coordinates')),
                ('is_visible', models.BooleanField(db_index=True, default=True, help_text='Show this location on the atlas', verbose_name='Visible')),
                ('release_type', models.CharField(choices=[('P', 'Photos'), ('S', 'Shares')], db_index=True, default='P', help_text='P = Photos (9 images), S = Shares (1 image + location)', max_length=1, verbose_name='Type')),
                ('year', models.IntegerField(blank=True, db_index=True, help_text='Year for archive grouping', null=True, verbose_name='Year')),
                ('order', models.IntegerField(db_index=True, default=0, help_text='Display order', verbose_name='Display Order')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created At')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modified At')),
            ],
            options={
                'verbose_name': 'Wiehr Atlas',
                'verbose_name_plural': 'Wiehr Atlas',
                'db_table': 'web_wiehr_atlas',
                'ordering': ('-internal_id',),
            },
        ),
        migrations.CreateModel(
            name='WiehrAtlasObjectImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(help_text='Upload image for this location', upload_to='atlas_images/', verbose_name='Image')),
                ('order', models.IntegerField(default=0, help_text='Order in which images are displayed (1, 2, 3...)', verbose_name='Display Order')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'Wiehr Atlas Image',
                'verbose_name_plural': 'Wiehr Atlas Images',
                'db_table': 'web_wiehr_atlas_object_image',
                'ordering': ('order', 'created_at'),
            },
        ),
        migrations.CreateModel(
            name='WiehrGlobeModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True, help_text='Release date', verbose_name='Date')),
                ('title', models.CharField(db_index=True, help_text='Release title', max_length=140, verbose_name='Title')),
                ('pitch', models.TextField(blank=True, help_text='Extended description or quote', null=True, verbose_name='Pitch')),
                ('is_visible', models.BooleanField(db_index=True, default=True, help_text='Show in public view')),
                ('release_type', models.CharField(choices=[('W', 'Wiehr'), ('E', 'External')], db_index=True, default='W', help_text='W = Wiehr Core, E = External release', max_length=1, verbose_name='Release Type')),
                ('year', models.IntegerField(blank=True, db_index=True, help_text='Release year for archive grouping', null=True, verbose_name='Year')),
                ('is_out', models.BooleanField(db_index=True, default=False, help_text='Marks release as publicly available and triggers team notifications', verbose_name='Is Out')),
                ('order', models.IntegerField(db_index=True, default=0, help_text='Display order', verbose_name='Order')),
                ('image', models.ImageField(blank=True, help_text='Cover artwork', null=True, upload_to='data/images/')),
                ('pdf_file', models.FileField(blank=True, help_text='PDF file for print QR', null=True, upload_to='data/release_pdfs/')),
                ('slug', models.SlugField(help_text='URL-friendly identifier (auto-generated from title)', max_length=222, unique=True, verbose_name='Slug')),
                ('tags', models.CharField(blank=True, help_text='Comma-separated tags (e.g., electronic, ambient, experimental)', max_length=500, null=True, verbose_name='Tags')),
                ('background_color', models.CharField(blank=True, help_text='Hex color code for page theme (e.g., #1DB954)', max_length=7, null=True, validators=[django.core.validators.RegexValidator(message='Enter a valid hex color code (e.g., #1DB954 or #FFF)', regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')], verbose_name='Background Color')),
                ('internal_id', models.CharField(blank=True, help_text='Unique release identifier (e.g., W001, E001)', max_length=10, null=True, unique=True, verbose_name='Internal ID')),
                ('geo', models.CharField(blank=True, help_text='Coordinates in format: 054° 03\' 28.7" N 008° 22\' 44.3" W', max_length=100, null=True, verbose_name='Geographic Coordinates')),
                ('listen_url', models.URLField(blank=True, help_text='Aggregator link (e.g. zvonko.link/ARCTICA1)', max_length=500, null=True, verbose_name='Listen URL')),
                ('lyrics_url', models.URLField(blank=True, help_text='Lyrics link (e.g. genius.com/...)', max_length=500, null=True, verbose_name='Lyrics URL')),
                ('watch_url', models.URLField(blank=True, help_text='Video link (e.g. youtube.com/watch?v=...)', max_length=500, null=True, verbose_name='Watch URL')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'Wiehr Globe',
                'verbose_name_plural': 'Wiehr Globe',
                'db_table': 'web_wiehr_globe',
                'ordering': ('-order', '-date'),
            },
        ),
        migrations.CreateModel(
            name='WiehrGlobeObjectArtist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text='Full artist name', max_length=140, verbose_name='Artist Name')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'Wiehr Globe Object Artist',
                'verbose_name_plural': 'Wiehr Globe Object Artist',
                'db_table': 'web_wiehr_globe_object_artist',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='WiehrLabModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_id', models.CharField(blank=True, help_text='Unique identifier (e.g., L001, L002)', max_length=10, null=True, unique=True, verbose_name='Internal ID')),
                ('title', models.CharField(db_index=True, max_length=140, verbose_name='Title')),
                ('description', ckeditor.fields.RichTextField(verbose_name='Description')),
                ('media', models.FileField(blank=True, help_text='Single cover media — GIF, PNG, JPG or WEBP. Uploaded as-is, no conversion.', null=True, upload_to='lab_media/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['gif', 'png', 'jpg', 'jpeg', 'webp'])], verbose_name='Media')),
                ('youtube_url', models.URLField(blank=True, default='', help_text='Clicking the cover opens this as an embedded video. Leave empty to keep the cover non-interactive.', max_length=500, verbose_name='YouTube URL')),
                ('role', models.CharField(db_index=True, max_length=140, verbose_name='Role')),
                ('slug', models.SlugField(help_text='URL-friendly identifier (auto-generated from title)', max_length=140, unique=True, verbose_name='Slug')),
                ('start_year', models.IntegerField(db_index=True, verbose_name='Start Year')),
                ('end_year', models.IntegerField(db_index=True, verbose_name='End Year')),
                ('order', models.IntegerField(default=0, verbose_name='Display Order')),
                ('is_visible', models.BooleanField(db_index=True, default=True, help_text='Show in public view', verbose_name='Visible')),
                ('release_type', models.CharField(choices=[('L', 'Lab')], db_index=True, default='L', help_text='L = Lab project', max_length=1, verbose_name='Type')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created At')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modified At')),
                ('extra_archives', models.ManyToManyField(blank=True, help_text='Ongoing work only appears under its start year automatically. Add years here to also surface it in those archives.', related_name='extra_lab_items', to='web.wiehrarchivemodel', verbose_name='Also show in these years')),
            ],
            options={
                'verbose_name': 'Wiehr Lab',
                'verbose_name_plural': 'Wiehr Lab',
                'db_table': 'web_wiehr_lab',
                'ordering': ('order', '-start_year'),
            },
        ),
        migrations.CreateModel(
            name='WiehrStorageModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_id', models.CharField(help_text='Unique storage identifier (e.g., S000, S001, S002)', max_length=10, unique=True, verbose_name='Internal ID')),
                ('slug', models.SlugField(help_text='URL-friendly identifier', max_length=140, unique=True, verbose_name='Slug')),
                ('title', models.CharField(help_text='Storage item title', max_length=200, verbose_name='Title')),
                ('description', models.TextField(help_text='Storage item description', verbose_name='Description')),
                ('file', models.FileField(help_text='Downloadable file', upload_to='storage/', verbose_name='File')),
                ('file_size', models.BigIntegerField(blank=True, help_text='File size in bytes (auto-calculated)', null=True, verbose_name='File Size')),
                ('cover_image', models.ImageField(help_text='Cover image for storage item', upload_to='storage/covers/', verbose_name='Cover Image')),
                ('file_type', models.CharField(help_text='Type of file (e.g., Telegram Theme, Font Family)', max_length=50, verbose_name='File Type')),
                ('download_count', models.IntegerField(default=0, help_text='Number of downloads', verbose_name='Download Count')),
                ('year', models.IntegerField(db_index=True, help_text='Year for archive grouping', verbose_name='Year')),
                ('order', models.IntegerField(db_index=True, default=0, help_text='Display order', verbose_name='Display Order')),
                ('is_visible', models.BooleanField(db_index=True, default=True, help_text='Show in public view', verbose_name='Visible')),
                ('access_type', models.CharField(choices=[('public', 'Public'), ('link', 'Link Only'), ('password', 'Link + Password'), ('license_key', 'License Key Required')], default='public', help_text='public = visible to all, link = anyone with URL, password = requires password, license_key = requires a valid License', max_length=15, verbose_name='Access Type')),
                ('access_password', models.CharField(blank=True, help_text='Password for protected items', max_length=100, verbose_name='Access Password')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created At')),
                ('preview_type', models.CharField(blank=True, choices=[('', 'None'), ('audio', 'Audio (uploaded file)'), ('image', 'Image (uploaded file)'), ('video', 'Embedded Video (YouTube)')], default='', help_text='Type of preview content', max_length=10, verbose_name='Preview Type')),
                ('preview_audio', models.FileField(blank=True, help_text="Used when Preview Type is 'audio' — your own uploaded audio file", null=True, upload_to='storage/previews/', verbose_name='Preview Audio')),
                ('preview_image', models.ImageField(blank=True, help_text="Used when Preview Type is 'image' — your own uploaded image file", null=True, upload_to='storage/previews/', verbose_name='Preview Image')),
                ('preview_url', models.URLField(blank=True, default='', help_text="Used when Preview Type is 'video' — a YouTube URL, same embed mechanism as Lab", max_length=500, verbose_name='Preview Video URL')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modified At')),
            ],
            options={
                'verbose_name': 'Wiehr Storage',
                'verbose_name_plural': 'Wiehr Storage',
                'db_table': 'web_wiehr_storage',
                'ordering': ['-order', '-created_at'],
                'indexes': [models.Index(fields=['-order', '-created_at'], name='web_wiehr_s_order_781de3_idx'), models.Index(fields=['is_visible'], name='web_wiehr_s_is_visi_ea85f5_idx'), models.Index(fields=['year'], name='web_wiehr_s_year_875ff4_idx'), models.Index(fields=['access_type'], name='web_wiehr_s_access__6658da_idx')],
            },
        ),
        migrations.CreateModel(
            name='WiehrStorageLinkModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Link label (e.g., THEME, DESIGN, EMOJI)', max_length=100, verbose_name='Label')),
                ('url', models.URLField(help_text='External link URL', max_length=500, verbose_name='URL')),
                ('order', models.IntegerField(default=0, help_text='Order of link display', verbose_name='Display Order')),
                ('storage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='web.wiehrstoragemodel', verbose_name='Storage Item')),
            ],
            options={
                'verbose_name': 'Storage Link',
                'verbose_name_plural': 'Storage Links',
                'db_table': 'web_wiehr_storage_link',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='WiehrLabObjectLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('website', models.CharField(max_length=140, verbose_name='Website')),
                ('description', models.CharField(max_length=140, verbose_name='Description')),
                ('url', models.URLField(max_length=500, verbose_name='URL')),
                ('order', models.IntegerField(default=0, help_text='Display order', verbose_name='Order')),
                ('lab', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='web.wiehrlabmodel')),
            ],
            options={
                'verbose_name': 'Wiehr Lab Link',
                'verbose_name_plural': 'Wiehr Lab Links',
                'db_table': 'web_wiehr_lab_object_link',
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='WiehrGlobeObjectToWiehrArtistObject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('primary', 'Primary Artist'), ('featured', 'Featured Artist')], db_index=True, default='primary', help_text='Primary = main artist, Featured = feat. artist', max_length=10, verbose_name='Role')),
                ('order', models.IntegerField(default=0, help_text='Display order', verbose_name='Order')),
                ('artist_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='release_roles', to='web.wiehrglobeobjectartist')),
                ('globe_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='artist_roles', to='web.wiehrglobemodel')),
            ],
            options={
                'verbose_name': 'Wiehr Globe Object To Wiehr Artist Object',
                'verbose_name_plural': 'Wiehr Globe Object To Wiehr Artist Object',
                'db_table': 'web_wiehr_globe_object_to_wiehr_artist_object',
                'ordering': ('order', 'artist_object__name'),
            },
        ),
        migrations.CreateModel(
            name='WiehrGlobeObjectCredits',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credit_type', models.CharField(choices=[('vocal', 'Vocal'), ('production', 'Production'), ('lyrics', 'Lyrics'), ('mixing', 'Mixing'), ('mastering', 'Mastering'), ('artwork', 'Artwork'), ('video', 'Video'), ('label', 'Label')], db_index=True, help_text='Type of contribution', max_length=20, verbose_name='Credit Type')),
                ('notes', models.CharField(blank=True, help_text='Additional notes about this credit', max_length=200, null=True, verbose_name='Notes')),
                ('order', models.IntegerField(default=0, help_text='Display order within credit type', verbose_name='Order')),
                ('artist_object', models.ForeignKey(help_text='Artist who contributed to this credit', on_delete=django.db.models.deletion.CASCADE, related_name='credits', to='web.wiehrglobeobjectartist')),
                ('globe_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credits', to='web.wiehrglobemodel')),
            ],
            options={
                'verbose_name': 'Wiehr Globe Object Credits',
                'verbose_name_plural': 'Wiehr Globe Object Credits',
                'db_table': 'web_wiehr_globe_object_credits',
                'ordering': ('credit_type', 'order', 'artist_object__name'),
            },
        ),
        migrations.AddIndex(
            model_name='wiehrglobeobjectartist',
            index=models.Index(fields=['name'], name='web_wiehr_g_name_f8770e_idx'),
        ),
        migrations.AddField(
            model_name='wiehrglobemodel',
            name='artists',
            field=models.ManyToManyField(blank=True, help_text='Artists associated with this release', related_name='releases', through='web.WiehrGlobeObjectToWiehrArtistObject', to='web.wiehrglobeobjectartist'),
        ),
        migrations.AddField(
            model_name='wiehratlasobjectimage',
            name='atlas_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='web.wiehratlasmodel', verbose_name='Atlas Location'),
        ),
        migrations.AddIndex(
            model_name='wiehratlasmodel',
            index=models.Index(fields=['is_visible'], name='web_wiehr_a_is_visi_ce45e6_idx'),
        ),
        migrations.AddIndex(
            model_name='wiehratlasmodel',
            index=models.Index(fields=['country_code'], name='web_wiehr_a_country_cf5f1a_idx'),
        ),
        migrations.AddIndex(
            model_name='wiehratlasmodel',
            index=models.Index(fields=['release_type'], name='web_wiehr_a_release_e9257c_idx'),
        ),
        migrations.AddIndex(
            model_name='wiehrarchivemodel',
            index=models.Index(fields=['-year'], name='web_wiehr_a_year_fba3ab_idx'),
        ),
        migrations.AddIndex(
            model_name='wiehrarchivemodel',
            index=models.Index(fields=['is_visible'], name='web_wiehr_a_is_visi_e2c318_idx'),
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['email'], name='web_team_email_c9695d_idx'),
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['is_blacklist', '-created_at'], name='web_team_is_blac_16a3e9_idx'),
        ),
        migrations.AddField(
            model_name='license',
            name='license_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='licenses', to='web.licensetype', verbose_name='License Type'),
        ),
        migrations.AddField(
            model_name='license',
            name='product_storage',
            field=models.ForeignKey(blank=True, help_text='Link to a real Storage item. Also gates that item’s download when its access type is "License Key Required".', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='licenses', to='web.wiehrstoragemodel', verbose_name='Product (Storage item)'),
        ),
        migrations.AddField(
            model_name='cvskill',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skills', to='web.cvprofile'),
        ),
        migrations.AddField(
            model_name='cvproject',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='web.cvprofile'),
        ),
        migrations.AddField(
            model_name='cvlanguage',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='languages', to='web.cvprofile'),
        ),
        migrations.AddField(
            model_name='cvexperience',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='experiences', to='web.cvprofile'),
        ),
        migrations.AddField(
            model_name='cveducation',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='education', to='web.cvprofile'),
        ),
        migrations.AddIndex(
            model_name='wiehrlabobjectlink',
            index=models.Index(fields=['lab', 'order'], name='web_wiehr_l_lab_id_466f02_idx'),
        ),
        migrations.AddIndex(
            model_name='wiehrlabmodel',
            index=models.Index(fields=['order', '-start_year'], name='web_wiehr_l_order_6cc3c4_idx'),
        ),
        migrations.AddIndex(
            model_name='wiehrlabmodel',
            index=models.Index(fields=['slug'], name='web_wiehr_l_slug_d92e72_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='wiehrglobeobjecttowiehrartistobject',
            unique_together={('globe_object', 'artist_object')},
        ),
        migrations.AddIndex(
            model_name='wiehrglobeobjectcredits',
            index=models.Index(fields=['globe_object', 'credit_type'], name='web_wiehr_g_globe_o_dee897_idx'),
        ),
        migrations.AddIndex(
            model_name='wiehrglobeobjectcredits',
            index=models.Index(fields=['artist_object'], name='web_wiehr_g_artist__43afae_idx'),
        ),
        migrations.AddIndex(
            model_name='wiehrglobemodel',
            index=models.Index(fields=['-order', '-date'], name='web_wiehr_g_order_17e365_idx'),
        ),
        migrations.AddIndex(
            model_name='wiehrglobemodel',
            index=models.Index(fields=['slug'], name='web_wiehr_g_slug_a9e0e2_idx'),
        ),
        migrations.AddIndex(
            model_name='wiehrglobemodel',
            index=models.Index(fields=['-date'], name='web_wiehr_g_date_d8b7e3_idx'),
        ),
        migrations.AddIndex(
            model_name='wiehratlasobjectimage',
            index=models.Index(fields=['atlas_object', 'order'], name='web_wiehr_a_atlas_o_e6bed1_idx'),
        ),
        migrations.AddIndex(
            model_name='license',
            index=models.Index(fields=['license_key'], name='web_license_license_c2855d_idx'),
        ),
        migrations.AddIndex(
            model_name='license',
            index=models.Index(fields=['product_storage'], name='web_license_product_c14f9e_idx'),
        ),
        migrations.AddField(
            model_name='wiehrstoragemodel',
            name='auto_issue_license_type',
            field=models.ForeignKey(blank=True, help_text='LicenseType created automatically for each visitor when Access Type is "Auto-issue" or "Auto-issue + Password" (e.g. Personal Exclusive License)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='auto_issue_items', to='web.licensetype', verbose_name='Auto-issue License Type'),
        ),
        migrations.AlterField(
            model_name='wiehrstoragemodel',
            name='access_type',
            field=models.CharField(choices=[('public', 'Public'), ('link', 'Link Only'), ('password', 'Link + Password'), ('license_key', 'License Key Required'), ('auto_issue', 'Auto-issue'), ('auto_issue_password', 'Auto-issue + Password')], default='public', help_text='public = visible to all, link = anyone with URL, password = requires password, license_key = requires a valid License, auto_issue = visitor fills in Legal Name + Email and a License is created for them automatically, auto_issue_password = same but password-gated first', max_length=25, verbose_name='Access Type'),
        ),
        migrations.RunPython(
            code=clear_dropped_preview_types,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name='wiehrstoragemodel',
            name='preview_audio',
        ),
        migrations.RemoveField(
            model_name='wiehrstoragemodel',
            name='preview_image',
        ),
        migrations.AlterField(
            model_name='wiehrstoragemodel',
            name='preview_type',
            field=models.CharField(blank=True, choices=[('', 'None'), ('video', 'Embedded Video (YouTube)')], default='', help_text='Type of preview content', max_length=10, verbose_name='Preview Type'),
        ),
        migrations.AlterField(
            model_name='shortener',
            name='short_url',
            field=models.CharField(blank=True, help_text='Leave blank for a random code, or name it (e.g. SUPPORT for /s/SUPPORT).', max_length=32, unique=True, verbose_name='Name / Short Code'),
        ),
        migrations.RemoveField(
            model_name='team',
            name='city',
        ),
    ]

import os
import random
import re
import string

from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils import timezone
from PIL import Image as PILImage
from ckeditor.fields import RichTextField
from slugify import slugify
from decimal import Decimal


hex_color_validator = RegexValidator(
    regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
    message='Enter a valid hex color code (e.g., #1DB954 or #FFF)'
)


def youtube_watch_url_to_embed(url):
    import re

    if not url:
        return ''

    patterns = [
        r'(?:youtube\.com/watch\?v=|youtube\.com/shorts/|youtu\.be/|youtube\.com/embed/)([\w-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return f'https://www.youtube.com/embed/{match.group(1)}'
    return ''


class WiehrArchiveModel(models.Model):
    internal_id = models.CharField(
        verbose_name='Internal ID',
        max_length=10,
        unique=True,
        help_text='Unique archive identifier (e.g., 2025, 2026)'
    )
    year = models.IntegerField(
        verbose_name='Year',
        unique=True,
        db_index=True,
        help_text='Archive year'
    )
    is_visible = models.BooleanField(
        verbose_name='Visible',
        default=True,
        db_index=True,
        help_text='Show in public view'
    )
    globe_count = models.IntegerField(
        verbose_name='Globe Count',
        default=0,
        help_text='Cached count of globe items'
    )
    atlas_count = models.IntegerField(
        verbose_name='Atlas Count',
        default=0,
        help_text='Cached count of atlas items'
    )
    lab_count = models.IntegerField(
        verbose_name='Lab Count',
        default=0,
        help_text='Cached count of lab items'
    )
    storage_count = models.IntegerField(
        verbose_name='Storage Count',
        default=0,
        help_text='Cached count of storage items'
    )
    total_count = models.IntegerField(
        verbose_name='Total Count',
        default=0,
        help_text='Cached total count of all items'
    )
    globe_ids = models.JSONField(
        verbose_name='Globe IDs',
        default=list,
        blank=True,
        help_text='Cached list of globe internal_ids'
    )
    atlas_ids = models.JSONField(
        verbose_name='Atlas IDs',
        default=list,
        blank=True,
        help_text='Cached list of atlas internal_ids'
    )
    lab_ids = models.JSONField(
        verbose_name='Lab IDs',
        default=list,
        blank=True,
        help_text='Cached list of lab internal_ids'
    )
    storage_ids = models.JSONField(
        verbose_name='Storage IDs',
        default=list,
        blank=True,
        help_text='Cached list of storage internal_ids'
    )
    created_at = models.DateTimeField(
        verbose_name='Created At',
        default=timezone.now
    )
    modified_at = models.DateTimeField(
        verbose_name='Modified At',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Wiehr Archive'
        verbose_name_plural = 'Wiehr Archives'
        db_table = 'web_wiehr_archive'
        ordering = ['-year']
        indexes = [
            models.Index(fields=['-year']),
            models.Index(fields=['is_visible']),
        ]

    def __str__(self):
        return f"{self.internal_id} ({self.total_count} items)"

    def refresh_counts(self):
        self.globe_ids = list(WiehrGlobeModel.objects.filter(
            is_visible=True, year=self.year
        ).values_list('internal_id', flat=True))
        self.globe_count = len(self.globe_ids)

        self.atlas_ids = list(WiehrAtlasModel.objects.filter(
            is_visible=True, year=self.year
        ).values_list('internal_id', flat=True))
        self.atlas_count = len(self.atlas_ids)

        # Automatic membership is by start_year; ongoing work (e.g. 2023 —
        # Present) would otherwise only ever show under its first year, so
        # entries manually pinned via extra_archives are unioned in.
        self.lab_ids = list(WiehrLabModel.objects.filter(
            models.Q(start_year=self.year) | models.Q(extra_archives=self),
            is_visible=True,
        ).distinct().values_list('internal_id', flat=True))
        self.lab_count = len(self.lab_ids)

        self.storage_ids = list(WiehrStorageModel.objects.filter(
            is_visible=True, year=self.year
        ).values_list('internal_id', flat=True))
        self.storage_count = len(self.storage_ids)

        self.total_count = (
            self.globe_count + self.atlas_count + self.lab_count +
            self.storage_count
        )
        self.save()

class WiehrGlobeObjectArtist(models.Model):
    name = models.CharField(
        verbose_name='Artist Name',
        max_length=140,
        db_index=True,
        help_text='Full artist name'
    )
    created_at = models.DateTimeField(
        verbose_name='Created At',
        default=timezone.now
    )

    class Meta:
        verbose_name = 'Wiehr Globe Object Artist'
        verbose_name_plural = 'Wiehr Globe Object Artist'
        db_table = 'web_wiehr_globe_object_artist'
        ordering = ('name',)
        indexes = [
            models.Index(fields=['name'])
        ]

    def __str__(self):
        return self.name


class WiehrGlobeModel(models.Model):
    date = models.DateField(
        verbose_name='Date',
        db_index=True,
        help_text='Release date'
    )
    title = models.CharField(
        verbose_name='Title',
        max_length=140,
        db_index=True,
        help_text='Release title'
    )
    pitch = models.TextField(
        verbose_name='Pitch',
        blank=True,
        null=True,
        help_text="Extended description or quote"
    )
    is_visible = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Show in public view'
    )
    release_type = models.CharField(
        verbose_name='Release Type',
        max_length=1,
        choices=[('W', 'Wiehr'), ('E', 'External')],
        default='W',
        db_index=True,
        help_text='W = Wiehr Core, E = External release'
    )
    year = models.IntegerField(
        verbose_name='Year',
        blank=True,
        null=True,
        db_index=True,
        help_text='Release year for archive grouping'
    )
    is_out = models.BooleanField(
        verbose_name='Is Out',
        default=False,
        db_index=True,
        help_text='Marks release as publicly available and triggers team notifications'
    )
    order = models.IntegerField(
        verbose_name='Order',
        default=0,
        db_index=True,
        help_text='Display order'
    )
    artists = models.ManyToManyField(
        'WiehrGlobeObjectArtist',
        through='WiehrGlobeObjectToWiehrArtistObject',
        related_name='releases',
        blank=True,
        help_text='Artists associated with this release'
    )
    image = models.ImageField(
        upload_to='data/images/',
        blank=True,
        null=True,
        help_text='Cover artwork'
    )
    pdf_file = models.FileField(
        upload_to='data/release_pdfs/',
        blank=True,
        null=True,
        help_text='PDF file for print QR'
    )
    slug = models.SlugField(
        verbose_name='Slug',
        max_length=222,
        unique=True,
        help_text='URL-friendly identifier (auto-generated from title)'
    )
    tags = models.CharField(
        verbose_name='Tags',
        max_length=500,
        blank=True,
        null=True,
        help_text='Comma-separated tags (e.g., electronic, ambient, experimental)'
    )
    background_color = models.CharField(
        verbose_name='Background Color',
        max_length=7,
        blank=True,
        null=True,
        validators=[hex_color_validator],
        help_text='Hex color code for page theme (e.g., #1DB954)'
    )

    internal_id = models.CharField(
        verbose_name='Internal ID',
        max_length=10,
        blank=True,
        null=True,
        unique=True,
        help_text='Unique release identifier (e.g., W001, E001)'
    )
    geo = models.CharField(
        verbose_name='Geographic Coordinates',
        max_length=100,
        blank=True,
        null=True,
        help_text='Coordinates in format: 054° 03\' 28.7" N 008° 22\' 44.3" W'
    )
    listen_url = models.URLField(
        verbose_name='Listen URL',
        max_length=500,
        blank=True,
        null=True,
        help_text='Aggregator link (e.g. zvonko.link/ARCTICA1)'
    )
    lyrics_url = models.URLField(
        verbose_name='Lyrics URL',
        max_length=500,
        blank=True,
        null=True,
        help_text='Lyrics link (e.g. genius.com/...)'
    )
    watch_url = models.URLField(
        verbose_name='Watch URL',
        max_length=500,
        blank=True,
        null=True,
        help_text='Video link (e.g. youtube.com/watch?v=...)'
    )
    created_at = models.DateTimeField(
        verbose_name='Created At',
        default=timezone.now
    )

    class Meta:
        ordering = ('-order', '-date')
        verbose_name = 'Wiehr Globe'
        verbose_name_plural = 'Wiehr Globe'
        db_table = 'web_wiehr_globe'

        indexes = [
            models.Index(fields=['-order', '-date']),
            models.Index(fields=['slug']),
            models.Index(fields=['-date']),
        ]

    def __str__(self):
        artist_names = ", ".join([ra.artist_object.name for ra in self.artist_roles.all()])
        if artist_names and self.title:
            return f"{artist_names} — {self.title}"
        elif self.title:
            return self.title
        return f"Release {self.id}"

    @property
    def display_title(self):
        primary = [r.artist_object.name for r in self.artist_roles.filter(role='primary').order_by('order')]
        featured = [r.artist_object.name for r in self.artist_roles.filter(role='featured').order_by('order')]
        main = ', '.join(primary) if primary else ''
        title = self.title or ''
        if featured:
            title = f"{title} (feat. {', '.join(featured)})"
        if main:
            return f"{main} — {title}"
        return title

    @property
    def display_release_title(self):
        return self.title or ''

    @property
    def featuring_text(self):
        featured = [r.artist_object.name for r in self.artist_roles.filter(role='featured').order_by('order')]
        if featured:
            return f"feat. {', '.join(featured)}"
        return ''

    @property
    def display_artist_title(self):
        primary = [r.artist_object.name for r in self.artist_roles.filter(role='primary').order_by('order')]
        return ', '.join(primary) if primary else ''

    def _get_or_create_short(self, long_url, suffix):
        if not self.internal_id or not long_url:
            return ''
        short_code = f"{self.internal_id}_{suffix}"
        obj, created = Shortener.objects.get_or_create(
            short_url=short_code,
            defaults={'long_url': long_url}
        )
        if not created and obj.long_url != long_url:
            obj.long_url = long_url
            obj.save()
        return f"/s/{short_code}"

    @property
    def listen_short(self):
        return self._get_or_create_short(self.listen_url, 'listen')

    @property
    def lyrics_short(self):
        return self._get_or_create_short(self.lyrics_url, 'lyrics')

    @property
    def watch_short(self):
        return self._get_or_create_short(self.watch_url, 'watch')

    def get_credits_by_artist(self):
        from collections import OrderedDict
        artist_credits = OrderedDict()
        for credit in self.credits.select_related('artist_object').order_by('artist_object__name', 'order'):
            name = credit.artist_object.name
            if name not in artist_credits:
                artist_credits[name] = []
            artist_credits[name].append(credit.get_credit_type_display())
        return [{'name': name, 'roles': ', '.join(roles)} for name, roles in artist_credits.items()]

    def get_tags_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def get_absolute_url(self):
        return reverse("globe_object_page", kwargs={"slug": self.slug})

    def _determine_image_identifier(self):
        identifier = self.internal_id or self.slug
        if not identifier and self.title:
            identifier = slugify(self.title)
        if not identifier and self.pk:
            identifier = f"release-{self.pk}"
        if not identifier:
            identifier = f"release-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        return identifier

    def _resize_image_variants(self, image_bytes, identifier):
        from io import BytesIO

        variants = {}
        try:
            img = PILImage.open(BytesIO(image_bytes))

            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            img_640 = img.copy()
            img_640.thumbnail((640, 640), PILImage.Resampling.LANCZOS)
            buffer_640 = BytesIO()
            img_640.save(buffer_640, format='JPEG', quality=85, optimize=True)
            variants['640'] = {
                'filename': f'data/images/{identifier}@640.jpg',
                'bytes': buffer_640.getvalue()
            }

            img_1280 = img.copy()
            img_1280.thumbnail((1280, 1280), PILImage.Resampling.LANCZOS)
            buffer_1280 = BytesIO()
            img_1280.save(buffer_1280, format='JPEG', quality=90, optimize=True)
            variants['1280'] = {
                'filename': f'data/images/{identifier}@1280.jpg',
                'bytes': buffer_1280.getvalue()
            }
        except Exception:
            variants['original'] = {
                'filename': f'{identifier}.jpg',
                'bytes': image_bytes
            }

        return variants

    def _process_image_bytes(self, image_bytes):
        if not image_bytes:
            return False

        identifier = self._determine_image_identifier()
        variants = self._resize_image_variants(image_bytes, identifier)

        if not variants:
            return False

        storage = self.image.storage
        upload_prefix = "data/images"
        original_name = getattr(self.image, "name", None)

        paths_to_cleanup = [
            f"{upload_prefix}/{identifier}.jpg",
            f"{upload_prefix}/{identifier}@640.jpg",
            f"{upload_prefix}/{identifier}@1280.jpg",
        ]

        for path in paths_to_cleanup:
            if storage.exists(path):
                storage.delete(path)

        for size in ["640", "1280"]:
            if size in variants:
                storage.save(
                    variants[size]['filename'],
                    ContentFile(variants[size]["bytes"])
                )

        if "1280" in variants:
            self.image.name = variants['1280']['filename']
            if hasattr(self.image, "_committed"):
                self.image._committed = True

        self._remove_original_file(original_name)
        return True

    def _remove_original_file(self, original_name):
        if not original_name or not self.image:
            return

        storage = self.image.storage
        new_name = self.image.name

        if original_name == new_name:
            return

        candidates = []
        if "/" in original_name:
            candidates.append(original_name)
        else:
            upload_to = self.image.field.upload_to.strip("/")
            if upload_to:
                candidates.append(f"{upload_to}/{original_name}")
            candidates.append(original_name)

        for candidate in candidates:
            if candidate == new_name:
                continue
            if storage.exists(candidate):
                storage.delete(candidate)
                break

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)

        if self.pk:
            old_instance = WiehrGlobeModel.objects.get(pk=self.pk)
            if old_instance.image and not self.image:
                storage = old_instance.image.storage
                identifier = old_instance._determine_image_identifier()
                for suffix in ["", "@640", "@1280"]:
                    filename = f"data/images/{identifier}{suffix}.jpg"
                    if storage.exists(filename):
                        storage.delete(filename)

            if old_instance.pdf_file and old_instance.pdf_file != self.pdf_file:
                storage = old_instance.pdf_file.storage
                old_pdf_path = old_instance.pdf_file.name
                if storage.exists(old_pdf_path):
                    storage.delete(old_pdf_path)

        if self.image and not getattr(self.image, '_committed', True):
            image_file = getattr(self.image, 'file', self.image)

            try:
                image_file.seek(0)
                image_bytes = image_file.read()
            except Exception:
                image_bytes = None

            if image_bytes:
                self._process_image_bytes(image_bytes)
            else:
                manual_path = getattr(self.image, 'name', None)
                storage = self.image.storage
                if manual_path and storage.exists(manual_path):
                    with storage.open(manual_path, 'rb') as fh:
                        self._process_image_bytes(fh.read())

        elif self.internal_id and self.image:
            import os

            current_filename = os.path.basename(self.image.name)
            expected_filename = f'{self.internal_id}@1280.jpg'
            if current_filename != expected_filename:
                storage = self.image.storage
                old_base = current_filename.replace('@1280.jpg', '').replace(
                    '@640.jpg', ''
                ).replace('.jpg', '')

                for suffix in ["", "@640", "@1280"]:
                    old_filename = f"data/images/{old_base}{suffix}.jpg"
                    new_filename = f"data/images/{self.internal_id}{suffix}.jpg"
                    if storage.exists(old_filename):
                        with storage.open(old_filename, 'rb') as f:
                            content = f.read()
                        storage.save(new_filename, ContentFile(content))
                        storage.delete(old_filename)

                self.image.name = f"data/images/{self.internal_id}@1280.jpg"

        super().save(*args, **kwargs)


class WiehrGlobeObjectToWiehrArtistObject(models.Model):
    ROLE_CHOICES = [
        ('primary', 'Primary Artist'),
        ('featured', 'Featured Artist'),
    ]

    globe_object = models.ForeignKey(
        WiehrGlobeModel,
        on_delete=models.CASCADE,
        related_name='artist_roles'
    )
    artist_object = models.ForeignKey(
        WiehrGlobeObjectArtist,
        on_delete=models.CASCADE,
        related_name='release_roles'
    )
    role = models.CharField(
        verbose_name='Role',
        max_length=10,
        choices=ROLE_CHOICES,
        default='primary',
        db_index=True,
        help_text='Primary = main artist, Featured = feat. artist'
    )
    order = models.IntegerField(
        verbose_name='Order',
        default=0,
        help_text='Display order'
    )

    class Meta:
        verbose_name = 'Wiehr Globe Object To Wiehr Artist Object'
        verbose_name_plural = 'Wiehr Globe Object To Wiehr Artist Object'
        db_table = 'web_wiehr_globe_object_to_wiehr_artist_object'

        ordering = ('order', 'artist_object__name')
        unique_together = ('globe_object', 'artist_object')

    def __str__(self):
        return f"{self.artist_object.name} - {self.globe_object.title}"


class WiehrGlobeObjectCredits(models.Model):
    CREDIT_TYPES = [
        ('vocal', 'Vocal'),
        ('production', 'Production'),
        ('lyrics', 'Lyrics'),
        ('mixing', 'Mixing'),
        ('mastering', 'Mastering'),
        ('artwork', 'Artwork'),
        ('video', 'Video'),
        ('label', 'Label'),
    ]

    globe_object = models.ForeignKey(
        WiehrGlobeModel,
        on_delete=models.CASCADE,
        related_name='credits'
    )
    artist_object = models.ForeignKey(
        WiehrGlobeObjectArtist,
        on_delete=models.CASCADE,
        related_name='credits',
        help_text='Artist who contributed to this credit'
    )
    credit_type = models.CharField(
        verbose_name='Credit Type',
        max_length=20,
        choices=CREDIT_TYPES,
        db_index=True,
        help_text='Type of contribution'
    )
    notes = models.CharField(
        verbose_name='Notes',
        max_length=200,
        blank=True,
        null=True,
        help_text='Additional notes about this credit'
    )
    order = models.IntegerField(
        verbose_name='Order',
        default=0,
        help_text='Display order within credit type'
    )

    class Meta:
        verbose_name = 'Wiehr Globe Object Credits'
        verbose_name_plural = 'Wiehr Globe Object Credits'
        ordering = ('credit_type', 'order', 'artist_object__name')
        db_table = 'web_wiehr_globe_object_credits'
        indexes = [
            models.Index(fields=['globe_object', 'credit_type']),
            models.Index(fields=['artist_object']),
        ]

    def __str__(self):
        return f"{self.artist_object.name} - {self.get_credit_type_display()} ({self.globe_object.title})"


class Team(models.Model):
    email = models.EmailField(
        verbose_name='Email',
        unique=True,
        help_text='Subscriber email address'
    )
    country = models.CharField(
        verbose_name='Country',
        max_length=100,
        blank=True,
        null=True,
        help_text='Subscriber country (optional)'
    )
    country_code = models.CharField(
        verbose_name='Country Code',
        max_length=2,
        blank=True,
        null=True,
        help_text='ISO 3166-1 alpha-2 country code'
    )
    disconnect_token = models.CharField(
        verbose_name='Disconnect Token',
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        help_text='Token for disconnect link'
    )
    is_blacklist = models.BooleanField(
        verbose_name='Blacklisted',
        default=False,
        help_text='Exclude from email campaigns for other reasons'
    )
    is_disconnected = models.BooleanField(
        verbose_name='Disconnected',
        default=False,
        help_text='User has disconnected from emails'
    )
    disconnected_at = models.DateTimeField(
        verbose_name='Disconnected At',
        blank=True,
        null=True,
        help_text='Date and time when the user disconnected'
    )
    created_at = models.DateTimeField(
        verbose_name='Subscribed At',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name='Updated At',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Wiehr Network'
        verbose_name_plural = 'Wiehr Network'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_blacklist', '-created_at']),
        ]

    def __str__(self):
        status = 'blacklisted' if self.is_blacklist else 'active'
        return f"{self.email} ({status})"


class CVProfile(models.Model):
    VERSION_CHOICES = [
        ('engineer', 'ENGINEER'),
        ('composer', 'COMPOSER'),
    ]
    version = models.CharField(max_length=20, choices=VERSION_CHOICES, unique=True)
    name = models.CharField(max_length=100, help_text="Full name")
    title = models.CharField(max_length=200, help_text="Job title / headline")
    bio = models.TextField(blank=True, help_text="Short professional summary")
    email = models.EmailField(help_text="Contact email for CV")
    location = models.CharField(max_length=100, blank=True)
    linkedin = models.CharField(max_length=100, blank=True, help_text="Display text, e.g. linkedin.com/in/wiehrcc")
    linkedin_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wiehr CV Profile'
        verbose_name_plural = 'Wiehr CV Profiles'
        ordering = ['version']

    def __str__(self):
        return f"CV — {self.get_version_display()} ({self.name})"


class CVExperience(models.Model):
    profile = models.ForeignKey(CVProfile, on_delete=models.CASCADE, related_name='experiences')
    role = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    company_url = models.URLField(blank=True)
    date = models.CharField(max_length=50, help_text="e.g. 03/2022 — Present")
    location = models.CharField(max_length=100, blank=True)
    bullets = models.TextField(help_text="One bullet point per line")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'CV Experience'
        verbose_name_plural = 'CV Experiences'
        ordering = ['order']

    def __str__(self):
        return f"{self.role} at {self.company}"

    def get_bullets_list(self):
        return [b.strip() for b in self.bullets.strip().splitlines() if b.strip()]


class CVSkill(models.Model):
    profile = models.ForeignKey(CVProfile, on_delete=models.CASCADE, related_name='skills')
    category = models.CharField(max_length=100, help_text="e.g. Backend, Frontend, DevOps")
    items = models.TextField(help_text="Comma-separated skills, e.g. Python, Django, Flask")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'CV Skill'
        verbose_name_plural = 'CV Skills'
        ordering = ['order']

    def __str__(self):
        return f"{self.category}: {self.items[:50]}"


class CVProject(models.Model):
    SECTION_CHOICES = [
        ('commercial', 'Commercial'),
        ('personal', 'Personal'),
    ]
    profile = models.ForeignKey(CVProfile, on_delete=models.CASCADE, related_name='projects')
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default='personal')
    name = models.CharField(max_length=200)
    project_type = models.CharField(max_length=100, help_text="e.g. Portfolio, Record Label")
    date = models.CharField(max_length=50, help_text="e.g. 01/2026 — Present")
    description = models.TextField()
    bullets = models.TextField(blank=True, help_text="One bullet point per line (optional, mainly for commercial projects)")
    link_text = models.CharField(max_length=200, blank=True, help_text="Display text for link")
    link_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'CV Project'
        verbose_name_plural = 'CV Projects'
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.project_type})"

    def get_bullets_list(self):
        return [b.strip() for b in self.bullets.strip().splitlines() if b.strip()]


class CVEducation(models.Model):
    profile = models.ForeignKey(CVProfile, on_delete=models.CASCADE, related_name='education')
    title = models.CharField(max_length=200)
    date = models.CharField(max_length=50, help_text="e.g. 09/2023 — Present")
    url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'CV Education'
        verbose_name_plural = 'CV Education'
        ordering = ['order']

    def __str__(self):
        return self.title


class CVLanguage(models.Model):
    profile = models.ForeignKey(CVProfile, on_delete=models.CASCADE, related_name='languages')
    language = models.CharField(max_length=50)
    level = models.CharField(max_length=100, help_text="e.g. C2 Proficient · EF SET Certified")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'CV Language'
        verbose_name_plural = 'CV Languages'
        ordering = ['order']

    def __str__(self):
        return f"{self.language}: {self.level}"


class WiehrAtlasModel(models.Model):
    internal_id = models.CharField(
        max_length=10,
        verbose_name='Internal ID',
        help_text='Interal ID for history'
    )
    country_code = models.CharField(
        verbose_name='Country Code',
        max_length=2,
        help_text='ISO 3166-1 alpha-2 country code (e.g., ge, by, ru)'
    )
    country_title = models.CharField(
        verbose_name='Country Title',
        max_length=100,
        help_text='Full country name (e.g., Georgia, Belarus, Russia)'
    )
    coordinates = models.CharField(
        verbose_name='Coordinates',
        max_length=200,
        help_text='Geographic coordinates (e.g., 41° 41\' 49.5672" N 44° 46\' 25.2264" E)'
    )
    is_visible = models.BooleanField(
        verbose_name='Visible',
        default=True,
        db_index=True,
        help_text='Show this location on the atlas'
    )
    release_type = models.CharField(
        verbose_name='Type',
        max_length=1,
        choices=[('P', 'Photos'), ('S', 'Shares')],
        default='P',
        db_index=True,
        help_text='P = Photos (9 images), S = Shares (1 image + location)'
    )
    year = models.IntegerField(
        verbose_name='Year',
        blank=True,
        null=True,
        db_index=True,
        help_text='Year for archive grouping'
    )
    order = models.IntegerField(
        verbose_name='Display Order',
        default=0,
        db_index=True,
        help_text='Display order'
    )
    created_at = models.DateTimeField(
        verbose_name='Created At',
        default=timezone.now
    )
    modified_at = models.DateTimeField(
        verbose_name='Modified At',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Wiehr Atlas'
        verbose_name_plural = 'Wiehr Atlas'
        db_table = 'web_wiehr_atlas'
        ordering = ('-internal_id',)
        indexes = [
            models.Index(fields=['is_visible']),
            models.Index(fields=['country_code']),
            models.Index(fields=['release_type']),
        ]

    def __str__(self):
        return f"{self.country_code} | {self.country_title}"

    def get_absolute_url(self):
        return reverse("atlas_object_page", kwargs={"internal_id": self.internal_id})


class WiehrAtlasObjectImage(models.Model):
    atlas_object = models.ForeignKey(
        WiehrAtlasModel,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Atlas Location'
    )
    image = models.ImageField(
        upload_to='atlas_images/',
        verbose_name='Image',
        help_text='Upload image for this location'
    )
    order = models.IntegerField(
        verbose_name='Display Order',
        default=0,
        help_text='Order in which images are displayed (1, 2, 3...)'
    )
    created_at = models.DateTimeField(
        verbose_name='Created At',
        default=timezone.now
    )

    class Meta:
        verbose_name = 'Wiehr Atlas Image'
        verbose_name_plural = 'Wiehr Atlas Images'
        db_table = 'web_wiehr_atlas_object_image'
        ordering = ('order', 'created_at')
        indexes = [
            models.Index(fields=['atlas_object', 'order']),
        ]

    def __str__(self):
        return f"Image for {self.atlas_object.country_code} (Order: {self.order})"


class WiehrLabModel(models.Model):
    internal_id = models.CharField(
        verbose_name='Internal ID',
        max_length=10,
        blank=True,
        null=True,
        unique=True,
        help_text='Unique identifier (e.g., L001, L002)'
    )
    title = models.CharField(
        verbose_name='Title',
        max_length=140,
        db_index=True
    )
    description = RichTextField(verbose_name='Description')
    media = models.FileField(
        verbose_name='Media',
        upload_to='lab_media/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['gif', 'png', 'jpg', 'jpeg', 'webp']
        )],
        help_text='Single cover media — GIF, PNG, JPG or WEBP. Uploaded as-is, no conversion.'
    )
    youtube_url = models.URLField(
        verbose_name='YouTube URL',
        max_length=500,
        blank=True,
        default='',
        help_text='Clicking the cover opens this as an embedded video. Leave empty to keep the cover non-interactive.'
    )
    role = models.CharField(
        verbose_name='Role',
        max_length=140,
        db_index=True
    )
    slug = models.SlugField(
        verbose_name='Slug',
        max_length=140,
        unique=True,
        help_text='URL-friendly identifier (auto-generated from title)'
    )
    start_year = models.IntegerField(verbose_name='Start Year', db_index=True)
    end_year = models.IntegerField(verbose_name='End Year', db_index=True)
    order = models.IntegerField(verbose_name='Display Order', default=0)
    is_visible = models.BooleanField(
        verbose_name='Visible',
        default=True,
        db_index=True,
        help_text='Show in public view'
    )
    extra_archives = models.ManyToManyField(
        'WiehrArchiveModel',
        verbose_name='Also show in these years',
        blank=True,
        related_name='extra_lab_items',
        help_text=(
            'Ongoing work only appears under its start year automatically. '
            'Add years here to also surface it in those archives.'
        )
    )
    release_type = models.CharField(
        verbose_name='Type',
        max_length=1,
        choices=[('L', 'Lab')],
        default='L',
        db_index=True,
        help_text='L = Lab project'
    )

    created_at = models.DateTimeField(
        verbose_name='Created At',
        default=timezone.now
    )
    modified_at = models.DateTimeField(
        verbose_name='Modified At',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Wiehr Lab'
        verbose_name_plural = 'Wiehr Lab'
        db_table = 'web_wiehr_lab'
        ordering = ('order', '-start_year')
        indexes = [
            models.Index(fields=['order', '-start_year']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.title}"

    def get_absolute_url(self):
        return reverse("lab_object_page", kwargs={"slug": self.slug})

    def get_year_range(self):
        if not self.end_year:
            return f"{self.start_year} — Present"
        if self.start_year == self.end_year:
            return str(self.start_year)
        return f"{self.start_year} — {self.end_year}"

    def youtube_embed_url(self):
        return youtube_watch_url_to_embed(self.youtube_url)

    @property
    def media_url(self):
        return self.media.url if self.media else ''

    @property
    def media_mime(self):
        import os

        ext = os.path.splitext(self.media.name)[1].lower() if self.media else ''
        return {
            '.gif': 'image/gif',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
        }.get(ext, 'image/png')

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)

        old_media_name = None
        if self.pk:
            old = WiehrLabModel.objects.filter(pk=self.pk).values_list('media', flat=True).first()
            old_media_name = old or None

        if self.media and not getattr(self.media, '_committed', True):
            import os

            ext = os.path.splitext(self.media.name)[1].lower() or '.png'
            self.media.name = f'{self.slug}{ext}'

        super().save(*args, **kwargs)

        new_media_name = self.media.name if self.media else None
        if old_media_name and old_media_name != new_media_name:
            storage = self.media.storage
            if storage.exists(old_media_name):
                storage.delete(old_media_name)


class WiehrLabObjectLink(models.Model):
    lab = models.ForeignKey(
        WiehrLabModel,
        on_delete=models.CASCADE,
        related_name='links'
    )
    website = models.CharField(verbose_name='Website', max_length=140)
    description = models.CharField(
        verbose_name='Description',
        max_length=140
    )
    url = models.URLField(verbose_name='URL', max_length=500)
    order = models.IntegerField(
        verbose_name='Order',
        default=0,
        help_text='Display order'
    )

    class Meta:
        verbose_name = 'Wiehr Lab Link'
        verbose_name_plural = 'Wiehr Lab Links'
        db_table = 'web_wiehr_lab_object_link'
        ordering = ('order',)
        indexes = [
            models.Index(fields=['lab', 'order']),
        ]

    def __str__(self):
        return f"{self.lab} - {self.website}"


class WiehrStorageModel(models.Model):
    ACCESS_CHOICES = [
        ('public', 'Public'),
        ('link', 'Link Only'),
        ('password', 'Link + Password'),
        ('license_key', 'License Key Required'),
        ('auto_issue', 'Auto-issue'),
        ('auto_issue_password', 'Auto-issue + Password'),
    ]

    internal_id = models.CharField(
        verbose_name='Internal ID',
        max_length=10,
        unique=True,
        help_text='Unique storage identifier (e.g., S000, S001, S002)'
    )
    slug = models.SlugField(
        verbose_name='Slug',
        max_length=140,
        unique=True,
        help_text='URL-friendly identifier'
    )
    title = models.CharField(
        verbose_name='Title',
        max_length=200,
        help_text='Storage item title'
    )
    description = models.TextField(
        verbose_name='Description',
        help_text='Storage item description'
    )
    file = models.FileField(
        upload_to='storage/',
        verbose_name='File',
        help_text='Downloadable file'
    )
    file_size = models.BigIntegerField(
        verbose_name='File Size',
        blank=True,
        null=True,
        help_text='File size in bytes (auto-calculated)'
    )
    cover_image = models.ImageField(
        upload_to='storage/covers/',
        verbose_name='Cover Image',
        help_text='Cover image for storage item'
    )
    file_type = models.CharField(
        verbose_name='File Type',
        max_length=50,
        help_text='Type of file (e.g., Telegram Theme, Font Family)'
    )
    download_count = models.IntegerField(
        verbose_name='Download Count',
        default=0,
        help_text='Number of downloads'
    )
    year = models.IntegerField(
        verbose_name='Year',
        db_index=True,
        help_text='Year for archive grouping'
    )
    order = models.IntegerField(
        verbose_name='Display Order',
        default=0,
        db_index=True,
        help_text='Display order'
    )
    is_visible = models.BooleanField(
        verbose_name='Visible',
        default=True,
        db_index=True,
        help_text='Show in public view'
    )
    access_type = models.CharField(
        verbose_name='Access Type',
        max_length=25,
        choices=ACCESS_CHOICES,
        default='public',
        help_text='public = visible to all, link = anyone with URL, password = requires password, license_key = requires a valid License, auto_issue = visitor fills in Legal Name + Email and a License is created for them automatically, auto_issue_password = same but password-gated first'
    )
    access_password = models.CharField(
        verbose_name='Access Password',
        max_length=100,
        blank=True,
        help_text='Password for protected items'
    )
    auto_issue_license_type = models.ForeignKey(
        'LicenseType',
        on_delete=models.PROTECT,
        related_name='auto_issue_items',
        verbose_name='Auto-issue License Type',
        blank=True,
        null=True,
        help_text='LicenseType created automatically for each visitor when Access Type is "Auto-issue" or "Auto-issue + Password" (e.g. Personal Exclusive License)'
    )
    created_at = models.DateTimeField(
        verbose_name='Created At',
        default=timezone.now
    )
    PREVIEW_TYPE_CHOICES = [
        ('', 'None'),
        ('video', 'Embedded Video (YouTube)'),
    ]

    preview_type = models.CharField(
        verbose_name='Preview Type',
        max_length=10,
        choices=PREVIEW_TYPE_CHOICES,
        blank=True,
        default='',
        help_text='Type of preview content'
    )
    preview_url = models.URLField(
        verbose_name='Preview Video URL',
        max_length=500,
        blank=True,
        default='',
        help_text="Used when Preview Type is 'video' — a YouTube URL, same embed mechanism as Lab"
    )
    modified_at = models.DateTimeField(
        verbose_name='Modified At',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Wiehr Storage'
        verbose_name_plural = 'Wiehr Storage'
        db_table = 'web_wiehr_storage'
        ordering = ['-order', '-created_at']
        indexes = [
            models.Index(fields=['-order', '-created_at']),
            models.Index(fields=['is_visible']),
            models.Index(fields=['year']),
            models.Index(fields=['access_type']),
        ]

    def __str__(self):
        return f"{self.internal_id} - {self.title}"

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def is_accessible(self, password=None):
        if self.access_type in ('password', 'auto_issue_password'):
            return password == self.access_password
        return True

    def get_absolute_url(self):
        return reverse("storage_object_page", kwargs={"slug": self.slug})

    def youtube_embed_url(self):
        return youtube_watch_url_to_embed(self.preview_url)

    @property
    def has_preview(self):
        if self.preview_type == 'video':
            return bool(self.youtube_embed_url())
        return False


class WiehrStorageLinkModel(models.Model):
    storage = models.ForeignKey(
        WiehrStorageModel,
        on_delete=models.CASCADE,
        related_name='links',
        verbose_name='Storage Item'
    )
    label = models.CharField(
        verbose_name='Label',
        max_length=100,
        help_text='Link label (e.g., THEME, DESIGN, EMOJI)'
    )
    url = models.URLField(
        verbose_name='URL',
        max_length=500,
        help_text='External link URL'
    )
    order = models.IntegerField(
        verbose_name='Display Order',
        default=0,
        help_text='Order of link display'
    )

    class Meta:
        verbose_name = 'Storage Link'
        verbose_name_plural = 'Storage Links'
        db_table = 'web_wiehr_storage_link'
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.label}: {self.url}"


class LicenseType(models.Model):
    name = models.CharField(
        verbose_name='Name',
        max_length=100,
        unique=True,
        help_text='e.g. Exclusive Personal License, Non-Exclusive Commercial License'
    )
    description = models.TextField(
        verbose_name='Description',
        blank=True,
        help_text='Optional internal note about what this license type covers'
    )

    class Meta:
        verbose_name = 'Wiehr License Type'
        verbose_name_plural = 'Wiehr License Types'
        db_table = 'web_license_type'
        ordering = ('name',)

    def __str__(self):
        return self.name


class License(models.Model):
    internal_id = models.CharField(
        verbose_name='Internal ID',
        max_length=10,
        unique=True,
        blank=True,
        help_text='Auto-generated on save (C001, C002, ...) if left blank'
    )
    license_key = models.CharField(
        verbose_name='License ID',
        max_length=64,
        unique=True,
        db_index=True,
        blank=True,
        help_text='Auto-generated on save if left blank'
    )
    license_type = models.ForeignKey(
        LicenseType,
        on_delete=models.PROTECT,
        related_name='licenses',
        verbose_name='License Type'
    )
    product_storage = models.ForeignKey(
        WiehrStorageModel,
        on_delete=models.SET_NULL,
        related_name='licenses',
        verbose_name='Product (Storage item)',
        blank=True,
        null=True,
        help_text='Link to a real Storage item. Also gates that item’s download when its access type is "License Key Required".'
    )
    product_text = models.CharField(
        verbose_name='Product (custom text)',
        max_length=200,
        blank=True,
        help_text='Used instead of the field above when the licensed product has no Storage item — e.g. "Wiehr Font Family"'
    )
    licensee_name = models.CharField(
        verbose_name='Licensee Name',
        max_length=200
    )
    licensee_email = models.EmailField(
        verbose_name='Licensee Email'
    )
    effective_date = models.DateField(
        verbose_name='Effective Date',
        default=timezone.now
    )
    is_active = models.BooleanField(
        verbose_name='Active',
        default=True,
        help_text='Uncheck to revoke — the license will no longer verify or unlock downloads'
    )
    created_at = models.DateTimeField(
        verbose_name='Created At',
        auto_now_add=True
    )
    modified_at = models.DateTimeField(
        verbose_name='Modified At',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Wiehr License'
        verbose_name_plural = 'Wiehr Licenses'
        db_table = 'web_license'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['license_key']),
            models.Index(fields=['product_storage']),
        ]

    def __str__(self):
        return f"{self.internal_id} — {self.licensee_name}"

    def save(self, *args, **kwargs):
        if not self.internal_id:
            last = License.objects.exclude(internal_id='').order_by('-id').first()
            next_num = 1
            if last and last.internal_id[1:].isdigit():
                next_num = int(last.internal_id[1:]) + 1
            self.internal_id = f'C{next_num:03d}'
        if not self.license_key:
            import secrets
            self.license_key = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def get_product_display(self):
        if self.product_storage:
            return self.product_storage.title
        return self.product_text or '—'




def image_compressor(sender, **kwargs):
    # loaddata sends raw=True: seeding a fresh deploy must not depend on media
    # files being present, and fixture rows are already-compressed originals.
    if kwargs.get("raw"):
        return

    if not (kwargs["created"] or kwargs["update_fields"] is not None):
        return

    instance = kwargs["instance"]
    if not instance.image:
        return

    try:
        path = instance.image.path
    except (ValueError, NotImplementedError):
        # No local filesystem path (e.g. remote storage backend)
        return

    if not os.path.exists(path):
        return

    with PILImage.open(path) as image:
        image.save(path, optimize=True, quality=40)


post_save.connect(image_compressor, sender=WiehrGlobeModel)


SHORT_CODE_CHARS = string.ascii_uppercase + string.digits
SHORT_CODE_LENGTH = 7

# Names live in the same namespace as generated codes, so anything that is
# already a route under /s/ or would break a URL is off limits.
SHORT_CODE_RESERVED = {'S', 'ADMIN', 'STATIC', 'MEDIA'}
SHORT_CODE_RE = re.compile(r'^[A-Z0-9][A-Z0-9_-]{0,31}$')


def create_short_code():
    while True:
        code = ''.join(random.choice(SHORT_CODE_CHARS) for _ in range(SHORT_CODE_LENGTH))
        if not Shortener.objects.filter(short_url__iexact=code).exists():
            return code


def normalize_short_code(value):
    """Uppercase a user-supplied name and check it can be a short code.

    Returns (code, error). Codes are stored and compared uppercase so
    /s/support and /s/SUPPORT resolve to the same link.
    """
    code = (value or '').strip().upper()
    if not code:
        return '', None
    if not SHORT_CODE_RE.match(code):
        return '', 'Names use letters, digits, - and _ only, and start with a letter or digit.'
    if code in SHORT_CODE_RESERVED:
        return '', 'That name is reserved.'
    return code, None


class ShortenerSettings(models.Model):
    password = models.CharField(
        verbose_name='Password',
        max_length=100,
        default='W1',
        help_text='Required on /s to create a short link. Change it here.'
    )
    modified_at = models.DateTimeField(verbose_name='Modified At', auto_now=True)

    class Meta:
        verbose_name = 'Wiehr Shortener Settings'
        verbose_name_plural = 'Wiehr Shortener Settings'
        db_table = 'web_shortener_settings'

    def __str__(self):
        return 'Shortener settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Shortener(models.Model):
    long_url = models.URLField(verbose_name='Long URL', max_length=2000)
    short_url = models.CharField(
        verbose_name='Name / Short Code',
        max_length=32,
        unique=True,
        blank=True,
        help_text='Leave blank for a random code, or name it (e.g. SUPPORT for /s/SUPPORT).'
    )
    full_url = models.CharField(verbose_name='Full URL', max_length=2000, blank=True)

    times_followed = models.PositiveIntegerField(verbose_name='Times Followed', default=0)
    created_at = models.DateTimeField('Created At', default=timezone.now, null=True)

    class Meta:
        verbose_name = 'Wiehr Shortener'
        verbose_name_plural = 'Wiehr Shortener'
        db_table = 'web_shortener'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.long_url} - {self.short_url}"

    def save(self, *args, **kwargs):
        if not self.short_url:
            self.short_url = create_short_code()
        else:
            # Only trimmed, never case-folded: existing codes like E007_watch
            # are already published, and lookups are case-insensitive anyway.
            self.short_url = self.short_url.strip()

        from wiehr import settings as project_settings
        self.full_url = f'{project_settings.SITE_URL}s/{self.short_url}'

        super().save(*args, **kwargs)


class QrCode(models.Model):
    object_id = models.CharField(max_length=100, verbose_name='Object ID')
    tag = models.CharField(max_length=100, verbose_name='Tag', blank=True)
    link = models.URLField(verbose_name='Link')

    wid = models.CharField(max_length=10, blank=True, null=True, verbose_name='WID', help_text='Release WID (e.g., W000, W001) to auto-set colors from Release')

    error_correction = models.CharField(max_length=1, choices=[('L', 'L'), ('M', 'M'), ('Q', 'Q'), ('H', 'H')], default='H', verbose_name='Error Correction')
    version = models.PositiveIntegerField(default=10, verbose_name='Version')
    border = models.PositiveIntegerField(default=8, verbose_name='Border')
    fg_color = models.CharField(max_length=7, default='#151617', verbose_name='Foreground Color')
    bg_color = models.CharField(max_length=7, default='#f4f4f4', verbose_name='Background Color')
    logo_size = models.FloatField(default=0.2, verbose_name='Logo Size')
    svg_size = models.PositiveIntegerField(default=320, verbose_name='SVG Size')

    created_at = models.DateTimeField('Created At', default=timezone.now, null=True)

    class Meta:
        verbose_name = 'Wiehr QR Code'
        verbose_name_plural = 'Wiehr QR Codes'
        db_table = 'web_qr_code'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.object_id} - {self.tag}"

    def get_config(self):
        config = {
            "error_correction": self.error_correction,
            "version": self.version,
            "border": self.border,
            "fg_color": self.fg_color,
            "bg_color": self.bg_color,
            "logo_size": self.logo_size,
            "svg_size": self.svg_size,
            "black_and_white": False
        }

        if self.wid:
            release = WiehrGlobeModel.objects.filter(internal_id=self.wid).first()
            if release and release.background_color:
                config["bg_color"] = release.background_color
                config["fg_color"] = invert_hex_color(release.background_color)

        return config

    def generate_print(self):
        import tempfile
        from pathlib import Path
        from .qrcode.print_generator import create_print_pdf
        from .qrcode.qr_generator import generate_qr_svg

        if self.wid:
            release = WiehrGlobeModel.objects.filter(internal_id=self.wid).first()
            if not release:
                raise ValueError("Release with WID not found.")

            config = {
                "title": release.title,
                "wid": release.internal_id,
                "geo": release.geo,
                "color": release.background_color,
                "bpm": None,
                "pdf_title": release.internal_id
            }
        else:
            config = {
                "title": None,
                "wid": None,
                "geo": None,
                "color": None,
                "bpm": None,
                "pdf_title": self.object_id
            }

        qr_config = self.get_config()
        qr_config["black_and_white"] = True
        qr_svg_content = generate_qr_svg(self.link, qr_config)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(qr_svg_content)
            qr_svg_path = Path(f.name)

        try:
            output_path = Path(__file__).parent / 'qrcode' / f"print_{config.get('pdf_title')}.pdf"
            create_print_pdf(output_path=output_path, qr_source=qr_svg_path, config=config)
            return output_path
        finally:
            qr_svg_path.unlink()


def invert_hex_color(hex_color):
    hex_color = (hex_color or '').lstrip('#')
    if len(hex_color) != 6:
        return '#ffffff'
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return '#{:02x}{:02x}{:02x}'.format(*(255 - c for c in rgb))

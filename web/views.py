import os
import datetime
import logging
import uuid
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from django.db.models import F, Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import cache

from wiehr import settings
from .models import *
from .email_utils import send_team_campaign, send_license_email


def classified_page(request, *args, **kwargs):
    context = {
        'site_url_nodashed': settings.SITE_URL_NODASHED,
    }
    return render(request, 'classified.html', context)


def inactive_redirect(request, *args, **kwargs):
    return classified_page(request)


def index(request):
    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/'
        target_url = f'{canonical_base}/'
        if current_url != target_url:
            return redirect(target_url)

    accept = request.META.get('HTTP_ACCEPT', '')
    if 'text/markdown' in accept:
        return _serve_markdown_index(request)

    context = {
        'site_url_nodashed': settings.SITE_URL_NODASHED,
        'visible_listeners': Team.objects.filter(
            is_disconnected=False, is_blacklist=False, country__isnull=False
        ).exclude(country='').count(),
    }

    return render(request, 'entities/index.html', context)


def archive_page(request):
    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/archive'
        target_url = f'{canonical_base}/archive'
        if current_url != target_url:
            return redirect(target_url)

    archives = list(WiehrArchiveModel.objects.filter(is_visible=True).order_by('year'))

    page_size = 10
    archive_pages = [archives[i:i + page_size] for i in range(0, len(archives), page_size)] or [[]]

    context = {
        'archives': archives,
        'archive_pages': archive_pages,
        'media_full': settings.MEDIA_FULL,
        'site_url_nodashed': settings.SITE_URL_NODASHED
    }

    return render(request, 'entities/archive.html', context)


def archive_object_page(request, slug):
    archive = WiehrArchiveModel.objects.filter(year=slug, is_visible=True).first()
    if not archive:
        raise Http404("No archive for that year")

    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/archive/{slug}'
        target_url = f'{canonical_base}/archive/{slug}'
        if current_url != target_url:
            return redirect(target_url)

    globe_items = WiehrGlobeModel.objects.filter(
        is_visible=True, year=archive.year,
    ).order_by('-date', '-order')
    atlas_items = WiehrAtlasModel.objects.filter(
        is_visible=True, year=archive.year,
    ).order_by('-created_at', '-order')
    lab_items = WiehrLabModel.objects.filter(
        Q(start_year=archive.year) | Q(extra_archives=archive),
        is_visible=True,
    ).distinct().order_by('-created_at', '-order')
    storage_items = WiehrStorageModel.objects.filter(
        is_visible=True, year=archive.year,
    ).order_by('-created_at', '-order')

    groups = [
        ('GLOBE', 'images/entities/globe.svg', [
            {'url': f'/globe/{i.slug}', 'number': i.internal_id, 'title': i.title}
            for i in globe_items
        ]),
        ('ATLAS', 'images/entities/atlas.svg', [
            {'url': f'/atlas/{i.internal_id}', 'number': i.internal_id, 'title': i.country_title}
            for i in atlas_items
        ]),
        ('STORAGE', 'images/entities/storage.svg', [
            {'url': f'/storage/{i.slug}', 'number': i.internal_id, 'title': i.title}
            for i in storage_items
        ]),
        ('LAB', 'images/entities/lab.svg', [
            {'url': f'/lab/{i.slug}', 'number': i.internal_id, 'title': i.title}
            for i in lab_items
        ]),
    ]

    context = {
        'archive': archive,
        'globe_items': globe_items,
        'atlas_items': atlas_items,
        'lab_items': lab_items,
        'storage_items': storage_items,
        'sections': _archive_object_sections(groups),
        'has_items': any(items for _, _, items in groups),
        'media_full': settings.MEDIA_FULL,
        'site_url_nodashed': settings.SITE_URL_NODASHED,
    }
    return render(request, 'objects/archive_object.html', context)


def _archive_object_sections(groups, per_section=10):
    """Split a year's items into sections of `per_section`, keeping the tree.

    Rows are either a group header or an item. When a group straddles a
    section boundary its header repeats at the top of the next section, so
    each section still reads as a complete tree rather than orphaned leaves.
    """
    sections = []
    current = []
    count = 0

    for label, icon, items in groups:
        if not items:
            continue
        current.append({'is_header': True, 'label': label, 'icon': icon})
        for item in items:
            if count == per_section:
                sections.append(current)
                current = [{'is_header': True, 'label': label, 'icon': icon}]
                count = 0
            current.append({'is_header': False, **item})
            count += 1

    if any(not row['is_header'] for row in current):
        sections.append(current)
    return sections


def globe_page(request):
    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/globe'
        target_url = f'{canonical_base}/globe'
        if current_url != target_url:
            return redirect(target_url)

    releases_with_geo = WiehrGlobeModel.objects.filter(
        is_visible=True,
        geo__isnull=False,
        release_type='W'
    ).exclude(geo='').order_by('internal_id')

    all_releases = WiehrGlobeModel.objects.filter(is_visible=True).order_by('-internal_id')

    context = {
        'releases': releases_with_geo,
        'all_releases': all_releases,
        'media_full': settings.MEDIA_FULL,
        'site_url_nodashed': settings.SITE_URL_NODASHED
    }

    return render(request, 'entities/globe.html', context)


def globe_object_page(request, slug):
    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/globe/{slug}'
        target_url = f'{canonical_base}/globe/{slug}'
        if current_url != target_url:
            return redirect(target_url)

    release = WiehrGlobeModel.objects.filter(slug=slug).first()
    if release and release.is_visible:
        credits_by_artist = release.get_credits_by_artist()
        inverted_color = invert_hex_color(release.background_color) if release.background_color else '#FFFFFF'
        inverted_text_color = invert_hex_color(release.background_color)

        context = {
            'release': release,
            'credits_by_artist': credits_by_artist,
            'inverted_color': inverted_color,
            'inverted_text_color': inverted_text_color,
            'media_full': settings.MEDIA_FULL,
            'site_url_nodashed': settings.SITE_URL_NODASHED,
        }

        return render(request, 'objects/globe_object.html', context)

    return redirect("/")


def atlas_page(request):
    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/atlas'
        target_url = f'{canonical_base}/atlas'
        if current_url != target_url:
            return redirect(target_url)

    atlas_objects = WiehrAtlasModel.objects.filter(is_visible=True).prefetch_related('images')

    atlas_data = []
    for atlas_object in atlas_objects:
        atlas_data.append({
            'id': atlas_object.id,
            'internal_id': atlas_object.internal_id,
            'country': atlas_object.country_title,
            'country_code': atlas_object.country_code.lower(),
            'coordinates': atlas_object.coordinates,
            'images_count': atlas_object.images.count(),
            'url': atlas_object.get_absolute_url(),
        })

    context = {
        'atlas_objects': atlas_objects,
        'atlas_data': atlas_data,
        'site_url_nodashed': settings.SITE_URL_NODASHED,
        'media_full': settings.MEDIA_FULL,
    }
    return render(request, 'entities/atlas.html', context)


def atlas_object_page(request, internal_id):
    from django.shortcuts import get_object_or_404

    atlas_object = get_object_or_404(
        WiehrAtlasModel,
        internal_id__iexact=internal_id,
        is_visible=True
    )

    images = atlas_object.images.order_by('order')

    context = {
        'atlas_object': atlas_object,
        'images': images,
        'site_url_nodashed': settings.SITE_URL_NODASHED,
        'media_full': settings.MEDIA_FULL,
    }
    return render(request, 'objects/atlas_object.html', context)


def lab_page(request):
    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/lab'
        target_url = f'{canonical_base}/lab'
        if current_url != target_url:
            return redirect(target_url)

    lab_list = WiehrLabModel.objects.filter(
        is_visible=True
    ).prefetch_related('links').order_by('-order', 'start_year')

    section_size = 5
    sections = []
    current_section = []
    for i, item in enumerate(lab_list):
        current_section.append(item)
        if len(current_section) == section_size:
            sections.append(current_section)
            current_section = []
    if current_section:
        sections.append(current_section)

    context = {
        'lab': lab_list,
        'sections': sections,
        'media_full': settings.MEDIA_FULL,
        'site_url_nodashed': settings.SITE_URL_NODASHED
    }

    return render(request, 'entities/lab.html', context)


def lab_object_page(request, slug):
    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/lab/{slug}'
        target_url = f'{canonical_base}/lab/{slug}'
        if current_url != target_url:
            return redirect(target_url)

    lab_object = WiehrLabModel.objects.prefetch_related(
        'links'
    ).filter(slug=slug).first()
    if lab_object:
        context = {
            'lab_object': lab_object,
            'media_full': settings.MEDIA_FULL,
            'site_url_nodashed': settings.SITE_URL_NODASHED
        }

        return render(request, 'objects/lab_object.html', context)
    else:
        return redirect("/")


def storage_page(request):
    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/storage'
        target_url = f'{canonical_base}/storage'
        if current_url != target_url:
            return redirect(target_url)

    storage_items = WiehrStorageModel.objects.filter(is_visible=True).order_by('order', 'created_at')

    total_cells = 25
    filled_ids = {item.internal_id: item for item in storage_items}
    grid_cells = []
    for i in range(total_cells):
        cell_id = f"S{i:03d}"
        if cell_id in filled_ids:
            item = filled_ids[cell_id]
            grid_cells.append({
                'id': cell_id,
                'slug': item.slug,
                'filled': True,
                'locked': item.access_type == 'password',
                'cover': item.cover_image.url if item.cover_image else '',
                'price': item.price_display,
            })
        else:
            grid_cells.append({'id': cell_id, 'filled': False})

    context = {
        'storage_list': storage_items,
        'grid_cells': grid_cells,
        'media_full': settings.MEDIA_FULL,
        'site_url_nodashed': settings.SITE_URL_NODASHED
    }

    return render(request, 'entities/storage.html', context)


def storage_object_page(request, slug):
    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/storage/{slug}'
        target_url = f'{canonical_base}/storage/{slug}'
        if current_url != target_url:
            return redirect(target_url)

    storage_obj = WiehrStorageModel.objects.filter(slug=slug, is_visible=True).first()
    if not storage_obj:
        return redirect("/storage")

    password_required = False
    license_key_required = False
    license_unlocked = False
    just_unlocked = False
    auto_issue_required = False
    auto_issue_unlocked = False
    access_granted = False
    error_message = None
    legal_name_value = ''
    email_value = ''

    needs_password = storage_obj.access_type in ('password', 'auto_issue_password')

    if needs_password:
        if request.method == 'POST' and 'password' in request.POST:
            entered_password = request.POST.get('password', '')
            if storage_obj.is_accessible(entered_password):
                access_granted = True
                request.session[f'storage_access_{storage_obj.id}'] = True
            else:
                error_message = 'Incorrect password'
                password_required = True
        elif request.session.get(f'storage_access_{storage_obj.id}'):
            access_granted = True
        else:
            password_required = True
    else:
        access_granted = True

    if storage_obj.access_type == 'license_key':
        license_key_required = True
        license_unlocked = bool(request.session.get(f'storage_license_unlock_{storage_obj.id}'))

        if request.method == 'POST' and 'license_key' in request.POST:
            entered_key = request.POST.get('license_key', '').strip()
            valid = License.objects.filter(
                license_key=entered_key, product_storage=storage_obj, is_active=True
            ).exists()
            if valid:
                license_unlocked = True
                just_unlocked = True
                request.session[f'storage_license_unlock_{storage_obj.id}'] = True
                # The key itself, not just the fact of it: the unlocked panel
                # links to /licensing?key=... so the buyer can pull their own
                # agreement, and that needs the actual value back.
                request.session[f'storage_license_key_{storage_obj.id}'] = entered_key
            else:
                error_message = 'Invalid or inactive license key for this item.'

    if storage_obj.access_type in ('auto_issue', 'auto_issue_password'):
        auto_issue_required = True
        auto_issue_unlocked = bool(request.session.get(f'storage_autoissue_unlock_{storage_obj.id}'))

        if access_granted and not auto_issue_unlocked and request.method == 'POST' and 'legal_name' in request.POST:
            legal_name_value = request.POST.get('legal_name', '').strip()
            email_value = request.POST.get('email', '').strip()

            if not legal_name_value:
                error_message = 'Please enter your legal name.'
            else:
                try:
                    validate_email(email_value)
                except ValidationError:
                    error_message = 'Please enter a valid email address.'

            if not error_message:
                if not storage_obj.auto_issue_license_type:
                    error_message = 'This item is not configured for auto-issue licensing yet. Contact hello@wiehr.cc.'
                else:
                    issued_license = License.objects.create(
                        license_type=storage_obj.auto_issue_license_type,
                        product_storage=storage_obj,
                        licensee_name=legal_name_value,
                        licensee_email=email_value,
                    )
                    auto_issue_unlocked = True
                    request.session[f'storage_autoissue_unlock_{storage_obj.id}'] = True
                    try:
                        send_license_email(issued_license)
                    except Exception:
                        logging.getLogger(__name__).exception('Failed to send license email for %s', issued_license.internal_id)

    download_locked = (license_key_required and not license_unlocked) or (auto_issue_required and not auto_issue_unlocked)

    license_key_value = request.session.get(f'storage_license_key_{storage_obj.id}', '') if license_unlocked else ''

    storage_links = storage_obj.links.all() if access_granted else []

    context = {
        'storage_object': storage_obj,
        'storage_links': storage_links,
        'access_granted': access_granted,
        'password_required': password_required,
        'license_key_required': license_key_required,
        'license_unlocked': license_unlocked,
        'license_key_value': license_key_value,
        'just_unlocked': just_unlocked,
        'auto_issue_required': auto_issue_required,
        'auto_issue_unlocked': auto_issue_unlocked,
        'download_locked': download_locked,
        'legal_name_value': legal_name_value,
        'email_value': email_value,
        'error_message': error_message,
        'media_full': settings.MEDIA_FULL,
        'site_url_nodashed': settings.SITE_URL_NODASHED
    }

    return render(request, 'objects/storage_object.html', context)


def storage_preview_download(request, slug):
    """The free sample. Deliberately ungated.

    The whole point of the preview is that someone who has not paid, not
    written to anyone and not been issued a key can still hear the thing, so
    this checks nothing except that a preview file exists. It does not touch
    download_count either - that counts sales of the real file.
    """
    storage_obj = WiehrStorageModel.objects.filter(slug=slug, is_visible=True).first()
    if not storage_obj or not storage_obj.preview_file:
        return redirect("/storage")

    return FileResponse(
        storage_obj.preview_file.open('rb'),
        as_attachment=True,
        filename=storage_obj.preview_file.name.split('/')[-1],
    )


def storage_download(request, slug):
    storage_obj = WiehrStorageModel.objects.filter(slug=slug, is_visible=True).first()
    if not storage_obj:
        return redirect("/storage")

    if storage_obj.access_type in ('password', 'auto_issue_password'):
        if not request.session.get(f'storage_access_{storage_obj.id}'):
            return redirect(f"/storage/{slug}")

    if storage_obj.access_type == 'license_key':
        if not request.session.get(f'storage_license_unlock_{storage_obj.id}'):
            return redirect(f"/storage/{slug}")

    if storage_obj.access_type in ('auto_issue', 'auto_issue_password'):
        if not request.session.get(f'storage_autoissue_unlock_{storage_obj.id}'):
            return redirect(f"/storage/{slug}")

    if storage_obj.file:
        storage_obj.download_count += 1
        storage_obj.save(update_fields=['download_count'])

        return FileResponse(storage_obj.file.open('rb'), as_attachment=True, filename=storage_obj.file.name.split('/')[-1])

    return redirect(f"/storage/{slug}")


PROFILE_VERSIONS = {
    'engineer': {
        'path': '/engineer',
        'kind': 'Engineer',
        'name': 'Yauheni (Eugene) Kandratovich',
        'headline': 'Lead Software Engineer | Python • AWS • DevOps • AI',
        'subject': 'Engineer',
        'paper_label': 'Professional CV (Resume)',
        'rates': [
            ('Backend / API Dev', '$60/hr'),
            ('ETL / Data Pipelines', '$65/hr'),
            ('AWS / DevOps', '$70/hr'),
            ('Custom Projects', 'quote on scope'),
        ],
    },
    'composer': {
        'path': '/composer',
        'kind': 'Composer',
        'name': 'Wiehr',
        'headline': 'Music Composer / Sound Designer / Production / Mixing / Mastering',
        'subject': 'Composer',
        'paper_label': 'One-pager',
        'rates': [
            ('Composition / Scoring', 'from $150/track'),
            ('Mixing', 'from $80/track'),
            ('Mastering', 'from $30/track'),
            ('Sound Design', '$35/hr (2hr min)'),
        ],
    },
}

ARTIST_BIO = (
    "Wiehr is a pseudonymous Belarus-born electronic composer and multidisciplinary "
    "artist creating cinematic, ambient, and experimental music through a synthetic "
    "orchestra approach."
)


def _profile_page(request, version, template):
    config = PROFILE_VERSIONS[version]

    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}{config["path"]}'
        target_url = f'{canonical_base}{config["path"]}'
        if current_url != target_url:
            return redirect(target_url)

    profile = CVProfile.objects.filter(version=version).first()

    context = {
        'site_url_nodashed': settings.SITE_URL_NODASHED,
        'version': version,
        'config': config,
        'bio': (profile.bio if profile and profile.bio else ARTIST_BIO),
        'rates': config['rates'],
        'download_url': f'{config["path"]}/download',
    }
    return render(request, template, context)


def engineer_page(request):
    return _profile_page(request, 'engineer', 'entities/engineer.html')


def composer_page(request):
    return _profile_page(request, 'composer', 'entities/composer.html')


def engineer_download(request):
    return _profile_download(request, 'engineer')


def composer_download(request):
    return _profile_download(request, 'composer')






def _profile_download(request, version):
    import io
    from .cv_builder import get_cv_pdf, get_cv_docx, get_cv_txt

    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '0')
    minute_key = f"cv_dl_min_{ip}"
    hour_key = f"cv_dl_hr_{ip}"
    minute_count = cache.get(minute_key, 0)
    hour_count = cache.get(hour_key, 0)
    if minute_count >= 5 or hour_count >= 15:
        return HttpResponse("Rate limited. Try again later.", status=429, content_type="text/plain")
    cache.set(minute_key, minute_count + 1, timeout=60)
    cache.set(hour_key, hour_count + 1, timeout=3600)

    fmt = request.GET.get('fmt', 'pdf')

    current_date = datetime.datetime.now().strftime("%d-%m-%Y")
    name_slug = "Yauheni-Kandratovich"

    if fmt == 'docx':
        docx_bytes = get_cv_docx(version)
        if not docx_bytes:
            return HttpResponse("CV not found. Please configure it in admin.", status=404)
        filename = f"CV_{name_slug}_{version}@{current_date}.docx"
        return FileResponse(
            io.BytesIO(docx_bytes),
            as_attachment=True,
            filename=filename,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    elif fmt == 'txt':
        txt_content = get_cv_txt(version)
        if not txt_content:
            return HttpResponse("CV not found. Please configure it in admin.", status=404)
        filename = f"CV_{name_slug}_{version}@{current_date}.txt"
        return FileResponse(
            io.BytesIO(txt_content.encode('utf-8')),
            as_attachment=True,
            filename=filename,
            content_type="text/plain; charset=utf-8",
        )
    else:
        pdf_bytes = get_cv_pdf(version)
        if not pdf_bytes:
            return HttpResponse("CV not found. Please configure it in admin.", status=404)
        filename = f"CV_{name_slug}_{version}@{current_date}.pdf"
        return FileResponse(
            io.BytesIO(pdf_bytes),
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )


def favicon(request):
    path = request.path.split('/')[1]

    mime_types = {
        'favicon-16x16.png': 'image/png',
        'favicon-48x48.png': 'image/png',
        'favicon-96x96.png': 'image/png',
        'favicon.png': 'image/png',
        'favicon.svg': 'image/svg+xml',
        'favicon.ico': 'image/x-icon',
        'apple-touch-icon.png': 'image/png',
        'site.webmanifest': 'application/manifest+json',
        'web-app-manifest-192x192.png': 'image/png',
        'web-app-manifest-512x512.png': 'image/png',
    }

    try:
        file_path = settings.BASE_DIR / 'web' / settings.STATIC_URL / f'favicon/{path}'
        file = file_path.open("rb")

        response = FileResponse(file)

        if path in mime_types:
            response['Content-Type'] = mime_types[path]

        response['Cache-Control'] = 'public, max-age=31536000, immutable'

        return response
    except Exception:
        return redirect("/")


def whoareyou_page(request):
    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/whoareyou'
        target_url = f'{canonical_base}/whoareyou'
        if current_url != target_url:
            return redirect(target_url)

    context = {
        'site_url_nodashed': settings.SITE_URL_NODASHED,
    }
    return render(request, 'entities/whoareyou.html', context)


def license_page(request):
    if os.environ.get('ENV') != 'DEV':
        canonical_base = get_canonical_base()
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        current_url = f'{scheme}://{host}/licensing'
        target_url = f'{canonical_base}/licensing'
        if current_url != target_url:
            return redirect(target_url)

    raw_key = (request.GET.get('key') or '').strip()
    result = None
    error = None

    if raw_key:
        licence = License.objects.select_related(
            'license_type', 'product_storage'
        ).filter(license_key=raw_key).first()

        if not licence:
            error = 'No license found for that key.'
        elif not licence.is_active:
            error = 'This license has been revoked.'
        else:
            result = licence

    context = {
        'site_url_nodashed': settings.SITE_URL_NODASHED,
        'raw_key': raw_key,
        'result': result,
        'error': error,
    }
    return render(request, 'entities/license.html', context)


def license_download(request, license_key):
    import io as _io
    from .license_builder import build_agreement_docx, build_agreement_pdf, build_agreement_text

    licence = License.objects.select_related('license_type', 'product_storage').filter(
        license_key=license_key.strip()
    ).first()
    if not licence or (not licence.is_active and not request.user.is_staff):
        return redirect('/licensing')

    fmt = request.GET.get('fmt', 'pdf')
    filename_base = f"WIEHR_LICENSE_{licence.internal_id}"

    if fmt == 'txt':
        return FileResponse(
            _io.BytesIO(build_agreement_text(licence).encode('utf-8')),
            as_attachment=True,
            filename=f"{filename_base}.txt",
            content_type='text/plain; charset=utf-8',
        )
    if fmt == 'docx':
        return FileResponse(
            _io.BytesIO(build_agreement_docx(licence)),
            as_attachment=True,
            filename=f"{filename_base}.docx",
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )
    return FileResponse(
        _io.BytesIO(build_agreement_pdf(licence)),
        as_attachment=True,
        filename=f"{filename_base}.pdf",
        content_type='application/pdf',
    )


SHORTENER_SESSION_KEY = 'shortener_authed'


def shortener_page(request):
    settings_row = ShortenerSettings.load()

    authed = request.session.get(SHORTENER_SESSION_KEY) is True

    created = None
    error = None
    gate_error = None

    if request.method == 'POST' and not authed:
        password = (request.POST.get('password') or '').strip()

        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '0')
        attempts_key = f'shortener_attempts_{ip}'
        attempts = cache.get(attempts_key, 0)

        if attempts >= 20:
            gate_error = 'Too many attempts. Try again later.'
        elif password != settings_row.password:
            cache.set(attempts_key, attempts + 1, timeout=900)
            gate_error = 'Wrong password.'
        else:
            cache.delete(attempts_key)
            request.session[SHORTENER_SESSION_KEY] = True
            return redirect('/s')

    elif request.method == 'POST':
        long_url = (request.POST.get('long_url') or '').strip()
        name = (request.POST.get('name') or '').strip()

        code = ''
        if not error:
            code, error = normalize_short_code(name)

        if not error and not long_url:
            error = 'Give me a URL.'

        if not error:
            try:
                URLValidator(schemes=['http', 'https'])(long_url)
            except ValidationError:
                error = 'That is not a valid http(s) URL.'

        if not error:
            if code:
                taken = Shortener.objects.filter(short_url__iexact=code).first()
                if taken and taken.long_url != long_url:
                    error = f'The name {code} already points somewhere else.'
                else:
                    created = taken or Shortener.objects.create(
                        long_url=long_url, short_url=code
                    )
            else:
                existing = Shortener.objects.filter(long_url=long_url).first()
                created = existing or Shortener.objects.create(long_url=long_url)

    context = {
        'site_url_nodashed': settings.SITE_URL_NODASHED,
        'created': created,
        'error': error,
        'gate_error': gate_error,
        'authed': authed,
        'recent': Shortener.objects.order_by('-created_at')[:5] if created else [],
    }
    return render(request, 'entities/shortener.html', context)


def short_redirect(request, short_url):
    shortener = Shortener.objects.filter(short_url__iexact=short_url).first()
    if not shortener:
        return redirect('/')

    Shortener.objects.filter(pk=shortener.pk).update(times_followed=F('times_followed') + 1)
    return redirect(shortener.long_url)


@staff_member_required
def generate_qr(request, pk):
    from .qrcode.qr_generator import generate_qr_svg

    qr_code = QrCode.objects.filter(pk=pk).first()
    if not qr_code:
        raise Http404('QR Code not found')

    svg_content = generate_qr_svg(qr_code.link, qr_code.get_config())
    response = HttpResponse(svg_content, content_type='image/svg+xml')
    response['Content-Disposition'] = f'attachment; filename="{qr_code.object_id}.svg"'
    return response


@staff_member_required
def generate_print_view(request, pk):
    qr_code = QrCode.objects.filter(pk=pk).first()
    if not qr_code:
        raise Http404('QR Code not found')

    try:
        pdf_path = qr_code.generate_print()
        with open(pdf_path, 'rb') as handle:
            pdf_data = handle.read()
        pdf_path.unlink()
    except Exception as exc:
        return HttpResponse(f'Error generating print: {exc}', status=500)

    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="print_{qr_code.wid or qr_code.object_id}.pdf"'
    return response


def privacy_page(request):
    context = {
        'site_url_nodashed': settings.SITE_URL_NODASHED,
    }
    return render(request, 'legal/privacy.html', context)


def terms_page(request):
    context = {
        'site_url_nodashed': settings.SITE_URL_NODASHED,
    }
    return render(request, 'legal/terms.html', context)


def support_page(request):
    context = {
        'site_url_nodashed': settings.SITE_URL_NODASHED,
    }
    return render(request, 'entities/support.html', context)



def disconnect(request, token=None):
    from django.utils import timezone
    email_prefill = request.GET.get('email', '').strip()
    subscription = None
    message = None

    if token:
        try:
            subscription = Team.objects.get(disconnect_token=token)
            subscription.is_disconnected = True
            subscription.disconnected_at = timezone.now()
            subscription.save()
            message = "You have been disconnected."
        except Team.DoesNotExist:
            message = "Invalid disconnection link."
    else:
        if request.method == 'POST':
            email = request.POST.get('email', '').strip().lower()
            if email:
                try:
                    subscription = Team.objects.get(email=email)
                    subscription.is_disconnected = True
                    subscription.disconnected_at = timezone.now()
                    subscription.save()
                    message = "You have been disconnected."
                except Team.DoesNotExist:
                    message = "Email not found in our list."
            else:
                message = "Provide your email address."

    if subscription and subscription.is_disconnected:
        show_form = False
    else:
        show_form = token is None

    context = {
        'site_url_nodashed': settings.SITE_URL_NODASHED,
        'message': message,
        'show_form': show_form,
        'email_prefill': email_prefill,
    }
    return render(request, 'entities/disconnect.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_subscribe(request):
    import json
    import uuid

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    email = (data.get('email') or '').strip().lower()
    country = (data.get('country') or '').strip()
    country_code = (data.get('country_code') or '').strip().upper()[:2]

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'error': 'Invalid email'}, status=400)

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
    cache_key = f"sub_api_{ip}"
    if cache.get(cache_key) is False:
        return JsonResponse({'error': 'Too many requests'}, status=429)

    subscription, created = Team.objects.get_or_create(email=email)

    if subscription.is_disconnected:
        subscription.is_disconnected = False
        subscription.disconnected_at = None

    if country:
        subscription.country = country
    if country_code:
        subscription.country_code = country_code

    if created:
        subscription.disconnect_token = str(uuid.uuid4())

    subscription.save()
    cache.set(cache_key, True, 30)
    cache.delete("network_locations_v1")

    if created:
        try:
            from .email_utils import send_team_campaign
            send_team_campaign(
                subject="hello.",
                title="thank you.",
                body='<span style="opacity:0.25;"># </span><span style="opacity:0.3;">C</span><span style="opacity:0.35;">o</span><span style="opacity:0.4;">n</span><span style="opacity:0.45;">n</span><span style="opacity:0.5;">e</span><span style="opacity:0.55;">c</span><span style="opacity:0.6;">t</span><span style="opacity:0.65;">i</span><span style="opacity:0.7;">n</span><span style="opacity:0.75;">g</span><span style="opacity:0.8;">...</span>\n\nYou have been connected.\n\n<b> See you soon.</b>',
                queryset=Team.objects.filter(pk=subscription.pk),
            )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error("Failed to send welcome email to %s: %s", email, exc)

    return JsonResponse({
        'message': 'You are visible now.',
        'visible_listeners': Team.objects.filter(
            is_disconnected=False, is_blacklist=False, country__isnull=False
        ).exclude(country='').count(),
    })


@require_http_methods(["GET"])
def api_network_locations(request):
    cache_key = "network_locations_v1"
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse(cached, safe=False)

    from django.db.models import Count
    locations = (
        Team.objects
        .filter(is_disconnected=False, is_blacklist=False, country__isnull=False)
        .exclude(country='')
        .values('country', 'country_code')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    result = [
        {'country': loc['country'], 'code': loc['country_code'] or '', 'count': loc['count']}
        for loc in locations
    ]
    cache.set(cache_key, result, 300)
    return JsonResponse(result, safe=False)


SEO_EXCLUDED_PATHS = {
    '/disconnect', '/admin',
    '/ads.txt', '/robots.txt', '/sitemap.xml', '/llms.txt',
    '/s',
}

SEO_ASSET_PREFIXES = ('/static/', '/media/')

SEO_ALLOWED_ASSET_PATHS = ('/static/css/', '/static/js/', '/static/font/', '/media/')
SEO_DISALLOWED_PATHS = (
    '/admin/', '/api/', '/s/', '/disconnect/',
    '/static/favicon/', '/static/images/platforms/',
)

SEO_EXCLUDED_SUFFIXES = ('/download',)

SEO_BOT_RULES = {
    'Nutch':           {'allow': [], 'disallow': ['/'], 'crawl_delay': None},
    'adsbot-google':   {'allow': ['/'], 'disallow': None, 'crawl_delay': None},
    'AhrefsBot':       {'allow': ['/'], 'disallow': None, 'crawl_delay': 10},
    'AhrefsSiteAudit': {'allow': ['/'], 'disallow': None, 'crawl_delay': 10},
    'MJ12bot':         {'allow': ['/'], 'disallow': None, 'crawl_delay': 10},
    'Pinterest':       {'allow': ['/'], 'disallow': None, 'crawl_delay': 1},
}

SEO_AI_BOTS = (
    'GPTBot', 'ChatGPT-User', 'OAI-SearchBot',
    'Google-Extended', 'GoogleOther',
    'anthropic-ai', 'Claude-Web', 'ClaudeBot',
    'CCBot', 'Bytespider', 'Diffbot',
    'FacebookBot', 'PerplexityBot',
    'Applebot-Extended', 'Applebot',
    'cohere-ai', 'YouBot', 'Amazonbot',
)


def seo_public_paths():
    """Static, parameter-free routes that are safe to advertise to crawlers.

    Derived from the URLconf so robots.txt and the sitemap track the real
    routes automatically — adding or removing a page needs no other edit.
    """
    from django.urls import URLPattern, URLResolver, get_resolver

    paths = []

    def walk(patterns, prefix=''):
        for entry in patterns:
            route = str(getattr(entry.pattern, '_route', '') or '')
            if isinstance(entry, URLResolver):
                walk(entry.url_patterns, prefix + route)
                continue
            if not isinstance(entry, URLPattern):
                continue
            full = prefix + route
            if '<' in full:  # parameterised, e.g. archive/<slug>
                continue
            path = _seo_normalise_path('/' + full.lstrip('/'))
            if path in paths:
                continue
            if path.startswith(SEO_DISALLOWED_PATHS):
                continue
            if path.endswith(SEO_EXCLUDED_SUFFIXES):
                continue
            if not _seo_path_is_live(path):
                continue
            paths.append(path)

    walk(get_resolver().url_patterns)
    return sorted(paths, key=lambda p: (p != '/', p))


def _seo_normalise_path(url):
    from urllib.parse import urlparse

    path = urlparse(url).path or '/'
    path = path.rstrip('/')
    return path or '/'


def _seo_path_is_live(path):
    from django.urls import Resolver404, resolve

    if path in SEO_EXCLUDED_PATHS:
        return False
    try:
        resolve(path)
    except Resolver404:
        return False
    return True


def robots_txt(request):
    """Generated from the URLconf — no database rows involved."""
    public_paths = seo_public_paths()
    wildcard_allow = public_paths + list(SEO_ALLOWED_ASSET_PATHS)
    wildcard_disallow = list(SEO_DISALLOWED_PATHS)

    groups = [('*', {'allow': wildcard_allow,
                     'disallow': wildcard_disallow,
                     'crawl_delay': None})]

    for agent, rule in SEO_BOT_RULES.items():
        groups.append((agent, {
            'allow': rule['allow'],
            'disallow': wildcard_disallow if rule['disallow'] is None else rule['disallow'],
            'crawl_delay': rule['crawl_delay'],
        }))

    for bot in SEO_AI_BOTS:
        groups.append((bot, {
            'allow': ['/', '/llms.txt'],
            'disallow': wildcard_disallow,
            'crawl_delay': None,
        }))

    lines = []
    for agent, group in groups:
        lines.append(f'User-agent: {agent}')
        for path in group['allow']:
            lines.append(f'Allow: {path}')
        for path in group['disallow']:
            lines.append(f'Disallow: {path}')
        if group['crawl_delay']:
            lines.append(f'Crawl-delay: {group["crawl_delay"]}')
        lines.append('')

    lines.append(f'Sitemap: {get_canonical_base()}/sitemap.xml')

    content = '\n'.join(lines).strip() + '\n'

    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['X-Content-Type-Options'] = 'nosniff'
    response['X-Robots-Tag'] = 'noindex'
    response['Cache-Control'] = 'public, max-age=86400'

    return response


def sitemap_xml(request):
    import xml.etree.ElementTree as ET
    
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

    seen_paths = set()

    def add_url(loc, changefreq, priority, lastmod=None):
        path = _seo_normalise_path(loc)
        if path in seen_paths or not _seo_path_is_live(path):
            return
        seen_paths.add(path)

        url_elem = ET.SubElement(urlset, 'url')
        ET.SubElement(url_elem, 'loc').text = f'https://wiehr.cc{path}' if path != '/' else 'https://wiehr.cc/'
        if lastmod:
            ET.SubElement(url_elem, 'lastmod').text = lastmod
        ET.SubElement(url_elem, 'changefreq').text = changefreq
        ET.SubElement(url_elem, 'priority').text = priority

    static_pages = [
        {'loc': '/',          'changefreq': 'weekly',  'priority': '1.0'},
        {'loc': '/archive',   'changefreq': 'weekly',  'priority': '0.9'},
        {'loc': '/globe',     'changefreq': 'weekly',  'priority': '0.9'},
        {'loc': '/atlas',     'changefreq': 'weekly',  'priority': '0.9'},
        {'loc': '/storage',   'changefreq': 'weekly',  'priority': '0.9'},
        {'loc': '/lab',       'changefreq': 'weekly',  'priority': '0.9'},
        {'loc': '/composer',  'changefreq': 'monthly', 'priority': '0.9'},
        {'loc': '/engineer',  'changefreq': 'monthly', 'priority': '0.9'},
        {'loc': '/whoareyou', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': '/support',   'changefreq': 'monthly', 'priority': '0.6'},
        {'loc': '/licensing', 'changefreq': 'monthly', 'priority': '0.5'},
        {'loc': '/privacy',   'changefreq': 'yearly',  'priority': '0.3'},
        {'loc': '/terms',     'changefreq': 'yearly',  'priority': '0.3'},
    ]
    for page in static_pages:
        add_url(page['loc'], page['changefreq'], page['priority'])

    for archive in WiehrArchiveModel.objects.filter(is_visible=True).order_by('-year'):
        stamp = archive.modified_at or archive.created_at
        add_url(f'/archive/{archive.year}', 'monthly', '0.7', stamp.strftime('%Y-%m-%d'))

    for release in WiehrGlobeModel.objects.filter(is_visible=True, slug__isnull=False).order_by('-order', '-date'):
        stamp = release.date or release.created_at
        add_url(f'/globe/{release.slug}', 'monthly', '0.8', stamp.strftime('%Y-%m-%d'))

    for atlas_obj in WiehrAtlasModel.objects.filter(is_visible=True).order_by('-internal_id'):
        stamp = atlas_obj.modified_at or atlas_obj.created_at
        add_url(f'/atlas/{atlas_obj.internal_id}', 'monthly', '0.7', stamp.strftime('%Y-%m-%d'))

    for project in WiehrLabModel.objects.filter(is_visible=True).order_by('-order', '-start_year'):
        stamp = project.modified_at or project.created_at
        add_url(f'/lab/{project.slug}', 'yearly', '0.6', stamp.strftime('%Y-%m-%d'))

    # 'link' means "anyone with the URL" — i.e. deliberately unlisted, so it has
    # no more business in a sitemap than a password-gated item does.
    for storage_item in WiehrStorageModel.objects.filter(is_visible=True).exclude(
            access_type__in=('password', 'link')).order_by('-order'):
        stamp = storage_item.modified_at or storage_item.created_at
        add_url(f'/storage/{storage_item.slug}', 'monthly', '0.6', stamp.strftime('%Y-%m-%d'))

    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(urlset, encoding='unicode')
    
    response = HttpResponse(xml_str, content_type='application/xml; charset=utf-8')
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'public, max-age=3600'
    
    return response


def handler404(request, exception = None):
    context = {'site_url_nodashed': settings.SITE_URL_NODASHED}
    return render(request, 'classified.html', context, status=404)


def handler500(request, exception = None):
    """500 page. Must never raise — Django has no further fallback.

    classified.html extends the base layout and runs {% compress %}, either of
    which can fail in exactly the situations that cause a 500 (missing offline
    manifest, database down). So it is attempted first for the branded look,
    with a static template that inherits nothing as the backstop.
    """
    context = {'site_url_nodashed': getattr(settings, 'SITE_URL_NODASHED', '')}
    try:
        return render(request, 'classified.html', context, status=500)
    except Exception:
        try:
            from django.template.loader import render_to_string
            return HttpResponse(render_to_string('custom_500.html'), status=500)
        except Exception:
            return HttpResponse(
                '<!doctype html><meta charset="utf-8"><title>500</title>'
                '<p>Something broke on our side. Try again shortly.</p>',
                status=500, content_type='text/html; charset=utf-8',
            )


def ads_txt_view(request):
    content = "# No ads on this site\n"
    return HttpResponse(content, content_type='text/plain; charset=utf-8')


def llms_txt_view(request):
    file_path = settings.BASE_DIR / 'web' / 'static' / 'assets' / 'llms.txt'
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        response = HttpResponse(content, content_type='text/plain; charset=utf-8')
        response['Cache-Control'] = 'public, max-age=86400'
        response['X-Robots-Tag'] = 'noindex'
        return response
    except Exception:
        return HttpResponse("# LLM indexing file", content_type='text/plain; charset=utf-8')


def _serve_markdown_index(request):
    file_path = settings.BASE_DIR / 'web' / 'static' / 'assets' / 'llms.txt'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        content = '# Wiehr. Official Website\n\nWiehr is a pseudonymous Belarus-born electronic composer and multidisciplinary artist creating cinematic, ambient, and experimental music through a synthetic orchestra approach.'
    response = HttpResponse(content, content_type='text/markdown; charset=utf-8')
    response['Cache-Control'] = 'public, max-age=86400'
    return response


def get_canonical_base():
    if os.environ.get('ENV') == 'DEV':
        return 'http://127.0.0.1:8000'
    return 'https://wiehr.cc'


def invert_hex_color(hex_color):
    if not hex_color or not hex_color.startswith('#'):
        return '#000000'

    hex_color = hex_color.lstrip('#')

    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])

    if len(hex_color) != 6:
        return '#000000'

    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r_inv = 255 - r
        g_inv = 255 - g
        b_inv = 255 - b

        return f'#{r_inv:02x}{g_inv:02x}{b_inv:02x}'
    except ValueError:
        return '#000000'


def archive_refresh_api(request):
    import hashlib
    import json
    
    client_hash = request.GET.get('hash', '')
    
    archives = WiehrArchiveModel.objects.filter(is_visible=True)
    archive_data = []
    
    for archive in archives:
        archive.refresh_counts()
        archive.save()
        
        archive_data.append({
            'id': archive.internal_id,
            'year': archive.year,
            'total': archive.total_count,
            'globe': archive.globe_count,
            'atlas': archive.atlas_count,
            'lab': archive.lab_count,
            'storage': archive.storage_count,
        })
    
    data_string = json.dumps(archive_data, sort_keys=True)
    current_hash = hashlib.md5(data_string.encode()).hexdigest()[:12]
    
    if client_hash == current_hash:
        return JsonResponse({
            'updated': False,
            'hash': current_hash,
            'message': 'Archive is up to date'
        })
    
    return JsonResponse({
        'updated': True,
        'hash': current_hash,
        'archives': archive_data
    })

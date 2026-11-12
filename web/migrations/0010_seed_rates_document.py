# One-time data migration: seed the Rates document and its services.

from django.db import migrations


def seed_rates(apps, schema_editor):
    WiehrDocument = apps.get_model('web', 'WiehrDocument')
    RatesService = apps.get_model('web', 'RatesService')

    doc, _ = WiehrDocument.objects.get_or_create(
        version='rates',
        defaults={
            'name': 'Wiehr',
            'title': 'Rates & Commissions',
            'bio': (
                'Commissioned music production and software engineering '
                'for creative projects, businesses, and independent artists.'
            ),
            'email': 'hello@wiehr.cc',
            'website': 'wiehr.cc',
        },
    )

    services = [
        {
            'category': 'COMPOSER SERVICES',
            'name': 'Composition & Scoring',
            'description': (
                'Original music for films, games, theatre, dance, and media. '
                'Cinematic, ambient, and experimental electronic compositions '
                'built around a synthetic-orchestra approach. Credits include '
                'Warsaw Film School, physical theatre, and brand campaigns.'
            ),
            'rate': 'from \u20ac500',
            'order': 1,
        },
        {
            'category': 'COMPOSER SERVICES',
            'name': 'Mixing & Mastering',
            'description': (
                'Stereo mixing and mastering for streaming platforms (LUFS). '
                'Focus on clarity, depth, and consistent playback across systems.'
            ),
            'rate': 'from \u20ac100 / track',
            'order': 2,
        },
        {
            'category': 'COMPOSER SERVICES',
            'name': 'Sound Design',
            'description': (
                'Original sound design and synthesis for film, theatre, games, '
                'and interactive media. Ambient, cyberpunk, DnB, techno, Foley, '
                'field recording, and sound processing.'
            ),
            'rate': 'from \u20ac300',
            'order': 3,
        },
        {
            'category': 'ENGINEER SERVICES',
            'name': 'Website Development',
            'description': (
                'Custom websites with Django, interactive frontends, and CMS '
                'backends. WebGL visualizations, music distribution platforms, '
                'release management. Full cycle from design to deployment, '
                'including domain, hosting, and SSL.'
            ),
            'rate': 'from \u20ac1 500',
            'order': 4,
        },
        {
            'category': 'ENGINEER SERVICES',
            'name': 'Software Engineering',
            'description': (
                'Full-stack: Python (Django, Flask, FastAPI), React, REST/gRPC '
                'APIs. Backend/API dev, data pipelines, ETL, third-party '
                'integrations, Celery background processing. '
                '5+ years in production systems: e-commerce (5M+ products), '
                'ML pipelines, GDPR health-data platforms.'
            ),
            'rate': '\u20ac55 / h',
            'order': 5,
        },
        {
            'category': 'ENGINEER SERVICES',
            'name': 'Cloud & Infrastructure',
            'description': (
                'AWS design with Terraform, Kubernetes, Docker. Lambda, S3, '
                'ECS, RDS, VPC, IAM, CI/CD, Grafana, Prometheus. '
                'AWS Certified Solutions Architect & Cloud Practitioner. '
                'Reduced AWS costs by $100K/yr.'
            ),
            'rate': '\u20ac60 / h',
            'order': 6,
        },
    ]

    for svc in services:
        RatesService.objects.get_or_create(
            document=doc,
            name=svc['name'],
            defaults=svc,
        )


def reverse_rates(apps, schema_editor):
    WiehrDocument = apps.get_model('web', 'WiehrDocument')
    WiehrDocument.objects.filter(version='rates').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0009_wiehr_document_rates'),
    ]

    operations = [
        migrations.RunPython(seed_rates, reverse_rates),
    ]

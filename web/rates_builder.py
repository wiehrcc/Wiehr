import io
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from django.conf import settings

CACHE_DIR = Path(settings.BASE_DIR) / "media" / "rates" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_PATH = CACHE_DIR / "rates.pdf"

FONT_REGULAR = "Courier"
FONT_BOLD = "Courier-Bold"


def _wrap_text(text, font_name, font_size, max_width):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def build_rates_pdf():
    buf = io.BytesIO()
    w, h = A4
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle("Rates & Commissions \u2014 Wiehr")
    c.setAuthor("Wiehr")
    c.setSubject("Commission rates")

    margin = 22 * mm
    col_w = w - 2 * margin
    y = h - 28 * mm
    line_h = 3.8 * mm

    ink = (0, 0, 0)
    secondary = (0.20, 0.20, 0.20)

    def _check_page(needed=0):
        nonlocal y
        if y < 25 * mm + needed:
            c.showPage()
            y = h - 28 * mm

    def _text(text, size=8, bold=False, color=None):
        nonlocal y
        font = FONT_BOLD if bold else FONT_REGULAR
        clr = color or ink
        for ln in _wrap_text(text, font, size, col_w):
            _check_page()
            c.setFont(font, size)
            c.setFillColorRGB(*clr)
            c.drawString(margin, y, ln)
            y -= line_h

    def _heading(text, size=10):
        nonlocal y
        _check_page(8 * mm)
        c.setFont(FONT_BOLD, size)
        c.setFillColorRGB(*ink)
        c.drawString(margin, y, text)
        y -= 6 * mm

    def _sub(text, size=9.5):
        nonlocal y
        _check_page(6 * mm)
        c.setFont(FONT_BOLD, size)
        c.setFillColorRGB(*ink)
        c.drawString(margin, y, text)
        y -= 5 * mm

    def _gap(amount=6):
        nonlocal y
        y -= amount * mm

    def _line():
        nonlocal y
        c.saveState()
        c.setStrokeColorRGB(*secondary)
        c.setLineWidth(0.4)
        c.line(margin, y, w - margin, y)
        c.restoreState()

    c.setFont(FONT_BOLD, 18)
    c.setFillColorRGB(*ink)
    c.drawString(margin, y, "RATES & COMMISSIONS")
    y -= 8 * mm

    c.setFont(FONT_REGULAR, 8)
    c.setFillColorRGB(*secondary)
    c.drawString(margin, y, "wiehr.cc  \u00b7  hello@wiehr.cc")
    y -= 14 * mm

    _line()
    y -= 10 * mm

    _text("I offer commissioned music production and software engineering services for creative projects, businesses, and independent artists.", color=secondary)
    _gap(8)

    _heading("COMPOSER SERVICES")
    _gap(2)

    _sub("Composition & Scoring")
    _text("Original music for films, games, theatre, dance, and other media. Cinematic, ambient, and experimental electronic compositions built around a synthetic-orchestra approach.")
    _gap(2)
    _text("Selected credits include Warsaw Film School short films, physical theatre performances, and limited-edition brand campaigns.", color=secondary)
    _gap(2)
    _text("For an estimate, share your project concept, intended mood, track count, duration, and musical direction. We\u2019ll agree on a timeline, budget, regular check-ins, and revisions.", color=secondary)
    _gap(6)

    _sub("Mixing & Mastering")
    _text("Stereo mixing and mastering for independent artists, prepared for streaming platforms and their loudness standards (LUFS). Working in FL Studio, with a focus on clarity, depth, and consistent playback across systems.")
    _gap(6)

    _sub("Sound Design")
    _text("Original sound design and synthesis for film, theatre, games, and interactive media. Covering ambient, cyberpunk, dance, drum & bass, and techno, including Foley, field recording, and sound processing.")
    _gap(10)

    _heading("ENGINEER SERVICES")
    _gap(2)

    _sub("Website Development")
    _text("Custom websites built with Django, interactive frontends, and CMS backends. From portfolio websites with WebGL visualizations to music distribution platforms with release management, artist profiles, and content administration.")
    _gap(2)
    _text("Full development cycle, from design to deployment, including domain, hosting, and SSL configuration.", color=secondary)
    _gap(6)

    _sub("Software Engineering")
    _text("Full-stack development with Python (Django, Flask, FastAPI), React, and REST/gRPC APIs.")
    _gap(2)
    _text("Services include:", color=secondary)
    _text("\u2022  Backend and API development", color=secondary)
    _text("\u2022  Data pipelines and ETL systems", color=secondary)
    _text("\u2022  Third-party integrations", color=secondary)
    _text("\u2022  Background processing with Celery", color=secondary)
    _gap(2)
    _text("5+ years of experience building production systems, including e-commerce platforms managing 5M+ products, ML-based detection pipelines, and GDPR-compliant health-data platforms.", color=secondary)
    _gap(6)

    _sub("Cloud & Infrastructure")
    _text("AWS infrastructure design and implementation using Terraform, Kubernetes, and Docker.")
    _gap(2)
    _text("Experience with Lambda, S3, ECS, RDS, VPC, IAM, CI/CD, and monitoring with Grafana and Prometheus.", color=secondary)
    _gap(2)
    _text("AWS Certified Solutions Architect and Cloud Practitioner. Reduced annual AWS costs by $100K through infrastructure optimization and lifecycle policies.", color=secondary)
    _gap(10)

    _line()
    y -= 6 * mm
    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColorRGB(*secondary)
    c.drawString(margin, y, "For inquiries and project estimates:")
    y -= 4 * mm
    c.setFont(FONT_BOLD, 7.5)
    c.setFillColorRGB(*ink)
    c.drawString(margin, y, "hello@wiehr.cc  \u00b7  wiehr.cc/about")

    c.save()
    return buf.getvalue()


def get_rates_pdf():
    if CACHE_PATH.exists():
        return CACHE_PATH.read_bytes()
    pdf_bytes = build_rates_pdf()
    CACHE_PATH.write_bytes(pdf_bytes)
    return pdf_bytes


def invalidate_rates_cache():
    if CACHE_PATH.exists():
        CACHE_PATH.unlink()

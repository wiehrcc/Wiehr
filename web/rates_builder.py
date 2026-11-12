import io
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def _register_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from django.conf import settings
    font_dir = os.path.join(settings.BASE_DIR, 'web', 'static', 'font')
    segoe = os.path.join(font_dir, 'SegoeUI-Regular.ttf')
    segoe_b = os.path.join(font_dir, 'SegoeUI-Bold.ttf')
    try:
        pdfmetrics.getFont('SegoeUI')
    except KeyError:
        pdfmetrics.registerFont(TTFont('SegoeUI', segoe))
        pdfmetrics.registerFont(TTFont('SegoeUI-Bold', segoe_b))
    return 'SegoeUI', 'SegoeUI-Bold'


FONT_REGULAR, FONT_BOLD = _register_fonts()


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


def _get_rates_data():
    from .models import WiehrDocument
    try:
        doc = WiehrDocument.objects.prefetch_related('services').get(version='rates')
    except WiehrDocument.DoesNotExist:
        return None
    services = []
    for svc in doc.services.all():
        services.append({
            'category': svc.category,
            'name': svc.name,
            'description': svc.description,
            'rate': svc.rate,
        })
    return {
        'name': doc.name,
        'title': doc.title,
        'bio': doc.bio,
        'email': doc.email,
        'website': doc.website,
        'services': services,
    }


def build_rates_pdf(data=None):
    if data is None:
        data = _get_rates_data()
    if not data:
        return _build_fallback_pdf()

    buf = io.BytesIO()
    w, h = A4
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle("Rates & Commissions \u2014 Wiehr")
    c.setAuthor(data.get('name', 'Wiehr'))
    c.setSubject("Commission rates")

    margin = 20 * mm
    col_w = w - 2 * margin
    y = h - 22 * mm
    line_h = 4 * mm

    ink = (0, 0, 0)

    def _text(text, size=8.5, bold=False):
        nonlocal y
        font = FONT_BOLD if bold else FONT_REGULAR
        for ln in _wrap_text(text, font, size, col_w):
            c.setFont(font, size)
            c.setFillColorRGB(*ink)
            c.drawString(margin, y, ln)
            y -= line_h

    def _heading(text, size=10):
        nonlocal y
        y -= 2 * mm
        c.setFont(FONT_BOLD, size)
        c.setFillColorRGB(*ink)
        c.drawString(margin, y, text)
        y -= 5.5 * mm

    def _sub(text, rate='', size=9):
        nonlocal y
        c.setFont(FONT_BOLD, size)
        c.setFillColorRGB(*ink)
        c.drawString(margin, y, text)
        if rate:
            rate_w = c.stringWidth(rate, FONT_REGULAR, size - 1)
            c.setFont(FONT_REGULAR, size - 1)
            c.drawString(w - margin - rate_w, y, rate)
        y -= 4 * mm

    def _gap(amount=3):
        nonlocal y
        y -= amount * mm

    c.setFont(FONT_BOLD, 14)
    c.setFillColorRGB(*ink)
    c.drawString(margin, y, "RATES & COMMISSIONS")
    y -= 6 * mm

    contact = data.get('website', 'wiehr.cc')
    email = data.get('email', 'hello@wiehr.cc')
    c.setFont(FONT_REGULAR, 8)
    c.setFillColorRGB(*ink)
    contact_str = f"{contact}  \u00b7  {email}"
    c.drawString(margin, y, contact_str)
    c.linkURL(f"https://{contact}", (margin, y - 1, margin + c.stringWidth(contact, FONT_REGULAR, 8), y + 8), relative=0)
    c.linkURL(f"mailto:{email}", (margin + c.stringWidth(f"{contact}  \u00b7  ", FONT_REGULAR, 8), y - 1, w - margin, y + 8), relative=0)
    y -= 8 * mm

    if data.get('bio'):
        _text(data['bio'])
        _gap(5)

    current_category = None
    for svc in data['services']:
        if svc['category'] != current_category:
            current_category = svc['category']
            _heading(current_category)
        _sub(svc['name'], svc.get('rate', ''))
        _text(svc['description'])
        _gap(3)

    _gap(3)
    c.setFont(FONT_REGULAR, 8)
    c.setFillColorRGB(*ink)
    c.drawString(margin, y, "For inquiries and estimates:")
    y -= 4 * mm
    c.setFont(FONT_BOLD, 8)
    c.setFillColorRGB(*ink)
    footer_str = f"{email}  \u00b7  {contact}/about"
    c.drawString(margin, y, footer_str)
    c.linkURL(f"mailto:{email}", (margin, y - 1, margin + c.stringWidth(email, FONT_BOLD, 8), y + 8), relative=0)
    c.linkURL(f"https://{contact}/about", (margin + c.stringWidth(f"{email}  \u00b7  ", FONT_BOLD, 8), y - 1, w - margin, y + 8), relative=0)

    c.save()
    return buf.getvalue()


def _build_fallback_pdf():
    buf = io.BytesIO()
    w, h = A4
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle("Rates & Commissions \u2014 Wiehr")
    c.setFont(FONT_BOLD, 14)
    c.drawString(20 * mm, h - 30 * mm, "RATES & COMMISSIONS")
    c.setFont(FONT_REGULAR, 9)
    c.drawString(20 * mm, h - 40 * mm, "Please contact hello@wiehr.cc for rates.")
    c.save()
    return buf.getvalue()


def get_rates_pdf():
    return build_rates_pdf()

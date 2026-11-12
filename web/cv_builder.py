import io
import os
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.colors import Color

from django.conf import settings

CACHE_DIR = Path(settings.BASE_DIR) / "media" / "cv" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
for _f in CACHE_DIR.glob("cv_*"):
    _f.unlink(missing_ok=True)

def _register_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font_dir = os.path.join(settings.BASE_DIR, 'web', 'static', 'font')
    segoe = os.path.join(font_dir, 'SegoeUI-Regular.ttf')
    segoe_b = os.path.join(font_dir, 'SegoeUI-Bold.ttf')
    pdfmetrics.registerFont(TTFont('SegoeUI', segoe))
    pdfmetrics.registerFont(TTFont('SegoeUI-Bold', segoe_b))
    return {'bold': 'SegoeUI-Bold', 'regular': 'SegoeUI'}


FONT_MAP = _register_fonts()

_MONTH_ABBR = {
    '01': 'Jan.', '02': 'Feb.', '03': 'Mar.', '04': 'Apr.',
    '05': 'May', '06': 'Jun.', '07': 'Jul.', '08': 'Aug.',
    '09': 'Sep.', '10': 'Oct.', '11': 'Nov.', '12': 'Dec.',
}


def _fmt_date(raw):
    """Convert '03/2022 — Present' to 'Mar. 2022 — Present'."""
    def _repl(m):
        mm_str, yyyy = m.group(1), m.group(2)
        return f"{_MONTH_ABBR.get(mm_str, mm_str)} {yyyy}"
    return re.sub(r'(\d{2})/(\d{4})', _repl, raw)


TEXT_FULL = Color(0, 0, 0, 1.0)


def _get_styles():
    fm = FONT_MAP
    return {
        "name": ParagraphStyle("CVName", fontName=fm["bold"], fontSize=16, leading=19, textColor=TEXT_FULL, spaceAfter=2),
        "title": ParagraphStyle("CVTitle", fontName=fm["regular"], fontSize=9, leading=12, textColor=TEXT_FULL, spaceAfter=1),
        "contact": ParagraphStyle("CVContact", fontName=fm["regular"], fontSize=8, leading=11, textColor=TEXT_FULL, spaceAfter=2),
        "bio": ParagraphStyle("CVBio", fontName=fm["regular"], fontSize=8, leading=11, textColor=TEXT_FULL, spaceAfter=3),
        "section": ParagraphStyle("CVSection", fontName=fm["bold"], fontSize=9, leading=12, textColor=TEXT_FULL, spaceBefore=8, spaceAfter=3),
        "company": ParagraphStyle("CVCompany", fontName=fm["bold"], fontSize=9, leading=12, textColor=TEXT_FULL, spaceAfter=0),
        "role_date": ParagraphStyle("CVRoleDate", fontName=fm["regular"], fontSize=8, leading=11, textColor=TEXT_FULL, spaceAfter=1),
        "bullet": ParagraphStyle("CVBullet", fontName=fm["regular"], fontSize=8, leading=11, textColor=TEXT_FULL, leftIndent=8, bulletIndent=0, spaceAfter=1),
        "skill": ParagraphStyle("CVSkill", fontName=fm["regular"], fontSize=8, leading=11, textColor=TEXT_FULL, spaceAfter=1),
        "project_name": ParagraphStyle("CVProjectName", fontName=fm["bold"], fontSize=9, leading=12, textColor=TEXT_FULL, spaceAfter=0),
        "project_desc": ParagraphStyle("CVProjectDesc", fontName=fm["regular"], fontSize=8, leading=11, textColor=TEXT_FULL, spaceAfter=1),
        "edu": ParagraphStyle("CVEdu", fontName=fm["regular"], fontSize=8, leading=11, textColor=TEXT_FULL, spaceAfter=2),
        "lang": ParagraphStyle("CVLang", fontName=fm["regular"], fontSize=8, leading=11, textColor=TEXT_FULL, spaceAfter=1),
    }


def _link(text, url):
    if url:
        return f'<a href="{url}" color="black">{text}</a>'
    return text


def _link_with_icon(text, url):
    if url:
        return f'<a href="{url}" color="black">{text} ■</a>'
    return text



def _get_cv_data(version):
    from .models import WiehrDocument
    try:
        profile = WiehrDocument.objects.prefetch_related(
            'experiences', 'skills', 'projects', 'education', 'languages'
        ).get(version=version)
    except WiehrDocument.DoesNotExist:
        return None

    def _project_dict(proj):
        return {
            "name": proj.name,
            "type": proj.project_type,
            "date": _fmt_date(proj.date),
            "desc": proj.description,
            "bullets": proj.get_bullets_list(),
            "link": proj.link_text,
            "url": proj.link_url,
        }

    all_projects = list(profile.projects.all())
    commercial = [_project_dict(p) for p in all_projects if p.section == "commercial"]
    personal = [_project_dict(p) for p in all_projects if p.section != "commercial"]

    return {
        "name": profile.name,
        "title": profile.title,
        "bio": profile.bio,
        "contact": {
            "email": profile.email,
            "location": profile.location,
            "linkedin": profile.linkedin,
            "linkedin_url": profile.linkedin_url,
            "website": profile.website,
        },
        "experience": [
            {
                "role": exp.role,
                "company": exp.company,
                "company_url": exp.company_url,
                "overview": exp.overview,
                "date": _fmt_date(exp.date),
                "location": exp.location,
                "bullets": exp.get_bullets_list(),
            }
            for exp in profile.experiences.all()
        ],
        "skills": [
            (skill.category, skill.items)
            for skill in profile.skills.all()
        ],
        "projects_commercial": commercial,
        "projects_personal": personal,
        "projects_personal_label": "WORKS" if version == "composer" else "PERSONAL PROJECTS",
        "education": [
            (edu.title, _fmt_date(edu.date), edu.url)
            for edu in profile.education.all()
        ],
        "languages": [
            (lang.language, lang.level)
            for lang in profile.languages.all()
        ],
        "updated_at": profile.updated_at,
    }



def _build_pdf(data):
    buffer = io.BytesIO()
    S = _get_styles()

    MARGIN_LR = 16 * mm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN_LR,
        rightMargin=MARGIN_LR,
        topMargin=12 * mm,
        bottomMargin=10 * mm,
        title=f'CV — {data["name"]}',
        author=data["name"],
    )

    elements = []

    elements.append(Paragraph(data["name"], S["name"]))
    elements.append(Paragraph(data["title"], S["title"]))

    contact_parts = []
    if data["contact"]["email"]:
        contact_parts.append(data["contact"]["email"])
    if data["contact"]["location"]:
        contact_parts.append(data["contact"]["location"])
    if data["contact"]["linkedin"]:
        contact_parts.append(_link(data["contact"]["linkedin"], data["contact"]["linkedin_url"]))
    if data["contact"]["website"]:
        contact_parts.append(_link(data["contact"]["website"], data["contact"]["website"]))
    elements.append(Paragraph(" | ".join(contact_parts), S["contact"]))

    if data.get("bio"):
        elements.append(Spacer(1, 2))
        elements.append(Paragraph(data["bio"], S["bio"]))

    if data["experience"]:
        elements.append(Paragraph("WORK EXPERIENCE", S["section"]))
        for i, exp in enumerate(data["experience"]):
            loc_part = f'  \u2014  {exp["location"]}' if exp.get("location") else ''
            company_line = f'{exp["company"]}{loc_part}'
            company_para = Paragraph(_link_with_icon(company_line, exp.get("company_url")), S["company"])
            elements.append(company_para)
            elements.append(Paragraph(f'{exp["role"]}  |  {exp["date"]}', S["role_date"]))
            for bullet in exp["bullets"]:
                elements.append(Paragraph(f"\u2022 {bullet}", S["bullet"]))
            if i < len(data["experience"]) - 1:
                elements.append(Spacer(1, 3))

    if data["skills"]:
        elements.append(Paragraph("SKILLS", S["section"]))
        for cat, items in data["skills"]:
            elements.append(Paragraph(f"<b>{cat}:</b>  {items}", S["skill"]))

    def _render_project_group(header, projects):
        elements.append(Paragraph(header, S["section"]))
        for proj in projects:
            link_part = ""
            if proj.get("link") and proj.get("url"):
                link_part = f'  |  {_link_with_icon(proj["link"], proj["url"])}'
            name_str = f'{proj["name"]} ({proj["type"]})  |  {proj["date"]}{link_part}'
            name_para = Paragraph(name_str, S["project_name"])
            elements.append(name_para)
            elements.append(Paragraph(proj["desc"], S["project_desc"]))
            for bullet in proj.get("bullets") or []:
                elements.append(Paragraph(f"\u2022 {bullet}", S["bullet"]))
            elements.append(Spacer(1, 3))

    if data["projects_personal"]:
        _render_project_group(data["projects_personal_label"], data["projects_personal"])
    if data["projects_commercial"]:
        _render_project_group("COMMERCIAL PROJECTS", data["projects_commercial"])

    if data["education"]:
        elements.append(Paragraph("EDUCATION &amp; CERTIFICATIONS", S["section"]))
        for title, date, url in data["education"]:
            edu_line = f"{title}  |  {date}"
            edu_para = Paragraph(_link_with_icon(edu_line, url), S["edu"])
            elements.append(edu_para)

    if data["languages"]:
        elements.append(Paragraph("LANGUAGES", S["section"]))
        for lang, level in data["languages"]:
            elements.append(Paragraph(f"<b>{lang}:</b>  {level}", S["lang"]))

    doc.build(elements)
    return buffer.getvalue()


def _build_docx(data):
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.oxml.ns import qn

    doc = Document()

    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(1.8)
    section.right_margin = Cm(1.8)
    section.top_margin = Cm(1.6)
    section.bottom_margin = Cm(1.0)

    font_name = "Segoe UI"
    black_c = RGBColor(0x00, 0x00, 0x00)
    secondary = RGBColor(0x33, 0x33, 0x33)

    def add_run(para, text, size=7.5, bold=False, color=black_c):
        run = para.add_run(text)
        run.font.name = font_name
        run._element.rPr.rFonts.set(qn('w:cs'), font_name)
        run.font.size = Pt(size)
        run.bold = bold
        run.font.color.rgb = color
        return run

    def add_hyperlink(para, text, url, size=7.5, bold=False, color=black_c):
        part = para.part
        r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
        hyperlink = para._element.makeelement(qn('w:hyperlink'), {qn('r:id'): r_id})
        new_run = para._element.makeelement(qn('w:r'), {})
        rPr = para._element.makeelement(qn('w:rPr'), {})
        rFonts = para._element.makeelement(qn('w:rFonts'), {qn('w:ascii'): font_name, qn('w:hAnsi'): font_name, qn('w:cs'): font_name})
        sz = para._element.makeelement(qn('w:sz'), {qn('w:val'): str(int(size * 2))})
        szCs = para._element.makeelement(qn('w:szCs'), {qn('w:val'): str(int(size * 2))})
        color_hex = str(color) if color else '000000'
        c = para._element.makeelement(qn('w:color'), {qn('w:val'): color_hex})
        rPr.append(rFonts)
        rPr.append(sz)
        rPr.append(szCs)
        rPr.append(c)
        if bold:
            b = para._element.makeelement(qn('w:b'), {})
            rPr.append(b)
        new_run.append(rPr)
        new_run.text = text
        hyperlink.append(new_run)
        para._element.append(hyperlink)

    p = doc.add_paragraph()
    p.space_after = Pt(0)
    p.space_before = Pt(0)
    add_run(p, data["name"], size=14, bold=True)

    p = doc.add_paragraph()
    p.space_after = Pt(0)
    p.space_before = Pt(0)
    add_run(p, data["title"], size=7.5, color=secondary)

    p = doc.add_paragraph()
    p.space_after = Pt(2)
    p.space_before = Pt(0)
    contact_parts = []
    if data["contact"]["email"]:
        contact_parts.append(data["contact"]["email"])
    if data["contact"]["location"]:
        contact_parts.append(data["contact"]["location"])
    add_run(p, " | ".join(contact_parts) + " | ", size=7, color=secondary)
    if data["contact"]["linkedin"] and data["contact"]["linkedin_url"]:
        add_hyperlink(p, data["contact"]["linkedin"], data["contact"]["linkedin_url"], size=7, color=secondary)

    if data.get("bio"):
        p = doc.add_paragraph()
        p.space_after = Pt(2)
        p.space_before = Pt(1)
        add_run(p, data["bio"], size=7, color=secondary)

    if data["experience"]:
        p = doc.add_paragraph()
        p.space_after = Pt(1)
        p.space_before = Pt(2)
        add_run(p, "WORK EXPERIENCE", size=7.5, bold=True, color=secondary)

        for exp in data["experience"]:
            p = doc.add_paragraph()
            p.space_after = Pt(0)
            p.space_before = Pt(1)
            if exp.get("company_url"):
                add_hyperlink(p, exp["company"], exp["company_url"], size=8, bold=True)
            else:
                add_run(p, exp["company"], size=8, bold=True)
            if exp.get("location"):
                add_run(p, f'  \u2014  {exp["location"]}', size=8, color=secondary)

            p = doc.add_paragraph()
            p.space_after = Pt(0)
            p.space_before = Pt(0)
            add_run(p, f'{exp["role"]}  |  {exp["date"]}', size=7, color=secondary)

            if exp.get("overview"):
                p = doc.add_paragraph()
                p.space_after = Pt(0)
                p.space_before = Pt(0)
                add_run(p, exp["overview"], size=7, color=secondary)

            for bullet in exp["bullets"]:
                p = doc.add_paragraph()
                p.space_after = Pt(0)
                p.space_before = Pt(0)
                add_run(p, f"\u2022 {bullet}", size=7, color=secondary)

    if data["skills"]:
        p = doc.add_paragraph()
        p.space_after = Pt(1)
        p.space_before = Pt(2)
        add_run(p, "SKILLS", size=7.5, bold=True, color=secondary)

        for cat, items in data["skills"]:
            p = doc.add_paragraph()
            p.space_after = Pt(0)
            p.space_before = Pt(0)
            add_run(p, f"{cat}: ", size=7, bold=True)
            add_run(p, items, size=7, color=secondary)

    def _render_project_group(header, projects):
        p = doc.add_paragraph()
        p.space_after = Pt(1)
        p.space_before = Pt(2)
        add_run(p, header, size=7.5, bold=True, color=secondary)

        for proj in projects:
            p = doc.add_paragraph()
            p.space_after = Pt(0)
            p.space_before = Pt(1)
            add_run(p, f'{proj["name"]} ({proj["type"]})  |  {proj["date"]}', size=7.5, bold=True)

            p = doc.add_paragraph()
            p.space_after = Pt(0)
            p.space_before = Pt(0)
            add_run(p, proj["desc"], size=7, color=secondary)
            if proj.get("link") and proj.get("url"):
                add_run(p, '  |  ', size=7, color=secondary)
                add_hyperlink(p, proj["link"] + ' \u25a0', proj["url"], size=7, color=secondary)

            for bullet in proj.get("bullets") or []:
                p = doc.add_paragraph()
                p.space_after = Pt(0)
                p.space_before = Pt(0)
                add_run(p, f"\u2022 {bullet}", size=7, color=secondary)

    if data["projects_personal"]:
        _render_project_group(data["projects_personal_label"], data["projects_personal"])
    if data["projects_commercial"]:
        _render_project_group("COMMERCIAL PROJECTS", data["projects_commercial"])

    if data["education"]:
        p = doc.add_paragraph()
        p.space_after = Pt(1)
        p.space_before = Pt(2)
        add_run(p, "EDUCATION & CERTIFICATIONS", size=7.5, bold=True, color=secondary)

        for title, date, url in data["education"]:
            p = doc.add_paragraph()
            p.space_after = Pt(0)
            p.space_before = Pt(0)
            if url:
                add_hyperlink(p, title + ' \u25a0', url, size=7, bold=True)
            else:
                add_run(p, title, size=7, bold=True)
            add_run(p, f'  |  {date}', size=7, color=secondary)

    if data["languages"]:
        p = doc.add_paragraph()
        p.space_after = Pt(1)
        p.space_before = Pt(2)
        add_run(p, "LANGUAGES", size=7.5, bold=True, color=secondary)

        for lang, level in data["languages"]:
            p = doc.add_paragraph()
            p.space_after = Pt(0)
            p.space_before = Pt(0)
            add_run(p, f"{lang}: ", size=7, bold=True)
            add_run(p, level, size=7, color=secondary)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _build_txt(data):
    lines = []
    lines.append(data["name"])
    lines.append(data["title"])
    contact_parts = []
    if data["contact"]["email"]:
        contact_parts.append(data["contact"]["email"])
    if data["contact"]["location"]:
        contact_parts.append(data["contact"]["location"])
    if data["contact"]["linkedin_url"]:
        contact_parts.append(data["contact"]["linkedin_url"])
    if data["contact"]["website"]:
        contact_parts.append(data["contact"]["website"])
    lines.append(" | ".join(contact_parts))
    if data.get("bio"):
        lines.append(data["bio"])
    lines.append("")

    if data["experience"]:
        lines.append("WORK EXPERIENCE")
        for exp in data["experience"]:
            company_line = exp["company"]
            if exp.get("company_url"):
                company_line += f' ({exp["company_url"]})'
            if exp.get("location"):
                company_line += f' \u2014 {exp["location"]}'
            lines.append(company_line)
            lines.append(f'{exp["role"]} | {exp["date"]}')
            if exp.get("overview"):
                lines.append(exp["overview"])
            for bullet in exp["bullets"]:
                lines.append(f"\u2022 {bullet}")
            lines.append("")

    if data["skills"]:
        lines.append("SKILLS")
        for cat, items in data["skills"]:
            lines.append(f"{cat}: {items}")
        lines.append("")

    def _render_project_group(header, projects):
        lines.append(header)
        for proj in projects:
            lines.append(f'{proj["name"]} ({proj["type"]}) | {proj["date"]}')
            lines.append(proj["desc"])
            for bullet in proj.get("bullets") or []:
                lines.append(f"\u2022 {bullet}")
            if proj.get("url"):
                lines.append(proj["url"])
        lines.append("")

    if data["projects_personal"]:
        _render_project_group(data["projects_personal_label"], data["projects_personal"])
    if data["projects_commercial"]:
        _render_project_group("COMMERCIAL PROJECTS", data["projects_commercial"])

    if data["education"]:
        lines.append("EDUCATION & CERTIFICATIONS")
        for title, date, url in data["education"]:
            line = f"{title} | {date}"
            if url:
                line += f" ({url})"
            lines.append(line)
        lines.append("")

    if data["languages"]:
        lines.append("LANGUAGES")
        for lang, level in data["languages"]:
            lines.append(f"{lang}: {level}")

    return "\n".join(lines)


def _cache_path(version, fmt):
    return CACHE_DIR / f"cv_{version}.{fmt}"


ALL_SECTIONS = {'experience', 'skills', 'commercial', 'personal', 'education', 'languages'}


def _filter_sections(data, sections):
    """Return a shallow copy of data with only the requested sections populated."""
    if sections is None:
        return data
    keep = set(sections) & ALL_SECTIONS
    filtered = dict(data)
    if 'experience' not in keep:
        filtered['experience'] = []
    if 'skills' not in keep:
        filtered['skills'] = []
    if 'commercial' not in keep:
        filtered['projects_commercial'] = []
    if 'personal' not in keep:
        filtered['projects_personal'] = []
    if 'education' not in keep:
        filtered['education'] = []
    if 'languages' not in keep:
        filtered['languages'] = []
    return filtered


def invalidate_cv_cache(version=None):
    versions = [version] if version else ['engineer', 'composer']
    for v in versions:
        for fmt in ('pdf', 'docx', 'txt'):
            path = _cache_path(v, fmt)
            if path.exists():
                path.unlink()


def get_cv_pdf(version='engineer', sections=None):
    use_cache = sections is None
    if use_cache:
        path = _cache_path(version, 'pdf')
        if path.exists():
            return path.read_bytes()

    data = _get_cv_data(version)
    if not data:
        return None

    pdf_bytes = _build_pdf(_filter_sections(data, sections))
    if use_cache:
        path.write_bytes(pdf_bytes)
    return pdf_bytes


def get_cv_docx(version='engineer', sections=None):
    use_cache = sections is None
    if use_cache:
        path = _cache_path(version, 'docx')
        if path.exists():
            return path.read_bytes()

    data = _get_cv_data(version)
    if not data:
        return None

    docx_bytes = _build_docx(_filter_sections(data, sections))
    if use_cache:
        path.write_bytes(docx_bytes)
    return docx_bytes


def get_cv_txt(version='engineer', sections=None):
    use_cache = sections is None
    if use_cache:
        path = _cache_path(version, 'txt')
        if path.exists():
            return path.read_text(encoding='utf-8')

    data = _get_cv_data(version)
    if not data:
        return None

    txt_content = _build_txt(_filter_sections(data, sections))
    if use_cache:
        path.write_text(txt_content, encoding='utf-8')
    return txt_content

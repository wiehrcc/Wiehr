import io

# Base-14 PDF font: on every machine, no embedding needed. licensee_name is
# always the buyer's passport-transliterated Latin name, so Courier's
# WinAnsi-only glyph set is not a limitation here.
PDF_FONT_REGULAR = 'Courier'
PDF_FONT_BOLD = 'Courier-Bold'


def _ensure_pdf_fonts():
    return True

FONT_FAMILY_BLOCK = """DIGITAL FONT STYLES (with glitch effects):
• Thin
• Medium
• Black

ANALOG FONT STYLES (without glitch effects):
• Light
• Regular
• Bold

CHARACTER SETS INCLUDED:
• Basic Latin (ASCII)
• Latin-1 Supplement
• Cyrillic
• Cyrillic Supplement

SUPPORTED CODEPAGES:
• Latin 1 (Windows 1252)
• Cyrillic (Windows 1251)
• Macintosh Character Set (US Roman)

FILE FORMATS COVERED:
• TrueType Font (.ttf)
• OpenType Font (.otf)
• Web Open Font Format (.woff, .woff2)
• Any future font formats developed"""

RULE = "=" * 80


def _section(number, title):
    return f"{RULE}\n{number}. {title}\n{RULE}"


def build_agreement_text(licence):
    product = licence.get_product_display()
    name = licence.licensee_name
    effective = licence.effective_date.strftime('%B %d, %Y')
    numeric_id = licence.internal_id[1:] if licence.internal_id[:1].isalpha() else licence.internal_id
    license_type = licence.license_type.name

    parts = [
        f"{license_type.upper()} AGREEMENT",
        "",
        f"Product: {product}",
        "Copyright: © 2025 — 2125 Wiehr",
        "Licensor (Author / Rights Holder): Wiehr",
        f"License Effective Date: {effective}",
        f"License Type: {license_type}",
        "",
        "LICENSEE",
        f"ID: {numeric_id}",
        f"Name: {name}",
        f"Email: {licence.licensee_email}",
        f"License ID: {licence.license_key}",
        "",
        _section(1, "SOFTWARE COVERED"),
        "",
        f"This license applies to {product} in all formats, styles, and variations:",
        "",
        FONT_FAMILY_BLOCK,
        "",
        _section(2, f"GRANT OF {license_type.upper()}"),
        "",
        f"The Licensor hereby grants {name} a personal, exclusive, non-transferable,",
        "non-sublicensable, worldwide, perpetual license to use the covered software for any",
        "purpose, including but not limited to:",
        "",
        "PERMITTED USES:",
        "• Personal projects and creative works",
        "• Commercial projects and business ventures",
        "• Client work and freelance services",
        "• Branding, logos, and corporate identity",
        "• Posters, albums, book covers, and packaging",
        "• Websites and web font embedding",
        "• Applications, games, and software development",
        "• Video production, motion graphics, and broadcast media",
        "• 3D modeling and digital content creation",
        "• Print and digital publishing",
        "• Merchandise and product design",
        "",
        "EXCLUSIVITY CLAUSE:",
        "This is an exclusive license agreement. No other individual or entity shall be granted",
        "the same rights under this license for the duration of this agreement. The Licensor",
        "retains the right to issue different types of licenses (non-exclusive, limited, etc.)",
        "to other parties, but no other exclusive personal license will be granted.",
        "",
        "LICENSEE RESTRICTION:",
        f"This license applies exclusively to the named Licensee ({name}) and cannot",
        "be transferred, assigned, shared, or used by any other person or entity, including",
        "employees, contractors, or family members, unless specifically authorized in writing",
        "by the Licensor.",
        "",
        _section(3, "PROHIBITED ACTIONS"),
        "",
        "The Licensee must NOT:",
        "",
        "• REDISTRIBUTION: Redistribute, share, sublicense, sell, rent, lease, or provide the",
        "  files to any third party in any form or manner",
        "",
        "• FILE SHARING: Upload the files to public repositories, websites, file-sharing",
        "  services, cloud storage, or any platform accessible by third parties",
        "",
        "• TEMPLATE DISTRIBUTION: Include the files in redistributable templates, themes,",
        "  UI kits, design systems, or any product that will be distributed to third parties",
        "",
        "• MODIFICATION: Modify, alter, decompile, reverse-engineer, extract, or create",
        "  derivative works of the software or any portion thereof",
        "",
        "• REPACKAGING: Repackage, subset, or embed the software in a manner that allows",
        "  extraction or use by third parties",
        "",
        "• COMMERCIAL DISTRIBUTION: Sell, license, or otherwise commercialize the software",
        "  itself or any modified versions thereof",
        "",
        "THIRD-PARTY REQUIREMENT:",
        f"Any third party requiring access to {product} must obtain a separate license",
        "directly from the Licensor (Wiehr) by contacting https://wiehr.cc or",
        "https://t.me/Wiehr",
        "",
        _section(4, "ATTRIBUTION"),
        "",
        "Attribution is OPTIONAL but appreciated where credits are normally provided.",
        "",
        "RECOMMENDED CREDIT TEXT:",
        f"{product} — © Wiehr",
        "or",
        f"Typography: {product} by Wiehr",
        "",
        "APPROPRIATE PLACEMENT FOR ATTRIBUTION:",
        "• Project credits and acknowledgments",
        "• Documentation, README files, or project descriptions",
        "• Website footer or \"About\" section",
        "• Application or game credits screens",
        "• Video credits or production notes",
        "• Book colophons or publication acknowledgments",
        "",
        "EXCEPTIONS:",
        "Attribution is NOT required within rasterized logos, images, or static visual elements",
        "where the software is not directly accessible or extractable.",
        "",
        _section(5, "OWNERSHIP AND INTELLECTUAL PROPERTY"),
        "",
        "This license does NOT transfer ownership of the software.",
        "",
        f"All intellectual property rights, title, interest, and ownership in {product},",
        "including all trademarks, copyrights, trade secrets, and proprietary rights,",
        "remain exclusively with the Licensor (Wiehr).",
        "",
        "The Licensee acknowledges that Wiehr is the exclusive owner of all rights to the",
        "software and that this license grants only the limited rights expressly",
        "described herein.",
        "",
        _section(6, "WARRANTY DISCLAIMER"),
        "",
        "The software is provided \"AS IS\", without warranty of any kind, express or",
        "implied, including but not limited to the warranties of merchantability, fitness for",
        "a particular purpose, and non-infringement.",
        "",
        "The Licensor does not warrant that the software will meet the Licensee's",
        "requirements, operate without interruption, or be error-free.",
        "",
        _section(7, "LIMITATION OF LIABILITY"),
        "",
        "In no event shall the Licensor be liable for any claim, damages, or other liability,",
        "whether in an action of contract, tort, or otherwise, arising from, out of, or in",
        "connection with the software or the use or other dealings in the software.",
        "",
        _section(8, "TERMINATION"),
        "",
        "This license is effective until terminated. The Licensor reserves the right to",
        "terminate this license immediately upon written notice if the Licensee breaches any",
        "term of this agreement.",
        "",
        "Upon termination:",
        "• All rights granted under this license shall immediately cease",
        f"• The Licensee must cease all use of {product}",
        "• The Licensee must delete or destroy all copies of the software in their",
        "  possession or control",
        "• Any projects created using it may remain in use, but no new projects may",
        "  be created using it",
        "",
        _section(9, "GOVERNING TERMS AND JURISDICTION"),
        "",
        "This agreement shall be governed by and construed in accordance with international",
        "intellectual property laws and treaties.",
        "",
        "This license applies worldwide and remains valid unless revoked in writing by the",
        "Licensor. Any disputes arising from this agreement shall be resolved through",
        "negotiation or, if necessary, through appropriate legal channels in a jurisdiction",
        "agreed upon by both parties.",
        "",
        _section(10, "CONTACT INFORMATION"),
        "",
        "LICENSOR:",
        "Name: Wiehr",
        "Website: https://wiehr.cc",
        "Telegram: https://t.me/Wiehr",
        "Email: hello@wiehr.cc",
        "",
        "LICENSEE:",
        f"ID: {numeric_id}",
        f"Name: {name}",
        f"Email: {licence.licensee_email}",
        f"License ID: {licence.license_key}",
        "",
        RULE,
        "SUMMARY",
        RULE,
        "",
        f"{product} is exclusively licensed to {name}.",
        "",
        "You can use it for ANY purpose (personal, commercial, client work, etc.) but you",
        "CANNOT share it, modify it, redistribute it, or give it to anyone else.",
        "",
        "Each person or organization wanting to use this must obtain their own license",
        "directly from Wiehr.",
        "",
        RULE,
        "LICENSE AUTHENTICATION",
        RULE,
        "",
        f"This license agreement was created on {effective}, and is digitally signed by",
        "the Licensor (Wiehr). Any unauthorized reproduction or modification of this license",
        "is strictly prohibited.",
        "",
        f"Verify this license at https://wiehr.cc/licensing?key={licence.license_key}",
        "",
        "For license verification, contact Wiehr at hello@wiehr.cc",
    ]

    return "\n".join(parts)


def build_agreement_pdf(licence):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as pdf_canvas

    font_name = PDF_FONT_REGULAR if _ensure_pdf_fonts() else 'Courier'

    text = build_agreement_text(licence)
    buffer = io.BytesIO()
    pdf = pdf_canvas.Canvas(buffer, pagesize=A4)
    _, height = A4

    pdf.setTitle(f'Wiehr License {licence.internal_id}')
    pdf.setAuthor('Wiehr')
    pdf.setSubject(licence.license_type.name)

    left = 12 * mm
    top = height - 15 * mm
    bottom = 15 * mm
    line_height = 3.4 * mm
    font_size = 7

    pdf.setFont(font_name, font_size)
    y = top

    for line in text.split("\n"):
        if y < bottom:
            pdf.showPage()
            pdf.setFont(font_name, font_size)
            y = top
        pdf.drawString(left, y, line)
        y -= line_height

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def build_agreement_docx(licence):
    from docx import Document
    from docx.shared import Pt

    text = build_agreement_text(licence)
    document = Document()

    style = document.styles['Normal']
    style.font.name = 'Courier New'
    style.font.size = Pt(7)
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.line_spacing = 1.0

    for line in text.split("\n"):
        document.add_paragraph(line)

    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

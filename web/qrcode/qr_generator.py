import json
import os
import re
import base64
from pathlib import Path
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H

CONFIG_PATH = Path(__file__).parent / "qr_config.json"
OUTPUT_SVG = Path(__file__).parent / "qr_release.svg"
DEFAULT_LOGO_SVG = Path(
    os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'web',
        'static',
        'images',
        'qr',
        'logo.svg'
    )
).resolve()

EC_MAP = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


def load_config(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def generate_qr_svg(data: str, config: dict = None) -> str:
    if config is None:
        config = load_config(CONFIG_PATH)
    matrix = make_matrix(data, config)
    svg = build_svg(matrix, config)
    return svg


def make_matrix(data: str, cfg: dict):
    ec = EC_MAP.get(cfg.get("error_correction", "M").upper(), ERROR_CORRECT_M)
    qr = qrcode.QRCode(
        version=cfg.get("version"),
        error_correction=ec,
        box_size=1,
        border=0,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.get_matrix()


def draw_square(x, y, size, color):
    return f'<rect x="{x:.6f}" y="{y:.6f}" width="{size:.6f}" height="{size:.6f}" fill="{color}" />'


def _parse_svg_viewbox(svg_text: str):
    m = re.search(r'viewBox="([^"]+)"', svg_text)
    if m:
        parts = re.split(r'[\s,]+', m.group(1).strip())
        if len(parts) >= 4:
            minx, miny, w, h = map(float, parts[:4])
            return minx, miny, w, h
    mw = re.search(r'width="([0-9.]+)(?:px)?"', svg_text)
    mh = re.search(r'height="([0-9.]+)(?:px)?"', svg_text)
    if mw and mh:
        w = float(mw.group(1))
        h = float(mh.group(1))
        return 0.0, 0.0, w, h
    return None


def _recolor_svg(svg_text: str, color: str):
    svg_text = re.sub(r'(?i)\bfill="[^"]*"', f'fill="{color}"', svg_text)
    svg_text = re.sub(r'(?i)style="([^"]*?)fill:[^;"]*;?([^"]*?)"', lambda m: f'style="{m.group(1)}fill:{color};{m.group(2)}"', svg_text)
    svg_text = re.sub(r'(?i)\bstroke="[^"]*"', f'stroke="{color}"', svg_text)
    svg_text = re.sub(r'(<svg[^>]*>)', r'\1<g fill="' + color + '" stroke="' + color + '">', svg_text, count=1, flags=re.I)
    svg_text = re.sub(r'(</svg>)\s*$', r'</g>\n\1', svg_text, count=1, flags=re.I)
    return svg_text


def embed_logo_svg(logo_svg_path: Path, svg_size: int,
                          logo_size_frac: float, fg_color: str, bg_color: str) -> str:
    logo_dim = int(round(svg_size * float(logo_size_frac)))
    if logo_dim <= 0:
        return ""

    padding_factor = 1.5
    bg_dim = int(round(logo_dim * padding_factor))
    
    x = (svg_size - logo_dim) / 2.0
    y = (svg_size - logo_dim) / 2.0
    
    bg_x = (svg_size - bg_dim) / 2.0
    bg_y = (svg_size - bg_dim) / 2.0

    parts = []
    parts.append(f'<rect x="{bg_x}" y="{bg_y}" width="{bg_dim}" '
                 f'height="{bg_dim}" fill="{bg_color}" rx="0" ry="0" />')

    svg_text = logo_svg_path.read_text(encoding="utf-8")
    svg_text = _recolor_svg(svg_text, fg_color)

    vb = _parse_svg_viewbox(svg_text)
    minx, miny, vw, vh = vb

    scale_x = logo_dim / vw
    scale_y = logo_dim / vh
    scale = min(scale_x, scale_y)

    transform = f'translate({x:.6f},{y:.6f}) scale({scale:.6f}) translate({-minx:.6f},{-miny:.6f})'
    svg_text_inner = re.sub(r'^\s*<\?xml[^>]*>\s*', '', svg_text, count=1)
    inner = re.sub(r'^.*?<svg[^>]*>', '', svg_text_inner, count=1, flags=re.S)
    inner = re.sub(r'</svg>\s*$', '', inner, count=1, flags=re.S)
    inner = inner.strip()
    parts.append(f'<g transform="{transform}">\n{inner}\n</g>')
    return "\n".join(parts)


def build_svg(matrix, cfg: dict):
    svg_size = int(cfg.get("svg_size", 1000))
    if cfg.get("black_and_white", False) is True:
        bg_color = "#F4F4F4"
        fg_color = "#151617"
    else:
        bg_color = cfg.get("bg_color", "#F4F4F4")
        fg_color = cfg.get("fg_color", "#151617")
    logo_size = float(cfg.get("logo_size", 0.2))

    if logo_size < 0.0:
        logo_size = 0.0
    if logo_size > 1.0:
        logo_size = 1.0

    rows = len(matrix)
    cols = len(matrix[0])
    scale = svg_size / max(rows, cols)

    svg_parts = []
    svg_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_size}" height="{svg_size}" viewBox="0 0 {svg_size} {svg_size}">')
    svg_parts.append(f'<rect width="100%" height="100%" fill="{bg_color}" />')

    for r, row in enumerate(matrix):
        for c, val in enumerate(row):
            if not val:
                continue
            x = c * scale
            y = r * scale
            svg_parts.append(draw_square(x, y, scale, fg_color))

    svg_parts.append(embed_logo_svg(DEFAULT_LOGO_SVG, svg_size, logo_size, fg_color, bg_color))

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def main():
    cfg = load_config(CONFIG_PATH)
    data = cfg.get("data", "https://wiehr.cc/s/W001")
    matrix = make_matrix(data, cfg)
    svg = build_svg(matrix, cfg)
    OUTPUT_SVG.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()

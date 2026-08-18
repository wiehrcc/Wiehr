from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
import tempfile

from reportlab.graphics import renderPDF
from reportlab.lib.colors import CMYKColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg

try:
    from fontTools.ttLib import TTFont as FTFont
except ImportError:
    FTFont = None

from .qr_generator import CONFIG_PATH, load_config

CONTENT_WIDTH_MM = 92.96
CONTENT_HEIGHT_MM = 66.21
MARGIN_MM = 4.0
PAGE_WIDTH_MM = 210.0
PAGE_HEIGHT_MM = 297.0
QR_SIZE_MM = 38
QR_POS_X_MM = 4
QR_POS_Y_MM = 4

QR_SOURCE_SVG = Path(r"C:\03-Music\@W1\@templates\W001@QR.svg")
BORDER_SVG = Path(
    Path(__file__).resolve().parents[2]
    / "web"
    / "static"
    / "images"
    / "qr"
    / "borders.svg"
)
OUTPUT_PDF = Path(__file__).parent / "qr_print.pdf"
FONT_PATH = Path(
    Path(__file__).resolve().parents[2]
    / "web"
    / "static"
    / "font"
    / "Wiehr-Black.ttf"
)
TITLE_FONT_NAME = "Wiehr"

PIXEL_FG_COLOR = "#151617"
DEFAULT_PIXEL_SIZE = 1.49
DEFAULT_PIXEL_GAP = 0
DEFAULT_DESTROY_THRESHOLD = 0.61
DEFAULT_DESTROY_SEED = "W000"

SEPARATORS = " ,\n\t\r"
NUMBER_RE = re.compile(r"[+-]?(?:\d*\.\d+|\d+)(?:[eE][+-]?\d+)?")


class MissingDependencyError(RuntimeError):
    pass


def mm_to_pt(value_mm: float) -> float:
    return value_mm * mm


def px_to_pt(value_px: float) -> float:
    return value_px * 72.0 / 96.0


def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    hex_color = hex_color.strip()
    if not hex_color:
        return 1.0, 1.0, 1.0
    if hex_color.startswith("#"):
        hex_color = hex_color[1:]
    if len(hex_color) == 3:
        hex_color = "".join(ch * 2 for ch in hex_color)
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex colour string: {hex_color!r}")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return r, g, b


def rgb_to_cmyk(rgb_color: Tuple[float, float, float]) -> Tuple[float, float, float, float]:
    r, g, b = rgb_color
    if (r, g, b) == (0.0, 0.0, 0.0):
        return 0.0, 0.0, 0.0, 1.0
    c = 1.0 - r
    m = 1.0 - g
    y = 1.0 - b
    k = min(c, m, y)
    if math.isclose(k, 1.0):
        return 0.0, 0.0, 0.0, 1.0
    denom = 1.0 - k
    c = (c - k) / denom
    m = (m - k) / denom
    y = (y - k) / denom
    return c, m, y, k


def _brighten_cmyk(components: Tuple[float, float, float, float], amount: float = 0.15) -> Tuple[float, float, float, float]:
    def _brighten(value: float) -> float:
        return max(0.0, value - value * amount)

    return tuple(_brighten(channel) for channel in components)


def _darken_cmyk(components: Tuple[float, float, float, float], amount: float = 0.25) -> Tuple[float, float, float, float]:
    def _darken(value: float) -> float:
        return min(1.0, value + (1.0 - value) * amount)

    return tuple(_darken(channel) for channel in components)


def _normalize_hex_color(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "#151617"
    if not value.startswith("#"):
        value = f"#{value}"
    if len(value) == 4:
        value = "#" + "".join(ch * 2 for ch in value[1:])
    return value[:7]


def _prepare_svg_drawing(svg_path: Path):
    if not svg_path.exists():
        raise FileNotFoundError(svg_path)
    return svg2rlg(str(svg_path))


def _scale_drawing(drawing, width_pt: float, height_pt: float) -> None:
    if drawing.width == 0 or drawing.height == 0:
        return
    scale_x = width_pt / drawing.width
    scale_y = height_pt / drawing.height
    drawing.scale(scale_x, scale_y)


def _draw_svg(canvas_obj, drawing, pos_x_pt: float, pos_y_pt: float) -> None:
    renderPDF.draw(drawing, canvas_obj, pos_x_pt, pos_y_pt)


def _apply_cmyk_color(node, color: CMYKColor) -> None:
    if hasattr(node, "fillColor"):
        node.fillColor = color
    if hasattr(node, "strokeColor"):
        node.strokeColor = color
    contents: Iterable = getattr(node, "contents", []) or []
    for child in contents:
        _apply_cmyk_color(child, color)


def _ensure_font_registered(font_path: Path, font_name: str) -> str:
    if font_name in pdfmetrics.getRegisteredFontNames():
        return font_name
    if not font_path.exists():
        raise FileNotFoundError(f"Font file not found: {font_path}")
    
    actual_font_path = font_path
    if font_path.suffix.lower() in ('.woff', '.woff2'):
        if FTFont is None:
            raise MissingDependencyError("fonttools is required to load WOFF fonts.")
        ft_font = FTFont(str(font_path))
        with tempfile.NamedTemporaryFile(suffix='.ttf', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            ft_font.save(str(tmp_path))
        actual_font_path = tmp_path
    
    try:
        pdfmetrics.registerFont(TTFont(font_name, str(actual_font_path)))
    except Exception as exc:
        raise MissingDependencyError(
            "Unable to load font. Convert the supplied WOFF to TTF/OTF or "
            "install ReportLab font support for WOFF files."
        ) from exc
    return font_name


@dataclass(frozen=True)
class PDFTextBlock:
    name: str
    left_mm: float
    right_mm: float
    top_offset_mm: float
    bottom_offset_mm: float
    font_size_px: float

    @property
    def width_mm(self) -> float:
        return self.right_mm - self.left_mm

    @property
    def height_mm(self) -> float:
        return self.bottom_offset_mm - self.top_offset_mm

    @property
    def font_size_pt(self) -> float:
        return px_to_pt(self.font_size_px)

    def draw(self, canvas_obj, text: str, font_name: str, color: CMYKColor, offset_x_mm: float = 0, offset_y_mm: float = 0) -> None:
        if not text:
            return
        text = str(text)
        content_origin_x = mm_to_pt(MARGIN_MM + offset_x_mm)
        content_origin_y = mm_to_pt(MARGIN_MM + offset_y_mm)
        content_height_pt = mm_to_pt(CONTENT_HEIGHT_MM)

        left_pt = content_origin_x + mm_to_pt(self.left_mm)
        right_pt = content_origin_x + mm_to_pt(self.right_mm)
        upper_pt = content_origin_y + content_height_pt - mm_to_pt(self.top_offset_mm)
        lower_pt = content_origin_y + content_height_pt - mm_to_pt(self.bottom_offset_mm)

        height_pt = upper_pt - lower_pt
        if height_pt <= 0:
            return

        center_x_pt = (left_pt + right_pt) / 2.0
        center_y_pt = lower_pt + height_pt / 2.0

        canvas_obj.saveState()
        canvas_obj.setFillColor(color, alpha=1.0)
        canvas_obj.setFont(font_name, self.font_size_pt)

        ascent = pdfmetrics.getAscent(font_name) / 1000.0 * self.font_size_pt
        descent = pdfmetrics.getDescent(font_name) / 1000.0 * self.font_size_pt
        baseline_y = center_y_pt - (ascent + descent) / 2.0

        canvas_obj.drawCentredString(center_x_pt, baseline_y, text)
        canvas_obj.restoreState()


PDF_TITLE_BLOCK = PDFTextBlock(
    name="pdf_title_block",
    left_mm=0,
    right_mm=84,
    top_offset_mm=52.5,
    bottom_offset_mm=67,
    font_size_px=20.0,
)

PDF_WID_BLOCK = PDFTextBlock(
    name="pdf_wid_block",
    left_mm=52,
    right_mm=78,
    top_offset_mm=10,
    bottom_offset_mm=21,
    font_size_px=60,
)

PDF_GEO_BLOCK = PDFTextBlock(
    name="pdf_geo_block",
    left_mm=54.5,
    right_mm=74.5,
    top_offset_mm=32.5,
    bottom_offset_mm=35,
    font_size_px=8,
)

PDF_COLOR_BLOCK = PDFTextBlock(
    name="pdf_color_block",
    left_mm=45.5,
    right_mm=60.5,
    top_offset_mm=40,
    bottom_offset_mm=48.5,
    font_size_px=14,
)

PDF_BPM_BLOCK = PDFTextBlock(
    name="pdf_bpm_block",
    left_mm=70,
    right_mm=82,
    top_offset_mm=40,
    bottom_offset_mm=48.5,
    font_size_px=14,
)


@dataclass
class Rect:
    x: float
    y: float
    width: float
    height: float
    is_hole: bool = False

    def contains(self, px: float, py: float) -> bool:
        return self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height


def _consume_number(source: str, start: int) -> tuple[float | None, int]:
    idx = start
    length = len(source)
    while idx < length and source[idx] in SEPARATORS:
        idx += 1
    if idx >= length:
        return None, idx
    match = NUMBER_RE.match(source, idx)
    if not match:
        return None, idx
    return float(match.group()), match.end()


def _polygon_area(points: List[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for i, (x1, y1) in enumerate(points):
        x2, y2 = points[(i + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return area / 2.0


def _extract_rectangles(path_data: str) -> List[Rect]:
    rects: List[Rect] = []
    idx = 0
    current = (0.0, 0.0)

    while idx < len(path_data):
        cmd = path_data[idx]
        if cmd not in "Mm":
            idx += 1
            continue

        is_relative = cmd == "m"
        idx += 1

        x, idx = _consume_number(path_data, idx)
        y, idx = _consume_number(path_data, idx)
        if x is None or y is None:
            raise ValueError("Malformed path: expected coordinates after 'M'.")
        if is_relative:
            x += current[0]
            y += current[1]

        current = (x, y)
        start_point = current
        points = [current]

        while idx < len(path_data):
            cmd = path_data[idx]
            if cmd in SEPARATORS:
                idx += 1
                continue

            if cmd in "Zz":
                idx += 1
                current = start_point
                break

            if cmd in "Mm":
                break

            if cmd in "Hh":
                relative = cmd == "h"
                idx += 1
                while True:
                    value, next_idx = _consume_number(path_data, idx)
                    if value is None:
                        break
                    idx = next_idx
                    new_x = current[0] + value if relative else value
                    current = (new_x, current[1])
                    points.append(current)
                continue

            if cmd in "Vv":
                relative = cmd == "v"
                idx += 1
                while True:
                    value, next_idx = _consume_number(path_data, idx)
                    if value is None:
                        break
                    idx = next_idx
                    new_y = current[1] + value if relative else value
                    current = (current[0], new_y)
                    points.append(current)
                continue

            if cmd in "Ll":
                relative = cmd == "l"
                idx += 1
                while True:
                    x_value, next_idx = _consume_number(path_data, idx)
                    if x_value is None:
                        break
                    y_value, next_idx = _consume_number(path_data, next_idx)
                    if y_value is None:
                        raise ValueError("Malformed path: expected y coordinate for 'L'.")
                    idx = next_idx
                    new_x = current[0] + x_value if relative else x_value
                    new_y = current[1] + y_value if relative else y_value
                    current = (new_x, new_y)
                    points.append(current)
                continue

            raise ValueError(f"Unsupported SVG command '{cmd}' encountered.")

        if len(points) < 2:
            continue

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max_x - min_x
        height = max_y - min_y
        if width <= 0 or height <= 0:
            continue

        area = _polygon_area(points)
        rects.append(Rect(min_x, min_y, width, height, is_hole=area < 0))

    return rects


def _format_float(value: float) -> str:
    text = f"{value:.4f}"
    text = text.rstrip("0").rstrip(".")
    return text or "0"


def _build_pixel_rects(
    rects: Iterable[Rect],
    view_width: float,
    view_height: float,
    pixel_size: float,
    pixel_gap: float,
) -> List[Rect]:
    rect_list = list(rects)
    if not rect_list:
        return []

    cols = max(1, int((view_width + pixel_gap) // (pixel_size + pixel_gap)))
    rows = max(1, int((view_height + pixel_gap) // (pixel_size + pixel_gap)))

    total_width = cols * pixel_size + (cols - 1) * pixel_gap
    total_height = rows * pixel_size + (rows - 1) * pixel_gap

    offset_x = (view_width - total_width) / 2.0
    offset_y = (view_height - total_height) / 2.0

    pixels: List[Rect] = []
    step = pixel_size + pixel_gap

    for row in range(rows):
        py = offset_y + row * step
        center_y = py + pixel_size / 2.0
        for col in range(cols):
            px = offset_x + col * step
            center_x = px + pixel_size / 2.0

            winding = 0
            for rect in rect_list:
                if rect.contains(center_x, center_y):
                    winding += -1 if rect.is_hole else 1

            if winding != 0:
                pixels.append(Rect(px, py, pixel_size, pixel_size))

    return pixels


def _apply_pixel_destruction(
    pixels: Sequence[Rect],
    threshold: float,
    seed: str,
    img_width,
    img_height,
) -> List[Rect]:
    if threshold <= 0:
        return list(pixels)

    if not pixels:
        return []

    clipped_threshold = max(0.0, min(threshold, 1.0))
    rng = random.Random(seed)
    survivors: List[Rect] = []

    min_x = min(p.x for p in pixels)
    min_y = min(p.y for p in pixels)
    max_x = max(p.x + p.width for p in pixels)
    max_y = max(p.y + p.height for p in pixels)

    for pixel in pixels:
        is_border = (
            pixel.x == min_x or
            pixel.y == min_y or
            pixel.x + pixel.width == max_x or
            pixel.y + pixel.height == max_y
        )

        if is_border or (not is_border and rng.random() <= clipped_threshold):
            survivors.append(pixel)

    return survivors


def _generate_pixelated_border_svg(
    svg_path: Path,
    *,
    pixel_size: float,
    pixel_gap: float,
    destroy_threshold: float,
    seed: str,
) -> str:
    svg_text = svg_path.read_text(encoding="utf-8")

    viewbox_match = re.search(r'viewBox="([^"]+)"', svg_text)
    if not viewbox_match:
        raise ValueError("Input SVG is missing a viewBox attribute.")

    viewbox_values = [float(part) for part in viewbox_match.group(1).split()]
    if len(viewbox_values) != 4:
        raise ValueError("viewBox must contain four numbers: min-x, min-y, width, height.")

    _, _, view_width, view_height = viewbox_values

    path_match = re.search(r'<path[^>]*d="([^"]+)"', svg_text)
    if not path_match:
        raise ValueError("No <path> element with a 'd' attribute found in SVG.")

    path_data = path_match.group(1)
    rects = _extract_rectangles(path_data)
    if not rects:
        raise ValueError("No rectangular subpaths could be derived from path data.")

    pixel_rects = _build_pixel_rects(rects, view_width, view_height, pixel_size, pixel_gap)
    pixel_rects = _apply_pixel_destruction(pixel_rects, destroy_threshold, seed, view_width, view_height)

    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox_match.group(1)}">']
    for rect in pixel_rects:
        lines.append(
            f'<rect x="{_format_float(rect.x)}" y="{_format_float(rect.y)}" '
            f'width="{_format_float(rect.width)}" height="{_format_float(rect.height)}" fill="{PIXEL_FG_COLOR}"/>'
        )
    lines.append("</svg>")

    return "\n".join(lines)


def create_print_pdf(
    output_path: Path = OUTPUT_PDF,
    qr_source: Path = QR_SOURCE_SVG,
    border_svg: Path = BORDER_SVG,
    config: dict = None,
) -> Path:
    bg_color = CMYKColor(0, 0, 0, 0, alpha=1)
    fg_color = CMYKColor(1, 1, 1, 1, alpha=1)
    font_name = _ensure_font_registered(FONT_PATH, TITLE_FONT_NAME)

    if config is None:
        try:
            config = load_config(CONFIG_PATH)
        except FileNotFoundError:
            config = {}

    page_width = mm_to_pt(PAGE_WIDTH_MM)
    page_height = mm_to_pt(PAGE_HEIGHT_MM)
    qr_width = mm_to_pt(QR_SIZE_MM)
    qr_height = mm_to_pt(QR_SIZE_MM)
    qr_drawing = _prepare_svg_drawing(qr_source)
    _scale_drawing(qr_drawing, qr_width, qr_height)

    destroy_seed = str((config or {}).get("wid") or DEFAULT_DESTROY_SEED)
    pixel_size = float(config.get("border_pixel_size", DEFAULT_PIXEL_SIZE)) if config else DEFAULT_PIXEL_SIZE
    pixel_gap = float(config.get("border_pixel_gap", DEFAULT_PIXEL_GAP)) if config else DEFAULT_PIXEL_GAP
    destroy_threshold_value = config.get("border_destroy_threshold") if config else None
    try:
        destroy_threshold = float(destroy_threshold_value) if destroy_threshold_value is not None else DEFAULT_DESTROY_THRESHOLD
    except (TypeError, ValueError):
        destroy_threshold = DEFAULT_DESTROY_THRESHOLD

    pixel_svg = _generate_pixelated_border_svg(
        border_svg,
        pixel_size=pixel_size,
        pixel_gap=pixel_gap,
        destroy_threshold=destroy_threshold,
        seed=destroy_seed,
    )

    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False, encoding="utf-8") as tmp_svg:
        tmp_svg.write(pixel_svg)
        pixel_border_path = Path(tmp_svg.name)

    try:
        border_drawing = _prepare_svg_drawing(pixel_border_path)
    finally:
        try:
            pixel_border_path.unlink(missing_ok=True)
        except FileNotFoundError:
            pass

    _scale_drawing(border_drawing, mm_to_pt(CONTENT_WIDTH_MM), mm_to_pt(CONTENT_HEIGHT_MM))
    _apply_cmyk_color(border_drawing, fg_color)

    c = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))
    c.setTitle(config.get("pdf_title", "QR Print"))
    c.setFillColor(CMYKColor(0, 0, 0, 0), alpha=1.0)
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    positions = []
    gap = 3.0
    num_cols = 2
    num_rows = 4
    total_content_width = num_cols * CONTENT_WIDTH_MM + (num_cols - 1) * gap
    total_content_height = num_rows * CONTENT_HEIGHT_MM + (num_rows - 1) * gap
    margin_x = (PAGE_WIDTH_MM - total_content_width) / 2
    margin_y = (PAGE_HEIGHT_MM - total_content_height) / 2
    for row in range(num_rows):
        for col in range(num_cols):
            x_mm = margin_x + col * (CONTENT_WIDTH_MM + gap)
            y_mm = margin_y + row * (CONTENT_HEIGHT_MM + gap)
            positions.append((x_mm, y_mm))

    title_text = config.get("title")
    wid_text = config.get("wid")
    geo_text = config.get("geo")
    color_text = config.get("color")
    bpm_text = config.get("bpm")

    c.beginForm('a7_form')
    c.setFillColor(bg_color, alpha=1.0)
    c.rect(0, 0, mm_to_pt(CONTENT_WIDTH_MM), mm_to_pt(CONTENT_HEIGHT_MM), fill=1, stroke=0)

    qr_pos_x = mm_to_pt(QR_POS_X_MM)
    qr_pos_y = mm_to_pt(CONTENT_HEIGHT_MM) - mm_to_pt(QR_POS_Y_MM + QR_SIZE_MM)
    _draw_svg(c, qr_drawing, qr_pos_x, qr_pos_y)

    _draw_svg(c, border_drawing, 0, 0)

    PDF_TITLE_BLOCK.draw(c, title_text, font_name, fg_color, 0, 0)
    PDF_WID_BLOCK.draw(c, wid_text, font_name, fg_color, 0, 0)
    PDF_GEO_BLOCK.draw(c, geo_text, font_name, fg_color, 0, 0)
    PDF_COLOR_BLOCK.draw(c, color_text, font_name, fg_color, 0, 0)
    PDF_BPM_BLOCK.draw(c, bpm_text, font_name, fg_color, 0, 0)
    c.endForm()

    for pos_x_mm, pos_y_mm in positions:
        c.saveState()
        c.translate(mm_to_pt(pos_x_mm), mm_to_pt(pos_y_mm))
        c.doForm('a7_form')
        c.restoreState()

    c.showPage()
    c.save()
    return output_path


def main() -> None:
    create_print_pdf()


if __name__ == "__main__":
    main()

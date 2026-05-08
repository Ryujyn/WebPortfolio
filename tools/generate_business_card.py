from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode.qr import QrCodeWidget


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "images"
OUT_DIR = ROOT / "assets" / "business-card"

LOGO_PATH = ASSET_DIR / "sparx-logo.png.png"
FRONT_PNG = OUT_DIR / "business-card-front.png"
BACK_PNG = OUT_DIR / "business-card-back.png"
PRINT_PDF = OUT_DIR / "business-card-print.pdf"

URL = "https://buildwithsparx.com"
NAME = "Rhachata Meesilp"
TITLE = "F&B Solutions Engineer"
EMAIL = "rrhata2001@gmail.com"
PHONE = "083-156-5944"
LINE_ID = "ryu2001."

DPI = 300
TRIM_W_MM = 90
TRIM_H_MM = 54          # standard CR80 height
BLEED_MM = 3
FULL_W_MM = TRIM_W_MM + BLEED_MM * 2
FULL_H_MM = TRIM_H_MM + BLEED_MM * 2

PX_PER_MM = DPI / 25.4
FULL_W = round(FULL_W_MM * PX_PER_MM)
FULL_H = round(FULL_H_MM * PX_PER_MM)
BLEED = round(BLEED_MM * PX_PER_MM)
TRIM_W = round(TRIM_W_MM * PX_PER_MM)
TRIM_H = round(TRIM_H_MM * PX_PER_MM)

OFF_WHITE = "#FAF7F2"
DARK = "#000000"           # pure black for PNG preview
WARM_GRAY = "#C8BFB0"
TEXT = "#000000"   # pure black → CMYK K=100% in PDF
MID_TEXT = "#666666"
LIGHT_TEXT = "#888888"

# Rich Black for print: CMYK C=60 M=40 Y=40 K=100 (Pillow uses 0–255 scale)
RICH_BLACK_CMYK = (round(60 * 255 / 100), round(40 * 255 / 100),
                   round(40 * 255 / 100), 255)  # (153, 102, 102, 255)

FONT_REG = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_LIGHT = Path(r"C:\Windows\Fonts\segoeuil.ttf")
FONT_MED = Path(r"C:\Windows\Fonts\segoeuib.ttf")


def mm_px(value: float) -> int:
    return round(value * PX_PER_MM)


def pt_px(value: float) -> int:
    return round(value * DPI / 72)


def load_font(path: Path, pt: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), pt_px(pt))


def dark_logo_mask() -> Image.Image:
    source = Image.open(LOGO_PATH).convert("RGB")
    gray = source.convert("L")
    mask = gray.point(lambda p: 255 if p < 210 else 0, "L")
    bbox = mask.getbbox()
    if bbox is None:
        raise RuntimeError("Could not detect dark logo pixels.")
    pad = 16
    bbox = (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(source.width, bbox[2] + pad),
        min(source.height, bbox[3] + pad),
    )
    return mask.crop(bbox)


def logo_image(width_mm: float, color: str) -> Image.Image:
    mask = dark_logo_mask()
    target_w = mm_px(width_mm)
    target_h = round(mask.height * target_w / mask.width)
    mask = mask.resize((target_w, target_h), Image.Resampling.LANCZOS)
    logo = Image.new("RGBA", mask.size, color)
    logo.putalpha(mask)
    return logo


def qr_grid(text: str) -> list[list[bool]]:
    qr = QrCodeWidget(text).qr
    qr.make()
    size = qr.getModuleCount()
    return [[bool(qr.isDark(r, c)) for c in range(size)] for r in range(size)]


def qr_image_transparent(size_mm: float) -> Image.Image:
    """QR code with transparent background — blends into card color."""
    modules = qr_grid(URL)
    module_count = len(modules)
    quiet = 3
    total_modules = module_count + quiet * 2
    target = mm_px(size_mm)
    scale = max(1, target // total_modules)
    qr_px = total_modules * scale
    image = Image.new("RGBA", (qr_px, qr_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    dark_rgba = (*[int(x) for x in bytes.fromhex(DARK.lstrip("#"))], 255)
    for r, row in enumerate(modules):
        for c, dark in enumerate(row):
            if dark:
                x0 = (c + quiet) * scale
                y0 = (r + quiet) * scale
                draw.rectangle(
                    (x0, y0, x0 + scale - 1, y0 + scale - 1),
                    fill=dark_rgba,
                )
    return image.resize((target, target), Image.Resampling.NEAREST)


def make_front() -> Image.Image:
    image = Image.new("RGB", (FULL_W, FULL_H), OFF_WHITE)
    draw  = ImageDraw.Draw(image)

    # ── Safe area bounds (5mm from every trim edge) ────────────────────────
    EDGE_PAD    = mm_px(5)
    safe_top    = BLEED + EDGE_PAD
    safe_bottom = BLEED + TRIM_H - EDGE_PAD
    safe_left   = BLEED + EDGE_PAD
    safe_right  = BLEED + TRIM_W - EDGE_PAD
    safe_h      = safe_bottom - safe_top

    # ── Fonts ──────────────────────────────────────────────────────────────
    name_font    = load_font(FONT_MED,   13.5)   # medium weight, 20% bigger
    title_font   = load_font(FONT_LIGHT,  8)
    contact_font = load_font(FONT_REG,    6.5)
    label_font   = load_font(FONT_REG,    5.5)

    # ── Measure name + title ───────────────────────────────────────────────
    name_bbox    = draw.textbbox((0, 0), NAME,  font=name_font)
    title_bbox   = draw.textbbox((0, 0), TITLE, font=title_font)
    name_h       = name_bbox[3]  - name_bbox[1]
    title_h      = title_bbox[3] - title_bbox[1]
    name_title_gap = mm_px(2)

    # ── Measure contact rows ───────────────────────────────────────────────
    contact_lines   = [EMAIL, PHONE, f"LINE: {LINE_ID}"]
    contact_row_gap = mm_px(1.5)
    sample_b = draw.textbbox((0, 0), EMAIL, font=contact_font)
    row_h    = sample_b[3] - sample_b[1]
    contact_block_h = len(contact_lines) * row_h + (len(contact_lines) - 1) * contact_row_gap

    # ── Vertically center the whole text block ────────────────────────────
    gap_4mm       = mm_px(4)
    total_block_h = name_h + name_title_gap + title_h + gap_4mm + contact_block_h
    block_y       = safe_top + (safe_h - total_block_h) // 2

    # ── Draw name + title ──────────────────────────────────────────────────
    draw.text((safe_left, block_y), NAME, font=name_font, fill=TEXT)
    draw.text((safe_left, block_y + name_h + name_title_gap), TITLE, font=title_font, fill=MID_TEXT)

    # ── Draw contacts ──────────────────────────────────────────────────────
    cy = block_y + name_h + name_title_gap + title_h + gap_4mm
    for line in contact_lines:
        draw.text((safe_left, cy), line, font=contact_font, fill=LIGHT_TEXT)
        cy += row_h + contact_row_gap

    # ── QR — bottom-right, 22mm, flush to safe_bottom ─────────────────────
    qr = qr_image_transparent(22)
    label_text = "View Work"
    label_bbox = draw.textbbox((0, 0), label_text, font=label_font)
    label_h    = label_bbox[3] - label_bbox[1]
    label_gap  = mm_px(1)

    qr_x = safe_right - qr.width
    qr_y = safe_bottom - label_h - label_gap - qr.height

    image.paste(qr, (qr_x, qr_y), qr)
    lbl_x = qr_x + (qr.width - (label_bbox[2] - label_bbox[0])) // 2
    draw.text((lbl_x, qr_y + qr.height + label_gap), label_text, font=label_font, fill=LIGHT_TEXT)

    return image


def make_back() -> Image.Image:
    image = Image.new("RGB", (FULL_W, FULL_H), DARK)
    logo = logo_image(38, "white")
    image.paste(logo, ((FULL_W - logo.width) // 2, (FULL_H - logo.height) // 2), logo)
    return image


def save_png(image: Image.Image, path: Path) -> None:
    """Save as RGB PNG — correct for screen preview."""
    image.save(path, dpi=(DPI, DPI))


def register_pdf_fonts() -> tuple[str, str, str]:
    pdfmetrics.registerFont(TTFont("SegoeUI", str(FONT_REG)))
    pdfmetrics.registerFont(TTFont("SegoeUILight", str(FONT_LIGHT)))
    pdfmetrics.registerFont(TTFont("SegoeUIMed", str(FONT_MED)))
    return "SegoeUI", "SegoeUILight", "SegoeUIMed"


def add_crop_marks(c: canvas.Canvas) -> None:
    page_w = FULL_W_MM * mm
    page_h = FULL_H_MM * mm
    bleed = BLEED_MM * mm
    trim_w = TRIM_W_MM * mm
    trim_h = TRIM_H_MM * mm
    c.setStrokeColor(colors.HexColor("#666666"))
    c.setLineWidth(0.35)

    xs = [bleed, bleed + trim_w]
    ys = [bleed, bleed + trim_h]
    for x in xs:
        c.line(x, 0, x, bleed - 0.7 * mm)
        c.line(x, page_h, x, page_h - bleed + 0.7 * mm)
    for y in ys:
        c.line(0, y, bleed - 0.7 * mm, y)
        c.line(page_w, y, page_w - bleed + 0.7 * mm, y)

    mark = 4 * mm
    c.line(bleed, bleed - mark, bleed, bleed - 0.7 * mm)
    c.line(bleed - mark, bleed, bleed - 0.7 * mm, bleed)
    c.line(bleed + trim_w, bleed - mark, bleed + trim_w, bleed - 0.7 * mm)
    c.line(bleed + trim_w + mark, bleed, bleed + trim_w + 0.7 * mm, bleed)
    c.line(bleed, bleed + trim_h + mark, bleed, bleed + trim_h + 0.7 * mm)
    c.line(bleed - mark, bleed + trim_h, bleed - 0.7 * mm, bleed + trim_h)
    c.line(bleed + trim_w, bleed + trim_h + mark, bleed + trim_w, bleed + trim_h + 0.7 * mm)
    c.line(bleed + trim_w + mark, bleed + trim_h, bleed + trim_w + 0.7 * mm, bleed + trim_h)


def add_side(c: canvas.Canvas, image: Image.Image) -> None:
    """Embed front card as lossless PNG — preserves sharp text and QR edges."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    c.drawImage(ImageReader(buffer), 0, 0, FULL_W_MM * mm, FULL_H_MM * mm)
    add_crop_marks(c)


def add_back_side(c: canvas.Canvas) -> None:
    """Back card: fill with native CMYKColor rectangle, then overlay logo PNG."""
    page_w = FULL_W_MM * mm
    page_h = FULL_H_MM * mm

    # setFillColorCMYK writes raw '/DeviceCMYK k' operator directly into PDF stream
    # — no RGB conversion, printer receives C=60 M=40 Y=40 K=100 exactly
    c.setFillColorCMYK(0.60, 0.40, 0.40, 1.00)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # White logo (RGBA PNG) — drawImage with mask='auto' respects transparency
    logo = logo_image(38, "white")
    lx_px = (FULL_W - logo.width) // 2
    ly_px = (FULL_H - logo.height) // 2

    lx_pt = lx_px / PX_PER_MM * mm
    ly_pt = (FULL_H - ly_px - logo.height) / PX_PER_MM * mm  # ReportLab: y from bottom
    lw_pt = logo.width / PX_PER_MM * mm
    lh_pt = logo.height / PX_PER_MM * mm

    buf = io.BytesIO()
    logo.save(buf, format="PNG")
    buf.seek(0)
    c.drawImage(ImageReader(buf), lx_pt, ly_pt, lw_pt, lh_pt, mask="auto")

    add_crop_marks(c)


def save_pdf(front: Image.Image, back: Image.Image) -> None:
    register_pdf_fonts()
    c = canvas.Canvas(str(PRINT_PDF), pagesize=(FULL_W_MM * mm, FULL_H_MM * mm))
    c.setTitle("SPARX Business Card")
    c.setAuthor(NAME)
    add_side(c, front)          # front: RGB → CMYK conversion
    c.showPage()
    add_back_side(c)            # back: built directly in CMYK Rich Black
    c.save()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    front = make_front()
    back = make_back()
    save_png(front, FRONT_PNG)
    save_png(back, BACK_PNG)
    save_pdf(front, back)
    print("assets/business-card/business-card-front.png")
    print("assets/business-card/business-card-back.png")
    print("assets/business-card/business-card-print.pdf")


if __name__ == "__main__":
    main()

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "dist"
PDF_PATH = OUT_DIR / "rhachata-meesilp-resume.pdf"
QR_SVG_PATH = OUT_DIR / "portfolio-qr.svg"
QR_PNG_PATH = OUT_DIR / "portfolio-qr.png"

OWNER = "Rhachata Meesilp"
BRAND = "Ryujyn"
ROLE = "COMMIS CHEF / AUTOMATION BUILDER"
WEBSITE_URL = "https://ryujyn.github.io/WebPortfolio/"
EMAIL = "rrhata2001@gmail.com"
PHONE = "083-156-5944"
LINE_ID = "ryu2001."
GITHUB = "github.com/ryujyn"
LOCATION = "Bangkok, Thailand"

NAVY = colors.HexColor("#0e1c34")
NAVY_2 = colors.HexColor("#16294a")
YELLOW = colors.HexColor("#f3c13a")
INK = colors.HexColor("#0e1c34")
MUTED = colors.HexColor("#4d5a72")
FAINT = colors.HexColor("#8693aa")
PAPER = colors.HexColor("#f6f8fc")
PAPER_2 = colors.HexColor("#eef2f9")
LINE_COLOR = colors.HexColor("#dbe1ec")
WHITE = colors.white


def _bits_from_int(value: int, length: int) -> list[int]:
    return [(value >> i) & 1 for i in reversed(range(length))]


def _gf_tables() -> tuple[list[int], list[int]]:
    exp = [0] * 512
    log = [0] * 256
    x = 1
    for i in range(255):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        exp[i] = exp[i - 255]
    return exp, log


GF_EXP, GF_LOG = _gf_tables()


def _gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return GF_EXP[GF_LOG[a] + GF_LOG[b]]


def _rs_generator(degree: int) -> list[int]:
    poly = [1]
    for i in range(degree):
        nxt = [0] * (len(poly) + 1)
        for j, coef in enumerate(poly):
            nxt[j] ^= _gf_mul(coef, 1)
            nxt[j + 1] ^= _gf_mul(coef, GF_EXP[i])
        poly = nxt
    return poly


def _rs_remainder(data: list[int], degree: int) -> list[int]:
    gen = _rs_generator(degree)
    rem = [0] * degree
    for byte in data:
        factor = byte ^ rem[0]
        rem = rem[1:] + [0]
        for i in range(degree):
            rem[i] ^= _gf_mul(gen[i + 1], factor)
    return rem


def _make_codewords(text: str) -> list[int]:
    data_capacity = 80  # QR version 4, error correction L.
    raw = text.encode("utf-8")
    bits: list[int] = [0, 1, 0, 0] + _bits_from_int(len(raw), 8)
    for byte in raw:
        bits += _bits_from_int(byte, 8)
    bits += [0] * min(4, data_capacity * 8 - len(bits))
    while len(bits) % 8:
        bits.append(0)

    data = []
    for i in range(0, len(bits), 8):
        value = 0
        for bit in bits[i : i + 8]:
            value = (value << 1) | bit
        data.append(value)

    pads = [0xEC, 0x11]
    while len(data) < data_capacity:
        data.append(pads[len(data) % 2])
    return data + _rs_remainder(data, 20)


def _blank_qr(version: int = 4) -> tuple[list[list[bool | None]], list[list[bool]]]:
    size = version * 4 + 17
    modules: list[list[bool | None]] = [[None] * size for _ in range(size)]
    function = [[False] * size for _ in range(size)]

    def set_module(r: int, c: int, dark: bool, is_function: bool = True) -> None:
        if 0 <= r < size and 0 <= c < size:
            modules[r][c] = dark
            if is_function:
                function[r][c] = True

    def finder(r: int, c: int) -> None:
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < size and 0 <= cc < size):
                    continue
                dark = 0 <= dr <= 6 and 0 <= dc <= 6 and (
                    dr in (0, 6) or dc in (0, 6) or (2 <= dr <= 4 and 2 <= dc <= 4)
                )
                set_module(rr, cc, dark)

    finder(0, 0)
    finder(0, size - 7)
    finder(size - 7, 0)

    for i in range(8, size - 8):
        dark = i % 2 == 0
        set_module(6, i, dark)
        set_module(i, 6, dark)

    for dr in range(-2, 3):
        for dc in range(-2, 3):
            set_module(26 + dr, 26 + dc, max(abs(dr), abs(dc)) != 1)

    set_module(25, 8, True)
    for i in range(9):
        if i != 6:
            set_module(8, i, False)
            set_module(i, 8, False)
    for i in range(8):
        set_module(size - 1 - i, 8, False)
        set_module(8, size - 1 - i, False)

    return modules, function


def _mask_bit(mask: int, r: int, c: int) -> bool:
    if mask == 0:
        return (r + c) % 2 == 0
    if mask == 1:
        return r % 2 == 0
    if mask == 2:
        return c % 3 == 0
    if mask == 3:
        return (r + c) % 3 == 0
    if mask == 4:
        return (r // 2 + c // 3) % 2 == 0
    if mask == 5:
        return ((r * c) % 2 + (r * c) % 3) == 0
    if mask == 6:
        return (((r * c) % 2 + (r * c) % 3) % 2) == 0
    return (((r + c) % 2 + (r * c) % 3) % 2) == 0


def _draw_data(modules: list[list[bool | None]], function: list[list[bool]], codewords: list[int], mask: int) -> None:
    size = len(modules)
    bits = []
    for byte in codewords:
        bits += _bits_from_int(byte, 8)
    bit_index = 0
    upwards = True
    c = size - 1
    while c > 0:
        if c == 6:
            c -= 1
        rows = range(size - 1, -1, -1) if upwards else range(size)
        for r in rows:
            for dc in (0, 1):
                cc = c - dc
                if function[r][cc]:
                    continue
                dark = bool(bits[bit_index]) if bit_index < len(bits) else False
                if _mask_bit(mask, r, cc):
                    dark = not dark
                modules[r][cc] = dark
                bit_index += 1
        upwards = not upwards
        c -= 2


def _format_bits(mask: int) -> int:
    data = (1 << 3) | mask
    value = data << 10
    gen = 0x537
    for i in range(14, 9, -1):
        if (value >> i) & 1:
            value ^= gen << (i - 10)
    return ((data << 10) | value) ^ 0x5412


def _draw_format(modules: list[list[bool | None]], mask: int) -> None:
    size = len(modules)
    bits = _format_bits(mask)

    def bit(i: int) -> bool:
        return ((bits >> i) & 1) != 0

    for i in range(6):
        modules[8][i] = bit(i)
    modules[8][7] = bit(6)
    modules[8][8] = bit(7)
    modules[7][8] = bit(8)
    for i in range(9, 15):
        modules[14 - i][8] = bit(i)
    for i in range(8):
        modules[size - 1 - i][8] = bit(i)
    for i in range(8, 15):
        modules[8][size - 15 + i] = bit(i)


def _penalty(modules: list[list[bool | None]]) -> int:
    size = len(modules)
    grid = [[bool(cell) for cell in row] for row in modules]
    score = 0

    for rows in (grid, list(map(list, zip(*grid)))):
        for row in rows:
            run_color = row[0]
            run_len = 1
            for cell in row[1:] + [not row[-1]]:
                if cell == run_color:
                    run_len += 1
                else:
                    if run_len >= 5:
                        score += 3 + (run_len - 5)
                    run_color = cell
                    run_len = 1

    for r in range(size - 1):
        for c in range(size - 1):
            block = grid[r][c]
            if grid[r][c + 1] == block and grid[r + 1][c] == block and grid[r + 1][c + 1] == block:
                score += 3

    dark = sum(cell for row in grid for cell in row)
    percent = dark * 100 / (size * size)
    score += int(abs(percent - 50) // 5) * 10
    return score


def make_qr(text: str) -> list[list[bool]]:
    from reportlab.graphics.barcode.qr import QrCodeWidget

    qr = QrCodeWidget(text).qr
    qr.make()
    size = qr.getModuleCount()
    return [[bool(qr.isDark(row, col)) for col in range(size)] for row in range(size)]


def write_qr_assets(grid: list[list[bool]]) -> ImageReader:
    size = len(grid)
    quiet = 4
    scale = 12
    total = (size + quiet * 2) * scale
    img = Image.new("RGB", (total, total), "white")
    pixels = img.load()
    for r, row in enumerate(grid):
        for c, dark in enumerate(row):
            if not dark:
                continue
            x0 = (c + quiet) * scale
            y0 = (r + quiet) * scale
            for y in range(y0, y0 + scale):
                for x in range(x0, x0 + scale):
                    pixels[x, y] = (14, 28, 52)

    img.save(QR_PNG_PATH)

    rects = []
    for r, row in enumerate(grid):
        for c, dark in enumerate(row):
            if dark:
                rects.append(
                    f'<rect x="{(c + quiet) * scale}" y="{(r + quiet) * scale}" width="{scale}" height="{scale}"/>'
                )
    QR_SVG_PATH.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total} {total}">'
        f'<rect width="{total}" height="{total}" fill="#fff"/><g fill="#0e1c34">{"".join(rects)}</g></svg>',
        encoding="utf-8",
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return ImageReader(buffer)


def draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float, size: int, leading: int, color=MUTED) -> float:
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if c.stringWidth(candidate, "Helvetica", size) <= width:
            line = candidate
        else:
            c.drawString(x, y, line)
            y -= leading
            line = word
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def heading(c: canvas.Canvas, text: str, x: float, y: float, dark: bool = False) -> None:
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(WHITE if dark else INK)
    c.drawString(x, y, text.upper())
    c.setStrokeColor(YELLOW)
    c.setLineWidth(2)
    c.line(x, y - 7, x + 42, y - 7)


def pill(c: canvas.Canvas, text: str, x: float, y: float, pad_x: float = 7) -> float:
    c.setFont("Helvetica-Bold", 7)
    text_w = c.stringWidth(text, "Helvetica-Bold", 7)
    w = text_w + pad_x * 2
    c.setFillColor(PAPER_2)
    c.roundRect(x, y - 2, w, 16, 8, stroke=0, fill=1)
    c.setFillColor(INK)
    c.drawString(x + pad_x, y + 3, text)
    return x + w + 5


def build_pdf(qr_image: ImageReader) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    c = canvas.Canvas(str(PDF_PATH), pagesize=A4)
    w, h = A4

    left_w = 205
    margin = 34
    right_x = left_w + 34
    right_w = w - right_x - margin

    c.setFillColor(PAPER)
    c.rect(0, 0, w, h, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.rect(0, 0, left_w, h, stroke=0, fill=1)

    # Header, adapted from the older resume: name centered at top with role below.
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 31)
    c.drawString(right_x, h - 64, OWNER)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(YELLOW)
    c.drawString(right_x, h - 84, ROLE)
    c.setFont("Helvetica", 9)
    c.setFillColor(FAINT)

    c.setFillColor(PAPER)
    c.rect(w - margin - 78, h - 96, 82, 18, stroke=0, fill=1)
    c.setFillColor(FAINT)
    c.drawRightString(w - margin, h - 84, "Resume / 2026")

    # Left column.
    lx = 28
    y = h - 76
    c.setFillColor(YELLOW)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(lx, y, BRAND.upper())
    y -= 18
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(lx, y, "Resume")
    y -= 42

    heading(c, "Contact", lx, y, dark=True)
    y -= 26
    contact_items = [
        ("EMAIL", EMAIL),
        ("PHONE", PHONE),
        ("LINE", LINE_ID),
        ("GITHUB", GITHUB),
        ("BASED IN", LOCATION),
    ]
    for label, value in contact_items:
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(YELLOW)
        c.drawString(lx, y, label)
        y -= 12
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#e5ecf7"))
        c.drawString(lx, y, value)
        y -= 20

    y -= 6
    heading(c, "Focus", lx, y, dark=True)
    y -= 27
    for item in ["Automation", "AI Agents", "Micro-SaaS", "B2B Tools"]:
        c.setFillColor(colors.HexColor("#223657"))
        c.roundRect(lx, y - 3, 132, 17, 8, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(lx + 9, y + 2, item)
        y -= 23

    y -= 4
    heading(c, "Core Skills", lx, y, dark=True)
    y -= 27
    for item in ["Beginner mindset", "Team Work", "Time Management", "Prioritize"]:
        c.setFillColor(colors.HexColor("#223657"))
        c.roundRect(lx, y - 3, 148, 17, 8, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(lx + 9, y + 2, item)
        y -= 23

    y -= 2
    heading(c, "Scan Website", lx, y, dark=True)
    y -= 118
    qr_size = 92
    c.setFillColor(WHITE)
    c.roundRect(lx, y, qr_size, qr_size, 8, stroke=0, fill=1)
    c.drawImage(qr_image, lx + 7, y + 7, qr_size - 14, qr_size - 14, mask="auto")
    c.setFont("Helvetica", 6.8)
    c.setFillColor(colors.HexColor("#d7e0ef"))
    c.drawString(lx, y - 13, WEBSITE_URL.replace("https://", ""))

    # Right column body.
    y = h - 128
    heading(c, "About me", right_x, y)
    y -= 25
    y = draw_wrapped(
        c,
        "A commis chef who is growing into automation and practical software. I understand restaurant operations from real kitchen work, "
        "and I use that background to build tools that reduce repeated checks, scattered data, and fragile daily workflows.",
        right_x,
        y,
        right_w,
        9,
        13,
        MUTED,
    )

    y -= 14
    heading(c, "Experience Snapshot", right_x, y)
    y -= 30
    experiences = [
        (
            "Tribe Sky Beach Club",
            "Nov 2025 - Present",
            "Current kitchen team member, supporting daily preparation and service in a high-traffic hospitality environment.",
            True,
        ),
        (
            "Siam Orchid cafe",
            "Jul 2024 - Oct 2025",
            "Prepared breakfast buffet stations including salads, fruits, bread, and main dishes, while replenishing food for daily service.",
            False,
        ),
        (
            "Thongyoy cafe",
            "Apr 2024 - Jun 2024",
            "Trained on the menu before store opening, made fruit smoothies, handled payments, prepared mango sticky rice, and checked stock.",
            False,
        ),
        (
            "Miracle Suvarnabhumi Airport Hotel",
            "Mar 2022 - Mar 2024",
            "Maintained station cleanliness, prepared ingredients for a la carte orders, cooked lunch and dinner, and helped prepare staff meals.",
            False,
        ),
    ]
    for name, period, detail, is_current in experiences:
        c.setFillColor(WHITE)
        c.roundRect(right_x, y - 68, right_w, 58, 9, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 13 if is_current else 12)
        c.drawString(right_x + 12, y - 27, name)
        c.setFillColor(YELLOW)
        c.setFont("Helvetica-Bold", 9.2 if is_current else 8.5)
        c.drawRightString(right_x + right_w - 12, y - 27, period)
        draw_wrapped(c, detail, right_x + 12, y - 43, right_w - 24, 7.6, 10, MUTED)
        y -= 74

    y -= 16
    heading(c, "Education", right_x, y)
    y -= 28
    education = [
        ("Chonburi Sukkabot School", "2014 - 2020", "Sci - Math Classroom, GPA 3.75"),
        ("Ramkhamhaeng University", "2022 - Present", "Continuing university studies while building practical work experience."),
    ]
    for school, period, detail in education:
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 9.2)
        c.drawString(right_x, y, school)
        c.setFillColor(FAINT)
        c.setFont("Helvetica-Bold", 7.8)
        c.drawRightString(right_x + right_w, y, period)
        y -= 13
        y = draw_wrapped(c, detail, right_x, y, right_w, 7.8, 10, MUTED)
        y -= 8

    y -= 2
    heading(c, "Portfolio Note", right_x, y)
    y -= 24
    draw_wrapped(
        c,
        "KitchenBot and future software work are kept on the web portfolio. Scan the QR code to review projects, screenshots, and technical details.",
        right_x,
        y,
        right_w,
        8.5,
        12,
        MUTED,
    )

    c.setFillColor(FAINT)
    c.setFont("Helvetica", 7.5)
    c.drawString(right_x, 36, "Resume first. Portfolio projects and technical details are available through the QR code.")

    c.setTitle(f"{OWNER} Resume")
    c.setAuthor(OWNER)
    c.save()
    return

    y -= 14
    heading(c, "Featured Project", right_x, y)
    y -= 34
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 25)
    c.drawString(right_x, y, "KitchenBot")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(YELLOW)
    c.drawString(right_x + 148, y + 5, "WEB APP + LINE BOT Â· LIVE IN USE")
    y -= 25
    y = draw_wrapped(
        c,
        "A kitchen stock system for a real restaurant, with LINE alerts when supplies run low.",
        right_x,
        y,
        right_w,
        10,
        14,
        MUTED,
    )

    sections = [
        (
            "Problem",
            "Kitchen teams were re-checking stock by hand every shift. Data lived in several places, and alerts often arrived too late to act on.",
        ),
        (
            "Solution",
            "A Flask + PostgreSQL service handles the stock truth, while LINE Messaging API delivers alerts into the chat the team already uses.",
        ),
        (
            "Impact",
            "Cuts manual checking, makes closing routines calmer, and gives a real base to grow into a small B2B SaaS for restaurants.",
        ),
    ]

    card_gap = 8
    card_w = (right_w - card_gap * 2) / 3
    card_y = y - 116
    for i, (title, body) in enumerate(sections):
        x = right_x + i * (card_w + card_gap)
        c.setFillColor(WHITE)
        c.roundRect(x, card_y, card_w, 104, 10, stroke=0, fill=1)
        c.setFillColor(YELLOW)
        c.setFont("Helvetica-Bold", 7.2)
        c.drawString(x + 10, card_y + 82, title.upper())
        draw_wrapped(c, body, x + 10, card_y + 67, card_w - 20, 7.2, 10, MUTED)
    y = card_y - 28

    heading(c, "Tech Stack", right_x, y)
    y -= 28
    stack = [
        "Python + Flask",
        "PostgreSQL on Render",
        "Vanilla JavaScript",
        "LINE Messaging API",
        "Render free tier",
        "UptimeRobot /ping every 5 min",
    ]
    x = right_x
    row_y = y
    for i, item in enumerate(stack):
        x = right_x + (i % 2) * 156
        row_y = y - (i // 2) * 24
        c.setFillColor(WHITE)
        c.roundRect(x, row_y - 3, 144, 17, 8, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 7.4)
        c.drawString(x + 8, row_y + 2, item)
    y = row_y - 35

    heading(c, "Skills", right_x, y)
    y -= 28
    x = right_x
    for item in ["Python", "Flask", "PostgreSQL", "JavaScript", "HTML", "CSS", "GitHub Actions", "Prompt Engineering"]:
        next_x = pill(c, item, x, y)
        if next_x > right_x + right_w - 70:
            y -= 22
            x = right_x
            next_x = pill(c, item, x, y)
        x = next_x

    c.setFillColor(FAINT)
    c.setFont("Helvetica", 7.5)
    c.drawString(right_x, 36, "Generated from the current WebPortfolio content. QR opens the live GitHub Pages portfolio.")

    c.setTitle(f"{OWNER} Portfolio")
    c.setAuthor(OWNER)
    c.save()


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    qr_grid = make_qr(WEBSITE_URL)
    qr_image = write_qr_assets(qr_grid)
    build_pdf(qr_image)
    print("dist/rhachata-meesilp-resume.pdf")
    print("dist/portfolio-qr.svg")
    print("dist/portfolio-qr.png")


if __name__ == "__main__":
    main()


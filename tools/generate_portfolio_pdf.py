from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "dist"
PDF_PATH = OUT_DIR / "rhachata-meesilp-portfolio.pdf"
QR_SVG_PATH = OUT_DIR / "portfolio-qr.svg"

OWNER = "Rhachata Meesilp"
BRAND = "Ryujyn"
ROLE = "Chef to Sales Engineer"
WEBSITE_URL = "https://ryujyn.github.io/WebPortfolio/"
EMAIL = "rrhata2001@gmail.com"
GITHUB = "github.com/ryujyn"
PHONE = "Available on request"
LINE = "Available on request"


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
    # QR version 4, error correction L: 80 data codewords + 20 EC codewords.
    data_capacity = 80
    raw = text.encode("utf-8")
    bits: list[int] = []
    bits += [0, 1, 0, 0]
    bits += _bits_from_int(len(raw), 8)
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

    def alignment(center_r: int, center_c: int) -> None:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                dark = max(abs(dr), abs(dc)) != 1
                set_module(center_r + dr, center_c + dc, dark)

    alignment(26, 26)
    set_module(25, 8, True)

    # Reserve format information cells.
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
                bit = bits[bit_index] if bit_index < len(bits) else 0
                dark = bool(bit)
                if _mask_bit(mask, r, cc):
                    dark = not dark
                modules[r][cc] = dark
                bit_index += 1
        upwards = not upwards
        c -= 2


def _format_bits(mask: int) -> int:
    data = (1 << 3) | mask  # Error correction L.
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

    pattern = [True, False, True, True, True, False, True, False, False, False, False]
    for rows in (grid, list(map(list, zip(*grid)))):
        for row in rows:
            for i in range(size - 10):
                chunk = row[i : i + 11]
                if chunk == pattern or chunk == list(reversed(pattern)):
                    score += 40

    dark = sum(cell for row in grid for cell in row)
    percent = dark * 100 / (size * size)
    score += int(abs(percent - 50) // 5) * 10
    return score


def make_qr(text: str) -> list[list[bool]]:
    codewords = _make_codewords(text)
    best = None
    for mask in range(8):
        modules, function = _blank_qr()
        _draw_data(modules, function, codewords, mask)
        _draw_format(modules, mask)
        score = _penalty(modules)
        if best is None or score < best[0]:
            best = (score, modules)
    assert best is not None
    return [[bool(cell) for cell in row] for row in best[1]]


def write_qr_svg(grid: list[list[bool]]) -> None:
    size = len(grid)
    scale = 8
    quiet = 4
    total = (size + quiet * 2) * scale
    rects = []
    for r, row in enumerate(grid):
        for c, dark in enumerate(row):
            if dark:
                rects.append(
                    f'<rect x="{(c + quiet) * scale}" y="{(r + quiet) * scale}" width="{scale}" height="{scale}"/>'
                )
    QR_SVG_PATH.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total} {total}">'
        f'<rect width="{total}" height="{total}" fill="#fff"/><g fill="#10203d">{"".join(rects)}</g></svg>',
        encoding="utf-8",
    )


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def text_line(x: float, y: float, text: str, size: int, font: str = "F1", color: str = "10 32 61") -> str:
    return f"{color} rg BT /{font} {size} Tf {x:.2f} {y:.2f} Td ({pdf_escape(text)}) Tj ET\n"


def rect(x: float, y: float, w: float, h: float, color: str, stroke: bool = False) -> str:
    op = "B" if stroke else "f"
    return f"{color} rg {x:.2f} {y:.2f} {w:.2f} {h:.2f} re {op}\n"


def wrap(text: str, max_chars: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def build_pdf(grid: list[list[bool]]) -> bytes:
    width, height = 595, 842
    navy = "16 32 61"
    navy_dark = "9 19 36"
    yellow = "243 193 58"
    paper = "245 247 251"
    muted = "82 97 120"
    white = "255 255 255"

    content = []
    content.append(rect(0, 0, width, height, paper))
    content.append(rect(0, 0, 178, height, navy_dark))
    content.append(rect(36, 716, 78, 6, yellow))
    content.append(text_line(36, 760, BRAND.upper(), 11, "F2", yellow))
    content.append(text_line(36, 735, OWNER, 24, "F2", white))
    content.append(text_line(36, 710, ROLE, 12, "F1", "205 215 232"))

    sidebar_items = [
        ("Email", EMAIL),
        ("GitHub", GITHUB),
        ("Phone", PHONE),
        ("LINE", LINE),
    ]
    y = 650
    for label, value in sidebar_items:
        content.append(text_line(36, y, label.upper(), 7, "F2", yellow))
        for line in wrap(value, 22):
            y -= 13
            content.append(text_line(36, y, line, 9, "F1", "232 238 248"))
        y -= 20

    qr_x, qr_y, qr_size = 44, 88, 92
    content.append(rect(qr_x - 8, qr_y - 8, qr_size + 16, qr_size + 16, white))
    cell = qr_size / (len(grid) + 8)
    for r, row in enumerate(grid):
        for c, dark in enumerate(row):
            if dark:
                content.append(rect(qr_x + (c + 4) * cell, qr_y + qr_size - (r + 5) * cell, cell, cell, navy))
    content.append(text_line(36, 62, "Scan for website portfolio", 8, "F2", yellow))
    content.append(text_line(36, 48, WEBSITE_URL.replace("https://", ""), 7, "F1", "205 215 232"))

    x0 = 214
    content.append(text_line(x0, 760, "Portfolio", 11, "F2", yellow))
    content.append(text_line(x0, 728, "Restaurant problems,", 28, "F2", navy))
    content.append(text_line(x0, 695, "built into practical systems.", 28, "F2", navy))
    intro = (
        "I build automation and restaurant-tech tools from real operational pain. "
        "My background in kitchen work helps me speak with owners, understand floor pressure, "
        "and turn repeated work into clear systems."
    )
    y = 656
    for line in wrap(intro, 62):
        content.append(text_line(x0, y, line, 10, "F1", muted))
        y -= 15

    content.append(rect(x0, 552, 333, 1, yellow))
    content.append(text_line(x0, 526, "Featured Project", 10, "F2", yellow))
    content.append(text_line(x0, 495, "KitchenBot", 32, "F2", navy))
    content.append(text_line(x0, 474, "Web App + LINE Bot | Live in use", 10, "F2", muted))

    sections = [
        ("Problem", "Stock checks were repeated by hand, data lived in scattered places, and low-stock alerts often arrived too late for fast restaurant decisions."),
        ("Solution", "A Flask + PostgreSQL web app connected to LINE Messaging API, so the team can track stock signals and receive alerts in the channel they already use."),
        ("Impact", "Less manual checking, more confidence during closing routines, and a practical base for a restaurant-focused micro-SaaS."),
    ]
    y = 438
    for label, body in sections:
        content.append(text_line(x0, y, label.upper(), 8, "F2", yellow))
        y -= 16
        for line in wrap(body, 64):
            content.append(text_line(x0, y, line, 9, "F1", muted))
            y -= 13
        y -= 12

    content.append(text_line(x0, 206, "Tech Stack", 10, "F2", yellow))
    stack = [
        "Backend: Python + Flask",
        "Database: PostgreSQL on Render",
        "Frontend: Vanilla JS",
        "Messaging: LINE Messaging API",
        "Hosting: Render free tier",
        "Uptime: UptimeRobot ping every 5 minutes",
    ]
    y = 180
    for i, item in enumerate(stack):
        col_x = x0 if i < 3 else x0 + 176
        row_y = y - (i % 3) * 24
        content.append(rect(col_x, row_y - 5, 154, 22, white))
        content.append(text_line(col_x + 8, row_y + 2, item, 7, "F2", navy))

    content.append(text_line(x0, 72, "Focus: Automation | AI Agents | Restaurant Tech | Micro-SaaS | B2B Sales Discovery", 8, "F2", muted))

    stream = "".join(content).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>".encode("latin-1"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream",
    ]

    pdf = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part) for part in pdf))
        pdf.append(f"{i} 0 obj\n".encode("latin-1") + obj + b"\nendobj\n")
    xref = sum(len(part) for part in pdf)
    pdf.append(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("latin-1"))
    for off in offsets[1:]:
        pdf.append(f"{off:010d} 00000 n \n".encode("latin-1"))
    pdf.append(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("latin-1")
    )
    return b"".join(pdf)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    grid = make_qr(WEBSITE_URL)
    write_qr_svg(grid)
    PDF_PATH.write_bytes(build_pdf(grid))
    print("dist/rhachata-meesilp-portfolio.pdf")
    print("dist/portfolio-qr.svg")


if __name__ == "__main__":
    main()

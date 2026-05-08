from PIL import Image

SRC  = r"C:\Users\Asus\OneDrive\เดสก์ท็อป\WebPortfolio\assets\images\sparx-logo.png.png"
OUT  = r"C:\Users\Asus\OneDrive\เดสก์ท็อป\WebPortfolio\assets\images\sparx-favicon.png"
SIZE = 512
PAD  = 60

src  = Image.open(SRC).convert("RGBA")
gray = src.convert("L")
mask = gray.point(lambda p: 255 if p < 200 else 0, "L")

x0, y0, x1, y1 = mask.getbbox()

# Auto-detect the gap between X mark and SPARX text
# Scan row by row, find the first blank gap row after mark starts
prev_has_ink = True
gap_row = None
for row in range(y0, y1):
    row_data = list(mask.crop((x0, row, x1, row + 1)).getdata())
    has_ink  = any(p > 0 for p in row_data)
    if prev_has_ink and not has_ink:
        gap_row = row   # first blank row = bottom of X mark
        break
    prev_has_ink = has_ink

cut_y = gap_row if gap_row else y0 + int((y1 - y0) * 0.68)

# Crop just the X mark
mark_mask = mask.crop((x0, y0, x1, cut_y))
bbox2     = mark_mask.getbbox()
mark_mask = mark_mask.crop(bbox2)   # tight crop

# Black mark on transparent background (Gemini style)
black = Image.new("RGBA", mark_mask.size, (15, 15, 15, 255))
black.putalpha(mark_mask)

mw, mh = black.size
scale   = min((SIZE - 2*PAD) / mw, (SIZE - 2*PAD) / mh)
nw, nh  = int(mw * scale), int(mh * scale)
black   = black.resize((nw, nh), Image.LANCZOS)

# Transparent background
favicon = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
favicon.paste(black, ((SIZE - nw) // 2, (SIZE - nh) // 2), black)
favicon.save(OUT, "PNG")
print("done")

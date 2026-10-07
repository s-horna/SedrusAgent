"""Shared rendering helpers: text logging, table drawing, scan degradation."""

from __future__ import annotations

import io
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas

FICTION_MARK = "TEST DOCUMENT - FICTITIOUS PERSONS, ACCOUNTS AND DATA. NOT A REAL STATEMENT."


# --------------------------------------------------------------------------- text log

@dataclass
class TextLog:
    """Every string drawn on each page, so gold quotes can be verified verbatim."""

    pages: dict[int, list[str]] = field(default_factory=dict)

    def add(self, page: int, text: str) -> None:
        self.pages.setdefault(page, []).append(text)

    def page_text(self, page: int) -> str:
        return norm(" ".join(self.pages.get(page, [])))

    def all_text(self) -> str:
        return norm(" ".join(" ".join(v) for _, v in sorted(self.pages.items())))


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


class LoggedCanvas(Canvas):
    """reportlab Canvas that records every drawString into a TextLog."""

    def __init__(self, path: str, log: TextLog, pagesize=letter, **kw):
        super().__init__(path, pagesize=pagesize, **kw)
        self.log = log
        self.setTitle("")
        self.setAuthor("")
        self.setCreator("")
        self.setProducer("")

    def _rec(self, text):
        self.log.add(self.getPageNumber(), str(text))

    def drawString(self, x, y, text, *a, **kw):
        self._rec(text)
        return super().drawString(x, y, text, *a, **kw)

    def drawRightString(self, x, y, text, *a, **kw):
        self._rec(text)
        return super().drawRightString(x, y, text, *a, **kw)

    def drawCentredString(self, x, y, text, *a, **kw):
        self._rec(text)
        return super().drawCentredString(x, y, text, *a, **kw)


# --------------------------------------------------------------------------- drawing

def text_block(c: Canvas, x: float, y: float, lines: list[str], font="Helvetica",
               size=9.0, leading=None, right=False) -> float:
    """Draw lines top-down from y; return the y below the block."""
    leading = leading or size * 1.25
    c.setFont(font, size)
    for line in lines:
        if right:
            c.drawRightString(x, y, line)
        else:
            c.drawString(x, y, line)
        y -= leading
    return y


def wrap(c: Canvas, text: str, width: float, font: str, size: float) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if c.stringWidth(trial, font, size) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def paragraph(c: Canvas, x: float, y: float, text: str, width: float, font="Helvetica",
              size=7.5, leading=None) -> float:
    return text_block(c, x, y, wrap(c, text, width, font, size), font, size, leading)


@dataclass
class Col:
    title: str
    width: float
    align: str = "left"  # left | right | center


def table(c: Canvas, x: float, y: float, cols: list[Col], rows: list[list[str]],
          size=7.5, header_size=None, header_font="Helvetica-Bold", font="Helvetica",
          row_h=None, rule=True, header_rule_width=0.8, zebra=False,
          bold_rows: set[int] | None = None) -> float:
    """Simple table. Header titles may contain '\\n'. Returns y below the table."""
    header_size = header_size or size
    row_h = row_h or size * 1.7
    bold_rows = bold_rows or set()
    total_w = sum(col.width for col in cols)

    max_lines = max(len(col.title.split("\n")) for col in cols)
    hy = y
    for i in range(max_lines):
        cx = x
        for col in cols:
            parts = col.title.split("\n")
            pad = max_lines - len(parts)
            if i >= pad:
                _cell(c, cx, hy, col, parts[i - pad], header_font, header_size)
            cx += col.width
        hy -= header_size * 1.2
    y = hy + header_size * 0.4
    if rule:
        c.setLineWidth(header_rule_width)
        c.line(x, y, x + total_w, y)
    y -= row_h * 0.85
    for r, row in enumerate(rows):
        if zebra and r % 2 == 1:
            c.setFillGray(0.93)
            c.rect(x, y - size * 0.45, total_w, row_h, stroke=0, fill=1)
            c.setFillGray(0)
        cx = x
        f = header_font if r in bold_rows else font
        for col, val in zip(cols, row):
            if val:
                _cell(c, cx, y, col, val, f, size)
            cx += col.width
        y -= row_h
    if rule:
        c.setLineWidth(0.4)
        c.line(x, y + row_h * 0.55, x + total_w, y + row_h * 0.55)
    return y


def _cell(c, cx, y, col, val, font, size):
    c.setFont(font, size)
    if col.align == "right":
        c.drawRightString(cx + col.width - 3, y, val)
    elif col.align == "center":
        c.drawCentredString(cx + col.width / 2, y, val)
    else:
        c.drawString(cx + 2, y, val)


def fiction_mark(c: Canvas, width: float, size=4.5) -> None:
    c.saveState()
    c.setFont("Helvetica", size)
    c.setFillGray(0.6)
    # Not logged: deliberately excluded from gold text.
    Canvas.drawCentredString(c, width / 2, 9, FICTION_MARK)
    c.restoreState()


def barcode(c: Canvas, x: float, y: float, seed: str, w=150, h=10) -> None:
    rnd = random.Random(seed)
    cx = x
    while cx < x + w:
        bw = rnd.choice([0.6, 0.9, 1.4])
        if rnd.random() > 0.35:
            c.rect(cx, y, bw, h * rnd.choice([0.5, 1.0]), stroke=0, fill=1)
        cx += bw + rnd.choice([0.6, 1.0])


def logo_box(c: Canvas, x: float, y: float, w: float, h: float, lines: list[str], size=9) -> None:
    """Generic wordmark block: white text on black square (no real trade dress)."""
    c.saveState()
    c.setFillGray(0)
    c.rect(x, y, w, h, stroke=0, fill=1)
    c.setFillGray(1)
    c.setFont("Times-Bold", size)
    ty = y + h - size - 3
    for line in lines:
        Canvas.drawString(c, x + 4, ty, line)
        ty -= size + 1
    c.restoreState()


# --------------------------------------------------------------------------- degradation

OCR_SUBS = [
    (r"\bUSD\b", "USO"), (r"\bOct\b", "Dct"), (r"\(Loss\)", "(Lossl"), (r"\bII\b", "Il"),
    (r"\bNet\b", "Nat"), (r"Interest", "lnterest"), (r"\bmade\b", "mada"),
]
OCR_CHARS = {"O": "0", "l": "1", "I": "l", "S": "5", "B": "8", "e": "c", "rn": "m", "m": "rn",
             ",": ".", ".": ","}


def corrupt_ocr(word: str, rnd: random.Random, rate: float) -> str:
    for pat, rep in OCR_SUBS:
        if re.search(pat, word) and rnd.random() < 0.6:
            word = re.sub(pat, rep, word)
    if rnd.random() < rate and len(word) > 2:
        keys = [k for k in OCR_CHARS if k in word]
        if keys:
            k = rnd.choice(keys)
            word = word.replace(k, OCR_CHARS[k], 1)
    return word


def degrade(img: Image.Image, rnd: random.Random, skew: float, noise: float = 18,
            blur: float = 0.6, dirt: int = 0) -> Image.Image:
    g = img.convert("L")
    if dirt:
        d = ImageDraw.Draw(g)
        W, H = g.size
        for _ in range(dirt):
            x, y = rnd.randint(0, W), rnd.randint(0, H)
            r = rnd.choice([1, 1, 1, 2])
            d.ellipse((x - r, y - r, x + r, y + r), fill=rnd.randint(60, 150))
    if skew:
        g = g.rotate(skew, resample=Image.BICUBIC, expand=False, fillcolor=255)
    if noise:
        # effect_noise is centred on 128; add it around the page's own values.
        g = ImageChops.add(g, Image.effect_noise(g.size, noise), scale=1.0, offset=-128)
    if blur:
        g = g.filter(ImageFilter.GaussianBlur(blur))
    # Push the background back to near-white, toner to near-black, like a copier.
    g = g.point(lambda v: 255 if v > 200 else int(v * 0.85))
    return g


def scanify(src: Path, dst: Path, *, seed: str, dpi=150, skew_range=0.6, ocr: str = "corrupt",
            ocr_rate=0.06, image_only_pages: set[int] = frozenset(), text_pages: set[int] = frozenset(),
            jpeg_quality=55, dirt=60) -> None:
    """Rasterize each page and rebuild the PDF, like printing + scanning to PDF.

    ocr: "none" (image only), "clean" (invisible exact text layer) or "corrupt"
    (invisible text layer with OCR-style errors). Pages in image_only_pages get
    no text layer; pages in text_pages are copied through untouched (still vector).
    Page numbers are 1-based.
    """
    rnd = random.Random(seed)
    srcdoc = pymupdf.open(src)
    out = pymupdf.open()
    for i, page in enumerate(srcdoc, start=1):
        if i in text_pages:
            out.insert_pdf(srcdoc, from_page=i - 1, to_page=i - 1)
            continue
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        skew = rnd.uniform(-skew_range, skew_range)
        img = degrade(img, rnd, skew, dirt=dirt)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=jpeg_quality)
        newp = out.new_page(width=page.rect.width, height=page.rect.height)
        newp.insert_image(newp.rect, stream=buf.getvalue())
        if ocr != "none" and i not in image_only_pages:
            for x0, y0, x1, y1, word, *_ in page.get_text("words"):
                if ocr == "corrupt":
                    word = corrupt_ocr(word, rnd, ocr_rate)
                fs = max(3.0, (y1 - y0) * 0.92)
                try:
                    newp.insert_text((x0, y1 - (y1 - y0) * 0.2), word, fontsize=fs,
                                     fontname="helv", render_mode=3)
                except Exception:
                    pass
    out.set_metadata({"producer": "Scanned Document", "creator": "", "title": "", "author": ""})
    out.save(dst, garbage=3, deflate=True)


def fixed_metadata(path: Path, producer: str) -> None:
    """Normalize PDF metadata (keeps rebuilds byte-stable-ish and removes generator hints)."""
    doc = pymupdf.open(path)
    doc.set_metadata({"producer": producer, "creator": "", "title": "", "author": "",
                      "creationDate": "", "modDate": ""})
    tmp = path.with_suffix(".tmp.pdf")
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    tmp.replace(path)

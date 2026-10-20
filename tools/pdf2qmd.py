# One-off converter: Word-made Trionic PDFs -> Quarto chapters + images.
# Usage: python -I tools/pdf2qmd.py <book>   (books in BOOKS below)
# The output is a first pass, cleanup happens by hand against the PDF.
import re, sys, pathlib, pymupdf

TAHOMA = {("Tahoma-Bold", 15.1): 1, ("Arial-BoldMT", 15.1): 1, ("Tahoma-Bold,Italic", 13.1): 2,
          ("Tahoma,Italic", 10.4): 3, ("Tahoma-Bold,Italic", 10.4): 4}
BOOKS = {
    "t5": ("Trionic 5.pdf", TAHOMA, False),
    "t7": ("Trionic 7.pdf", TAHOMA, False),
    "t8": ("Trionic 8.pdf", {("Tahoma", 15.1): 1, ("Calibri", 15.1): 1, ("Tahoma", 13.1): 2, ("Calibri", 13.1): 2,
                             ("Calibri", 11.3): 3, ("Tahoma-Bold,Italic", 10.4): 3, ("Tahoma,Italic", 10.4): 4}, False),
    # manuals: level comes from the number of " – " in "Menu – Item – Subitem"
    "t5-manual": ("T5_manual.pdf", {("Arial-BoldMT", 15.1): 1, ("Arial-BoldItalicMT", 13.1): 2,
                                    ("Arial-BoldItalicMT", 9.5): 2}, True),
    "t7-manual": ("T7_manual.pdf", {("Arial-BoldMT", 15.1): 1, ("Tahoma-Bold,Italic", 11.3): 1,
                                    ("Arial-BoldItalicMT", 13.1): 2, ("Tahoma-Bold", 9.5): 2,
                                    ("Arial-BoldItalicMT", 9.5): 2}, True),
    "t8-manual": ("T8_manual.pdf", {("Calibri", 15.1): 1, ("Calibri", 13.1): 2, ("Tahoma", 11.3): 2,
                                    ("Calibri", 10.4): 3, ("Calibri", 9.5): 2}, True),
}
TOP, BOTTOM = 50, 728          # header / footer zones (pt)
TEXT_W = 612 - 2 * 92          # text width of the originals
DPI = 150
CAPTION = re.compile(r"^(image|figure|picture)\s*\d+\s*[:.]\s*", re.I)
BULLETS = "•▪-"


def bold(s): return "Bold" in s["font"] or s["flags"] & 16
def italic(s): return "Italic" in s["font"] or "Oblique" in s["font"] or s["flags"] & 2


def esc(t):
    t = t.replace("\\", "\\\\").replace("*", "\\*").replace("$", "\\$").replace("@", "\\@")
    t = t.replace("<", "\\<").replace("`", "\\`")
    return re.sub(r"(^|\W)_|_(\W|$)", lambda m: m.group(0).replace("_", "\\_"), t)


def line_spans(l):
    """Spans of a line with small-caps lowercased (smaller caps than the line's largest)."""
    big = max(s["size"] for s in l["spans"])
    out = []
    for s in l["spans"]:
        t = s["text"]
        if t.isupper() and s["size"] < big - 0.5:
            t = t.lower()
        out.append((t, bool(bold(s)), bool(italic(s)), s["font"]))
    return out


def inline(spans, heading=False):
    """Markdown for a run of spans, bold/italic merged over neighbours."""
    runs = []
    for t, b, i, _ in spans:
        if heading: b = i = False
        if runs and runs[-1][1:] == (b, i): runs[-1][0] += t
        else: runs.append([t, b, i])
    out = ""
    for t, b, i in runs:
        core = t.strip()
        if not core: out += t; continue
        mark = ("**" if b else "") + ("*" if i else "")
        lead, trail = t[: len(t) - len(t.lstrip())], t[len(t.rstrip()):]
        out += lead + mark + esc(core) + mark[::-1] + trail
    return out


def semantic(text):
    # ponytail: sentence split on ". X", misses "e.g. Foo" style abbreviations, fine for a first pass
    return re.sub(r"(?<=[a-z0-9)\]][.!?]) +(?=[A-Z“\"(])", "\n", text)


def merge_rects(rects, pad=3):
    # tiles can be single pixel rows (zero height), give them some body so they touch
    rects = [pymupdf.Rect(r) + (0, -0.5, 0, 0.5) for r in rects]
    changed = True
    while changed:
        changed = False
        out = []
        for r in rects:
            for j, o in enumerate(out):
                if (o + (-pad, -pad, pad, pad)).intersects(r):
                    out[j] = o | r; changed = True; break   # Rect |= rebinds, it doesn't update the list
            else:
                out.append(pymupdf.Rect(r))
        rects = out
    return rects


def thumb(page, r):
    gray = pymupdf.Pixmap(pymupdf.csGRAY, page.get_pixmap(clip=r, dpi=144))
    return bytes(pymupdf.Pixmap(gray, 8, 8, None).samples)


def inside(r, regions):
    c = pymupdf.Point((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
    return any(c in g for g in regions)


def table_rows(page, t):
    """Cells from the words under each column band, Word's double borders merged away."""
    xs = sorted({round(c[0]) for c in t.cells if c} | {round(c[2]) for c in t.cells if c})
    b = []
    for x in xs:
        if not b or x - b[-1] >= 6: b.append(x)
    cols = list(zip(b, b[1:]))
    words = page.get_text("words", clip=t.bbox)
    rows = []
    for r in t.rows:
        cells = [[] for _ in cols]
        for w in words:
            cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
            if r.bbox[1] <= cy <= r.bbox[3]:
                for k, (a, c) in enumerate(cols):
                    if a <= cx <= c: cells[k].append(w); break
        rows.append([esc(" ".join(w[4] for w in sorted(c, key=lambda w: (round(w[3] / 3), w[0])))).replace("|", "\\|")
                     for c in cells])
    rows = [r for r in rows if any(r)]
    keep = [k for k in range(len(cols)) if any(r[k] for r in rows)]
    return [[r[k] for k in keep] for r in rows] or [[""]]


def block_item(lines, head, styles, manual, pno):
    first = next(s for s in lines[0]["spans"] if s["text"].strip())
    sty = (first["font"], round(first["size"], 1))
    spans = [sp for l in lines for sp in line_spans(l) + [(" ", False, False, "")]]
    plain = re.sub(r"\s+", " ", "".join(t for t, *_ in spans)).strip()
    if head:
        if pno == 1: return "skip", None                        # title page, the template makes its own
        lvl = min(3, 1 + plain.count(" – ")) if manual else styles[sty]
        return "h", (lvl, plain)
    if CAPTION.match(plain):
        return "cap", inline(spans).strip()
    if "Courier" in first["font"] or first["size"] < 6.7:
        return "code", ["".join(s["text"] for s in l["spans"]).rstrip() for l in lines]
    if plain[0] in BULLETS or lines[0]["spans"][0]["font"] == "SymbolMT":
        cur, entries = [], []
        for l in lines:
            lt = "".join(s["text"] for s in l["spans"]).strip()
            sp = line_spans(l)
            if lt and lt[0] in BULLETS:
                if cur: entries.append(cur)
                cur = []
                sp = [(t.lstrip(BULLETS + " \t"), b, i, f) for t, b, i, f in sp if f != "SymbolMT"]
            cur += sp + [(" ", False, False, "")]
        if cur: entries.append(cur)
        return "list", [re.sub(r"\s+", " ", inline(e)).strip() for e in entries]
    md = " ".join(inline(line_spans(l)).strip() for l in lines)
    return "p", re.sub(r"\s+", " ", md).strip()


def convert(key):
    pdf, styles, manual = BOOKS[key]
    out = pathlib.Path(key); img = out / "images"
    img.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pathlib.Path("original") / pdf)
    icons = {}                      # name -> mean colour of legend icon
    elems = []                      # (kind, payload)
    in_toc = False
    for page in doc:
        pno = page.number + 1
        elems.append(("page", pno))
        items = []                  # (y, kind, payload)
        tables = [t for t in page.find_tables().tables if t.row_count > 1 or t.col_count > 1]
        tregs = [pymupdf.Rect(t.bbox) for t in tables]
        # figures: image tiles merged, plus busy vector clusters (charts) outside tables
        raw = [i["bbox"] for i in page.get_image_info() if i["bbox"][1] > TOP - 10 and i["bbox"][3] < BOTTOM + 10]
        paths = page.get_drawings()
        for c in page.cluster_drawings(drawings=paths):
            if c.width > 40 and c.height > 40 and not any(c.intersects(t) for t in tregs) \
                    and sum(1 for p in paths if pymupdf.Rect(p["rect"]) in c + (-1, -1, 1, 1)) >= 10:
                raw.append(c)
        figs, small = [], []
        for r in merge_rects(raw):
            (small if r.width < 22 and r.height < 22 else figs).append(r)
        small = [r for r in merge_rects(small, pad=5) if r.width < 22 and r.height < 22]   # icons come as slivers
        figs = [f for f in figs if f.width > 8 and f.height > 8]
        tables = [t for t in tables if not inside(t.bbox, figs)]
        tregs = [pymupdf.Rect(t.bbox) for t in tables]
        for n, f in enumerate(figs, 1):
            pix = page.get_pixmap(clip=f, dpi=DPI)
            name = f"p{pno:03d}-{n}"
            data = pix.tobytes("png")
            if len(data) > 250_000:
                data, name = pix.tobytes("jpeg", jpg_quality=85), name + ".jpg"
            else:
                name += ".png"
            (img / name).write_bytes(data)
            items.append((f.y0, "fig", (name, min(100, round(f.width / TEXT_W * 100)))))
        for t in tables:
            items.append((t.bbox[1], "table", table_rows(page, t)))
        lines_y = []
        for blk in page.get_text("dict")["blocks"]:
            if blk["type"] != 0: continue
            if blk["bbox"][1] < TOP or blk["bbox"][3] > BOTTOM: continue
            lines = [l for l in blk["lines"] if "".join(s["text"] for s in l["spans"]).strip()
                     and not inside(l["bbox"], figs + tregs)]
            if not lines: continue
            text = " ".join("".join(s["text"] for s in l["spans"]) for l in lines)
            # the original table of contents, up to the first chapter after it
            if re.fullmatch(r"\s*table of contents\s*", text, re.I): in_toc = True; continue
            if in_toc:
                if not any(styles.get((s["font"], round(s["size"], 1))) == 1 or (manual and (s["font"], round(s["size"], 1)) in styles)
                           for l in lines for s in l["spans"][:1]): continue
                in_toc = False
            if re.search(r"\.{6,}", text): continue
            # split the block: heading lines stand alone, a line ending short ends a paragraph
            groups = []
            for l in lines:
                lt = "".join(t for t, *_ in line_spans(l)).strip()
                lines_y.append((l["bbox"][1], l["bbox"][3], lt))
                first = next(s for s in l["spans"] if s["text"].strip())
                head = (first["font"], round(first["size"], 1)) in styles and len(lt) < 120
                if groups and groups[-1][0] == head and not groups[-1][2]:
                    groups[-1][1].append(l)
                else:
                    groups.append([head, [l], False])
                groups[-1][2] = not head and l["bbox"][2] < 470
            for head, gl, _ in groups:
                items.append((gl[0]["bbox"][1],) + block_item(gl, head, styles, manual, pno))
        # margin / heading icons
        for r in ([] if in_toc else small):
            col = thumb(page, r)
            near = [t for y0, y1, t in lines_y if y0 - 4 <= (r.y0 + r.y1) / 2 <= y1 + 4]
            for name in ("references", "advanced"):
                if any(t.strip().lower().startswith(name) for t in near) and name not in icons:
                    icons[name] = col
                    page.get_pixmap(clip=r, dpi=600).save(str(img / f"icon-{name}.png"))
            items.append((r.y0, "icon", col))
        items.sort(key=lambda it: (it[0], it[1] != "icon"))
        elems += [(k, p) for _, k, p in items]
    write(out, elems, icons)


def write(out, elems, icons):
    chapters, cur, title = [], [], "Front matter"
    pending_icon, last = None, None
    def flush():
        if cur: chapters.append((title, cur[:]))
    i = 0
    while i < len(elems):
        k, p = elems[i]
        if k == "page":
            cur.append(f"<!-- page {p} -->")
        elif k == "icon":
            dist = sorted((sum(abs(a - b) for a, b in zip(c, p)) / 64, n) for n, c in icons.items())
            pending_icon = dist[0][1] if dist and dist[0][0] < 30 else None
        elif k == "h":
            lvl, text = p
            cls = f" {{.{pending_icon}}}" if pending_icon else ""
            pending_icon = None
            if lvl == 1:
                flush(); cur.clear(); title = text
            cur.append(f"{'#' * lvl} {esc(text)}{cls}")
        elif k == "fig":
            name, w = p
            cap = ""
            if i + 1 < len(elems) and elems[i + 1][0] == "cap":
                cap = CAPTION.sub("", elems[i + 1][1].replace("**", "")).strip(); i += 1
            stem = name.rsplit(".", 1)[0]
            attrs = f"#fig-{stem} " if cap else ""
            cur.append(f"![{cap}](images/{name}){{{attrs}width={w}%}}")
        elif k == "cap":
            cur.append(f"<!-- caption without figure: {p} -->\n{semantic(p)}")
        elif k == "table":
            rows = p
            w = max(len(r) for r in rows)
            rows = [r + [""] * (w - len(r)) for r in rows]
            t = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * w]
            t += ["| " + " | ".join(r) + " |" for r in rows[1:]]
            cur.append("\n".join(t))
        elif k == "code":
            if last == "code": cur[-1] = cur[-1][:-4] + "\n" + "\n".join(p) + "\n```"
            else: cur.append("```\n" + "\n".join(p) + "\n```")
        elif k == "list":
            md = "\n".join(f"- {semantic(x)}".replace("\n", "\n  ") for x in p)
            if last == "list": cur[-1] += "\n" + md
            else: cur.append(md)
        elif k == "p":
            # join paragraphs split by a page break
            prev = next((j for j in range(len(cur) - 1, -1, -1) if not cur[j].startswith("<!--")), None)
            if prev is not None and p[:1].islower() and cur[prev][-1:].isalnum() and "page" in cur[-1]:
                cur[prev] = semantic(cur[prev] + " " + p)
            else:
                cur.append(semantic(p))
        if k != "icon": last = k
        i += 1
    flush()
    names = []
    for n, (t, body) in enumerate(chapters):
        slug = "00-front" if n == 0 else f"{n:02d}-" + re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:40]
        (out / f"{slug}.qmd").write_text("\n\n".join(body) + "\n")
        names.append(f"{slug}.qmd")
    print("\n".join(names))


if __name__ == "__main__":
    assert merge_rects([(0, 0, 10, 1), (0, 3, 10, 4), (50, 50, 60, 60)]) == [pymupdf.Rect(0, -0.5, 10, 4.5), pymupdf.Rect(50, 49.5, 60, 60.5)]
    for k in sys.argv[1:]: convert(k)

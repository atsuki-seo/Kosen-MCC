import sys, re, json, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
p = pdf.pages[184]
SPLIT = 356; L, R, TOP, BOT = 72, 1113, 132, 701
# horizontal edges merged per y: covered x-intervals
cov = {}
for e in p.edges:
    if e["orientation"] == "h" and TOP - 1 <= e["top"] <= BOT + 1:
        cov.setdefault(round(e["top"]), []).append((e["x0"], e["x1"]))
def covers(iv, a, b):
    iv = sorted(iv); x = a
    for s, t in iv:
        if s <= x + 3 and t > x: x = t
    return x >= b - 3
def bands(a, b):
    ys = sorted(y for y, iv in cov.items() if covers(iv, a, b))
    ys = [y for i, y in enumerate(ys) if i == 0 or y - ys[i - 1] > 3]
    return list(zip(ys, ys[1:]))
def text(x0, x1, y0, y1):
    c = p.crop((x0, y0, x1, y1), strict=False)
    return [l.strip() for l in (c.extract_text() or "").split("\n") if l.strip()]
lb, rb = bands(L + 20, SPLIT), bands(SPLIT, R)
print("left bands:", len(lb), "right bands:", len(rb))
items = []
for y0, y1 in lb:
    t = " ".join(text(L, SPLIT, y0, y1))
    if not t: continue
    m = re.match(r'^(\d(?:\.\d)?)\s+(.*)$', t)
    items.append({"y": (y0, y1), "num": m.group(1) if m else None, "title": m.group(2) if m else t})
rights = [((y0, y1), text(SPLIT, R, y0, y1)) for y0, y1 in rb]
for it in items:
    a, b = it["y"]
    it["mcc"] = [ln for (y0, y1), lines in rights if y0 < (a + b) / 2 < y1 or a <= (y0 + y1) / 2 <= b for ln in lines]
    # dedupe keep order
    seen = []; [seen.append(x) for x in it["mcc"] if x not in seen]; it["mcc"] = seen
for it in items: print(it["num"], "|", it["title"][:52], "|", [m[:44] for m in it["mcc"]])

import sys, collections, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
for pg in (183, 184, 185):
    p = pdf.pages[pg - 1]
    t = max(p.find_tables(), key=lambda t: (t.bbox[2]-t.bbox[0])*(t.bbox[3]-t.bbox[1]))
    x0, top, x1, bot = t.bbox
    vs = collections.Counter(); hs = collections.Counter()
    for e in p.edges:
        if e["orientation"] == "v": vs[round(e["x0"])] += round(e["bottom"] - e["top"])
        else: hs[round(e["top"])] += round(e["x1"] - e["x0"])
    print(f"#### p{pg} page={round(p.width)}x{round(p.height)} table bbox={[round(v) for v in t.bbox]}")
    print("  vertical x -> total length:", sorted((x, l) for x, l in vs.items() if l > 40))
    print("  horizontal y -> total length:", sorted((y, l) for y, l in hs.items() if l > 40))
    ws = p.extract_words(use_text_flow=False, keep_blank_chars=False)
    xs = collections.Counter(round(w["x0"] / 5) * 5 for w in ws if top < w["top"] < bot)
    print("  word left-edge x histogram:", sorted(xs.items()))

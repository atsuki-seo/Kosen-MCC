import sys, re, collections, unicodedata, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
odd = collections.Counter(); where = collections.defaultdict(set); cid = []; pua = []; imgs = {}
samples = []
for i, p in enumerate(pdf.pages):
    if p.images: imgs[i + 1] = len(p.images)
    t = p.extract_text() or ""
    if "(cid:" in t: cid.append(i + 1)
    for ch in t:
        cat = unicodedata.category(ch)
        o = ord(ch)
        if cat in ("Co", "Cn") or o == 0xFFFD: pua.append((i + 1, hex(o)))
        elif cat in ("Sm", "So", "Sk", "Mn", "Lm") or 0x370 <= o <= 0x3FF or 0x2070 <= o <= 0x209F:
            odd[ch] += 1; where[ch].add(i + 1)
    if 44 <= i < 62:
        for ln in t.split("\n"):
            if re.search(r'[=∫Σ√^_]|sin|cos|log|[a-z]\s?[0-9]\b', ln): samples.append((i + 1, ln[:90]))
print("pages with (cid:):", cid)
print("private-use/unknown chars:", len(pua), pua[:10])
print("pages with images:", imgs)
print("symbol chars:")
for ch, n in odd.most_common(60): print("  ", repr(ch), unicodedata.name(ch, "?")[:32], n, sorted(where[ch])[:8])
print("formula-like lines in I/II (pdf p45-62):", len(samples))
for s in samples[:40]: print("  ", s)

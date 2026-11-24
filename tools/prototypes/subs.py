import sys, collections, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
# 1) image pages inside part 2-3
for n in (47, 48, 153, 154, 180):
    p = pdf.pages[n - 1]
    big = [(round(im["width"]), round(im["height"])) for im in p.images]
    print(f"p{n}: images={len(big)} sizes(sample)={sorted(set(big))[:6]} text-head={(p.extract_text() or '')[:60]!r}")
# 2) sub/superscripts: chars notably smaller than the line's dominant size
hits = collections.defaultdict(list)
for i in range(44, 181):
    p = pdf.pages[i]
    lines = collections.defaultdict(list)
    for c in p.chars: lines[round(c["bottom"] / 6)].append(c)
    sizes = collections.Counter(round(c["size"], 1) for c in p.chars)
    if not sizes: continue
    main = sizes.most_common(1)[0][0]
    small = [c for c in p.chars if c["size"] < main * 0.8 and c["text"].strip()]
    if small:
        hits[i + 1] = "".join(c["text"] for c in small)[:60]
print("pages (45-181) with small-size chars:", len(hits))
for k, v in list(hits.items())[:40]: print("  ", k, repr(v))

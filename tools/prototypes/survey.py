import sys, re, collections, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
code = re.compile(r'^\s*((?:[IVX]+)\s?(?:-[A-Z])?(?:-\d+)?(?:-\d+)?)\s+(\S.{0,30})$')
hdrs = collections.Counter(); heads = []
for i, p in enumerate(pdf.pages):
    if i < 44: continue
    txt = p.extract_text() or ""
    for ln in txt.split("\n"):
        m = code.match(ln)
        if m and len(ln) < 45: heads.append((i + 1, ln.strip()))
    for t in p.extract_tables():
        for r in t:
            if r and r[0] and r[0].replace(" ", "") in ("学習内容", "分類", "項目", "領域", "単元", "レベル"):
                hdrs[tuple((c or "").replace("\n", "") for c in r)] += 1
print("== header rows"); [print(v, k) for k, v in hdrs.most_common()]
print("== headings:", len(heads))
depth = collections.Counter(len(re.split('-', h.split()[0])) for _, h in heads)
print(depth)
for pg, h in heads[:400]:
    if not re.match(r'^[IVX]+\s?-[A-Z]-\d+ ', h) or pg in (90, 91, 96): print(pg, h)

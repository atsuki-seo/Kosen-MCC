import sys, re, collections, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
def n(s): return re.sub(r"\s", "", s or "")
HDR = {"学習内容"}
sec_re = re.compile(r'(?m)^(?:\d-\d\.\d\s+)?((?:IX|IV|V?I{0,3})\s?-?[A-I]?(?:-\d+)?)\s+\S')
counts = collections.Counter(); splits = []; noend = []; cur = None; mode = None; last_goal = None
plus = collections.Counter(); hairyo = 0
for i in range(48, 180):
    p = pdf.pages[i]
    text = p.extract_text() or ""
    part = "core/model" if i < 152 else "plus"
    for t in p.find_tables():
        rows = t.extract()
        # section code: nearest heading text above the table
        above = p.crop((0, 0, p.width, max(t.bbox[1], 1))).extract_text() or ""
        codes = re.findall(r'(?m)^(?:\d-\d\.\d\s+)?((?:IX|IV|VI{0,3}|I{1,3})\s?(?:-[A-I])?(?:-\d+)?)\s+[^\s\d]', above)
        first = True
        for r in rows:
            c0 = n(r[0])
            if c0.startswith("【教育領域の到達目標】") or c0.startswith("【事業概要】"):
                if codes: cur = codes[-1].replace(" ", "")
                mode = None; continue
            if c0 in HDR: mode = "goal"; first = False; continue
            if c0 == "学習領域": mode = "hairyo"; first = False; continue
            if len(r) < 2: continue
            g = n(r[1])
            if mode == "goal" and g:
                if first and last_goal and not last_goal.endswith(("。", "．", ".")) and not c0:
                    splits.append((i + 1, last_goal[-12:], g[:12]))
                else:
                    (plus if part == "plus" else counts)[cur if part != "plus" else "plus"] += 1
                    if not g.endswith(("。", "．", ".")): noend.append((i + 1, g[-25:]))
                last_goal = g
            elif mode == "hairyo" and g:
                hairyo += 1
            first = False
top = collections.Counter()
for k, v in counts.items(): top[re.match(r'[IVX]+', k).group(0) if k else "?"] += v
print("core/model goals by major:", dict(top), "total", sum(counts.values()))
print("sections seen:", len(counts))
print("plus goals:", dict(plus), " 配慮事項 rows:", hairyo)
print("row split across pages:", len(splits)); [print("  ", s) for s in splits[:12]]
print("goal cells not ending with 。:", len(noend)); [print("  ", s) for s in noend[:15]]

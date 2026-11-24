import sys, collections, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
shape = collections.Counter(); goal_rows = 0; odd = []; notable = 0; contd = 0
for i, p in enumerate(pdf.pages):
    ts = p.extract_tables()
    if not ts: notable += 1
    for t in ts:
        cols = tuple(sorted({len(r) for r in t}))
        hdr = next((r for r in t if r and r[0] and r[0].replace(" ","") == "学習内容"), None)
        kind = "goal" if hdr else "other"
        if hdr:
            goal_rows += sum(1 for r in t if len(r) > 1 and r[1] and r[1] != hdr[1])
        elif len(cols) == 1 and cols[0] in (2, 3) and i >= 44 and i < 170:
            contd += 1; goal_rows += sum(1 for r in t if len(r) > 1 and r[1])
            kind = "contd?"
        shape[(kind, cols)] += 1
        if kind == "other": odd.append((i + 1, cols, len(t)))
print("pages without tables:", notable)
for k, v in sorted(shape.items(), key=lambda x: -x[1]): print(v, k)
print("approx goal rows:", goal_rows, "continuation tables:", contd)
print("other tables (page, cols, rows):", odd[:60])

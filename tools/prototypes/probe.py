import sys, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
start = None
for i, p in enumerate(pdf.pages):
    t = p.extract_text() or ""
    if "V-D-1 プログラミング" in t and "教育領域の到達目標" in t:
        start = i; break
print("V-D starts at pdf page index", start, "of", len(pdf.pages))
for i in range(start, start + 2):
    p = pdf.pages[i]
    tables = p.extract_tables()
    print(f"--- page {i+1}: {len(tables)} tables")
    for t in tables:
        print("  rows:", len(t), "cols:", {len(r) for r in t})
        for r in t:
            print("   ", [None if c is None else c.replace("\n", "⏎") for c in r])

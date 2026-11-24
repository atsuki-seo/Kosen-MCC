import sys, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
def find(s, a=44):
    for i in range(a, len(pdf.pages)):
        if s in (pdf.pages[i].extract_text() or ""): return i
for label, key, nrows in [("IV-A", "2-4.1 IV-A", 4), ("VI-A", "3-2.1 VI-A", 5), ("配慮", "3-3.1 機械系分野", 5), ("plus", "2-2.1 COMPASS", 5), ("ABET", "1-1.1 ABET", 3), ("CDIO", "1-1.2 CDIO", 4), ("指導要領", "モデルコアカリキュラム・学習内容の到達目標", 4), ("評価", "2-1 分野別の工学実験・実習能力の育成、評価", 4)]:
    i = find(key)
    if label in ("ABET", "CDIO", "評価", "指導要領", "plus"): i = find(key, 150)
    p = pdf.pages[i]
    print(f"\n######## {label} pdf p{i+1}")
    txt = (p.extract_text() or "").split("\n")
    print("  TEXT:", " / ".join(l[:38] for l in txt[:7]))
    for t in p.extract_tables()[:2]:
        print("  TABLE rows", len(t), "cols", {len(r) for r in t})
        for r in t[:nrows]:
            print("    ", [None if c is None else c.replace("\n", "⏎")[:60] for c in r])

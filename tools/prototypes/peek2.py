import sys, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
for pg, lim in ((55, 6), (145, 5), (185, 14)):
    p = pdf.pages[pg - 1]
    print(f"#### p{pg}")
    for t in p.extract_tables()[:1]:
        for r in t[:lim]: print("   ", [None if c is None else c.replace("\n", "⏎")[:46] for c in r])

import sys, re, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
def norm(s): return re.sub(r"\s", "", s or "")
print("== per page (pdf 181-234): tables, cols, share of page text inside tables")
for i in range(180, 234):
    p = pdf.pages[i]
    ts = p.find_tables()
    full = norm(p.extract_text())
    intab = sum(len(norm(c)) for t in ts for r in t.extract() for c in r if c)
    cols = [sorted({len(r) for r in t.extract()}) for t in ts]
    head = (p.extract_text() or "").split("\n")[0][:28]
    print(f"p{i+1:3d} tabs={len(ts)} cols={cols} in_table={intab}/{len(full)} {head}")

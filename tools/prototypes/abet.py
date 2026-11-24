import sys, re, pdfplumber
pdf = pdfplumber.open(sys.argv[1])
PAT = [r'(?m)^(?=\d\. )', r'(?m)^(?=\([a-i]\) ?)', r'(?m)^(?=WK\d: )', r'(?m)^(?=[A-Z][A-Za-z ,&-]+\n?WA\d+:|WA\d+:)', r'(?m)^(?=[ⅠⅡⅢⅣⅤⅥⅦⅧⅨ] )']
rows = []
for pg in (183, 184):
    t = max(pdf.pages[pg - 1].find_tables(), key=lambda t: t.bbox[3] - t.bbox[1]).extract()
    for r in t:
        if r[0] and re.match(r'\d\. ', r[0]): rows.append((pg, r))
print("correspondence rows:", len(rows))
for pg, r in rows:
    parts = [[s.strip().replace("\n", " ") for s in re.split(PAT[i], c or "") if s.strip()] for i, c in enumerate(r)]
    print(f"p{pg} ABET {parts[0][0][:3]} | JABEE {[s[:3] for s in parts[1]]} | WK {[s[:4] for s in parts[2]]} | WA {[re.search(r'WA\d+', s).group(0) if re.search(r'WA\d+', s) else s[:10] for s in parts[3]]} | MCC {[s[:12] for s in parts[4]]}")

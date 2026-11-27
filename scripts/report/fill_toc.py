"""Fill the TOC / list-of-figures / list-of-tables fields of a docx with cached entries (page numbers from a
LibreOffice render), so the lists show even before Word updates the fields.
    python3 fill_toc.py <report.docx> <toc.json>
"""
import json, os, re, subprocess, sys, tempfile, zipfile, shutil, html

SOFFICE = "/root/.claude/skills/synced/d2341152-3539-4360-91dd-dd2a213ff8d7_bdd6674e-5083-4725-9357-974e20a10d5a/docx/scripts/office/soffice.py"
docx, tocj = sys.argv[1], sys.argv[2]
items = json.load(open(tocj))
tmp = tempfile.mkdtemp()
subprocess.run(["python3", SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", tmp, docx], capture_output=True)
pdf = os.path.join(tmp, os.path.splitext(os.path.basename(docx))[0] + ".pdf")
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
pages = [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", pdf, "-"], capture_output=True, text=True).stdout for i in range(1, n + 1)]
norm = lambda s: re.sub(r"\s+", " ", s).strip()
labels = []
for t in pages:
    lines = [l.strip() for l in t.strip().splitlines() if l.strip()]
    labels.append(lines[-1].split()[-1] if lines else "")
flat = [norm(t) for t in pages]
start = next(i for i, t in enumerate(flat) if "1. INTRODUCTION 1.1 Background" in t or re.search(r"\b1\. INTRODUCTION\b", t) and labels[i] == "1")
pos = start
found = {}
for k, it in enumerate(items):
    key = it["text"] if "kind" not in it else f'{it["kind"]} {it["n"]} - '
    probe = norm(key)[:60]
    for j in range(pos if "kind" not in it else start, n):
        if probe in flat[j]:
            found[k] = labels[j]
            if "kind" not in it:
                pos = j
            break
    else:
        found[k] = ""
        print("not found:", key)

def entry(style, text, page):
    t = html.escape(text, quote=False)
    return (f'<w:p><w:pPr><w:pStyle w:val="{style}"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9350"/></w:tabs>'
            f'<w:ind w:left="{360 if style == "TOC2" else 0}" w:hanging="0"/></w:pPr>'
            f'<w:r><w:t xml:space="preserve">{t}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>{page}</w:t></w:r></w:p>')

heads = "".join(entry("TOC1" if it["lvl"] == 1 else "TOC2", it["text"], found[k]) for k, it in enumerate(items) if "kind" not in it)
figs = "".join(entry("TableofFigures", it["text"], found[k]) for k, it in enumerate(items) if it.get("kind") == "Figure")
tabs = "".join(entry("TableofFigures", it["text"], found[k]) for k, it in enumerate(items) if it.get("kind") == "Table")

w = tempfile.mkdtemp()
with zipfile.ZipFile(docx) as z:
    z.extractall(w)
p = os.path.join(w, "word", "document.xml")
s = open(p, encoding="utf-8").read()
s = s.replace('TOC \\a &quot;Figure&quot; \\h', 'TOC \\h \\z \\c &quot;Figure&quot;').replace('TOC \\a &quot;Table&quot; \\h', 'TOC \\h \\z \\c &quot;Table&quot;')
s = s.replace('TOC \\h \\o &quot;1-2&quot;', 'TOC \\o &quot;1-2&quot; \\h \\z \\u')
for instr, body in (('TOC \\o &quot;1-2&quot; \\h \\z \\u', heads), ('TOC \\h \\z \\c &quot;Figure&quot;', figs), ('TOC \\h \\z \\c &quot;Table&quot;', tabs)):
    i = s.index(instr)
    j = s.index('<w:fldChar w:fldCharType="separate"/></w:r></w:p>', i) + len('<w:fldChar w:fldCharType="separate"/></w:r></w:p>')
    s = s[:j] + body + s[j:]
open(p, "w", encoding="utf-8").write(s)
out = docx + ".tmp"
names = zipfile.ZipFile(docx).namelist()
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for nm in names:
        if not nm.endswith("/"):
            z.write(os.path.join(w, nm), nm)
shutil.move(out, docx)
print("filled", sum(1 for v in found.values() if v), "of", len(items), "entries; body starts on pdf page", start + 1)

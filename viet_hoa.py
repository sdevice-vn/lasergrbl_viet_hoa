#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viet hoa LaserGRBL: chay trong workflow sau khi clone ma nguon goc.

Cach dung:  python viet_hoa.py <thu_muc_goc_cua_LaserGRBL> [--no-retarget]

Viec script lam:
  1. Voi moi file X.resx co san cac ban dich khac (X.fr.resx, X.es.resx, ...),
     tao X.vi.resx tu bo tu dien vi_translations.json (chuoi tieng Anh -> tieng Viet).
  2. Khai bao cac file X.vi.resx moi vao LaserGRBL.csproj.
  3. Dat tieng Viet lam ngon ngu mac dinh (khi nguoi dung chua chon ngon ngu nao).
  4. Them muc "Tieng Viet" vao menu Language.
  5. Doi TargetFrameworkVersion v4.0 -> v4.8 (may build GitHub khong con goi .NET 4.0).
  6. Dich CSDL vat lieu (StandardMaterials.psh) bang vi_materials.json.
  7. Va CSDL vat lieu: tu chep StandardMaterials.psh sang %APPDATA%\\LaserGRBL (ban goc do trinh cai dat lam).
Moi buoc deu bao loi ro rang (va dung build) neu ma nguon goc da thay doi qua nhieu.
"""
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, unescape

HERE = os.path.dirname(os.path.abspath(__file__))
CULTURE = "vi"
CULTURE_RE = re.compile(r"\.[a-z]{2,3}(-[A-Za-z]{2,4})?\.resx$")


def read(path):
    """Doc file giu nguyen BOM va kieu xuong dong."""
    with open(path, "rb") as f:
        raw = f.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    return text, bom


def write(path, text, bom):
    with open(path, "wb") as f:
        f.write((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))


def eol_of(text):
    return "\r\n" if "\r\n" in text else "\n"


def fail(msg):
    print("LOI: " + msg, file=sys.stderr)
    sys.exit(1)


def replace_once(text, old, new, what):
    if text.count(old) != 1:
        fail("Khong tim thay (hoac thay vi tri khong duy nhat) cho '%s' - ma nguon goc co the da thay doi." % what)
    return text.replace(old, new)


# ---------------------------------------------------------------- 1. resx
def make_resx(base, translations, report):
    d = os.path.dirname(base)
    stem = os.path.basename(base)[:-5]
    siblings = [p for p in glob.glob(os.path.join(d, stem + ".*.resx"))
                if CULTURE_RE.search(p) and not p.endswith("." + CULTURE + ".resx")]
    if not siblings:
        return None

    keys = set()
    for s in siblings:
        try:
            for e in ET.parse(s).getroot().iter("data"):
                keys.add(e.get("name"))
        except ET.ParseError:
            pass

    entries = []
    for e in ET.parse(base).getroot().iter("data"):
        k = e.get("name")
        if k not in keys or e.get("type") is not None or k.startswith(">>"):
            continue
        v = e.find("value")
        if v is None or not v.text or not re.search(r"[A-Za-z]{2}", v.text):
            continue
        if v.text in translations:
            entries.append((k, translations[v.text]))
        else:
            report.append((os.path.relpath(base, PROJ), k, v.text))
    if not entries:
        return None

    text, _ = read(base)
    ends = [m.end() for m in re.finditer(r"</resheader>", text)]
    if not ends:
        fail("File resx khong hop le: " + base)
    eol = eol_of(text)
    out = [text[:ends[-1]]]
    for k, v in entries:
        v = escape(v).replace("\r\n", "\n").replace("\n", eol)
        out.append('%s  <data name="%s" xml:space="preserve">%s    <value>%s</value>%s  </data>'
                   % (eol, escape(k, {'"': "&quot;"}), eol, v, eol))
    out.append(eol + "</root>" + eol)
    target = os.path.join(d, stem + "." + CULTURE + ".resx")
    write(target, "".join(out), True)
    return target


def register_in_csproj(csproj_text, new_files):
    added = 0
    for target in new_files:
        rel = os.path.relpath(target, PROJ).replace("/", "\\")
        rel_base = rel[: -len(".vi.resx")]
        # tim 1 muc EmbeddedResource cua ngon ngu khac cung form de sao chep (giu DependentUpon...)
        pat = re.compile(r'([ \t]*)<EmbeddedResource Include="%s\.[a-z]{2,3}(?:-[A-Za-z]{2,4})?\.resx"(?:\s*/>|>.*?</EmbeddedResource>)'
                         % re.escape(rel_base), re.S)
        m = pat.search(csproj_text)
        if not m:
            print("CANH BAO: khong tim thay muc mau trong csproj cho " + rel)
            continue
        block = re.sub(r'Include="%s\.[a-z]{2,3}(?:-[A-Za-z]{2,4})?\.resx"' % re.escape(rel_base),
                       lambda _m: 'Include="%s"' % rel, m.group(0), count=1)
        eol = eol_of(csproj_text)
        csproj_text = csproj_text[: m.end()] + eol + block + csproj_text[m.end():]
        added += 1
    return csproj_text, added


# ---------------------------------------------------------------- 2b. CSDL vat lieu
def translate_materials(proj):
    """Dich du lieu trong StandardMaterials.psh (Material, Action, Remarks, Thickness) bang vi_materials.json."""
    src = os.path.join(proj, "StandardMaterials.psh")
    table = os.path.join(HERE, "vi_materials.json")
    if not (os.path.isfile(src) and os.path.isfile(table)):
        print("CANH BAO: khong co StandardMaterials.psh hoac vi_materials.json - bo qua dich CSDL vat lieu")
        return
    with open(table, encoding="utf-8") as f:
        tr = json.load(f)
    text, bom = read(src)
    stat = {"dich": 0, "thieu": 0}
    missing = set()

    def sub(m):
        tag, raw = m.group(2), m.group(3)
        val = unescape(raw, {"&apos;": "'", "&quot;": '"'})
        vi = tr.get(tag, {}).get(val)
        if vi is None:
            if re.search(r"[A-Za-z]{2}", val) and tag in ("Material", "Remarks"):
                stat["thieu"] += 1
                missing.add((tag, val))
            return m.group(0)
        stat["dich"] += 1
        return m.group(1) + escape(vi) + m.group(4)

    text = re.sub(r"(<(Material|Remarks|Action|Thickness)>)(.*?)(</\2>)", sub, text, flags=re.S)
    # Luoc do MaterialDB.xsd co rang buoc duy nhat (Model, Material, Thickness, Action).
    # Nhieu ten tieng Anh khac nhau (vd "Kraft Paper"/"KraftPaper") co the cung ra 1 ban dich
    # -> trung khoa -> app bao loi va bo qua TOAN BO file. Them hau to (2), (3)... cho dong trung.
    seen = set()
    dup = {"n": 0}

    def val(blk, tag):
        mm = re.search(r"<%s>(.*?)</%s>" % (tag, tag), blk, re.S)
        return mm.group(1) if mm else ""

    def dedupe(m):
        blk = m.group(0)
        model, mat, th, act = (val(blk, t) for t in ("Model", "Material", "Thickness", "Action"))
        n = 1
        key = (model, mat, th, act)
        while key in seen:
            n += 1
            key = (model, "%s (%d)" % (mat, n), th, act)
        seen.add(key)
        if n > 1:
            dup["n"] += 1
            blk = re.sub(r"(<Material>)(.*?)(</Material>)",
                         lambda mm: "%s%s (%d)%s" % (mm.group(1), mm.group(2), n, mm.group(3)),
                         blk, count=1, flags=re.S)
        return blk

    text = re.sub(r"<Materials>.*?</Materials>", dedupe, text, flags=re.S)
    print("CSDL vat lieu: da danh so lai %d dong trung khoa sau khi dich" % dup["n"])
    write(src, text, bom)
    print("CSDL vat lieu: da dich %d o, %d o chua co ban dich" % (stat["dich"], stat["thieu"]))
    for tag, val in sorted(missing)[:20]:
        print("  chua dich [%s] %r" % (tag, val[:60]))


# ---------------------------------------------------------------- 3,4. code
def patch_code(proj):
    # --- Program.cs : ngon ngu mac dinh = tieng Viet
    p = os.path.join(proj, "Program.cs")
    t, bom = read(p)
    eol = eol_of(t)
    old = "if (ci != null) Thread.CurrentThread.CurrentUICulture = ci;"
    new = old + eol + "\t\t\telse Thread.CurrentThread.CurrentUICulture = new System.Globalization.CultureInfo(\"vi\"); //Viet hoa: mac dinh tieng Viet"
    t = replace_once(t, old, new, "Program.cs: dat CurrentUICulture")
    write(p, t, bom)

    # --- MainForm.cs : handler cho muc menu Tieng Viet
    p = os.path.join(proj, "MainForm.cs")
    t, bom = read(p)
    eol = eol_of(t)
    anchor = "private void MNEnglish_Click(object sender, EventArgs e)"
    i = t.find(anchor)
    if i < 0 or t.count(anchor) != 1:
        fail("MainForm.cs: khong tim thay MNEnglish_Click")
    ls = t.rfind("\n", 0, i) + 1
    handler = eol.join([
        "\t\tprivate void MNVietnamese_Click(object sender, EventArgs e)",
        "\t\t{",
        "\t\t\tSetLanguage(new System.Globalization.CultureInfo(\"vi\"));",
        "\t\t}",
        "", ""])
    t = t[:ls] + handler + t[ls:]
    write(p, t, bom)

    # --- MainForm.Designer.cs : tao + dang ky muc menu
    p = os.path.join(proj, "MainForm.Designer.cs")
    t, bom = read(p)
    eol = eol_of(t)
    decl = "this.japaneseToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();"
    t = replace_once(t, decl, decl + eol + "\t\t\tthis.MNVietnamese = new System.Windows.Forms.ToolStripMenuItem();", "Designer: khai bao khoi tao")

    m = re.search(r"(this\.linguaToolStripMenuItem\.DropDownItems\.AddRange\(new System\.Windows\.Forms\.ToolStripItem\[\] \{\s*)(this\.MNEnglish,)", t)
    if not m:
        fail("Designer: khong tim thay danh sach menu ngon ngu")
    t = t[: m.start(2)] + "this.MNVietnamese," + eol + "            " + t[m.start(2):]

    marker = "this.MNEnglish.Click += new System.EventHandler(this.MNEnglish_Click);"
    block = eol.join([
        marker,
        "\t\t\t// ",
        "\t\t\t// MNVietnamese",
        "\t\t\t// ",
        "\t\t\tthis.MNVietnamese.Name = \"MNVietnamese\";",
        "\t\t\tthis.MNVietnamese.Text = \"Ti\\u1ebfng Vi\\u1ec7t\";",
        "\t\t\tthis.MNVietnamese.Click += new System.EventHandler(this.MNVietnamese_Click);"])
    t = replace_once(t, marker, block, "Designer: thuoc tinh MNEnglish")

    field = "private System.Windows.Forms.ToolStripMenuItem japaneseToolStripMenuItem;"
    t = replace_once(t, field, field + eol + "\t\tprivate System.Windows.Forms.ToolStripMenuItem MNVietnamese;", "Designer: khai bao field")
    write(p, t, bom)

    # --- PSHelper/MaterialDB.cs : CSDL vat lieu. Ban goc dung trinh cai dat (Inno Setup) chep
    # StandardMaterials.psh vao %APPDATA%\\LaserGRBL; ban zip khong co buoc nay nen CSDL rong.
    # Vá: tu chep file tu thu muc chay chuong trinh sang %APPDATA%\\LaserGRBL neu thieu/cu hon.
    p = os.path.join(proj, "PSHelper", "MaterialDB.cs")
    t, bom = read(p)
    eol = eol_of(t)
    old = 'public static string ServerFile { get => System.IO.Path.Combine(LaserGRBL.GrblCore.DataPath, "StandardMaterials.psh"); }'
    new = eol.join([
        "public static string ServerFile",
        "\t\t{",
        "\t\t\tget",
        "\t\t\t{",
        '\t\t\t\tstring dst = System.IO.Path.Combine(LaserGRBL.GrblCore.DataPath, "StandardMaterials.psh");',
        "\t\t\t\ttry",
        "\t\t\t\t{",
        '\t\t\t\t\tstring src = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "StandardMaterials.psh");',
        "\t\t\t\t\tif (System.IO.File.Exists(src) && (!System.IO.File.Exists(dst) || System.IO.File.GetLastWriteTimeUtc(src) > System.IO.File.GetLastWriteTimeUtc(dst)))",
        "\t\t\t\t\t\tSystem.IO.File.Copy(src, dst, true);",
        "\t\t\t\t}",
        "\t\t\t\tcatch { }",
        "\t\t\t\treturn dst;",
        "\t\t\t}",
        "\t\t}"])
    t = replace_once(t, old, new, "MaterialDB.cs: ServerFile")
    if "using System;" not in t:
        t = replace_once(t, "namespace ", "using System;" + eol + "namespace ", "MaterialDB.cs: namespace") if t.count("namespace ") == 1 else t
    write(p, t, bom)


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        fail("Thieu tham so: thu muc goc LaserGRBL")
    root = args[0]
    PROJ = os.path.join(root, "LaserGRBL")
    csproj = os.path.join(PROJ, "LaserGRBL.csproj")
    if not os.path.isfile(csproj):
        fail("Khong thay " + csproj)

    with open(os.path.join(HERE, "vi_translations.json"), encoding="utf-8") as f:
        translations = json.load(f)

    report, created = [], []
    for base in sorted(glob.glob(os.path.join(PROJ, "**", "*.resx"), recursive=True)):
        if CULTURE_RE.search(base):
            continue
        t = make_resx(base, translations, report)
        if t:
            created.append(t)
    print("Da tao %d file .vi.resx" % len(created))
    if not created:
        fail("Khong tao duoc file dich nao - cau truc ma nguon goc co the da thay doi.")

    text, bom = read(csproj)
    text, added = register_in_csproj(text, created)
    print("Da khai bao %d file trong LaserGRBL.csproj" % added)
    if added != len(created):
        fail("Co file .vi.resx khong khai bao duoc vao csproj")
    if "--no-retarget" not in sys.argv:
        text = re.sub(r"<TargetFrameworkVersion>v4\.0</TargetFrameworkVersion>",
                      "<TargetFrameworkVersion>v4.8</TargetFrameworkVersion>", text)
    write(csproj, text, bom)

    translate_materials(PROJ)
    patch_code(PROJ)
    print("Da dat tieng Viet mac dinh + them menu ngon ngu")

    if report:
        print("\n%d chuoi chua co ban dich (se hien tieng Anh):" % len(report))
        for f, k, v in report:
            print("  %s :: %s :: %r" % (f, k, v[:60]))

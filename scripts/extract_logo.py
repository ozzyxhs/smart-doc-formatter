# -*- coding: utf-8 -*-
"""从规范 PDF 提取内嵌图片，列出尺寸/比例，找校名标准字图（约 120x30mm，宽高比~4:1）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
import fitz

pdf = sys.argv[1] if len(sys.argv) > 1 else r"fixtures\农大格式要求.pdf"
outdir = Path(r"app\_jobs\_logo"); outdir.mkdir(parents=True, exist_ok=True)
d = fitz.open(pdf)
seen = set()
for pno in range(d.page_count):
    for img in d[pno].get_images(full=True):
        xref = img[0]
        if xref in seen:
            continue
        seen.add(xref)
        try:
            pix = fitz.Pixmap(d, xref)
            if pix.n > 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            f = outdir / f"img_p{pno + 1}_x{xref}.png"
            pix.save(str(f))
            print(f"page {pno + 1} xref {xref}: {pix.width}x{pix.height} ratio={pix.width / max(pix.height,1):.2f} -> {f.name}")
        except Exception as e:
            print("skip", xref, e)
print("done; images in", outdir)

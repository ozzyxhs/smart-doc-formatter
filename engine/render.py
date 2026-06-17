"""把成品 docx 渲染成页面图片（所见即所得预览）。

docx→PDF 走 PowerShell + Word COM 子进程（比 pywin32 在本机更稳）；PDF→PNG 走 pymupdf。
Windows + 已装 Word。渲染结果缓存在 <job>/_pages/，只渲一次。
"""
import subprocess
import threading
from pathlib import Path

_lock = threading.Lock()


def _docx_to_pdf(docx_path, pdf_path):
    docx_path = str(docx_path)
    pdf_path = str(pdf_path)
    script = (
        "$ErrorActionPreference='Stop'\n"
        "$word = New-Object -ComObject Word.Application\n"
        "$word.Visible = $false\n"
        "try {\n"
        f"  $doc = $word.Documents.Open([string]'{docx_path}', $false, $true)\n"
        f"  $doc.ExportAsFixedFormat([string]'{pdf_path}', [int]17)\n"
        "  $doc.Close($false)\n"
        "} finally { $word.Quit() }\n"
    )
    ps1 = Path(pdf_path).with_suffix(".convert.ps1")
    ps1.write_text(script, encoding="utf-8-sig")  # BOM → PowerShell 正确读中文路径
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
            capture_output=True, timeout=180,
        )
        if r.returncode != 0 or not Path(pdf_path).exists():
            raise RuntimeError((r.stderr or b"").decode("utf-8", "ignore")[:300] or "Word 导出失败")
    finally:
        try:
            ps1.unlink()
        except OSError:
            pass


def render_pages(docx_path, pages_dir, dpi=110):
    """渲染成 page1.png…，返回页数。已渲染则复用缓存。"""
    import fitz
    pages_dir = Path(pages_dir)
    marker = pages_dir / "count.txt"
    if marker.exists():
        return int(marker.read_text(encoding="utf-8"))
    with _lock:
        if marker.exists():
            return int(marker.read_text(encoding="utf-8"))
        pages_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = Path(docx_path).with_suffix(".pdf")
        _docx_to_pdf(docx_path, pdf_path)
        doc = fitz.open(str(pdf_path))
        n = doc.page_count
        for i in range(n):
            doc[i].get_pixmap(dpi=dpi).save(str(pages_dir / f"page{i + 1}.png"))
        doc.close()
        marker.write_text(str(n), encoding="utf-8")
        return n

"""建设期 LLM 缝②：规范文档 → 声明式模板 YAML（"规范→模板"编译器）。

两种输入都支持：
  - 规范条文文档(pdf/docx 里是规则文字) → LLM 读规则；
  - 样本/模板 docx → python-docx 读「实际生效的格式」(边距/样式/字体/字号) → LLM 归并成 YAML。
样本模式更可靠：格式数值来自文件本身，不靠 LLM 猜。
"""
import re
import json
import subprocess
from pathlib import Path
import yaml
from docx import Document
from docx.oxml.ns import qn
from . import llm, config


def _emu_mm(v):
    return round(v / 36000, 1) if v else None


def _run_font(run):
    rPr = run._element.find(qn("w:rPr"))
    ea = lat = sz = None
    b = run.bold
    if rPr is not None:
        rf = rPr.find(qn("w:rFonts"))
        if rf is not None:
            ea = rf.get(qn("w:eastAsia")); lat = rf.get(qn("w:ascii"))
        s = rPr.find(qn("w:sz"))
        if s is not None:
            sz = int(s.get(qn("w:val"))) / 2
    return ea, lat, sz, b


def _docx_facts(doc):
    """读样本 docx 里实际生效的格式：页面/边距 + 各样式的字体字号缩进样本。"""
    sec = doc.sections[0]
    facts = {
        "page": {"width_mm": _emu_mm(sec.page_width), "height_mm": _emu_mm(sec.page_height),
                 "margins_mm": {"top": _emu_mm(sec.top_margin), "bottom": _emu_mm(sec.bottom_margin),
                                "left": _emu_mm(sec.left_margin), "right": _emu_mm(sec.right_margin)}},
        "styles": {},
    }
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        sname = (p.style.name if p.style else "Normal") or "Normal"
        st = facts["styles"].setdefault(sname, {"count": 0, "samples": []})
        st["count"] += 1
        if len(st["samples"]) < 3 and p.runs:
            ea, lat, sz, b = _run_font(p.runs[0])
            fli = p.paragraph_format.first_line_indent
            st["samples"].append({"text": t[:28], "eastAsia": ea, "latin": lat, "pt": sz, "bold": b,
                                  "align": str(p.alignment), "first_line_indent_mm": _emu_mm(fli) if fli else None})
    return facts


def _doc_to_docx(src, dst):
    script = ("$ErrorActionPreference='Stop'\n$w=New-Object -ComObject Word.Application\n$w.Visible=$false\n"
              f"try{{$d=$w.Documents.Open([string]'{src}',$false,$true);$d.SaveAs([string]'{dst}',[int]16);$d.Close($false)}}finally{{$w.Quit()}}")
    ps1 = Path(dst).with_suffix(".conv.ps1")
    ps1.write_text(script, encoding="utf-8-sig")
    try:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
                       capture_output=True, timeout=120)
    finally:
        try:
            ps1.unlink()
        except OSError:
            pass


def _read_spec(path):
    path = Path(path)
    ext = path.suffix.lower()
    text, facts = "", None
    if ext == ".doc":
        dst = path.with_suffix(".converted.docx")
        _doc_to_docx(path, dst)
        path, ext = dst, ".docx"
    if ext == ".docx":
        d = Document(str(path))
        text = "\n".join(p.text for p in d.paragraphs if p.text.strip())[:6000]
        facts = _docx_facts(d)
    elif ext == ".pdf":
        from pypdf import PdfReader
        r = PdfReader(str(path))
        text = "\n".join((pg.extract_text() or "") for pg in r.pages)[:8000]
    return text, facts


def _parse_yaml(text):
    t = (text or "").strip()
    t = re.sub(r"^```(?:yaml)?\s*|\s*```$", "", t, flags=re.S)
    return yaml.safe_load(t)


_SYS = (
    "你是排版规范编译器。把给定的【规范/样本】抽成一份与【schema 样例】完全同结构的 YAML 模板，"
    "供确定性排版引擎读取。规则：①优先采用【样本实际格式 facts】里的真实数值(边距/字号pt/字体/缩进)；"
    "②规范文本里有明确规则的也采纳；③字号尽量转成中文字号名(小二/三号/五号…)，并保留 size_table；"
    "④封面/摘要/目录/标题分级/正文/三线表/页眉页脚/页码/参考文献等字段尽量补全，缺的给合理默认；"
    "⑤meta.id/name/institution/doc_type 留占位，调用方会覆盖。只输出 YAML 本体，不要解释、不要代码围栏。"
)


def extract_template(path, *, tid, name, institution, doc_type="thesis"):
    """规范文档 → draft YAML(dict) + 读到的 facts。"""
    text, facts = _read_spec(path)
    example = (config.TEMPLATES_DIR / "neau-bachelor-thesis-2025.yaml").read_text(encoding="utf-8")
    user = (
        f"【schema 样例（农大，仅示意结构，不要照抄数值）】\n{example}\n\n"
        f"【新规范】name={name} institution={institution} doc_type={doc_type}\n\n"
        f"【样本实际格式 facts（来自文件，最可信）】\n{json.dumps(facts, ensure_ascii=False) if facts else '（无，纯文本规范）'}\n\n"
        f"【规范/样本文本】\n{text}"
    )
    out = llm.chat([{"role": "system", "content": _SYS}, {"role": "user", "content": user}],
                   thinking=True, max_tokens=12000)
    y = _parse_yaml(out) or {}
    y.setdefault("meta", {})
    y["meta"].update({"id": tid, "name": name, "institution": institution, "doc_type": doc_type})
    return y, facts

"""确定性排版：读 区块流 + 结构标签 + 模板 YAML，重建一份合规 docx。

核心保证：**文本逐 run 原样拷贝**（内容守恒 by construction），只接管排版层。
分三节：封面(无页眉无码) / 前置(摘要·目录, 罗马页码) / 正文(阿拉伯, 重起1)。
"""
import re
from docx import Document
from docx.enum.section import WD_SECTION
from . import docx_utils as DU

_FRONT_MARKERS = {"abstract_cn_title", "abstract_en_title", "abstract_cn_body",
                  "abstract_en_body", "keywords_cn", "keywords_en", "toc_title", "toc_item"}
_FIELD_KW = ("学院", "专业", "班级", "姓名", "学号", "指导教师", "研究方向", "导师")


def _spec_for(label, template):
    """前置/正文标签 -> 排版规格。bold=None 保留源 run 加粗。"""
    t = template
    body = t["body_paragraph"]
    body_cn = body["font"]["cn"]; body_latin = body["font"]["latin"]
    body_sz = DU.pt_of(t, body["font"]["size"])
    hcn = t["fonts"]["heading_cn"]; latin = t["fonts"]["default_latin"]

    def heading(n):
        h = t["headings"].get(f"level_{n}", {})
        return dict(cn=h.get("font_cn", hcn), latin=h.get("latin", latin),
                    size=DU.pt_of(t, h.get("size", "小四")), bold=True,
                    align=h.get("align", "left"),
                    first_line_chars=h.get("first_line_indent_chars", 0),
                    line_single=True, before_lines=h.get("space_before_lines"),
                    after_lines=h.get("space_after_lines"),
                    page_break=h.get("page_break_before", False))

    base_body = dict(cn=body_cn, latin=body_latin, size=body_sz, bold=None,
                     align=body["align"], first_line_chars=body["first_line_indent_chars"],
                     line_single=True, before_lines=None, after_lines=None, page_break=False)

    if label in ("heading_1", "heading_2", "heading_3", "heading_4", "heading_5"):
        return heading(int(label[-1]))
    if label in ("reference_title", "ack_title"):
        s = heading(1); s["page_break"] = True; return s
    if label == "toc_title":
        s = heading(1); s["page_break"] = False; return s
    if label == "abstract_cn_title":
        return dict(cn=hcn, latin=latin, size=DU.pt_of(t, "小二"), bold=True, align="center",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=False)
    if label == "abstract_en_title":
        return dict(cn=latin, latin=latin, size=DU.pt_of(t, "小二"), bold=True, align="center",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=False)
    if label == "abstract_en_body":
        s = dict(base_body); s["cn"] = latin; s["latin"] = latin; return s
    if label in ("table_title", "figure_title"):
        return dict(cn=body_cn, latin=latin, size=DU.pt_of(t, "五号"), bold=None, align="center",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=False)
    if label == "note":
        s = dict(base_body); s["size"] = DU.pt_of(t, "小五"); s["first_line_chars"] = 1; return s
    # body / keywords_* / abstract_cn_body / toc_item / reference_item / ack_body / blank
    return base_body


def _cover_spec(text, label, template):
    """封面行 -> 精确版式（农大）。"""
    t = template
    hcn = t["fonts"]["heading_cn"]; latin = t["fonts"]["default_latin"]; song = t["fonts"]["default_cn"]
    txt = (text or "").strip()
    base = dict(latin=latin, line_single=True, first_line_chars=0,
                before_lines=None, after_lines=None, page_break=False, align="center")
    if label == "title_main":                                   # 题目：黑体 二号
        return {**base, "cn": hcn, "size": DU.pt_of(t, "二号"), "bold": True, "before_lines": 2}
    if label == "title_en":
        return {**base, "cn": latin, "size": DU.pt_of(t, "二号"), "bold": True, "before_lines": 1}
    if re.search(r"(本科)?(毕业论文|毕业设计)", txt) and len(txt) <= 8:  # 文种：隶书 一号
        return {**base, "cn": "隶书", "size": DU.pt_of(t, "一号"), "bold": False, "before_lines": 3}
    if re.search(r"\d{4}\s*年", txt) and len(txt) <= 16:        # 日期：黑体 小二
        return {**base, "cn": hcn, "size": DU.pt_of(t, "小二"), "bold": False, "before_lines": 2}
    if ("：" in txt or ":" in txt) and any(k in txt for k in _FIELD_KW):  # 信息栏：黑体 小三
        return {**base, "cn": hcn, "size": DU.pt_of(t, "小三"), "bold": False, "before_lines": 1.2}
    return {**base, "cn": song, "size": DU.pt_of(t, "小三"), "bold": False}


def _add_paragraph(out, block, spec):
    p = out.add_paragraph()
    runs = block.get("runs") or ([{"text": block.get("text", ""), "bold": False, "italic": False}])
    for rd in runs:
        if rd["text"] == "":
            continue
        r = p.add_run(rd["text"])
        eff_bold = spec["bold"] if spec["bold"] is not None else rd["bold"]
        DU.set_run_font(r, cn=spec["cn"], latin=spec["latin"], size_pt=spec["size"],
                        bold=eff_bold, italic=rd["italic"])
    DU.set_paragraph_format(p, align=spec["align"], first_line_chars=spec["first_line_chars"],
                            line_spacing_single=spec["line_single"],
                            before_lines=spec.get("before_lines"), after_lines=spec.get("after_lines"),
                            page_break_before=spec.get("page_break"))
    return p


def _add_table(out, block, template):
    n_rows = max(block["n_rows"], 1); n_cols = max(block["n_cols"], 1)
    table = out.add_table(rows=n_rows, cols=n_cols)
    table.alignment = 1
    tconf = template["tables"]
    content_cn = tconf["content"]["font"]; content_latin = tconf["content"]["latin"]
    content_sz = DU.pt_of(template, tconf["content"]["size"])
    for ri, row in enumerate(block["rows"]):
        for ci, cell_text in enumerate(row):
            if ri < n_rows and ci < n_cols:
                cell = table.cell(ri, ci)
                cell.text = cell_text
                for p in cell.paragraphs:
                    p.alignment = 1
                    for r in p.runs:
                        DU.set_run_font(r, cn=content_cn, latin=content_latin, size_pt=content_sz)
    DU.apply_three_line_table(table, top_bottom_pt=tconf["border"]["top_bottom_pt"],
                              middle_pt=tconf["border"]["middle_pt"])
    return table


def _pick_title(blocks, labels):
    for b in blocks:
        if b["kind"] == "paragraph" and labels.get(b["idx"]) == "title_main" and b["text"].strip():
            return b["text"].strip()
    cands = [b["text"].strip() for b in blocks[:12] if b["kind"] == "paragraph" and b["text"].strip()]
    return max(cands, key=len) if cands else ""


def _partition(blocks, labels):
    """切成 封面 / 前置(摘要·目录) / 正文。"""
    n = len(blocks); cover_end = n; body_start = n
    for i, b in enumerate(blocks):
        lab = labels.get(b["idx"]) if b["kind"] == "paragraph" else None
        if cover_end == n and lab in _FRONT_MARKERS:
            cover_end = i
        if body_start == n and lab == "heading_1":
            body_start = i
    if body_start < cover_end:
        body_start = cover_end
    return blocks[:cover_end], blocks[cover_end:body_start], blocks[body_start:]


def _emit(out, blocks, template, *, cover=False, labels=None):
    for b in blocks:
        if b["kind"] == "table":
            _add_table(out, b, template)
            continue
        if cover and b.get("empty"):
            continue                       # 封面不复制源里的空行，自己控间距→保证一页
        lab = labels.get(b["idx"], "body") if labels else "body"
        spec = _cover_spec(b["text"], lab, template) if cover else _spec_for(lab, template)
        _add_paragraph(out, b, spec)


def format_docx(blocks, labels, template, out_path):
    out = Document()
    title = _pick_title(blocks, labels)
    cover, front, body = _partition(blocks, labels)

    groups = [(cover, "cover"), (front, "front"), (body, "body")]
    groups = [(b, role) for (b, role) in groups if b]
    if not groups:
        groups = [(blocks, "body")]

    roles = []
    for i, (blks, role) in enumerate(groups):
        if i > 0:
            out.add_section(WD_SECTION.NEW_PAGE)
        _emit(out, blks, template, cover=(role == "cover"), labels=labels)
        roles.append(role)

    # 删掉 Document() 自带的首个空段（封面顶部多余空行）
    ps = out.paragraphs
    if ps and not ps[0].text.strip() and not ps[0].runs:
        ps[0]._element.getparent().remove(ps[0]._element)

    # 逐节配置页面 + 页眉 + 分节页码
    foot_fmt = template["footer"]["page_number"]["format"]
    for sec, role in zip(out.sections, roles):
        DU.set_page(sec, template)
        if role == "cover":
            DU.blank_header_footer(sec)                              # 封面：无页眉、无页码
        elif role == "front":
            DU.setup_title_header(sec, template, title)
            DU.setup_pagenum_footer(sec, template, "n")             # 罗马
            DU.set_page_number_format(sec, "lowerRoman", start=1)
        else:
            DU.setup_title_header(sec, template, title)
            DU.setup_pagenum_footer(sec, template, foot_fmt)        # 阿拉伯 - n -
            DU.set_page_number_format(sec, "decimal", start=1)

    out.save(out_path)
    change_log = [
        {"what": "页面规范化", "detail": f"A4 · 边距 {template['page']['margins_mm']} mm · 网格 38×38"},
        {"what": "封面重排", "detail": "文种隶书一号·题目黑体二号·信息栏黑体小三·独立成页·不编页码"},
        {"what": "分节页码", "detail": "封面无码 → 摘要/目录罗马数字 → 正文阿拉伯数字重起 1"},
        {"what": "字体统一", "detail": f"中文 {template['fonts']['default_cn']} / 西文 {template['fonts']['default_latin']}（eastAsia 分绑）"},
        {"what": "标题层级重构", "detail": "按结构识别套各级标题；章另起页"},
        {"what": "页眉双线", "detail": "正文区页眉=论文题目+粗细双线（封面/扉页不带）"},
        {"what": "三线表", "detail": "表格统一为开放式三线格（上下 1.5 磅 / 表头下 0.5 磅）"},
    ]
    return {"out_path": out_path, "title": title, "change_log": change_log,
            "sections": roles}

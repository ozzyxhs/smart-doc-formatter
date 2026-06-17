"""确定性排版：读 区块流 + 结构标签 + 模板 YAML，重建一份合规 docx。

核心保证：**文本逐 run 原样拷贝**（内容守恒 by construction），只接管排版层。
"""
from docx import Document
from . import docx_utils as DU


def _spec_for(label, template):
    """标签 -> 排版规格。bold=None 表示保留源 run 的加粗（如关键词前缀/斜体变量）。"""
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
                    line_single=True,
                    before_lines=h.get("space_before_lines"),
                    after_lines=h.get("space_after_lines"),
                    page_break=h.get("page_break_before", False))

    base_body = dict(cn=body_cn, latin=body_latin, size=body_sz, bold=None,
                     align=body["align"], first_line_chars=body["first_line_indent_chars"],
                     line_single=True, before_lines=None, after_lines=None, page_break=False)

    if label in ("heading_1", "heading_2", "heading_3", "heading_4", "heading_5"):
        return heading(int(label[-1]))
    if label in ("reference_title", "ack_title", "toc_title"):
        s = heading(1); s["page_break"] = (label != "toc_title"); return s
    if label == "title_main":
        return dict(cn=hcn, latin=latin, size=DU.pt_of(t, "二号"), bold=True, align="center",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=False)
    if label == "title_en":
        return dict(cn=latin, latin=latin, size=DU.pt_of(t, "二号"), bold=True, align="center",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=False)
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
    if label == "cover":
        return dict(cn=body_cn, latin=latin, size=DU.pt_of(t, "小三"), bold=None, align="center",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=False)
    # body / keywords_* / abstract_cn_body / toc_item / reference_item / ack_body / blank / fallback
    return base_body


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
    n_rows = max(block["n_rows"], 1)
    n_cols = max(block["n_cols"], 1)
    table = out.add_table(rows=n_rows, cols=n_cols)
    table.alignment = 1  # center
    tconf = template["tables"]
    content_cn = tconf["content"]["font"]; content_latin = tconf["content"]["latin"]
    content_sz = DU.pt_of(template, tconf["content"]["size"])
    for ri, row in enumerate(block["rows"]):
        for ci, cell_text in enumerate(row):
            if ri < n_rows and ci < n_cols:
                cell = table.cell(ri, ci)
                cell.text = cell_text                       # 文本原样
                for p in cell.paragraphs:
                    p.alignment = 1
                    for r in p.runs:
                        DU.set_run_font(r, cn=content_cn, latin=content_latin, size_pt=content_sz)
    DU.apply_three_line_table(table, top_bottom_pt=tconf["border"]["top_bottom_pt"],
                              middle_pt=tconf["border"]["middle_pt"])
    return table


def _setup_header_footer(out, template, title):
    section = out.sections[0]
    # 页眉 = 论文题目，宋体小五居中，粗细双线
    h = template["header"]
    hp = section.header.paragraphs[0]
    hp.text = ""
    section.header.is_linked_to_previous = False
    run = hp.add_run(title or "")
    DU.set_run_font(run, cn=h["font"]["cn"], latin=h["font"]["latin"],
                    size_pt=DU.pt_of(template, h["font"]["size"]))
    DU.set_paragraph_format(hp, align=h["font"]["align"])
    DU.set_double_bottom_border(hp, upper_pt=h["border_below"]["upper_pt"])
    # 页脚 = 页码 - n -
    f = template["footer"]
    fp = section.footer.paragraphs[0]
    fp.text = ""
    section.footer.is_linked_to_previous = False
    DU.set_paragraph_format(fp, align=f["font"]["align"])
    DU.add_page_number_field(fp, fmt=f["page_number"]["format"])
    for r in fp.runs:
        DU.set_run_font(r, cn=f["font"]["cn"], latin=f["font"]["latin"],
                        size_pt=DU.pt_of(template, f["font"]["size"]))


def _pick_title(blocks, labels):
    for b in blocks:
        if b["kind"] == "paragraph" and labels.get(b["idx"]) == "title_main" and b["text"].strip():
            return b["text"].strip()
    # 兜底：前 12 段里最长的非空行
    cands = [b["text"].strip() for b in blocks[:12] if b["kind"] == "paragraph" and b["text"].strip()]
    return max(cands, key=len) if cands else ""


def format_docx(blocks, labels, template, out_path):
    out = Document()
    DU.set_page(out.sections[0], template)
    title = _pick_title(blocks, labels)
    _setup_header_footer(out, template, title)

    change_log = []
    for b in blocks:
        if b["kind"] == "paragraph":
            label = labels.get(b["idx"], "body")
            spec = _spec_for(label, template)
            _add_paragraph(out, b, spec)
        else:
            _add_table(out, b, template)

    # 删掉 Document() 默认产生的首个空段（若存在且我们已加内容）
    body = out.element.body
    first = body.find(DU.qn("w:p"))
    out.save(out_path)
    change_log = [
        {"what": "页面规范化", "detail": f"A4 · 边距 {template['page']['margins_mm']} mm · 网格 38×38"},
        {"what": "字体统一", "detail": f"中文 {template['fonts']['default_cn']} / 西文 {template['fonts']['default_latin']}（eastAsia 分绑）"},
        {"what": "标题层级重构", "detail": "按结构识别套各级标题字体字号缩进"},
        {"what": "页眉页脚", "detail": "页眉=论文题目+粗细双线；页脚=页码 - n -"},
        {"what": "三线表", "detail": "表格统一为开放式三线格（上下 1.5 磅 / 表头下 0.5 磅）"},
    ]
    return {"out_path": out_path, "title": title, "change_log": change_log}

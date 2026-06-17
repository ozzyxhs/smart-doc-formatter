"""确定性排版：读 区块流 + 结构标签 + 模板 YAML，重建一份合规 docx。

核心保证：**文本逐 run 原样拷贝**（内容守恒 by construction），只接管排版层。
分三节：封面(无页眉无码) / 前置(摘要·目录, 罗马页码) / 正文(阿拉伯, 重起1)。
"""
import re
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Mm, Pt
from . import docx_utils as DU
from . import config

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
        s = heading(1); s["page_break"] = True; return s        # 目录另起一页
    if label == "abstract_cn_title":
        return dict(cn=hcn, latin=latin, size=DU.pt_of(t, "小二"), bold=True, align="center",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=False)
    if label == "title_en":                                     # 2.5 英文摘要另起一页（题目=第1行）
        return dict(cn=latin, latin=latin, size=DU.pt_of(t, "小二"), bold=True, align="center",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=True)
    if label == "abstract_en_title":                            # "Abstract"=第2行，跟在题目后同页
        return dict(cn=latin, latin=latin, size=DU.pt_of(t, "小二"), bold=True, align="center",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=False)
    if label == "abstract_en_body":
        s = dict(base_body); s["cn"] = latin; s["latin"] = latin; return s
    if label == "keywords_cn":                                  # 关键词顶格(缩进0)，前缀加粗保留
        return dict(cn=body_cn, latin=body_latin, size=body_sz, bold=None, align="left",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=False)
    if label == "keywords_en":                                  # Key words 顶格 TNR
        return dict(cn=latin, latin=latin, size=body_sz, bold=None, align="left",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=False)
    if label in ("table_title", "figure_title"):
        return dict(cn=body_cn, latin=latin, size=DU.pt_of(t, "五号"), bold=None, align="center",
                    first_line_chars=0, line_single=True, before_lines=None, after_lines=None, page_break=False)
    if label == "note":
        s = dict(base_body); s["size"] = DU.pt_of(t, "小五"); s["first_line_chars"] = 1; return s
    # body / keywords_* / abstract_cn_body / toc_item / reference_item / ack_body / blank
    return base_body


_LABEL_TO_SLOT = {"cover_doctype": "doctype", "title_main": "title_cn",
                  "title_en": "title_en", "cover_field": "field", "cover_date": "date"}


def _emit_cover(out, cover_blocks, template, labels):
    """封面：完全数据驱动（读 template['cover']）。logo + 槽位格式 + 空白行结构全从 YAML 来，零农大硬编码。"""
    cv = template.get("cover", {})
    slots = cv.get("slots", {})
    blanks = cv.get("blanks", {})
    align = cv.get("align", "center")
    latin = template["fonts"]["default_latin"]
    blank_cn = cv.get("blank", {}).get("font", template["fonts"]["default_cn"])
    blank_sz = DU.pt_of(template, cv.get("blank", {}).get("size", "五号"))

    def slot_spec(slot):
        s = slots.get(slot, slots.get("other", {}))
        return dict(cn=s.get("font", template["fonts"]["default_cn"]), latin=latin,
                    size=DU.pt_of(template, s.get("size", "小三")), bold=s.get("bold", False),
                    align=s.get("align", align), first_line_chars=s.get("first_line_indent_chars", 0),
                    line_single=True, before_lines=None, after_lines=None, page_break=False)

    def add_blanks(n):
        for _ in range(int(n or 0)):
            p = out.add_paragraph()
            r = p.add_run(" ")
            DU.set_run_font(r, cn=blank_cn, latin=latin, size_pt=blank_sz)
            DU.set_paragraph_format(p, align=align, line_spacing_single=True)

    # 行1：校名标准字图（模板furniture，无文字→不影响内容守恒）
    logo = cv.get("logo")
    if logo:
        asset = config.TEMPLATES_DIR / logo["asset"]
        if asset.exists():
            p = out.add_paragraph()
            p.alignment = DU.ALIGN["center"]
            try:
                p.add_run().add_picture(str(asset), width=Mm(logo["width_mm"]), height=Mm(logo["height_mm"]))
            except Exception:
                pass

    inserted = set()
    for b in cover_blocks:
        if b["kind"] != "paragraph" or b.get("empty"):
            continue                                   # 丢源空行，按 blanks 自己控间距
        slot = _LABEL_TO_SLOT.get(labels.get(b["idx"], "cover"), "other")
        if slot in ("title_cn", "title_en") and "title" not in inserted:
            add_blanks(blanks.get("after_doctype", 0)); inserted.add("title")
        if slot == "field" and "field" not in inserted:
            add_blanks(blanks.get("after_title", 0)); inserted.add("field")
        if slot == "date" and "date" not in inserted:
            add_blanks(blanks.get("after_fields", 0)); inserted.add("date")
        _add_paragraph(out, b, slot_spec(slot))


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


_TOC_PAGE_RE = re.compile(r"\s*([0-9IVXLCMivxlcm]+)\s*$")
_TOC_NUM_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)")


def _add_toc_item(out, block, template):
    """目录条目（2.6）：章/节/条三级缩进 + 页码右对齐 + 点引线。数据来自 template['table_of_contents']。"""
    toc = template.get("table_of_contents", {})
    latin = toc.get("number_letter_font", template["fonts"]["default_latin"])
    text = block["text"].strip()
    page = ""
    title = text
    m = _TOC_PAGE_RE.search(text)
    if m:                                   # 末尾的数字/罗马 = 页码（剥掉只换 tab，_norm 比对仍守恒）
        page = m.group(1)
        title = text[:m.start()].rstrip()
    lm = _TOC_NUM_RE.match(title)
    level = min((lm.group(1).count(".") + 1) if lm else 1, 3)
    lv = toc.get(f"level_{level}", {})
    cn = lv.get("font", template["fonts"]["default_cn"])
    bold = bool(lv.get("bold", False))
    indent = lv.get("indent_chars", level - 1)
    size = DU.pt_of(template, lv.get("size", "五号"))

    p = out.add_paragraph()
    tw = template["page"]["width_mm"] - template["page"]["margins_mm"]["left"] - template["page"]["margins_mm"]["right"]
    p.paragraph_format.tab_stops.add_tab_stop(Mm(tw), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    r1 = p.add_run(title + ("\t" if page else ""))
    DU.set_run_font(r1, cn=cn, latin=latin, size_pt=size, bold=bold)
    if page:
        r2 = p.add_run(page)
        DU.set_run_font(r2, cn=cn, latin=latin, size_pt=size, bold=False)   # 页码不加粗
    DU.set_paragraph_format(p, align="left", first_line_chars=indent, line_spacing_single=True)


def _emit(out, blocks, template, labels=None):
    """前置/正文区：按结构标签查 _spec_for 套版。"""
    for b in blocks:
        if b["kind"] == "table":
            _add_table(out, b, template)
            continue
        lab = labels.get(b["idx"], "body") if labels else "body"
        if lab == "toc_item":
            _add_toc_item(out, b, template)
            continue
        _add_paragraph(out, b, _spec_for(lab, template))


def format_docx(blocks, labels, template, out_path):
    out = Document()
    # 全局：Normal 段前段后0、单倍行距（农大要求；避免 Word 默认段后间距把封面撑到两页）
    nf = out.styles["Normal"].paragraph_format
    nf.space_before = Pt(0); nf.space_after = Pt(0); nf.line_spacing = 1.0
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
        if role == "cover":
            _emit_cover(out, blks, template, labels)
        else:
            _emit(out, blks, template, labels)
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

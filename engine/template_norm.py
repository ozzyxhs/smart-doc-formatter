"""模板规整：把任意模板（手工/编译器产出/聊天改过）深合并到一份完整默认骨架上，
保证引擎要读的每个键都存在且类型可用。配合 docx_utils 里取值时的强转兜底，
让"编译出来千奇百怪的模板"也排版不崩。引擎只消费 normalize() 后的模板。
"""
import copy

# 引擎会读到的全部字段的中性默认骨架（无院校专属值，如不含 logo）
DEFAULTS = {
    "meta": {"id": "tpl", "name": "", "institution": "", "doc_type": "thesis",
             "min_word_count": {"thesis": 8000, "design": 5000}},
    "size_table": {"初号": 42, "小初": 36, "一号": 26, "小一": 24, "二号": 22, "小二": 18,
                   "三号": 16, "小三": 15, "四号": 14, "小四": 12, "五号": 10.5, "小五": 9,
                   "六号": 7.5, "小六": 6.5},
    "page": {"size": "A4", "width_mm": 210, "height_mm": 297,
             "margins_mm": {"top": 25.4, "bottom": 25.4, "left": 25.4, "right": 25.4},
             "grid": {"type": "lines_and_chars", "lines_per_page": 38, "chars_per_line": 38}},
    "fonts": {"default_cn": "宋体", "default_latin": "Times New Roman", "heading_cn": "黑体"},
    "header": {"margin_mm": 15, "content": "thesis_title",
               "font": {"cn": "宋体", "latin": "Times New Roman", "size": "小五", "align": "center"},
               "border_below": {"style": "double", "upper_pt": 3, "lower": "hairline"}},
    "footer": {"margin_mm": 15,
               "font": {"cn": "宋体", "latin": "Times New Roman", "size": "小五", "align": "center"},
               "page_number": {"format": "- n -"}},
    "pagination": {"cover_titlepage": "none", "frontmatter": "roman", "body": "arabic"},
    "cover": {"align": "center", "line_spacing": "single",
              "blank": {"font": "宋体", "size": "五号"},
              "blanks": {"after_doctype": 2, "after_title": 2, "after_fields": 2},
              "slots": {
                  "doctype":  {"font": "黑体", "size": "一号"},
                  "title_cn": {"font": "黑体", "size": "二号", "bold": True},
                  "title_en": {"font": "Times New Roman", "size": "二号", "bold": True},
                  "field":    {"font": "黑体", "size": "小三", "first_line_indent_chars": 0, "align": "center"},
                  "date":     {"font": "黑体", "size": "小二"},
                  "other":    {"font": "宋体", "size": "小三"}}},
    "body_paragraph": {"font": {"cn": "宋体", "latin": "Times New Roman", "size": "五号"},
                       "first_line_indent_chars": 2, "align": "justify", "line_spacing": "single"},
    "headings": {
        "level_1": {"numbering": "1", "name": "章", "font_cn": "黑体", "latin": "Times New Roman",
                    "size": "小二", "bold": True, "first_line_indent_chars": 0, "space_before_lines": 0.5,
                    "space_after_lines": 0.5, "line_spacing": "single", "page_break_before": True, "align": "center"},
        "level_2": {"numbering": "1.1", "name": "节", "font_cn": "黑体", "latin": "Times New Roman",
                    "size": "小三", "bold": True, "first_line_indent_chars": 1, "line_spacing": "single"},
        "level_3": {"numbering": "1.1.1", "name": "条", "font_cn": "黑体", "latin": "Times New Roman",
                    "size": "四号", "bold": True, "first_line_indent_chars": 2, "line_spacing": "single"},
        "level_4": {"numbering": "1.1.1.1", "name": "款", "font_cn": "黑体", "latin": "Times New Roman",
                    "size": "小四", "bold": True, "first_line_indent_chars": 2, "line_spacing": "single"},
        "level_5": {"numbering": "(1)", "name": "项", "font_cn": "黑体", "latin": "Times New Roman",
                    "size": "小四", "bold": True, "first_line_indent_chars": 2, "line_spacing": "single"}},
    "tables": {"style": "three_line", "border": {"top_bottom_pt": 1.5, "middle_pt": 0.5},
               "content": {"font": "宋体", "latin": "Times New Roman", "size": "小五"}},
    "table_of_contents": {"number_letter_font": "Times New Roman",
                          "level_1": {"font": "黑体", "size": "五号", "bold": True, "indent_chars": 0},
                          "level_2": {"font": "宋体", "size": "五号", "indent_chars": 1},
                          "level_3": {"font": "宋体", "size": "五号", "indent_chars": 2}},
    "references": {"requirements": {}},
}


def _deep_merge(base, over):
    """深合并；类型保护：默认是 dict 而覆盖值不是 dict 时，保留默认 dict（丢弃畸形覆盖），
    避免编译模板把标量塞到引擎需要 dict 的位置导致下标崩。"""
    out = copy.deepcopy(base)
    if not isinstance(over, dict):
        return out
    for k, v in over.items():
        if isinstance(out.get(k), dict):
            if isinstance(v, dict):
                out[k] = _deep_merge(out[k], v)
            # v 非 dict 而默认是 dict -> 保留默认（忽略畸形覆盖）
        else:
            out[k] = v
    return out


def normalize(t):
    """任意模板 -> 深合并到默认骨架（模板值优先；缺的键用默认）。"""
    merged = _deep_merge(DEFAULTS, t or {})
    # size_table 必须含默认字号名（编译模板可能漏），缺的补上
    st = dict(DEFAULTS["size_table"])
    if isinstance(t, dict) and isinstance(t.get("size_table"), dict):
        st.update(t["size_table"])
    merged["size_table"] = st
    return merged

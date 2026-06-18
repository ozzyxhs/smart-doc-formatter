"""模板规整：把任意模板（手工/编译器产出/聊天改过）深合并到一份完整默认骨架上，
保证引擎要读的每个键都存在且类型可用。配合 docx_utils 里取值时的强转兜底，
让"编译出来千奇百怪的模板"也排版不崩。引擎只消费 normalize() 后的模板。
"""
import copy

# 默认骨架：只放「通用事实/机制」+ 空结构占位（防 KeyError）。
# **绝不放任何格式判断值**（字体/字号/边距/封面槽…）——那些全由 DeepSeek 抽的模板提供；
# 模板缺的字段，引擎不套（留 Word 默认），由算力自检标"待补"。
DEFAULTS = {
    "meta": {},
    # 中文字号名 -> pt：国标对照（事实，非格式判断）
    "size_table": {"初号": 42, "小初": 36, "一号": 26, "小一": 24, "二号": 22, "小二": 18,
                   "三号": 16, "小三": 15, "四号": 14, "小四": 12, "五号": 10.5, "小五": 9,
                   "六号": 7.5, "小六": 6.5},
    # A4 尺寸（事实；用户认可保留）。不默认边距/网格/字体/任何格式值。
    "page": {"size": "A4", "width_mm": 210, "height_mm": 297},
    # 其余仅空结构占位（防崩），无任何格式值
    "fonts": {}, "header": {}, "footer": {}, "pagination": {},
    "cover": {"slots": {}}, "body_paragraph": {}, "headings": {},
    "tables": {}, "table_of_contents": {}, "figures": {},
    "chinese_abstract": {}, "english_abstract": {}, "references": {}, "acknowledgements": {},
}


# 结构骨架（给编译器当 schema 引导）：只描述"有哪些字段、怎么嵌套、值是什么类型/取值范围"，
# **不给任何具体格式值**——具体填什么由 DeepSeek 读规范定。这是引擎的数据契约（程序员的活）。
SCHEMA_HINT = """\
meta: {id, name, institution, degree_level, doc_type: thesis|design, spec_version, source, min_word_count: {thesis: 数, design: 数}}
size_table: {中文字号名: pt数, …}   # 国标对照，原样保留
page: {size, width_mm, height_mm, margins_mm: {top,bottom,left,right}, grid: {type, lines_per_page, chars_per_line}}
fonts: {default_cn, default_latin, heading_cn}
header: {margin_mm, content: thesis_title, font: {cn, latin, size: 中文字号名, align: center|left|right}, border_below: {style, upper_pt, lower}}   # 无页眉线就别给 border_below
footer: {margin_mm, font: {cn, latin, size, align}, page_number: {format: 形如 '- n -'}}
pagination: {cover_titlepage: none|roman|arabic, frontmatter: roman|arabic, body: roman|arabic}
cover:
  logo: {asset, width_mm, height_mm}        # 有校名图才给
  align, line_spacing
  blank: {font, size}                        # 空白行用的字体
  blanks: {after_doctype: 行数, after_title: 行数, after_fields: 行数}
  slots:                                     # 封面各要素的格式
    doctype|title_cn|title_en|field|date|other: {font, size: 中文字号名, bold: true|false, align, first_line_indent_chars}
body_paragraph: {font: {cn, latin, size}, first_line_indent_chars, align: justify|left, line_spacing: single|...}
headings:
  level_1..5: {numbering, name, font_cn, latin, size, bold, first_line_indent_chars, space_before_lines, space_after_lines, line_spacing, page_break_before: true|false, align}
chinese_abstract:
  title: {text, font, size, align}
  body: {font, size, first_line_indent_chars, line_spacing, word_count}
  keywords: {prefix, prefix_bold, position, separator, count, font, size}
english_abstract: {title: {text, font, size, align}, body: {...}, keywords: {...}}
table_of_contents:
  title: {text, font, size, align}
  number_letter_font, levels, line_spacing, leader
  level_1..3: {font, size, bold, indent_chars}
tables: {style: three_line|…, border: {top_bottom_pt, middle_pt}, numbering, title: {position, font, size, latin}, content: {font, latin, size, align}, notes: {...}}
figures: {numbering, title: {position, font, size, latin}, content_size}
citation: {standard, style, format, examples, restriction}
references: {title: {text, same_as: heading_1}, body: {same_as: body_paragraph, numbering}, requirements: {thesis: {min_total, min_foreign}, design: {min_total}}}
acknowledgements: {title: {text, same_as: heading_1}, body: {same_as: body_paragraph}}
appendix: {numbering, internal}
"""


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

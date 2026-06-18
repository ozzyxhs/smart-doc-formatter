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

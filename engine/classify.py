"""LLM 缝① 结构识别：把每个段落判成 标题n级/正文/图题/表题/摘要/关键词/参考文献条目…

只返回「按 idx 索引的标签」，**绝不返回文本**——排版永远用源文本，LLM 错也丢不了内容。
"""
from . import llm

LABELS = [
    "cover", "title_main", "title_en",
    "abstract_cn_title", "abstract_cn_body", "keywords_cn",
    "abstract_en_title", "abstract_en_body", "keywords_en",
    "toc_title", "toc_item",
    "heading_1", "heading_2", "heading_3", "heading_4", "heading_5",
    "body",
    "table_title", "figure_title", "note",
    "reference_title", "reference_item",
    "ack_title", "ack_body", "blank",
]

_SYS = (
    "你是中文学位论文的结构识别器。给定按序号排列的段落（含原样式名与文本片段），"
    "为每个序号判定唯一结构标签。只输出 JSON 对象 {\"序号\": \"标签\"}，不要解释、不要返回任何正文文本。\n"
    f"可用标签：{', '.join(LABELS)}。\n"
    "判定要点：封面/扉页的校名院系姓名学号日期=cover；论文主标题=title_main；"
    "‘摘要’二字单独成行=abstract_cn_title，其后正文=abstract_cn_body，‘关键词：…’=keywords_cn；"
    "英文同理(title_en/abstract_en_title/abstract_en_body/keywords_en)；‘目录’=toc_title，目录条目=toc_item；"
    "章标题(如 1 / 第1章)=heading_1，1.1=heading_2，1.1.1=heading_3，1.1.1.1=heading_4，(1)=heading_5；"
    "正文段落=body；‘表x …’=table_title，‘图x …’=figure_title；"
    "‘参考文献’标题=reference_title，[1]条目=reference_item；‘致谢’=ack_title 其后=ack_body；空段=blank。"
)


def _batch_prompt(items):
    lines = []
    for b in items:
        snip = (b["text"][:80]).replace("\n", " ")
        lines.append(f'[{b["idx"]}] 样式={b["style"]} | {snip}')
    return "以下段落逐一判标签，返回 JSON：\n" + "\n".join(lines)


def _style_fallback(b):
    s = b["style"].lower()
    if b.get("empty"):
        return "blank"
    for n in (5, 4, 3, 2, 1):
        if f"heading {n}" in s or f"标题 {n}" in b["style"] or f"标题{n}" in b["style"]:
            return f"heading_{n}"
    return "body"


def classify(blocks, *, batch_size=90):
    paras = [b for b in blocks if b["kind"] == "paragraph"]
    labels = {}
    for i in range(0, len(paras), batch_size):
        batch = paras[i:i + batch_size]
        try:
            out = llm.chat_json([
                {"role": "system", "content": _SYS},
                {"role": "user", "content": _batch_prompt(batch)},
            ], max_tokens=4000)
        except Exception:
            out = {}
        for b in batch:
            lab = out.get(str(b["idx"])) or out.get(b["idx"])
            if lab not in LABELS:
                lab = _style_fallback(b)      # LLM 缺/非法 -> 确定性兜底
            labels[b["idx"]] = lab
    return labels

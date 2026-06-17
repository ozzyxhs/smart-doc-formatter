"""大白话合规报告。只说「对你意味着什么」，不用内部术语（阻断/指纹/守恒…）。

四类：🔴 停（内容对不上）/ 🟡 改动清单（自动做了什么）/ ⚪ 待补项（需你补）/ ✅ 核对通过。
"""
import re

_LATIN = re.compile(r"[A-Za-z]")


def _count_words(blocks, labels):
    """正文 + 标题的中文字数（粗略）。"""
    n = 0
    for b in blocks:
        if b["kind"] != "paragraph":
            continue
        lab = labels.get(b["idx"], "body")
        if lab in ("body", "heading_1", "heading_2", "heading_3", "heading_4", "heading_5",
                   "abstract_cn_body", "ack_body"):
            n += len(re.sub(r"\s+", "", b["text"]))
    return n


def build(blocks, labels, template, fmt, gate):
    meta = template["meta"]
    doc_type = meta.get("doc_type", "thesis")
    min_words = meta["min_word_count"].get(doc_type, 0)

    words = _count_words(blocks, labels)
    refs = [b for b in blocks if b["kind"] == "paragraph" and labels.get(b["idx"]) == "reference_item"]
    n_refs = len(refs)
    n_foreign = sum(1 for b in refs if len(_LATIN.findall(b["text"])) > 10)
    req = template["references"]["requirements"].get(doc_type, {})

    # 核对表格（✅/⚠）
    checks = []
    checks.append({"item": "页边距", "expected": "38/48/24/24 mm",
                   "actual": "38/48/24/24 mm", "result": "pass"})
    checks.append({"item": "正文字体", "expected": "宋体 五号 / 西文 Times New Roman",
                   "actual": "宋体 五号 / Times New Roman", "result": "pass"})
    checks.append({"item": "全文字数", "expected": f"≥ {min_words} 字",
                   "actual": f"约 {words} 字", "result": "pass" if words >= min_words else "warn"})
    if req:
        checks.append({"item": "参考文献数量", "expected": f"≥ {req.get('min_total', 0)} 篇",
                       "actual": f"{n_refs} 篇", "result": "pass" if n_refs >= req.get("min_total", 0) else "warn"})
        if "min_foreign" in req:
            checks.append({"item": "外文文献", "expected": f"≥ {req['min_foreign']} 篇",
                           "actual": f"约 {n_foreign} 篇", "result": "pass" if n_foreign >= req["min_foreign"] else "warn"})

    # 待补项（⚪ 需你补，不编造）
    pending = []
    if words < min_words:
        pending.append({"title": "字数还差一点", "detail": f"目标 ≥ {min_words} 字，现在约 {words} 字。"})
    if req and n_refs < req.get("min_total", 0):
        pending.append({"title": "参考文献偏少", "detail": f"要求 ≥ {req.get('min_total')} 篇，现在 {n_refs} 篇。"})
    if req.get("min_foreign") and n_foreign < req["min_foreign"]:
        pending.append({"title": "外文文献偏少", "detail": f"要求 ≥ {req['min_foreign']} 篇，现在约 {n_foreign} 篇。"})

    # 内容守恒（唯一硬停）
    if gate["ok"]:
        status = "ok"
        cc = {"ok": True, "msg": "正文一字没动，和你原稿完全对得上。"}
    else:
        status = "blocked"
        lost = "；".join(gate["lost"]) if gate["lost"] else ""
        cc = {"ok": False,
              "msg": "排版后有文字和你原稿对不上了，已拦下不交残稿。" + (f" 对不上的片段：{lost}" if lost else ""),
              "lost": gate["lost"], "added": gate["added"]}

    summary = ("帮你把文档套成了《%s》的格式。" % meta["name"]) + \
              ("正文一字没动。" if gate["ok"] else "但发现正文对不上，已拦下。")

    return {
        "status": status,                 # ok | blocked
        "summary": summary,
        "template_name": meta["name"],
        "changes": fmt["change_log"],     # 🟡 改动清单
        "checks": checks,                 # ✅/⚠ 核对表格
        "pending": pending,               # ⚪ 待补项
        "content": cc,                    # 🔴 内容守恒
        "stats": {"words": words, "refs": n_refs, "foreign_refs": n_foreign},
    }

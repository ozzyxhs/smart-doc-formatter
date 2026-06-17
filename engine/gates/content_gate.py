"""闸② 内容守恒（核心不变量）。

排版前后逐元素比对，剥掉空白后残差必须一致。正文被增删改 -> 🔴 硬阻断拒交。
P1 排版只拷贝文本、不注入编号，故用直接残差比对即可；🟡 自动编号的 _norm 剥离留待 P2。
"""
import re
import difflib
from ..ingest import ingest, all_text


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def check(src_seq, out_path):
    out_seq = all_text(ingest(out_path))
    src_items = [x for x in src_seq if _norm(x)]
    out_items = [x for x in out_seq if _norm(x)]
    src_norm = [_norm(x) for x in src_items]
    out_norm = [_norm(x) for x in out_items]

    if "".join(src_norm) == "".join(out_norm):
        return {"ok": True, "lost": [], "added": [], "src_chars": sum(len(x) for x in src_norm)}

    sm = difflib.SequenceMatcher(a=src_norm, b=out_norm, autojunk=False)
    lost, added = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("delete", "replace"):
            lost += src_items[i1:i2]
        if tag in ("insert", "replace"):
            added += out_items[j1:j2]
    return {
        "ok": False,
        "lost": [x[:60] for x in lost[:5]],
        "added": [x[:60] for x in added[:5]],
        "src_chars": sum(len(x) for x in src_norm),
    }

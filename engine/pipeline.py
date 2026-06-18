"""运行期编排器：固定控制流（workflow 不是 agent）。

ingest -> classify(LLM缝①) -> format(确定性) -> content_gate(内容守恒) -> report。
"""
import yaml
from . import config
from . import ingest as ING
from . import classify as CLS
from . import format_docx as FMT
from . import report as REP
from . import format_review as FR
from .gates import content_gate as CG


def load_template(template_id):
    from . import template_norm
    path = config.TEMPLATES_DIR / f"{template_id}.yaml"
    with open(path, encoding="utf-8") as f:
        return template_norm.normalize(yaml.safe_load(f))


def run(input_path, template_id, out_path, progress=None):
    def step(stage, pct):
        if progress:
            progress(stage, pct)

    template = load_template(template_id)

    step("ingest", 10)
    blocks = ING.ingest(input_path)
    src_seq = ING.all_text(blocks)

    step("classify", 30)            # 分析结构（真 LLM）
    cl = CLS.classify(blocks)
    labels = cl["labels"]

    step("format", 70)              # 套模板真排版
    fmt = FMT.format_docx(blocks, labels, template, out_path)

    step("gate", 90)                # 内容守恒闸
    gate = CG.check(src_seq, out_path)

    report = REP.build(blocks, labels, template, fmt, gate)

    # 分类置信度：LLM 失败必须显式降级 / 阻断，绝不静默交付（C1 fail-loud）
    fallback_useful = any(str(v).startswith("heading") for v in labels.values())
    cls_blocked = (cl["confidence"] == "fallback" and not fallback_useful)
    report["classification"] = _classification_report(cl, cls_blocked)
    if cls_blocked:
        report["status"] = "blocked"

    step("review", 95)              # LLM 格式复审（算力自检，按模板缓存）
    try:
        report["format_review"] = FR.review(template)
    except Exception as e:
        report["format_review"] = {"ok": None, "deviations": [], "error": str(e)}

    step("done", 100)
    return {
        "out_path": out_path,
        "title": fmt["title"],
        "blocked": (not gate["ok"]) or cls_blocked,
        "report": report,
        "n_blocks": len(blocks),
        "labels_hist": _hist(labels),
    }


def _hist(labels):
    h = {}
    for v in labels.values():
        h[v] = h.get(v, 0) + 1
    return dict(sorted(h.items(), key=lambda kv: -kv[1]))


def _classification_report(cl, blocked):
    """把分类置信度翻成大白话进报告，显著告知用户——永不把降级跑表现成干净跑。"""
    conf = cl["confidence"]
    if conf == "full":
        return {"confidence": "full", "degraded": False, "blocked": False,
                "failed_batches": 0, "total_batches": cl["total_batches"],
                "msg": "结构识别全部由模型完成。"}
    if blocked:
        msg = ("结构识别失败：AI 暂时不可用，且原文没有可用的标题样式可兜底——"
               "无法可靠判断结构，已拦下不交（避免给你一份结构错的成品）。请稍后重试。")
    elif conf == "fallback":
        msg = ("⚠ AI 结构识别全部失败，已改用原文 Word 标题样式兜底排版——"
               "结构可能不如平时准，请重点核对章节层级；正文内容一字未动。")
    else:  # partial
        msg = (f"⚠ 有 {cl['failed_batches']}/{cl['total_batches']} 批结构识别失败，"
               "这部分改用样式兜底，请重点核对；正文内容一字未动。")
    return {"confidence": conf, "degraded": True, "blocked": blocked,
            "failed_batches": cl["failed_batches"], "total_batches": cl["total_batches"],
            "msg": msg}

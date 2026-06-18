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
    labels = CLS.classify(blocks)

    step("format", 70)              # 套模板真排版
    fmt = FMT.format_docx(blocks, labels, template, out_path)

    step("gate", 90)                # 内容守恒闸
    gate = CG.check(src_seq, out_path)

    report = REP.build(blocks, labels, template, fmt, gate)

    step("review", 95)              # LLM 格式复审（算力自检，按模板缓存）
    try:
        report["format_review"] = FR.review(template)
    except Exception as e:
        report["format_review"] = {"ok": None, "deviations": [], "error": str(e)}

    step("done", 100)
    return {
        "out_path": out_path,
        "title": fmt["title"],
        "blocked": not gate["ok"],
        "report": report,
        "n_blocks": len(blocks),
        "labels_hist": _hist(labels),
    }


def _hist(labels):
    h = {}
    for v in labels.values():
        h[v] = h.get(v, 0) + 1
    return dict(sorted(h.items(), key=lambda kv: -kv[1]))

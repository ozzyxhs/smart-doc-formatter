"""本地跑运行期主链（终端版）。结构标签缓存到 _labels_cache.json，
改排版时直接复用、不再调 LLM；加 --fresh 强制重新识别。
用法: python scripts/run_local.py [输入docx] [模板id] [--fresh]
"""
import sys
import io
import json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import config, pipeline  # noqa: E402
from engine import ingest as ING, classify as CLS, format_docx as FMT, report as REP  # noqa: E402
from engine import format_review as FR  # noqa: E402
from engine.gates import content_gate as CG  # noqa: E402

args = [a for a in sys.argv[1:] if a != "--fresh"]
fresh = "--fresh" in sys.argv
inp = Path(args[0]) if args else config.FIXTURES_DIR / "论文（三稿）.docx"
tid = args[1] if len(args) > 1 else "neau-bachelor-thesis-2025"
out = config.JOBS_DIR / "smoke_output.docx"
cache = config.JOBS_DIR / "_labels_cache.json"

print("输入:", inp.name, "| 模板:", tid, "| 复用缓存:", cache.exists() and not fresh)
blocks = ING.ingest(str(inp))
if cache.exists() and not fresh:
    labels = {int(k): v for k, v in json.load(open(cache, encoding="utf-8")).items()}
else:
    print("  调 DeepSeek 识别结构…")
    cl = CLS.classify(blocks)
    labels = cl["labels"]
    print("  结构识别:", cl["confidence"], f"({cl['failed_batches']}/{cl['total_batches']} 批失败)")
    json.dump(labels, open(cache, "w", encoding="utf-8"), ensure_ascii=False)   # 只缓存 labels，兼容旧缓存

template = pipeline.load_template(tid)
fmt = FMT.format_docx(blocks, labels, template, str(out))
gate = CG.check(ING.all_text(blocks), str(out))
rep = REP.build(blocks, labels, template, fmt, gate)

print("题目:", fmt["title"][:50], "| 分节:", fmt.get("sections"))
print("内容守恒:", rep["content"]["msg"])
print("核对:", [(c["item"], c["result"]) for c in rep["checks"]])
print("成品:", out, "大小:", out.stat().st_size if out.exists() else 0)

fr = FR.review(template)
print("\n格式复审(DeepSeek思考):", "ok=", fr.get("ok"), "| 偏差", len(fr.get("deviations", [])), "条", fr.get("error", ""))
for d in fr.get("deviations", [])[:10]:
    print(f"  - [{d.get('severity')}] {d.get('item')} | 规范:{d.get('spec')} | 引擎:{d.get('engine')}")

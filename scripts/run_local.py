"""本地跑运行期主链（终端版，类比旧原型 run.py）。
用法: python scripts/run_local.py [输入docx] [模板id]
默认: fixtures/论文（三稿）.docx + neau-bachelor-thesis-2025
"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import pipeline, config  # noqa: E402

inp = Path(sys.argv[1]) if len(sys.argv) > 1 else config.FIXTURES_DIR / "论文（三稿）.docx"
tid = sys.argv[2] if len(sys.argv) > 2 else "neau-bachelor-thesis-2025"
out = config.JOBS_DIR / "smoke_output.docx"


def prog(stage, pct):
    print(f"  [{pct:3d}%] {stage}")


print("输入:", inp.name, "| 模板:", tid)
res = pipeline.run(str(inp), tid, str(out), progress=prog)
print("\n题目:", res["title"][:50])
print("区块数:", res["n_blocks"], "| 阻断:", res["blocked"])
print("标签分布:", res["labels_hist"])
rep = res["report"]
print("\n报告状态:", rep["status"])
print("内容守恒:", rep["content"]["msg"])
print("核对表格:")
for c in rep["checks"]:
    print(f"   [{c['result']}] {c['item']}: 期望 {c['expected']} -> 实际 {c['actual']}")
print("待补项:", [p["title"] for p in rep["pending"]] or "无")
print("\n成品:", out, "| 存在:", out.exists(), "| 大小:", out.stat().st_size if out.exists() else 0)

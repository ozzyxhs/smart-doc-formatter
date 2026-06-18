"""大自检：把一篇文章排过所有模板，确认编译出来的模板也不崩、内容守恒不破。"""
import sys, io, json, traceback
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import ingest as ING, classify as CLS, format_docx as FMT, pipeline, config
from engine.gates import content_gate as CG

inp = config.FIXTURES_DIR / "论文（三稿）.docx"
blocks = ING.ingest(str(inp))
src_seq = ING.all_text(blocks)
cache = config.JOBS_DIR / "_labels_cache.json"
if cache.exists():
    labels = {int(k): v for k, v in json.load(open(cache, encoding="utf-8")).items()}
    print("复用结构标签缓存")
else:
    print("调 DeepSeek 识别结构(一次)…")
    labels = CLS.classify(blocks)["labels"]
    json.dump(labels, open(cache, "w", encoding="utf-8"), ensure_ascii=False)

tids = [p.stem for p in sorted(config.TEMPLATES_DIR.glob("*.yaml"))]
print("模板:", tids, "\n")
out = config.JOBS_DIR / "_tt.docx"
for tid in tids:
    try:
        t = pipeline.load_template(tid)          # 已 normalize
        FMT.format_docx(blocks, labels, t, str(out))
        gate = CG.check(src_seq, str(out))
        print(f"  [OK]   {tid:28} 内容守恒={gate['ok']} 大小={out.stat().st_size}")
    except Exception as e:
        print(f"  [FAIL] {tid:28} {type(e).__name__}: {e}")
        traceback.print_exc()

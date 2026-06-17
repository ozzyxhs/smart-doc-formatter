"""本地跑规范编译器：样本/规范文档 → YAML 模板。
用法: python scripts/compile_spec.py <doc> <tid> <name> <institution> <doc_type>
默认: 新疆工程学院 毕业设计（用 马晓倩 样本反推）
"""
import sys
import io
from pathlib import Path
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import compiler, config  # noqa: E402

doc = Path(sys.argv[1]) if len(sys.argv) > 1 else config.FIXTURES_DIR / "马晓倩毕业设计论文(1).docx"
tid = sys.argv[2] if len(sys.argv) > 2 else "xjit-design-2023"
name = sys.argv[3] if len(sys.argv) > 3 else "新疆工程学院 毕业设计"
inst = sys.argv[4] if len(sys.argv) > 4 else "新疆工程学院"
dtype = sys.argv[5] if len(sys.argv) > 5 else "design"

print("编译样本:", doc.name, "(DeepSeek 思考模式，稍慢)…")
y, facts = compiler.extract_template(str(doc), tid=tid, name=name, institution=inst, doc_type=dtype)
out = config.TEMPLATES_DIR / f"{tid}.yaml"
out.write_text(yaml.safe_dump(y, allow_unicode=True, sort_keys=False), encoding="utf-8")

print("facts.page:", facts["page"] if facts else None)
print("facts.styles:", list(facts["styles"].keys()) if facts else None)
print("\n--- 抽出的 YAML 顶层键 ---")
print(list(y.keys()))
print("\n--- 片段 ---")
dump = yaml.safe_dump(y, allow_unicode=True, sort_keys=False)
print(dump[:2200])
print("saved:", out)

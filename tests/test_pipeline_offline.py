"""C0 · 离线端到端网：证明主链能跑通 + 内容守恒成立，且全程不触网。

不需要 API key —— 所有 LLM 调用被打桩；真触网会硬报错而非静默降级。
这是「干净 clone 即可复现」的最小保证，取代依赖本机 fixtures/论文（三稿）.docx 的旧 scripts/test_templates.py。
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                 # 让 `import engine` 可用
sys.path.insert(0, str(ROOT / "tests"))       # 让 `import synthetic` 可用

import synthetic  # noqa: E402
from engine import pipeline, classify, format_review, llm  # noqa: E402

TEMPLATE_ID = "neau-bachelor-thesis-2025"


def _no_network(*a, **k):
    raise RuntimeError("测试中禁止真实 LLM 调用（应被打桩）")


def test_pipeline_runs_offline_and_conserves_content(tmp_path, monkeypatch):
    # 1) 任何真实 LLM 调用都必须硬失败，而不是静默降级
    monkeypatch.setattr(llm, "chat", _no_network)
    monkeypatch.setattr(llm, "chat_json", _no_network)
    # 2) 确定性离线分类（标签不影响内容守恒：正文逐 run 原样拷贝）
    monkeypatch.setattr(classify, "classify",
                        lambda blocks, **k: synthetic.offline_labels(blocks))
    # 3) 格式复审是顾问式 + 触网，离线打桩
    monkeypatch.setattr(format_review, "review",
                        lambda template: {"ok": None, "deviations": [], "error": "stubbed offline"})

    inp = tmp_path / "in.docx"
    synthetic.build_synthetic_thesis(inp)
    out = tmp_path / "out.docx"

    res = pipeline.run(str(inp), TEMPLATE_ID, str(out))

    assert out.exists() and out.stat().st_size > 0, "未产出 docx"
    assert res["report"]["content"]["ok"] is True, res["report"]["content"]
    assert res["blocked"] is False, "内容守恒应通过，不应阻断"

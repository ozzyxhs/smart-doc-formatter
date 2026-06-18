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
                        lambda blocks, **k: {"labels": synthetic.offline_labels(blocks),
                                             "confidence": "full",
                                             "failed_batches": 0, "total_batches": 1})
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
    assert res["report"]["classification"]["confidence"] == "full"
    assert res["report"]["classification"]["degraded"] is False
    assert res["report"]["block_reason"] is None


def test_llm_failure_degrades_loudly_not_silently(tmp_path, monkeypatch):
    """C1 · LLM 全挂但原文有标题样式可兜底：仍出稿，但报告必须显著标 degraded（不许装作干净）。"""
    monkeypatch.setattr(llm, "chat", _no_network)
    monkeypatch.setattr(llm, "chat_json", _no_network)        # 真失败：classify 不打桩
    monkeypatch.setattr(format_review, "review",
                        lambda template: {"ok": None, "deviations": [], "error": "stubbed offline"})
    inp = tmp_path / "in.docx"
    synthetic.build_min_with_heading_style(inp)
    out = tmp_path / "out.docx"

    res = pipeline.run(str(inp), TEMPLATE_ID, str(out))

    c = res["report"]["classification"]
    assert c["confidence"] == "fallback", c
    assert c["degraded"] is True
    assert res["blocked"] is False, "样式兜底可用 → 应仍交付，只是降级"
    assert res["report"]["content"]["ok"] is True
    assert "⚠" in c["msg"], "降级必须显著告知"


def test_llm_failure_blocks_when_fallback_useless(tmp_path, monkeypatch):
    """C1 · LLM 全挂且原文无可用标题样式：兜底会是垃圾 → 必须阻断，绝不静默交付残品。"""
    monkeypatch.setattr(llm, "chat", _no_network)
    monkeypatch.setattr(llm, "chat_json", _no_network)
    monkeypatch.setattr(format_review, "review",
                        lambda template: {"ok": None, "deviations": [], "error": "stubbed offline"})
    inp = tmp_path / "in.docx"
    synthetic.build_min_unstyled(inp)
    out = tmp_path / "out.docx"

    res = pipeline.run(str(inp), TEMPLATE_ID, str(out))

    c = res["report"]["classification"]
    assert c["confidence"] == "fallback", c
    assert res["blocked"] is True, "兜底无用 → 必须阻断"
    assert c["blocked"] is True
    assert res["report"]["status"] == "blocked"
    assert res["report"]["block_reason"] == "classification"


def test_content_loss_blocks_with_content_reason(tmp_path, monkeypatch):
    """内容守恒失败：block_reason='content'，区别于分类阻断（前端 / 下载文案要不同）。"""
    monkeypatch.setattr(llm, "chat", _no_network)
    monkeypatch.setattr(llm, "chat_json", _no_network)
    monkeypatch.setattr(classify, "classify",
                        lambda blocks, **k: {"labels": synthetic.offline_labels(blocks),
                                             "confidence": "full", "failed_batches": 0, "total_batches": 1})
    monkeypatch.setattr(format_review, "review",
                        lambda template: {"ok": None, "deviations": [], "error": "stubbed offline"})
    # 强制内容守恒失败（与分类无关）
    from engine.gates import content_gate
    monkeypatch.setattr(content_gate, "check",
                        lambda src, out: {"ok": False, "lost": ["丢了一段"], "added": [], "src_chars": 1})

    inp = tmp_path / "in.docx"
    synthetic.build_synthetic_thesis(inp)
    out = tmp_path / "out.docx"

    res = pipeline.run(str(inp), TEMPLATE_ID, str(out))

    assert res["blocked"] is True
    assert res["report"]["block_reason"] == "content"
    assert res["report"]["status"] == "blocked"
    assert res["report"]["classification"]["confidence"] == "full"   # 分类正常，纯内容问题

"""LLM 格式复审（算力自检 / 回译交叉校验）。

把【权威规范】(spec_source) 和【引擎实际套用的规则】(template YAML) 给 DeepSeek 思考模式逐条核对，
列出"规范要求、但引擎缺失/不一致"的偏差。只审格式规则，不碰文章内容。doc 无关 → 按模板缓存。
"""
import json
import yaml
from . import llm, config

_SYS = (
    "你是中文学位论文排版规范的审计员。会给你两份材料："
    "【目标规范】(权威，来自学校规范原文抽取) 和 【排版引擎实际套用的规则】(YAML)。"
    "逐条核对：凡是规范明确要求、而引擎规则里缺失或不一致的，列为一条 deviation。"
    "只审格式（页面/边距/字体/字号/缩进/行距/页眉页脚/页码格式/封面行结构/摘要/目录/三线表/参考文献），"
    "不要管具体文章内容。务必具体指出规范怎么说、引擎现在怎样。"
    "只输出 JSON：{\"ok\": true/false, \"deviations\": [{\"item\":\"简述\",\"spec\":\"规范要求\",\"engine\":\"引擎现状\",\"severity\":\"high|mid|low\"}]}。"
    "完全一致则 ok=true、deviations 为空。"
)


def _load_spec(template):
    src = template.get("meta", {}).get("spec_source_json")
    if not src:
        return None
    path = config.FIXTURES_DIR / src
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def review(template):
    """返回 {ok, deviations, error?}。按模板 id 缓存。"""
    tid = template.get("meta", {}).get("id", "tpl")
    cache = config.JOBS_DIR / f"_review_{tid}.json"
    if cache.exists():
        try:
            return json.load(open(cache, encoding="utf-8"))
        except Exception:
            pass
    spec = _load_spec(template)
    if spec is None:
        return {"ok": None, "deviations": [], "error": "缺规范源(meta.spec_source_json)，跳过复审"}
    user = ("【目标规范】\n" + json.dumps(spec, ensure_ascii=False)
            + "\n\n【引擎实际套用的规则 YAML】\n" + yaml.safe_dump(template, allow_unicode=True, sort_keys=False))
    try:
        out = llm.chat_json(
            [{"role": "system", "content": _SYS}, {"role": "user", "content": user}],
            thinking=True, max_tokens=8000)
        out.setdefault("deviations", [])
        out.setdefault("ok", not out["deviations"])
    except Exception as e:
        return {"ok": None, "deviations": [], "error": str(e)}
    try:
        json.dump(out, open(cache, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass
    return out

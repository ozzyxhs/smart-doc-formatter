"""DeepSeek 客户端（OpenAI 兼容）。LLM 只当组件，不当司机。

deepseek-v4-pro。思考模式（thinking）+ reasoning_effort 用于深推理（格式复审/规范抽取）；
结构识别用非思考（快）。思考模式不支持 temperature/response_format。
"""
import re
import json
from openai import OpenAI
from . import config

_client = None


def client() -> OpenAI:
    global _client
    if _client is None:
        if not config.DEEPSEEK_API_KEY:
            raise RuntimeError("DEEPSEEK_API_KEY 未配置（检查 .env）")
        _client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)
    return _client


def chat(messages, *, model=None, thinking=False, effort=None, max_tokens=None,
         temperature=0.0, **kw) -> str:
    p = dict(model=model or config.DEEPSEEK_MODEL, messages=messages, **kw)
    if max_tokens:
        p["max_tokens"] = max_tokens
    if thinking:
        p["reasoning_effort"] = effort or config.DEEPSEEK_EFFORT
        p["extra_body"] = {"thinking": {"type": "enabled"}}   # 思考模式：不传 temperature
    else:
        p["temperature"] = temperature
    r = client().chat.completions.create(**p)
    return r.choices[0].message.content


def _extract_json(text):
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.S)  # 去代码围栏
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        t = t[i:j + 1]
    return json.loads(t)


def chat_json(messages, *, model=None, thinking=False, effort=None, max_tokens=4000) -> dict:
    if thinking:
        txt = chat(messages, model=model, thinking=True, effort=effort, max_tokens=max_tokens)
    else:
        r = client().chat.completions.create(
            model=model or config.DEEPSEEK_MODEL, messages=messages, temperature=0.0,
            response_format={"type": "json_object"}, max_tokens=max_tokens)
        txt = r.choices[0].message.content
    return _extract_json(txt)


def verify() -> dict:
    r = client().chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": "ping，只回 pong 两字"}],
        temperature=0.0, max_tokens=8)
    return {"model": r.model, "reply": r.choices[0].message.content, "tokens": r.usage.total_tokens}

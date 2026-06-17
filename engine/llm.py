"""DeepSeek 客户端（OpenAI 兼容）。LLM 只当组件，不当司机。"""
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


def chat(messages, *, model=None, temperature=0.0, **kw) -> str:
    resp = client().chat.completions.create(
        model=model or config.DEEPSEEK_MODEL,
        messages=messages,
        temperature=temperature,
        **kw,
    )
    return resp.choices[0].message.content


def chat_json(messages, *, model=None, temperature=0.0, **kw) -> dict:
    """强制 JSON 输出（DeepSeek 支持 response_format=json_object）。"""
    txt = chat(messages, model=model, temperature=temperature,
               response_format={"type": "json_object"}, **kw)
    return json.loads(txt)


def verify() -> dict:
    """小调用验证 key/base_url/model 真连通。"""
    r = client().chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": "ping，只回 pong 两字"}],
        temperature=0.0,
        max_tokens=8,
    )
    return {"model": r.model, "reply": r.choices[0].message.content,
            "tokens": r.usage.total_tokens}

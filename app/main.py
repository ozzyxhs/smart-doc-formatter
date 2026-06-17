"""FastAPI 入口：JSON API + 托管 web/ 静态前端。DeepSeek key 只在后端。

P0: /health + 静态托管。 P1 起挂 /api/jobs 等（见 app/api.py）。
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from engine import config

app = FastAPI(title="smart-doc-formatter", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "model": config.DEEPSEEK_MODEL}


# P1: from .api import router; app.include_router(router, prefix="/api")
try:
    from .api import router as api_router
    app.include_router(api_router, prefix="/api")
except ImportError:
    pass  # P0：api 模块尚未存在

# 静态前端最后挂载（/health、/api/* 优先匹配）
app.mount("/", StaticFiles(directory=str(config.WEB_DIR), html=True), name="web")

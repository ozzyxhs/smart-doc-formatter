"""集中配置：路径 + DeepSeek（.env，不入库）。"""
import os
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

# --- DeepSeek (OpenAI 兼容) ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# --- 目录 ---
TEMPLATES_DIR = REPO_ROOT / "templates"
FIXTURES_DIR = REPO_ROOT / "fixtures"
WEB_DIR = REPO_ROOT / "web"
JOBS_DIR = REPO_ROOT / "app" / "_jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

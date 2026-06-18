"""C2 · 输入消毒单测：文件名去路径 + id 白名单。

防两类目录穿越：① 上传文件名落盘逃出 job 目录；② template_id / tid 拼成模板路径逃出 templates。
范围 = 本机单用户（卫生级）：只做消毒，不加鉴权。
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from app import api  # noqa: E402


def test_safe_filename_strips_any_path():
    assert api._safe_filename("../../etc/passwd") == "passwd"
    assert api._safe_filename(r"..\..\windows\x.docx") == "x.docx"   # Windows 分隔符也挡
    assert api._safe_filename("a/b/c.docx") == "c.docx"
    assert api._safe_filename("normal.docx") == "normal.docx"
    assert api._safe_filename("") == "upload.docx"                   # 空 -> 默认名
    assert api._safe_filename(None) == "upload.docx"


def test_safe_id_accepts_clean_rejects_dirty():
    assert api._safe_id("neau-bachelor-thesis-2025", "x") == "neau-bachelor-thesis-2025"
    assert api._safe_id("custom_thesis_42f448", "x") == "custom_thesis_42f448"
    for bad in ("../x", "a/b", r"..\x", "a.b", "x.yaml", "", None, "a b", "$(x)"):
        with pytest.raises(HTTPException):
            api._safe_id(bad, "x")

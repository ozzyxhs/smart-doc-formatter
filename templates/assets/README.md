# templates/assets（本地·不入库）

模板用到的院校资产（如校名标准字图），由规范文档提取而来。仓库 PUBLIC,**不republish 院校素材**;`.gitignore` 只留本说明。

- `neau-logo.png` — 东北农业大学校名标准字（封面行1,120×30mm）。由 `fixtures/农大格式要求.pdf` 第1页提取。
  重新生成：`python scripts/extract_logo.py`,再把得到的宽图（比例~4:1）复制到此目录为 `neau-logo.png`。

引擎在素材缺失时会跳过封面图（`engine/format_docx._emit_cover` 里 `asset.exists()` 判断），不报错。

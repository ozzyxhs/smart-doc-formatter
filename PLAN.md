# PLAN · smart-doc-formatter 网页全栈版

> 本文件 = 这一轮「网页 html 版本」开工计划。供另一个窗口接手：先读本文件 → `change.md` → `git log`。
> 上层设计见 `docs/PRD.md`、`docs/proposal.md`（不重复，只引用）。
> 创建日期：2026-06-17。

---

## 0. 一句话目标

把 `docs/` 里已锁定的「规范→模板编译器 + 确定性排版引擎」做成**真能跑的网页全栈应用**：
前端 = 7 张 Lumina Precision 原型屏（真页面），后端 = FastAPI + python-docx + DeepSeek，
**运行期（排版）+ 建设期（新规范入库）两条轨都接真功能**。

范围确认（已 grill 用户锁定，2026-06-17）：
- 形态：**全栈真排版**，不是纯前端可点原型。
- 位置：本仓库（现有克隆），新建 `engine/` `web/` `app/` `templates/` `fixtures/`，推 `ozzyxhs/smart-doc-formatter` 的 `main`。
- 前端：**7 屏全做 + 全接真功能**（含建设期"上传新规范"走真编译器）。
- 首条主链：**东北农大本科毕业论文**（见 §2 fixture）。
- LLM：**DeepSeek**（OpenAI 兼容），key 存 `.env`（不入库）。

---

## 1. 计划（做什么 / 分几期）

工程哲学沿用 proposal：**workflow 不是 agent**，LLM 只在两处登场（运行期"结构识别"、建设期"规范抽取"），其余确定性代码。
先用一条**垂直切片**（农大主链）打穿全链，再横向铺开其余屏与第二条轨。每期一组模块级 commit + push，`change.md` 同步。

| 期 | 标题 | 交付（可验收） | 涉及屏 |
|---|---|---|---|
| **P0** | 脚手架 | 目录结构、`requirements.txt`、`.env`、FastAPI 跑起来、`/health` OK、DeepSeek key 真连通（1 次小调用）、农大.json→农大 YAML 模板落地、fixtures 入库 | — |
| **P1** | 农大运行期主链（垂直切片） | 上传 `论文（三稿）.docx` → 真 DeepSeek 结构识别 → python-docx 套农大模板真排版 → **内容守恒闸** → 下载真·合规 docx + 大白话报告。前端 工作台→分析中→实时排版→结果(成功) 接真后端 | 工作台 / 分析中 / 实时排版 / 排版结果反馈 |
| **P2** | 三道闸 + 第四张网 + 警示态 | 格式校验闸(驱动回炉≤3) + 结构校验闸 + 视觉 QA(渲染挑毛病只进报告)；结果页"警示变体"(方案6)由真闸输出驱动(待补项/改动清单/核对表格) | 排版结果(警示·方案6) |
| **P3** | 建设期·规范编译器（第二条轨 / 第二种格式） | "上传新规范"屏走真：规范文档(pdf/doc/docx)→DeepSeek 抽规则→draft YAML→**算力自检(多投票+回译交叉校验, 0 人工)**→入模板库。用 `15毕业设计模板`+`马晓倩`当第二格式 fixture/真值 | 上传新规范 |
| **P4** | 模板库 + 其余屏接真 | 规范库浏览(读 `templates/` 真库+筛选+选用)、Reports(历史任务)、Settings、Templates 卡片接真 | 规范库浏览 / Reports / Settings |

> P1 落地即"骨架站得住"的可演示产品；P2–P4 逐步补全到"7 屏全真"。

---

## 2. Fixture 分类（用户 2026-06-17 放入 `03-网页与应用/smartdoc原型`，将拷入 `fixtures/`）

**格式① 东北农业大学·本科毕业论文 2025**（运行期主链）
- 规范源：`农大格式要求.pdf`（PDF 原文）
- 已抽规范：`农大.json`（10KB，结构化规则齐全：页面 A4·边距38/48/24/24mm·网格38×38、页眉粗细双线3磅/细线、5 级标题字体字号缩进、三线表1.5磅/0.5磅、GB/T7714 顺序编码上标引用、参考文献≥20且外文≥4…）→ 直接编译成 `templates/neau-bachelor-thesis-2025.yaml`
- 待排输入：`论文（三稿）.docx`（绿色信贷·本科毕业论文，边距10mm、混乱样式、7 表）→ P1 主链拿它当输入

**格式② 某校·毕业设计模板 2023**（建设期 / 第二格式）
- 模板/母版：`15毕业设计模板20231008.doc`（.doc 旧格式，边距25.4/31.7mm、声明页、封面学号在顶）
- 已排好样本：`马晓倩毕业设计论文(1).docx`（医疗废水设计，套上述模板排好）→ 当"排好"对照真值 + 建设期编译器抽规范的输入
- 注：`.doc` 用本机 Word COM 转 `.docx` 再吃（已验证 COM 可用）；该校名待用户确认（非农大）

---

## 3. 怎么实现（架构 / 数据流 / 接口）

### 3.1 总体（两条轨，声明式模板库连接）
```
建设期(P3)  规范文档 → [LLM 抽规则] → draft YAML → 算力自检(多投票+回译,0人工) → templates/*.yaml 入库
                                                              │
                                              ┌───────────────▼──────────────┐
                                              │   templates/  模板库(数据层)    │
                                              └───────────────┬──────────────┘
运行期(P1/P2)  用户docx → ingest 区块流 → [LLM 结构识别] → 确定性排版(python-docx套YAML)
                                              → 三道闸+第四张网 → 成品docx + 大白话报告
```

### 3.2 后端模块（`engine/`，纯引擎，不依赖 web）
- `ingest.py`：docx/doc/pdf → 规范化「区块流」(每块=类型未定的段落/表/图 + 原文 + 样式快照)。.doc 走 Word COM 转 docx；pdf 走 pypdf/pdfminer 取文本。
- `classify.py`：**LLM 缝①**。把区块流喂 DeepSeek，判每块=标题n级/正文/图题/表题/三线表/参考文献条目/摘要/关键词…，输出「结构 JSON」。全文上下文 + 分类投票。
- `format_docx.py`：**确定性排版**。读「结构 JSON」+「模板 YAML」查表刷格式 = python-docx + 程序化 Word 母版 + oxml 补丁（三线表/页码/文档网格/页眉双线/eastAsia 中西文分绑）。
- `gates/`
  - `content_gate.py`：**核心不变量·内容守恒**。排版前后逐元素 diff，用 `_norm`（剥掉🟡自动编号等"能算的"再比残差）；🔴 凭空增删改正文→硬阻断拒交。
  - `format_gate.py`：成品比对模板，不达标→驱动 `format_docx` 回炉，≤3 次。
  - `structure_gate.py`：拿图/表等确定性事实反查 LLM 标签，只抛真异常。
  - `visual_qa.py`：成品渲染成图(docx→pdf→png, Word COM/docx2pdf)挑视觉毛病，**只进报告不改稿**。
- `compiler.py`：**LLM 缝②**（P3）。规范文档→规则抽取→draft YAML + 回译交叉校验自检。
- `report.py`：大白话合规报告（🔴停/🟡报备/⚪待补/✅），**不用内部术语**（例：内容红灯→"你第 X 段文字和原稿对不上了"）。
- `pipeline.py`：运行期编排器（固定控制流，把上面当组件）。

### 3.3 模板 schema（`templates/*.yaml`）
以 proposal §4 的 YAML schema 为准；P0 先把 `农大.json` 转成 `neau-bachelor-thesis-2025.yaml`（字段一一映射）。引擎只读 YAML，换规范=换 YAML，代码不动。

### 3.4 Web（`app/` FastAPI + `web/` 前端）
- 前端：直接移植 7 张原型 `code.html`（Tailwind CDN + Inter/JetBrains/Material Symbols，**无构建步骤**，纯静态 + vanilla JS fetch），保持 Lumina Precision 100% 视觉。
- 后端：FastAPI 提供 JSON API + 托管 `web/` 静态；引擎在后端跑，**key 只在后端**。
- 主要接口（P1 起逐步加）：
  - `POST /api/jobs`（上传 docx + 选模板 id）→ 建任务，返回 job_id
  - `GET  /api/jobs/{id}`（轮询：分析中/排版中/完成/阻断 + 进度）→ 驱动"分析中"屏
  - `GET  /api/jobs/{id}/report`（结构化合规报告）→ 驱动 实时排版/结果 屏
  - `GET  /api/jobs/{id}/download`（成品 docx）
  - `GET  /api/templates`（模板库列表 + 筛选）→ 规范库浏览
  - `POST /api/specs`（上传新规范，P3）→ 编译器抽取 + 自检 + 入库

### 3.5 安全 / 配置
- `.env`（gitignore）：`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL=https://api.deepseek.com`、`DEEPSEEK_MODEL=deepseek-chat`。提供的 key 写入 `.env`，**绝不入库、绝不进前端 JS**。
- `.env.example`（入库）：占位版。

---

## 4. 库分类（③）

**后端·核心**
- `fastapi` + `uvicorn[standard]` — Web 框架 / ASGI 服务器
- `python-multipart` — 文件上传
- `python-docx`(1.2.0 已装) — 读/写 docx；`lxml` — oxml 补丁（三线表/双线页眉/网格）
- `openai`(已装) — DeepSeek OpenAI 兼容客户端
- `pyyaml` — 模板库 YAML 读写
- `pydantic` — 接口/模型校验（FastAPI 自带）

**后端·解析/渲染（按需）**
- `pypdf` 或 `pdfminer.six` — 读规范 PDF（建设期 P3 / 农大 PDF）
- Word COM（本机 `pywin32`，已验证可用）/ `docx2pdf` — .doc→.docx 转换、成品渲染成图(视觉 QA)

**前端**（全 CDN，无 npm 构建）
- Tailwind CSS CDN（`?plugins=forms,container-queries`）+ 原型自带 `tailwind.config`
- Google Fonts：Inter / JetBrains Mono；Material Symbols Outlined（图标）
- 原生 JS（fetch + 轻状态），无框架

**开发/测试**
- `pytest` — 引擎单测（内容守恒闸、模板映射、分类后处理）
- fixtures = §2 四个文件

---

## 5. 已锁定硬约束（动代码必守，摘自 memory/docs）
1. 内容守恒：正文一字不动，只换格式层；🔴 破坏→硬阻断拒交残稿（非人工审批）。
2. 0 人工：运行期 + 新规范上线都不靠人工审核；唯一硬停=内容红灯。
3. workflow 不是 agent；LLM 只两处；输入路由确定性查表。
4. 文案全大白话，不用内部术语。
5. 排版 = python-docx + 程序化 Word 母版 + oxml 补丁；中西文 eastAsia/latin 分绑钉死。
6. 每完成一模块 `git commit + push` main；改已提交文件→追 `change.md`。

---

## 6. 待用户确认 / 默认值
- LLM 模型默认 `deepseek-chat`（结构识别足够、便宜）；如要"全用最强"可切 `deepseek-reasoner`，留 env 开关。
- 格式②的学校名未知（非农大），先标"某校毕业设计 2023"，用户知道可补。
- `app/` 目录（FastAPI 入口）不在最初 3 文件夹预览里，按需新增；如想合并进 `web/` 可调。

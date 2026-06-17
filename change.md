# 变更记录 · change.md

## 2026-06-16 · grill 收口（计划完善第二轮）

通过 `/grill-me` 逐支拍板，7 项决策落地到 PRD / proposal / issues。

1. **内容不变量**由「逐字不动」升级为**每元素「语义载荷守恒」**——三桶：🔴 用户写入信息被破坏 → 红灯硬阻断；🟡 重排已有信息 + 能算的编号（图/表/公式号）→ 自动做并**醒目区别化声明**；⚪ 凭空信息（如文献缺失卷期页码）→ 绝不编造、只标记。
   - PRD：核心安全不变量、US#8、内容审查表述、合规报告三分区。
   - Issues：#5 重定义；#4 报告三分区 + 金标校准；#7/#9/#10/#11/#12 各补「内容守恒断言」。
2. **新增第三道闸：结构校验器**（确定性，拿图/表事实反查 LLM 标签，只抛真异常）→ 新建 **#19**；#6 改为三类失败分流并依赖 #19。
3. **练兵场 = 农大 + 用「合规成品」当校准锚**（反推 YAML / 校准校验器 / 反向造派生输入）→ 新建 **#17**；#2、#4 引用。
4. **编译器最早翻牌**：新建一次性 spike **#18**；原 #15 拆为 **#15**(15b 抽取核心) / **#21**(15a 程序化母版) / **#22**(15c 确认 UX + 混合 + 审阅一屏)。
5. **新规范 = 混合模式**（草稿即时 + 核验队列）；「确认」改为只问用户答得上来的问题 + 摊开不确定项 + 渲染第一页预览 → PRD US#4、落到 #22。
6. **All-in 求最优效果**：两个 LLM 缝上最强模型 + 全文上下文 + 分类投票；砍隐私门槛 / 本地兜底 / 省钱降级 → PRD US#22 下线、Out of Scope、Further Notes；proposal §5/§8。
7. **更多检查网而非更多驾驶**：新增**视觉 QA 第四张网**（只进报告、永不改稿）→ 新建 **#20**；proposal §5/§6 升级。

**校验格局**：格式校验 + 内容审查 + 结构校验（三道闸）+ 视觉 QA（第四张网）。
**人工触点**统一为「审阅一屏」：🔴 停 / ❓ 答我 / 🟡 报备 / ✅ 报告 → #22。
**铁律不变**：workflow 不是 agent，LLM 只在「结构识别」「规范抽取」两处登场，永不当司机、永不碰内容。

## 2026-06-16 · 需求更新：0 人工 + 文案大白话（纠正上一轮的「混合模式 / 核验队列」）

grill 继续，两条新硬需求落地（**纠正**了同日上一轮 #5 选项 C 引入的人工核验）：

1. **0 人工全自动（硬需求）**：整条流程——运行期 + 全新规范上线——都不靠人工审核（用户 / 后台都不要）。**废除「人工核验队列 + 用户逐项确认」**。
   - 新规范"读得对不对"改由**算力自检**兜底：最强模型 + 多次投票 + **回译交叉校验**（模型把抽出的 YAML 复述成人话，与规范原文逐条比对）——专堵三道闸查不到的「规范本身被读错」，**用算力换人工**。
   - 不确定项**透明摊进报告**，用户想看才看、不卡流程。
   - **唯一硬停 = 内容守恒红灯**（拒交残稿，非人工审批，正常永不触发）。
   - 落点：PRD（Solution、US#4/#24、新增「0 人工」决策、目标规范来源、结构闸、阶段路线）；proposal（§2/§3/§4 全部「人工校验」→「算力自检」）；issue **#22 重写**（核验队列→算力自检 + 只读审阅报告）、#19 / #6（异常→标报告不卡人）、#15（交付自检）。
2. **界面 / 报告文案全大白话**：只说「对你意味着什么」，不用内部术语（阻断 / 指纹 / 报备 / 核验 / 合规核对…）。落点：PRD 界面决策 + issue #16 / #22。

> 「审阅一屏」从"人工闸"降级为**只读报告**（用户可看、不被要求）。前后端原型（仓库外、另线 throwaway）本轮按用户要求丢开，不入库。

## 2026-06-17 · 开建网页全栈版（P0 脚手架）

用户拍板：把 docs 锁定的设计做成**真能跑的网页全栈应用**（7 屏全接真 + 运行期/建设期两轨），建在本仓库、推 main。详见 `PLAN.md`。本轮 = P0 + P1（用户已确认开工）。

P0（本提交）：
- 新增目录 `engine/`(config/llm) `app/`(FastAPI main) `web/`(静态壳) `templates/` `fixtures/`。
- `requirements.txt` + `.env.example`（真 key 在 `.env`，gitignore）。
- `农大.json` → `templates/neau-bachelor-thesis-2025.yaml`（手工映射 schema：页面/字号表/页眉双线/5级标题/三线表/GB7714引用…）。
- DeepSeek key **已验真连通**（`deepseek-chat`→deepseek-v4-flash，回 pong）。FastAPI `/health` + 静态托管 TestClient 验过 200。
- **隐私**：仓库 PUBLIC，`fixtures/` 含真实学生论文（马晓倩）+ 真实论文，**不入库**（`.gitignore: fixtures/* !README.md`），仅留本地；`fixtures/README.md` 记录清单与角色。

## 2026-06-17 · P1 引擎：农大运行期主链跑通（已端到端验证）

新增 `engine/`：`ingest`(docx→保序区块流) → `classify`(LLM缝①·DeepSeek结构识别,按idx标签·永不返回文本) → `format_docx`(确定性重建,文本逐run拷贝→内容守恒by construction) → `gates/content_gate`(内容守恒闸,残差比对,正文变动→🔴硬阻断) → `report`(大白话报告) → `pipeline`(固定控制流编排)。oxml 补丁集中在 `docx_utils`。`scripts/run_local.py`+`inspect_docx.py` 本地 CLI。

**验证**（fixtures/论文（三稿）.docx → 农大模板）：结构识别正确（题目/中英摘要/关键词/目录/标题1-3/40条文献/7表题/6图题）；内容守恒 ✅「一字没动」；成品 docx 真实合规——边距38/48/24/24、docGrid 38×38、页眉=题目+粗细双线、页脚 PAGE 域、eastAsia 分绑（宋体/TNR/黑体）、关键词前缀加粗保留、7 个三线表（上下1.5磅·无竖线）。报告核对全 pass（字数21601、文献40、外文13）。

待 P2：封面精确字体（隶书一号等）、分节页码（封面不编/前置罗马/正文阿拉伯）、格式回炉闸/结构闸/视觉QA、警示态。

## 2026-06-17 · P1 Web：API + 4 屏前端接真（已浏览器验证）

- `app/main.py`(FastAPI+静态托管+/static no-cache) + `app/api.py`：`POST /api/jobs`(上传docx+模板)、`POST /api/jobs/demo`(内置样例)、`GET /api/jobs/{id}`(轮询·后台线程跑pipeline)、`/report`、`/preview`(成品文本预览)、`/download`(成品docx；blocked 时拒下)、`GET /api/templates`。
- `web/` 4 屏（移植 Lumina Precision 原型，Tailwind CDN+共享 `tailwind-config.js`/`theme.css`，原生 JS）：工作台(上传/选规范/试用样例)→分析中(进度环·真轮询)→实时排版(成品预览+规则核对+「内容一字未动」)→排版结果(改动清单/待补项/核对清单+下载)。
- **浏览器端到端验证**（preview, 端口8011）：试用样例→真 DeepSeek 识别→排版→下载 `已排版_论文（三稿）.docx`(77KB, 正确 docx MIME)；4 屏渲染与原型一致；内容守恒 badge 正常。
- 运行：repo 根 `python -m uvicorn app.main:app --reload`（DeepSeek key 读 `.env`）。
- 注：fixtures 与 `app/_jobs/`（含上传/成品，带论文内容）均 gitignore，不入公开库。

## 2026-06-17 · 补：格式②校名确认

用户确认格式②（15毕业设计模板 + 马晓倩论文）= **新疆工程学院**。更新 `PLAN.md`(§2/§6) + `fixtures/README.md`。P3 建设期编译器将以此为第二格式。

## 2026-06-17 · P2 封面 + 分节页码 + 真渲染预览（已渲染验证）

用户反馈"封面/排版/分页全错、论文显示一页"。查实：真实导出 docx = 37 页（非一页），"一页"是 P1 那个假文本预览。本轮修三处：

1. **分节重构** `format_docx`：切 封面 / 前置(摘要·目录) / 正文 三节。`docx_utils` 加 `set_page_number_format`(pgNumType) / `setup_title_header` / `setup_pagenum_footer` / `blank_header_footer`。验证(check_sections)：节0封面=无页眉无码；节1=lowerRoman start1；节2=decimal start1（正文重起）。
2. **封面精确版式**：文种隶书一号·题目黑体二号·信息栏黑体小三·日期黑体小二，独立成一页，**封面不带页眉/页码**；丢掉源里的空行自己控间距→封面回到 1 页；空字段不编造。
3. **真渲染预览**：`engine/render.py`（PowerShell+Word COM 导 PDF → pymupdf 转 PNG，缓存 `<job>/_pages/`，不依赖 pywin32）；api 加 `/jobs/{id}/pages` + `/page/{n}`；`web/workspace.html` 左栏改成真实页面图（37 张）滚动预览。

附带补提交 P1 验证期的小改：`/api/jobs/demo`(试用样例)、工作台"试用样例"按钮、`/static` no-cache 中间件、静态资源 `?v=` 防缓存。删 `scripts/render_check.py`(坏的 pywin32 诊断脚本)；加 `scripts/check_sections.py`。requirements 加 `pymupdf`。

**渲染验证**（论文三稿→农大）：封面 1 页且字体/无页眉无码全对；摘要页带双线页眉；37 页；内容守恒仍 ✅。待 P3：建设期"上传新规范"编译器（新疆工程学院第二格式）+ 结构闸/视觉QA/警示态。

## 2026-06-17 · P2.5 严格对齐农大 2.3-2.6 + 引擎数据驱动 + 换最强模型

用户质疑：没按 2.3-2.6 来、封面缺校名图、信息栏该首行缩进5字符不是居中、为何硬编码农大而不交给 DeepSeek。**确实没全 follow,本轮全部改对**。

- **模型**：`deepseek-chat`(flash)→ **`deepseek-v4-pro`**(最强,查官方文档确认)。`engine/llm.py` 支持思考模式(`reasoning_effort` + `extra_body.thinking`,不传 temperature)+ 稳健 JSON 解析。结构识别用 v4-pro 非思考(快);复审/抽规范用思考+high。`.env`/`.env.example` 同步。
- **引擎改数据驱动(核心)**：删掉 `_cover_spec` 里硬编码的农大 if/正则。新增 `cover:` schema 进 YAML(logo/slots/blanks),`_emit_cover` 全从模板读;`classify` 细分封面标签(cover_doctype/field/date);新增 `_add_toc_item` 从 `table_of_contents` 数据出三级目录。**换学校=只换 YAML,引擎不动**。
- **校名图**：`scripts/extract_logo.py` 从农大PDF提取校名标准字(486×121,~4:1)→ `templates/assets/neau-logo.png`(gitignore,不republish),封面行1插入 120×30mm。
- **逐条对齐 2.3-2.6(渲染核对)**：2.3 封面=校名图+隶书一号+黑体二号+信息栏黑体小三首行缩进5字符+日期黑体小二,**一页**,无页眉无码;2.4 关键词顶格加粗;2.5 英文摘要**另起一页**(题目+Abstract同页);2.6 目录**另起页+三级缩进+页码右对齐+点引线**+一级加粗+罗马/阿拉伯。全局 Normal 段前段后0/单倍行距。内容守恒仍 ✅。
- 待办：**LLM 格式复审**(拿规范逐条审"套出来对不对"→报告/回炉,用户要的第二件);新疆工程学院第二格式(P3 编译器)。

## 2026-06-17 · LLM 格式复审 + 模型并发/运行指示

- **LLM 格式复审(用户要的第二件)**：`engine/format_review.py`——DeepSeek v4-pro 思考模式拿【权威规范 农大.json】逐条审【引擎实际套用的 YAML】,列"规范要求、引擎缺/错"的偏差(item/spec/engine/severity)。doc 无关→按模板缓存。pipeline 加 review 步,报告含 `format_review`,`web/result.html` 新增"格式复审"区展示。**实测发现 8 处真偏差**(公式排版缺失[高]/英文题目行未落数据[高]/目录编号空格/封面空白行减少 等)——审计员真能挑出我漏的。
- **模型**：结构识别曾试 flash 提速,但用户定"宁慢勿错用最强"→`DEEPSEEK_CLASSIFY_MODEL` 默认回 `deepseek-v4-pro`(想快可设 flash)。`classify` 批次改 `ThreadPoolExecutor` 并发(单批慢,并发压总耗时)。
- **运行指示(用户要求)**：`analyzing.html` 加"运行中 · Ns"计时 + ping 点 + review 阶段文案,长步骤也明确没挂。
- 已知小瑕：报告"页面规范化"打印了 dict 原文(待美化)。

## 2026-06-17 · P3a 规范编译器核心（样本→YAML，新疆工程学院验证）

用户拍板建编译器(P3)。`engine/compiler.py`：规范文档 → 声明式 YAML 模板。
- 两种输入：规范条文(pdf/docx 文字)→LLM 读规则；样本/模板 docx→`python-docx` 读「实际生效格式」(边距/样式/字体/字号/缩进 facts)→LLM 归并。样本模式更可靠(数值来自文件)。
- LLM 缝②：DeepSeek v4-pro 思考模式，喂 农大 YAML 当 schema 样例 + facts + 文本 → 出 draft YAML。
- **验证(新疆工程学院，用 马晓倩 样本反推)**：产出 `templates/xjit-design-2023.yaml`，自动抓到真实差异——边距 25.4/31.7(非农大38/48/24/24)、正文小四(非五号)、封面有**学号行**、有**声明页**(declaration)。引擎不动，只多一份 YAML。
- `scripts/compile_spec.py` 本地 CLI。待办：算力自检(回译校验)、"上传新规范"屏接真、端到端排文章验证。

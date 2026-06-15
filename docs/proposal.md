# 智能文档排版工具 · 方案文档

> 一句话定位：把任意一份「内容已写好」的 pdf/doc/docx，自动套上某个学校 / 期刊 / 机构要求的格式标准，输出合规成品。
> 核心不是「一个排版工具」，而是 **「规范 → 模板」的编译器 + 一个越攒越厚、可持续新增格式的模板库**。

---

## 1. 设计理念（先把方向想对）

这不是「靠手工多攒几个模板」的体力活——那是纯体力，攒得再多也只是线性堆叠。真正的工程支点有两个：

1. **让「做模板」接近零成本** —— 做一个规范编译器，把任意一份格式要求文档自动变成可执行模板。价值不在模板数量，而在**上线速度**和**长尾覆盖**（小众院校、期刊投稿格式、公司报告、标书……一个个手工做谁都嫌烦，编译器批量产）。
2. **一套引擎，通吃所有规范** —— 结构识别 + 排版引擎全程只写一套；每来一份新规范，变的只是模板库里多一份 YAML（**数据，不是代码**）。

> 工具的价值 = 模板库的广度 + 时效 + 编译器的上线速度 + 「输出即合规」的可靠性。LLM 不是关键（API 谁都能调），**编译器和模板库才是**。

---

## 2. 总体架构：拆成「建设期 / 运行期」两条轨

这是和「个人脚本」最本质的区别——把**造模板**和**用模板跑文档**彻底分开，中间用一个**声明式模板库**连接。

```
建设期（离线，决定可扩展性）
  规范文档(PDF/Word) → 规范编译器(LLM抽规则) → 声明式模板(YAML) → 人工校验一次 → 入库
                                                                         │
                                                          ┌──────────────▼──────────────┐
                                                          │   模板库（核心资产 / 数据层）   │
                                                          │  可声明 · 可维护 · 可扩展 · 自增长 │
                                                          └──────────────┬──────────────┘
                                                                         │ 读取
运行期（每次排版任务）                                                      ▼
  用户文档(doc/docx/pdf) → 结构识别(LLM分类) → 确定性排版(python-docx套模板) → 校验+合规报告 → 成品docx
```

**关键认知：结构识别 + 排版引擎全程只写一套，对所有规范通用；每来一份新规范，变的只是模板库里多一个 YAML 文件。** 这就是能规模化的根本——不是每份规范手工调，而是编译器批量产。

### 内部实现形态（已定）
- 全链路里 **LLM 只在两处登场**：运行期的「结构识别」（把每个段落判成标题/正文/图题/三线表/参考文献条目…），建设期的「规范抽取」。其余全是确定性代码。
- **不是 agent，是 workflow**：控制流固定可知，LLM 当组件不当司机。线上一条确定性流水线 + 一个有上限的「校验→不过回炉」循环；建设期一个会用工具的单 agent + 人工闸。**不上多 agent 团队**——它会把成本、延迟、不确定性全推向你最不想要的方向，直接破坏「确定性 + 低成本 + 输出可控合规」。

---

## 3. 多规范适配机制（核心）

> 目标：新增一份规范 = 上传它的格式要求 + 人工对一次样张，**不写代码**。

### 3.1 三个解耦层

| 层 | 通用还是专属 | 由谁产出 |
|---|---|---|
| 结构识别（认识"这是几级标题/图题/文献"）| **全规范通用**，只写一套 | LLM + 工程 |
| 排版引擎（把结构刷成 Word）| **全规范通用**，只写一套 | 工程 |
| 模板（"本校一级标题=黑体小二号段前0.5行…"）| **每份规范一份**，纯数据 | 规范编译器 + 人工校验 |

引擎读「结构 JSON」+「模板 YAML」两个输入，查表刷格式。**换规范 = 换那份 YAML，引擎一行不动。**

### 3.2 规范编译器（把覆盖面做宽的关键）

输入一份规范（PDF / Word / 网页截图），LLM 抽取出结构化规则，产出：
1. 一份 **draft 模板 YAML**（见第 4 节 schema）；
2. 一份 **预制 Word 母版 `reference.docx`**（页面设置、文档网格、页眉双线、各级命名样式都配好——这些在 Word 里点几下就成，犯不着用代码硬怼 XML）。

然后**人工对一份样张校验一次**，改掉抽错的字段 → 入库。之后用这份规范的所有文档都自动套用，无需再人工。

> 这一步是「先窄后宽」的窄：阶段 0 一份规范手工做模板都行；阶段 1 把编译器做出来，才能高效覆盖长尾。

---

## 4. 模板库设计（可持续存新格式）

> 目标：这个工具后面能**不断往里加新格式**，且新增格式是「数据」不是「代码」。

### 4.1 模板 = 一份 YAML（格式就是数据）

下面是用**东北农大 2025 规范**填出来的真实样例（**仅作 schema 示例**，任何学校 / 期刊 / 机构都按这套字段填即可）：

```yaml
template:
  id: neau-bachelor-thesis-2025      # 学校-学历-类型-年份，全局唯一
  name: 东北农业大学 本科毕业论文（设计）
  institution: 东北农业大学
  degree_level: bachelor             # bachelor | master | doctor
  doc_type: thesis                   # thesis | design
  spec_version: "2025.03"
  source: 东北农业大学教务处《本科毕业论文（设计）撰写规范》
  updated_at: 2025-03-01
  min_word_count: 8000               # 毕业论文≥8000；毕业设计≥5000

page:
  size: A4                           # 210 × 297 mm
  margins_mm: { top: 38, bottom: 48, left: 24, right: 24 }
  grid: { type: lines_and_chars, lines_per_page: 38, chars_per_line: 38 }

# 中文 eastAsia + 西文 latin 分开绑定——这是中文 Word 排版的核心坑，模板里钉死
fonts:
  default_cn: 宋体
  default_latin: Times New Roman     # 数字与字母统一 TNR
  heading_cn: 黑体

header:
  margin_mm: 28
  font: { cn: 宋体, size: 小五, align: center }
  content: thesis_title              # 页眉文字 = 论文题目
  border_below: { style: double, weight_pt: 3, thick_on: top }   # 粗细双线，粗线在上

footer:
  margin_mm: 38
  font: { cn: 宋体, size: 小五, align: center }
  page_number:
    format: "-n-"
    cover_titlepage: none            # 封面、扉页不编页码
    frontmatter: roman               # 摘要、目录用罗马数字
    body: arabic                     # 正文起阿拉伯数字，分节重启

styles:
  heading_1:
    font: { cn: 黑体, latin: Times New Roman, size: 小二 }
    bold: true
    indent_chars: 0
    spacing: { before_lines: 0.5, after_lines: 0.5, line: single }
    page_break_before: true          # 每章另起一页
  heading_2: { font: { cn: 黑体, size: 小三 }, indent_chars: 1, spacing: { line: single } }
  heading_3: { font: { cn: 黑体, size: 四号 }, indent_chars: 2 }
  heading_4: { font: { cn: 黑体, size: 小四 }, indent_chars: 2 }
  body:
    font: { cn: 宋体, latin: Times New Roman, size: 五号 }
    indent_chars: 2
    align: justify
    spacing: { line: single }

abstract_cn:
  title: { text: 摘要, font: { cn: 黑体, size: 小二 }, align: center }
  body: { indent_chars: 2, font: { cn: 宋体, size: 五号 } }
  keywords: { label: "关键词：", bold: true, sep: "；", count: [3, 5] }
abstract_en:
  new_page: true
  title: { text: Abstract, size: 小二, align: center }
  keywords: { label: "Key words：", bold: true, sep: ";" }
  font: Times New Roman

table:
  style: three_line                  # 开放式三线表，无竖线
  borders_pt: { top: 1.5, bottom: 1.5, inner: 0.5 }
  caption: { position: above, numbering: by_chapter, font: { cn: 宋体, size: 五号, latin: Times New Roman } }   # 表3.1
  body_font: { cn: 宋体, size: 小五, latin: Times New Roman, align: center }

figure:
  caption: { position: below, numbering: by_chapter, font: { cn: 宋体, size: 五号, latin: Times New Roman } }    # 图3-1

formula:
  numbering: by_chapter              # (1-1)
  number_align: right
  editor: omml

references:
  standard: GB/T 7714-2015
  style: numeric                     # 顺序编码制 [1]
  in_text: superscript               # 上标 [1]
  research_min: 20                   # 研究类≥20，其中外文≥4
  foreign_min: 4
  design_min: 10                     # 毕业设计≥10
```

> 好处：**编译器能生成它、非工程师也能维护它、它本身就是工具的「数据层」。**

### 4.2 模板库的目录与索引（怎么存）

```
templates/
├── _schema/
│   └── template.schema.json         # 用它校验每一份模板合法性（必填项、取值范围）
├── neau/                            # 东北农业大学
│   ├── bachelor-thesis-2025.yaml
│   ├── master-thesis-2025.yaml
│   └── _assets/
│       ├── reference.docx           # 预制 Word 母版（页面设置+命名样式+页眉双线）
│       └── logo.png                 # 校名/校徽图片
├── pku/ ...
└── _journals/                       # 期刊投稿格式也进同一个库
    └── ...
registry.json                        # 总索引：省份→学历→院校→模板ID→版本→状态
```

`registry.json` 让运行期一步查到「某规范」对应的 `YAML + reference.docx`，也支撑前端「省份→学历→院校」三级筛选。

### 4.3 新增 / 更新一个格式的流程（自增长）

```
上传规范 → 规范编译器产 draft(YAML + reference.docx) → 人工对样张校验 → 提交入库
         （写入 templates/<规范>/、更新 registry.json、打 version tag）→ 上线
```

- **可选 · 提交入口**：开放「提交我的规范」，用户上传规范 → 编译器产 → 人工过 → 入库。模板库**自增长**。
- **版本与时效**：每份模板带 `spec_version` + `updated_at`；`registry.json` 留版本历史。规范每年小改会「漂」，配一个**「规范变更监测 → 一键重编译」**的内部流程——勤维护就持续保持覆盖面与准确度。

---

## 5. 技术选型 / 工具链（每段缝什么）

| 阶段 | 选型 | 备选 / 说明 |
|---|---|---|
| ① 输入解析 | docx 用 **pandoc**；pdf 用 **MinerU**（中文学术，公式表格强）；老 `.doc` 先 **LibreOffice --headless** 转 | 统一入口可用 **markitdown**；pdf 备选 **marker** |
| ② 中间表示 | **自定义区块流（JSON 区块列表）**，每块带 `type` + 内容 | 轻量场景可用 Markdown，但复杂三线表/公式会丢 |
| ③ 结构识别（唯一 LLM） | 接 **DeepSeek / 通义千问 API** + **Instructor**（Pydantic 强约束输出）；长论文分章节喂 | 隐私敏感时改本地 **Ollama + Qwen** / **Outlines** 约束生成（接口已留口，改一行） |
| ④ 结构契约 | **Pydantic** 模型 = 区块类型；LLM 这头输出、排版那头读取，对同一份 schema | 你要亲手写的第一样东西 |
| ⑤ 确定性排版 | **python-docx** + 预制 **Word 母版**；公式用 **pandoc**（LaTeX→OMML）；可叠 **docxtpl** | 中文 eastAsia 字体、文档网格、页眉双线全甩给母版；三线表边框 + 页码域写 oxml 补丁 |
| ⑥ 校验 / 合规报告 | 重开 docx 逐项断言（页边距/字体/样式），不过传回③重排 | 借 **PaperFormatDetect** 思路；可选 LibreOffice→PDF→视觉模型瞄一眼 |
| 编排 | 纯 Python 状态机即可（线性 + 一个重试环） | 要显式重试图用 **LangGraph**；编译器那步可选 **PydanticAI** |
| 界面 | 自用 **Gradio** / CLI；服务化 **FastAPI**；可包成 **MCP** 从 Claude 驱动 | — |

**LLM 路线已定 = 接 API**（DeepSeek / 通义千问）。把这步封在 Instructor/Pydantic 接口后面，隐私敏感场景能改一行切回本地 Ollama + Qwen。

**成本控制**：全链路只有结构识别烧 token。便宜模型做分类，只对低置信度区块升级贵模型；同结构缓存；批量调用。

---

## 6. 可复用的开源工具（一路上挑出来能用的）

### 直接可借的现成项目

| 工具 | 链接 | 在本方案里的角色 |
|---|---|---|
| **gov-doc-formatter** | https://github.com/Drenches/gov-doc-formatter | **架构蓝本**。LLM 多步流水线给公文按 GB/T 9704-2012 排版（python-docx + 通义）。直接 fork 当骨架：把公文样式换成论文、把区块类型扩展开 |
| **PaperFormatDetect** | https://github.com/siyuanzhou/PaperFormatDetect | **校验/合规报告**这步的思路来源：提取上传论文与模板的同种属性逐项比对 |
| **bibtex2gbt7714** | https://github.com/FDscend/bibtex2gbt7714 | **参考文献**：BibTeX → GB/T 7714-2015，支持批量命令行 |
| **fdscend_word_addin** | https://github.com/FDscend/fdscend_word_addin | Word 加载项（含上面的文献转换），可视化操作参考 |
| **Office-Word-MCP-Server** | https://github.com/GongRzhe/Office-Word-MCP-Server | 最流行的 Word MCP（python-docx），让 AI 驱动改 docx；也可做对外集成面 |
| **MCP-Doc** | https://github.com/MeterLong/MCP-Doc | 另一个 Word MCP，编辑时保留原样式 |
| **java-poi** | https://github.com/land007/java-poi | 规则式「刷格式」参考（原为标书设计，思路可借） |
| **ChineseResearchLaTeX** | https://github.com/huangwb8/ChineseResearchLaTeX | LaTeX 路线 / PDF·DOCX 双输出参考（多数学校只收 Word，不建议为此入坑） |

### 通用基础库（工具链）

| 工具 | 链接 | 用途 |
|---|---|---|
| **python-docx** | https://github.com/python-openxml/python-docx | 渲染核心 |
| **python-docx-template (docxtpl)** | https://github.com/elapouya/python-docx-template | Word 母版 Jinja2 套用 |
| **pandoc** | https://github.com/jgm/pandoc | docx/odt ↔ Markdown/AST，公式 LaTeX→OMML |
| **MinerU** | https://github.com/opendatalab/MinerU | PDF（中文学术）→ Markdown，公式/表格/阅读顺序 |
| **markitdown** | https://github.com/microsoft/markitdown | 多格式 → Markdown（喂 LLM 的统一入口） |
| **marker** | https://github.com/VikParuchuri/marker | PDF → Markdown（备选） |
| **Instructor** | https://github.com/567-labs/instructor | LLM 结构化输出（基于 Pydantic），结构识别这步的关键 |
| **Outlines** | https://github.com/dottxt-ai/outlines | 约束生成（本地模型时用，强制 JSON 合规） |
| **LangGraph** | https://github.com/langchain-ai/langgraph | 需要显式校验/重试图时的编排（可选） |
| **PydanticAI** | https://github.com/pydantic/pydantic-ai | 类型安全 agent 框架（规范编译器那步可选） |

---

## 7. 分阶段路线图（技术里程碑，只排顺序与「要验证什么」）

- **阶段 0 · 打穿一条链。** 用一份规范端到端做透（模板手工做都行）。验证两件事：整条链跑通、「输出即合规」站得住。**一份规范做到零格式错误，比十份做到 80 分更有价值。**
- **阶段 1 · 造编译器（真正的解锁点）。** 「规范 PDF → 声明式模板」自动化。从此高效覆盖长尾：小众院校、各期刊投稿规范、开题/综述/实习报告等子模板。
- **阶段 2 · 加固与自增长。** 成本工程、隐私加固、规范变更监测 + 一键重编译、**「提交规范」的众包入口**（可选）。
- **（可选）其它规范场景复用。** 同一引擎可对准期刊、标书、公文等其它规范；把「格式化引擎」包成 **MCP / 库**，供别的程序（写作工具、文档工具）直接调用。

---

## 8. 必须踩对的几条线

- **死守「只做格式」的产品边界。** 排版是纯工具，无争议。但旁边的**降AIGC / 降重 / 代写**是另一回事——监管正在收紧，有合规 + 伦理风险。**核心产品只做格式**，这条边界一开始就划清楚。
- **数据隐私要当回事。** 处理的是**未发表论文 + 个人信息**，很敏感。**注意：已定走 API，内容会发给模型服务商**——选服务商时确认其「不留存 / 不拿内容训练」条款，做加密传输、用完即删；遇到极敏感内容，切本地模型那条口子（接口已留）。
- **模板时效是负担也是要点。** 规范每年小改，模板会漂。配「变更监测 + 一键重编译」流程，勤维护才能持续准确。
- **别贪多，先窄后宽。** 阶段 0 把一条链做到极致，再用编译器扩。守住「一套引擎、模板是数据」的架构，扩张才不会重写。

---

## 9. 下一步

从**阶段 0 的可跑骨架**开工：一套通用的结构识别 + 排版引擎（**接 DeepSeek / Qwen API**）、一份规范的 YAML 模板（上面东北农大样例可直接用作 schema 起点）、把「渲染→重解析→diff→合规报告」校验环做出来当 demo。

**已确定的关键决策：**
1. **LLM 路线：接 API**（DeepSeek / 通义千问），不走本地；调用封在 Instructor/Pydantic 接口后面，保留一行切本地的口子。
2. **无特定滩头规范**：不绑定具体学校，用通用 schema；东北农大 YAML 仅作填写示例。

或者先丢一份带几级标题、一张三线表、几条参考文献的论文样例，跑通整条链、连合规报告一起看效果。

---

*本文件可持续迭代：模板部分（第 4 节）就是产品的「数据层」，每新增一份规范，往 `templates/` 加一份 YAML 即可。*

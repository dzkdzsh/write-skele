# write-skele

中文学术写作与 LaTeX 工程的规则骨架，供写作类工程项目作为 `AGENT.md` 载入。

`AGENT.md` 本身只保留硬规则与索引（约 80 行），细则按需读取：

| 文件 | 内容 |
|---|---|
| `AGENT.md` | 任务验收、标题与文风、数据与图、文献、工程组织、交付、自查、索引 |

多工具兼容：`ln -s AGENT.md AGENTS.md` 与 `ln -s AGENT.md CLAUDE.md`，只维护一份源文件。
| `docs/style.md` | 三层问题框架、判断规则、断言分级、21 组改写对照、检查方法 |
| `docs/wording.md` | 分「硬禁／提示」两档的词表，`scripts/style_scan.py` 自动读取 |
| `docs/references.md` | Crossref 检索参数、刊名筛选、证据等级、开放获取、DOI 核对与占比统计脚本 |
| `docs/typesetting.md` | 编译顺序、六项检查命令、版式问题、模板改造 |
| `docs/project.md` | 单个项目的档案格式（示例为占位内容，换工程时整份重写） |
| `docs/peer-projects.md` | 同类开源项目调研、可借鉴机制与采纳／不采纳结论 |
| `scripts/` | `style_scan.py`（按词表扫正文）、`bib_audit.py`（DOI 核对）、`oa_fetch.py`／`oa_detail.py`（开放获取与摘要） |

## 用法

新工程开工前，把 `AGENT.md` 与 `docs/` 复制到工程根目录，然后：

1. 重写 `docs/project.md`，填入本次的题目、模板、数据脚本、文献规模。
2. 按 `AGENT.md` 第 2 节确认标题规范，按第 3 节确认文风。
3. 写完后按第 8 节编译三遍并跑检查。

`AGENT.md` 里的规则来自若干次真实的返工：禁用词表是逐条攒出来的，不是预设的；每一条后面都能指到一次具体的错误。

## 结构原则

`AGENT.md` 是索引，不是手册。加规则前先问一句：不写这条，Agent 每次都会做错吗？答否就删。文件超过 200 行后，模型对规则的遵循率开始下降，此时应拆分而不是压缩文字。

## 许可

MIT，见 `LICENSE`。

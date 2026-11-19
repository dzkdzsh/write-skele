# 同类开源项目调研与采纳结论

调研时间：2026-11-20。目的：找与 write-skele 定位相近的开源项目，提取可借鉴的机制，决定哪些进入本骨架。

## 一、调研对象

| 项目 | 定位 | 规模 | 与本骨架的关系 |
|---|---|---|---|
| [agents.md](https://agents.md/) / [规范](https://github.com/agentsmd/agents.md) | 给编码 agent 的统一指令文件，60k+ 项目采用，Linux 基金会托管 | 规范 + 示例 | 文件命名与分层机制可借鉴；领域不同（编码 vs 学术写作） |
| [GitHub 官方分析](https://github.blog/2025-02-26-how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) | 分析 2500+ agent 文件的有效性研究 | 研究报告 | 提出「命令前置、示例优于解释、三层边界、角色具体化」四条实证结论 |
| [acquat/claude-academic-workflows](https://github.com/acquat/claude-academic-workflows) | 学术论文写作工作流，9 份 hard rule | 学术，最贴近 | 硬规则组织、质量门、验证协议可直接借鉴 |
| [ammelsayed/academic_writing_skills](https://github.com/ammelsayed/academic_writing_skills) | 三个学术写作 skill（写论文/综述/审稿） | 学术，最贴近 | 段落纪律、反向提纲、claim-evidence 映射可借鉴 |
| [pedrohcgs/claude-code-my-workflow](https://github.com/pedrohcgs/claude-code-my-workflow) | 28 skills + 14 agents + 24 rules，经济学博士课实战 | 学术，宽泛 | 规则从真实错误中长出来的思路值得学 |

## 二、可借鉴机制与采纳结论

### 采纳（已落入本骨架）

1. **证据必须当场核验，不能用会话记忆。** 来源：acquat `no-fabrication.md`。原句：「Verify directly — Read or grep the source in the current turn. Not session memory.」写入 `AGENT.md` 第 5 节：数值、引用、文献结论必须当轮读源文件确认。这条正好补上本骨架的漏洞——此前只要求「由脚本产出」，没要求「写进正文那一刻再核一次」，而数值在会话中途可能已被改过。

2. **写入前的自检清单（pattern triggers）。** 来源同上。列出必须触发核验的句子类型：数值、文件路径、引文页码、枚举清单、否定性断言。本骨架把它压成一条：写数字、`\cite`、页码、`[file:line]` 时，当轮必须有工具结果支撑。已入 `docs/references.md`。

3. **失手后的固定动作。** 来源同上四步：承认 → 修正实例 → 记 `[LEARN]` 到记忆 → 排查同类错误。本骨架此前只「改了就算」，没有第四步。已入 `docs/references.md`，并写入 AGENT.md 第 8 节自查。

4. **反向提纲（reverse outline）。** 来源：ammelsayed `academic-paper`。做法：每节写完后按顺序记「节论点、每段主题句、段下证据」，再检查映射——每段主题句是否支撑节论点，每条证据是否支撑主题句，映射不上的段删掉或重写。这比笼统的「段首给判断」更可执行。写入 `docs/style.md`。

5. **claim-evidence 映射表。** 来源同上。每个判断标 `Claim: … | Evidence: … | Status: supported / needs evidence`，无证则弱化或删除。与本骨架已有「每个数值可复算」互补：那条管数值，这条管论断。写入 `docs/style.md`。

6. **三层边界（always / ask first / never）。** 来源：GitHub 官方分析 + agentkit 最佳实践。把「不要做X」的散列表改成三层显式边界，尤其区分「禁止」与「需先询问」。本骨架此前只有禁令，没有「需先问」这一类。写入 `AGENT.md` 第 6 节。

7. **完成前声明实际核验了什么、没核验什么。** 来源：ammelsayed「Then report what you actually verified, and name what you did not check.」此前本骨架只列检查项，不要求报告未检查项。写入 `AGENT.md` 第 8 节。

8. **别名兼容：AGENT.md / AGENTS.md / CLAUDE.md。** 来源：agents.md 规范与 agentkit。用符号链接让多工具都能读到，避免复制出不一致的副本。写入 `README.md` 与 `AGENT.md` 开头。

### 需讨论后决定（未落入）

- **量化质量门（80/90/95 分 + 扣分表）。** acquat 的做法很完整，但本骨架的服务对象是课程论文，不是投稿；引入分数会让轻量工程变重。若用于学位论文或投稿，可在单独的 quality-gates 文档中加一份。
- **`lit_review.md` 持久台账：每读一篇先入账再引用。** 对综述类写作价值极高，但课程论文引用量小（十余条），台账成本大于收益。文献证据等级表 `evidence.csv` 已承担部分功能。
- **plan-first：非平凡任务先进 plan mode 并把计划存档。** 适合多人协作与长周期项目，单人课程论文会让流程变繁。

### 不采纳（与本骨架冲突或不适用）

- **「文章超 50 页也不拆文件」「图用独立 .tex 导出 PDF，不内联 tikzpicture」**（ammelsayed）。这是该项目的个人偏好：它的场景是期刊论文（单文件够用、图作为外部资源便于投稿系统处理）。本骨架服务的是 50 页以上课程论文，分章是必需；图用 TikZ 内联是为了字体与正文一致，这条已在本项目验证过，不改。
- **「article 与 thesis 用同一套骨架」**（ammelsayed）。本骨架明确区分多份独立报告，不共用封面与目录。
- **Role/persona 声明式开头**（GitHub 官方分析）。对「一个 agent 干一类活」的编码场景有效；本骨架是写作约束文件，开头写「你是学术写作专家」不产生额外约束，占行且无收益。

## 三、一条元结论

GitHub 对 2500+ 文件的分析里，最有价值的一句不是具体规则，而是判断标准：**成功的 agent 文件给 agent 具体工作、确切命令、明确边界和好输出的例子；失败的文件只会说「你是一个有帮助的助手」。** 本骨架已经做到「具体约束 + 可执行脚本」，欠缺的是「边界分层」和「核验的动作化」，这次补齐的正是这两处。

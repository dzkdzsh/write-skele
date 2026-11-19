# 排版与校验

配合根目录 `AGENT.md` 使用。只在编译、查版式、改模板时读这一份。

## 一、编译顺序

顺序不可省，`bibtex` 必须在两次 `xelatex` 之间：

```bash
xelatex -interaction=nonstopmode main.tex
bibtex main
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex   # 刷新 .toc 与交叉引用
```

改过标题必须连跑两遍，否则目录里还是旧标题。

## 二、每次改动后的六项检查

```bash
grep -c "^!" main.log                        # 错误数，应为 0
grep -o "([0-9]* pages" main.log | tail -1   # 页数
grep -c "Reference.*undefined" main.log      # 未解析引用，应为 0
pdftotext main.pdf - | grep -c "??"          # 正文中的 ??，应为 0
pdfimages -list main.pdf                     # 应无位图（TikZ 工程）
grep -c Overfull main.log                    # 溢出，尽量为 0
```

另两条按需跑：

```bash
grep -rn -E "算账|一笔账|划算|吃掉|吞掉|买单|性价比|天花板|红利|雪球" --include="*.tex" .
python bib_audit.py                          # 书目 DOI 核对，见 docs/references.md
```

隐喻扫描只能防复发，扫不到没预料到的新词。发现一个新隐喻，就补进 `AGENT.md` 的禁用表与这条命令。

## 三、版式检查

1. 逐页渲染成图，看近空白页。章节末只剩数行会形成孤页，用补充一段内容、加一张表或微调文字长度消除，不要用 `\vspace` 硬凑。
2. 查图题与图形是否被拉到不同页、表格是否跨页断行。跨页表格用 `longtable` 并重复表头。
3. 浮动体集中出现时，页面会出现整页只有一张表。把表移到首次引用的段落之后，或改成非浮动结构（`\captionof`），比对空间更可靠。
4. 封面单独导出核对一次：中英文标题、姓名学号、学院专业、导师职称是否都替换。

## 四、模板改造

1. 不改模板原始目录，复制出独立工程再改。
2. 用文档类选项实现类型替换，不直接改封面代码：

```latex
\DeclareOption{<新选项名>}{
  \renewcommand{\dissertationtype}{<对应学位类型>}
  \renewcommand{\covertitletext}{<中文封面类型>}
  \renewcommand{\covertitleentext}{<英文封面类型>}
  \renewcommand{\evenpagemark}{<页眉文字>}
  \renewcommand{\DegLv}{<学位层次>}
}
```

调用：`\documentclass[<新选项名>, ...]{<文档类>}`。选项名与宏名都取自模板本身，先用 `grep` 确认原有定义再改。

3. 封面信息用 `\newcommand` 集中在主文件顶部（题目、姓名、学号、专业、学院、导师、职称），改一处全篇生效。
4. 字体目录若为相对路径加载，工程必须自带该目录，缺了会报找不到字体，错误信息不会指向目录本身。
5. 部分文献样式（bst）对 `@inproceedings` 强制要求 `address` 与 `organization`，缺字段会印出「缺」占位。换模板后先用一条会议文献试编译。

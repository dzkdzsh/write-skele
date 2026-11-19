# 文献核验

配合根目录 `AGENT.md` 使用。只在处理参考文献时读这一份。

## 一、检索

书目一律由元数据接口生成，不从记忆编写。条目错一个卷号，读者无法复核，作者也无法自证。

1. 入口 `https://api.crossref.org/works`。Crossref 的记录由出版方提交，含 DOI、刊名、卷、期、页、出版日期。
2. 参数：`query.bibliographic=<主题词>` 排序候选；`filter=from-pub-date:<起>,until-pub-date:<止>,type:journal-article` 限定时间窗与类型；`rows=25`；`select=DOI,title,author,container-title,volume,issue,page,published,published-print`。漏写 `select` 会因返回体过大被截断。
3. 出版年取 `published-print` 或 `published` 的 `date-parts`，不得由卷号推断。提取提示词要显式点名该字段，否则模型常只给姓氏与标题。
4. 一次查询覆盖一个子方向，例如「某类结构的性能比较」「某类方法的误差分析」「某类实测数据」。大而全的查询相关性会迅速下降。
5. 经典文献可凭常识确定，但定稿前必须反查 DOI 并解析核对。反查用 `query.bibliographic=<标题>`，取归一化标题完全一致的那条；教材与早期会议录常无 DOI，改用 ISBN 或出版方页面核对。字母相近的缩写（如 `ACSSC` 与 `ACSSCOM`）肉眼难辨，一处笔误就返回 404，只能靠脚本发现。

## 二、筛选

Crossref 只证明文献存在，不证明值得引用。

| 保留 | 剔除 |
|---|---|
| 本领域主流期刊与会议（IEEE Transactions 系列、Elsevier 与 Springer 的学科主刊） | 收费即发、审稿形同虚设的刊（以版面费为主要门槛的各类 IJxxx、IJSxxx） |
| 学科内持续产出的中等刊物 | 主题不符的邻近领域（纯数学、密码学等，除非确实构成方法来源） |
| 有 DOI 与完整卷期页的记录 | 同一作者在同一刊物的系列拆分投稿 |

近期文献要真正支撑正文，覆盖方法比较、实测数据、应用限制三个层面，不得堆在引言作装饰性引用。

## 三、引用句与原文的对应

1. 引用句中的判断，以标题与摘要能支撑为限。标题只说「提出某方法」，就不写「指标下降三成」。
2. 具体数值、对比结论、实验条件，只有读过原文才可引用。未读全文时，把这些文献放在综述性句子里，不与本文数据并列。
3. 写「文献表明……」就默认已读该文；没读就改成「该文提出……」。
4. 证据等级记入独立的 `refs/evidence.csv`，不写进 bib 的 `note`（bst 会把 note 印进参考文献）。三级：`fulltext` / `abstract` / `title`。只有 `fulltext` 可承载数值型引用；引用摘要里的数字时，句中必须写「该文报告」。

## 四、原文获取

按可复现性与合规性排序：

1. 开放获取：OpenAlex 的 `open_access.oa_url`、Unpaywall、Semantic Scholar 的 `openAccessPdf`，以及预印本、作者主页、机构仓库。
2. 摘要级：Crossref 的 `abstract`，OpenAlex 的 `abstract_inverted_index`（可重建摘要）。成本极低，能把等级从 `title` 提到 `abstract`。
3. 机构订阅：通过学校图书馆的正式入口访问，并在附录注明获取途径。
4. 脚本抓取有硬限制：ACM、Wiley、MDPI、Elsevier 对非浏览器请求返回 403 或挑战页，拿到的是 HTML。能稳定下载的只有机构仓库与部分作者自存档。「OA 覆盖率」与「脚本可下载率」是两个数，前者定证据等级，后者只决定自动化能走多远。
5. 不使用 Sci-Hub 一类侵权镜像：法律责任由使用者承担；镜像域名频繁失效，流程不可复现；此类来源无法写进方法说明，等于把核验做成不可审计的黑箱。

## 五、定稿核对

逐条解析 DOI，比对标题、刊名、年份：

```python
import io, json, re, urllib.request
bib = io.open("refs.bib", encoding="utf-8").read()
for key, blk in re.findall(r"@\w+\{([^,]+),(.*?)\n\}", bib, re.S):
    m = re.search(r"doi\s*=\s*\{([^}]+)\}", blk)
    if not m:
        print("NO-DOI  ", key); continue
    url = "https://api.crossref.org/works/" + m.group(1)
    req = urllib.request.Request(url, headers={"User-Agent": "bib-audit/1.0"})
    try:
        msg = json.load(urllib.request.urlopen(req, timeout=20))["message"]
        print("OK      %-20s %s | %s" % (key, msg.get("title", ["?"])[0][:48],
                                         msg["published"]["date-parts"][0][0]))
    except Exception as exc:
        print("FAIL    %-20s %s" % (key, exc))
```

判定：`NO-DOI` 需人工确认；`FAIL` 说明 DOI 错误或已撤稿；`OK` 但标题不一致说明转录有误。

## 六、占比统计

统计正文实际引用的条目（读 `.bbl`），不计 `.bib` 里未引用的：

```python
import io, re
bib = io.open("refs.bib", encoding="utf-8").read()
years = {}
for b in re.split(r"\n(?=@)", bib):
    k = re.match(r"@\w+\{([^,]+),", b); y = re.search(r"year\s*=\s*\{?(\d{4})", b)
    if k and y: years[k.group(1).strip()] = int(y.group(1))
used = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}",
                  io.open("main.bbl", encoding="utf-8").read())
n = sum(1 for k in used if years.get(k, 0) >= 2022)
print("%d/%d = %.1f%%" % (n, len(used), 100.0 * n / max(len(used), 1)))
```

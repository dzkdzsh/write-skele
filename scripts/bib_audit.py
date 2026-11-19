"""书目 DOI 核对：逐条解析 refs.bib 中的 DOI，比对标题与出版年。

用法：
    python bib_audit.py [refs.bib] [--json out.json]

输出每行的状态：
    OK       DOI 可解析，列出 Crossref 记录的标题与出版年
    NO-DOI   条目缺少 doi 字段，无法机读核验
    FAIL     DOI 错误、条目已撤稿或网络不可达（附原因）

比对规则：标题去掉所有非字母数字字符、转小写后取前 40 字符比较，避免
连字符（‐ 与 -）和大小写造成的假告警。年份取 published-print，缺省时取
published，与书目中「按刊期年填写」的惯例一致。
"""

import io
import json
import re
import sys
import time
import unicodedata
import urllib.request

API = "https://api.crossref.org/works/"
CONTACT = "bib-audit/1.0 (mailto:audit@example.org)"


def norm(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if c.isalnum())
    return text.lower()


def parse_bib(path):
    text = io.open(path, encoding="utf-8").read()
    entries = []
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, re.S):
        kind, key, body = m.group(1), m.group(2).strip(), m.group(3)
        title = re.search(r"title\s*=\s*\{(.+?)\},", body, re.S)
        year = re.search(r"year\s*=\s*\{?(\d{4})", body)
        doi = re.search(r"doi\s*=\s*\{([^}]+)\}", body)
        entries.append({
            "kind": kind,
            "key": key,
            "title": re.sub(r"[{}]", "", title.group(1)).strip() if title else "",
            "year": int(year.group(1)) if year else None,
            "doi": doi.group(1).strip() if doi else None,
        })
    return entries


def fetch(doi, tries=3):
    url = API + doi + "?mailto=audit@example.org"
    last = None
    for n in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": CONTACT})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)["message"]
        except Exception as exc:                      # 429 与超时都重试
            last = exc
            time.sleep(2.0 * (n + 1))
    raise last


def cr_year(msg):
    for field in ("published-print", "published", "issued"):
        parts = msg.get(field, {}).get("date-parts")
        if parts and parts[0] and parts[0][0]:
            return parts[0][0]
    return None


def main():
    path, out = "refs.bib", None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--json":
            out = args[i + 1]
        elif not a.startswith("--"):
            path = a

    rows = []
    for e in parse_bib(path):
        if not e["doi"]:
            print("NO-DOI   %-22s %s" % (e["key"], e["title"][:56]))
            rows.append(dict(e, status="NO-DOI"))
            continue
        try:
            msg = fetch(e["doi"])
            title = (msg.get("title") or ["?"])[0]
            year = cr_year(msg)
            same = norm(title)[:40] == norm(e["title"])[:40]
            flag = ""
            if not same:
                flag = "   <- 标题不一致"
            elif e["year"] and year and abs(year - e["year"]) > 0:
                flag = "   <- 年份差 %d" % (e["year"] - year)
            print("OK       %-22s %4s | %s%s" % (e["key"], year or "?", title[:50], flag))
            rows.append(dict(e, status="OK", cr_title=title, cr_year=year,
                             title_match=same))
        except Exception as exc:
            print("FAIL     %-22s %s" % (e["key"], exc))
            rows.append(dict(e, status="FAIL", error=str(exc)))
        time.sleep(0.4)

    ok = sum(1 for r in rows if r["status"] == "OK")
    bad = sum(1 for r in rows if r.get("title_match") is False)
    print("\n合计 %d 条：可解析 %d，无 DOI %d，失败 %d，标题不一致 %d" % (
        len(rows), ok,
        sum(1 for r in rows if r["status"] == "NO-DOI"),
        sum(1 for r in rows if r["status"] == "FAIL"), bad))

    if out:
        io.open(out, "w", encoding="utf-8").write(
            json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

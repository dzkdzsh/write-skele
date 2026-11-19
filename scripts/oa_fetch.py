"""按 DOI 查询开放获取版本（OpenAlex），并下载可合法获取的 PDF。

用法：
    python oa_fetch.py refs.bib --out refs
输出：
    终端一张覆盖率表；--out 指定目录时，把有 pdf_url 的文献下载到该目录
"""

import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "oa-fetch/1.0 (mailto:audit@example.org)"}


def cited_keys(bib_path):
    """只取正文实际引用的条目：读出 main.bbl 里的 bibitem 键。"""
    d = os.path.dirname(bib_path)
    bbl = os.path.join(d, "main.bbl")
    if not os.path.exists(bbl):
        return None
    txt = io.open(bbl, encoding="utf-8").read()
    return set(re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", txt))


def parse_bib(path):
    text = io.open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, re.S):
        key, body = m.group(2).strip(), m.group(3)
        doi = re.search(r"doi\s*=\s*\{([^}]+)\}", body)
        title = re.search(r"title\s*=\s*\{(.+?)\},", body, re.S)
        out[key] = {
            "doi": doi.group(1).strip() if doi else None,
            "title": re.sub(r"[{}]", "", title.group(1)).strip() if title else key,
        }
    return out


def openalex(doi):
    url = "https://api.openalex.org/works/doi:%s?mailto=audit@example.org" % doi.lower()
    for n in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 * (n + 1))
    return None


def download(url, path):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=45) as r:
            data = r.read()
        if len(data) < 20000 or not data[:4] == b"%PDF":
            return False
        io.open(path, "wb").write(data)
        return True
    except Exception:
        return False


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = None
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
        args = [a for a in args if a != out]
    if out:
        os.makedirs(out, exist_ok=True)

    seen, rows = set(), []
    for bib_path in args:
        cited = cited_keys(bib_path)
        for key, e in parse_bib(bib_path).items():
            if cited is not None and key not in cited:
                continue
            if not e["doi"] or e["doi"].lower() in seen:
                continue
            seen.add(e["doi"].lower())
            rec = openalex(e["doi"])
            if not rec:
                rows.append(dict(key=key, doi=e["doi"], status="API-FAIL"))
                print("%-20s %-12s %s" % (key, "API-FAIL", e["doi"]))
                continue
            oa = rec.get("open_access", {})
            loc = rec.get("best_oa_location") or {}
            pdf = loc.get("pdf_url")
            has_abs = bool(rec.get("abstract_inverted_index"))
            status = oa.get("oa_status") or "closed"
            rows.append(dict(key=key, doi=e["doi"], status=status, pdf=pdf,
                             abstract=has_abs, title=e["title"]))
            print("%-20s %-12s %-5s %s" % (key, status, "ABS" if has_abs else "   ",
                                           (pdf or "")[:72]))
            if out and pdf:
                safe = re.sub(r"[^A-Za-z0-9._-]", "_", key) + ".pdf"
                ok = download(pdf, os.path.join(out, safe))
                print("%-20s %s" % ("", "downloaded " + safe if ok else "download failed"))
            time.sleep(0.3)

    n = len(rows)
    oa_n = sum(1 for r in rows if r.get("pdf"))
    abs_n = sum(1 for r in rows if r.get("abstract"))
    print("\n合计 %d 条：有开放 PDF %d，有摘要 %d" % (n, oa_n, abs_n))
    io.open("oa_report.json", "w", encoding="utf-8").write(
        json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

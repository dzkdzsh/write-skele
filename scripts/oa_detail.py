"""从 OpenAlex / Unpaywall 取开放全文链接，并重建摘要（用于核对引用是否成立）。

用法：
    python oa_detail.py refs.bib --pdf refs --abs abstracts.txt
输出：
    --pdf  有开放 PDF 的条目下载到该目录
    --abs  把每条的重建摘要写入该文件（无摘要的标注 NONE）
"""

import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "oa-detail/1.0 (mailto:audit@example.org)"}
MAIL = "audit@example.org"


def cited_keys(bib_path):
    bbl = os.path.join(os.path.dirname(bib_path), "main.bbl")
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
        out[key] = {"doi": doi.group(1).strip() if doi else None,
                    "title": re.sub(r"[{}]", "", title.group(1)).strip() if title else key}
    return out


def get(url, tries=3):
    for n in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 * (n + 1))
    return None


def rebuild(inv):
    """OpenAlex 的 abstract_inverted_index 还原成文本。"""
    if not inv:
        return None
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def download(url, path):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            data = r.read()
        if len(data) > 20000 and data[:4] == b"%PDF":
            io.open(path, "wb").write(data)
            return True
    except Exception:
        pass
    return False


def main():
    pdf_dir = abs_file = None
    if "--pdf" in sys.argv:
        pdf_dir = sys.argv[sys.argv.index("--pdf") + 1]
        os.makedirs(pdf_dir, exist_ok=True)
    if "--abs" in sys.argv:
        abs_file = sys.argv[sys.argv.index("--abs") + 1]
    skips = {v for k, v in zip(sys.argv, sys.argv[1:]) if False}
    args = [a for a in sys.argv[1:] if not a.startswith("--")
            and a not in (pdf_dir, abs_file)]

    seen, out_lines, stats = set(), [], {"pdf": 0, "abs": 0, "n": 0}
    for bib_path in args:
        cited = cited_keys(bib_path)
        for key, e in parse_bib(bib_path).items():
            if cited is not None and key not in cited:
                continue
            if not e["doi"] or e["doi"].lower() in seen:
                continue
            seen.add(e["doi"].lower())
            stats["n"] += 1
            rec = get("https://api.openalex.org/works/doi:%s?mailto=%s" % (e["doi"].lower(), MAIL))
            abstract, pdf = None, None
            if rec:
                abstract = rebuild(rec.get("abstract_inverted_index"))
                loc = rec.get("best_oa_location") or {}
                pdf = loc.get("pdf_url")
                if not pdf and (rec.get("open_access", {}).get("is_oa")):
                    for l in rec.get("locations") or []:
                        if l.get("pdf_url"):
                            pdf = l["pdf_url"]
                            break
            if not pdf:                      # Unpaywall 兜底
                up = get("https://api.unpaywall.org/v2/%s?email=%s" % (e["doi"], MAIL))
                if up:
                    best = up.get("best_oa_location") or {}
                    pdf = best.get("url_for_pdf")
            if pdf and pdf_dir:
                safe = re.sub(r"[^A-Za-z0-9._-]", "_", key) + ".pdf"
                if download(pdf, os.path.join(pdf_dir, safe)):
                    stats["pdf"] += 1
                    print("PDF      %-20s %s" % (key, safe))
                else:
                    print("PDF-FAIL %-20s %s" % (key, pdf[:70]))
            if abstract:
                stats["abs"] += 1
                out_lines.append("### %s | %s\n%s\n" % (key, e["doi"], abstract[:1200]))
            else:
                out_lines.append("### %s | %s\nNONE\n" % (key, e["doi"]))
            time.sleep(0.3)

    if abs_file:
        io.open(abs_file, "w", encoding="utf-8").write("\n".join(out_lines))
    print("\n合计 %d 条：下载 PDF %d，有摘要 %d" % (stats["n"], stats["pdf"], stats["abs"]))


if __name__ == "__main__":
    main()

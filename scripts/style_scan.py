"""按 docs/文风词表.md 扫描正文，分「硬禁」与「提示」两组输出。

词表是唯一来源：标题含「硬禁」的小节按错误处理（退出码 1），
含「提示」的小节只列出来供人判断，不影响退出码；「单字」小节跳过。

用法：
    python scripts/style_scan.py                 # 扫当前目录下所有 .tex
    python scripts/style_scan.py src --ext .md   # 指定目录与后缀
    python scripts/style_scan.py --list          # 只列出解析到的词
"""

import io
import os
import re
import sys

DEFAULT_MD = os.path.join("docs", "文风词表.md")


def load_terms(md_path):
    """返回 (硬禁词表, 提示词表)。按小节标题分类。"""
    hard, soft = [], []
    bucket = None
    for line in io.open(md_path, encoding="utf-8"):
        raw = line.rstrip("\n")
        if raw.startswith("## "):
            title = raw[3:]
            if "单字" in title:
                bucket = None
            elif "提示" in title:
                bucket = soft
            else:
                bucket = hard
            continue
        line = raw.strip()
        if bucket is None or not line.startswith("- ") or "：" not in line:
            continue
        body = re.sub(r"（[^）]*）", "", line.split("：", 1)[1])
        for t in re.split(r"[、,，]", body):
            t = t.strip()
            if len(t) >= 2:                      # 单字误报太多，交人工
                bucket.append(t)
    # 长的优先，避免短词抢先匹配
    return (sorted(set(hard), key=len, reverse=True),
            sorted(set(soft), key=len, reverse=True))


def walk(root, ext):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
        for name in filenames:
            if name.endswith(ext):
                yield os.path.join(dirpath, name)


def scan(root, ext, terms):
    pattern = re.compile("|".join(map(re.escape, terms))) if terms else None
    hits = []
    if not pattern:
        return hits
    for path in walk(root, ext):
        for n, line in enumerate(io.open(path, encoding="utf-8", errors="ignore"), 1):
            found = pattern.findall(line)
            if found:
                hits.append((path, n, sorted(set(found)), line.strip()[:80]))
    return hits


def main():
    args = sys.argv[1:]
    root, ext, md, only_list = ".", ".tex", DEFAULT_MD, False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--ext":
            ext = args[i + 1]; i += 2; continue
        if a == "--md":
            md = args[i + 1]; i += 2; continue
        if a == "--list":
            only_list = True; i += 1; continue
        root = a; i += 1

    if not os.path.exists(md):
        print("找不到词表：%s" % md)
        return 2
    hard, soft = load_terms(md)

    if only_list:
        print("硬禁 %d 词：%s" % (len(hard), "、".join(hard)))
        print("提示 %d 词：%s" % (len(soft), "、".join(soft)))
        return 0

    hard_hits = scan(root, ext, hard)
    print("== 硬禁（必须改）")
    for path, n, found, text in hard_hits:
        print("%s:%d  [%s]  %s" % (path, n, ",".join(found), text))
    if not hard_hits:
        print("无")

    soft_hits = scan(root, ext, soft)
    print("\n== 提示（人工判断：断言强度、模糊限定、句首连接词）")
    for path, n, found, text in soft_hits[:30]:
        print("%s:%d  [%s]  %s" % (path, n, ",".join(found), text))
    if not soft_hits:
        print("无")
    elif len(soft_hits) > 30:
        print("…… 其余 %d 处略" % (len(soft_hits) - 30))

    print("\n硬禁 %d 处，提示 %d 处；单字词未扫描，见词表第五节。"
          % (len(hard_hits), len(soft_hits)))
    return 1 if hard_hits else 0


if __name__ == "__main__":
    sys.exit(main())

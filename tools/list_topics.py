#!/usr/bin/env python3
"""data/*.json の既存題材を、カテゴリ別・年齢順に一覧表示する（content-writer の重複回避用）。

使い方:
  python3 tools/list_topics.py              # 全カテゴリ
  python3 tools/list_topics.py teen young   # カテゴリ（id の先頭語）で絞る
  python3 tools/list_topics.py --ids        # id だけを1行ずつ（grep 用）
"""
import glob, json, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = 24  # イベント本文の先頭何文字を出すか


def load():
    rows = []  # (category, kind, age0, age1, id, label, file)
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "*.json"))):
        f = os.path.basename(p)
        d = json.load(open(p, encoding="utf-8"))
        for t in d.get("tracks", []):
            g = t.get("gate", {}).get("age", [0, 0])
            rows.append(("track", "T", g[0], g[1], t["id"], t.get("name", ""), f))
        for x in d.get("decisions", []):
            a = x.get("age", [0, 0])
            rows.append((x["id"].split("_")[0], "D", a[0], a[1], x["id"], x.get("title", ""), f))
        for x in d.get("events", []):
            a = x.get("age", [0, 0])
            t = x.get("text", "")
            head = t[:HEAD] + ("…" if len(t) > HEAD else "")
            rows.append((x["id"].split("_")[0], "E", a[0], a[1], x["id"], f"[{x.get('tier', '?')}] {head}", f))
    return rows


def main(argv):
    ids_only = "--ids" in argv
    cats = {a for a in argv if not a.startswith("--")}
    rows = [r for r in load() if not cats or r[0] in cats]
    if ids_only:
        for r in sorted(rows, key=lambda r: r[4]):
            print(r[4])
        return
    by = defaultdict(list)
    for r in rows:
        by[r[0]].append(r)
    for cat in sorted(by):
        rs = sorted(by[cat], key=lambda r: ("TDE".index(r[1]), r[2], r[3], r[4]))
        nd = sum(r[1] == "D" for r in rs)
        ne = sum(r[1] == "E" for r in rs)
        print(f"## {cat}  (分岐 {nd} / イベント {ne})")
        for r in rs:
            print(f"{r[1]} {r[2]:>3}-{r[3]:<3} {r[4]:<28} {r[5]}  <{r[6]}>")
        print()


if __name__ == "__main__":
    main(sys.argv[1:])

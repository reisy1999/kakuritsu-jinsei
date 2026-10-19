#!/usr/bin/env python3
"""data/*.json を1つにまとめ、template.html の GEN に埋め込んで公開用HTMLを書き出す"""
import json, glob, re, sys
out = sys.argv[1] if len(sys.argv) > 1 else "dist/kakuritsu-jinsei.html"
G = {"decisions": [], "events": [], "tracks": []}
for p in sorted(glob.glob("data/*.json")):
    d = json.load(open(p, encoding="utf-8"))
    for k in G: G[k] += d.get(k, [])
t = open("template.html", encoding="utf-8").read()
blob = "const GEN=" + json.dumps(G, ensure_ascii=False, separators=(",", ":")) + ";"
t = re.sub(r"/\*GEN_START\*/.*?/\*GEN_END\*/", lambda m: "/*GEN_START*/" + blob + "/*GEN_END*/", t, flags=re.S)
import os; os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
open(out, "w", encoding="utf-8").write(t)
print(f"built {out}: decisions={len(G['decisions'])} events={len(G['events'])} tracks={len(G['tracks'])}")

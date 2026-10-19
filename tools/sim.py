#!/usr/bin/env python3
"""バランス確認用シミュレーション。data/*.json を template.html に埋め込み、ランダムに選ぶ人生を N 回回して集計する。

使い方:
  python3 tools/sim.py                 # 2000回
  python3 tools/sim.py -n 5000 --seed 1
  python3 tools/sim.py --unused        # 一度も出なかった生成分岐の id も表示
  python3 tools/sim.py --json          # 集計を JSON で出力（比較・記録用）
"""
import argparse, json, os, subprocess, sys, tempfile
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STUB = '''const el=()=>({innerHTML:"",textContent:"",hidden:false,classList:{toggle(){},add(){}},onclick:null,prepend(){},appendChild(){},querySelectorAll(){return[]},scrollIntoView(){}});
const els={};globalThis.document={getElementById:id=>els[id]||(els[id]=el()),createElement:()=>el()};
globalThis.matchMedia=()=>({matches:true});globalThis.window={scrollTo(){}};
'''
SEEDED = '''{let a=%d>>>0;Math.random=function(){a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296}}
'''


def build_js(tmp, seed):
    html = os.path.join(tmp, "built.html")
    subprocess.run([sys.executable, os.path.join(ROOT, "build.py"), html], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    t = open(html, encoding="utf-8").read()
    js = t[t.index("<script>") + 8:t.rindex("</script>")].rstrip()
    assert js.endswith("newLife();"), "template.html の末尾が newLife(); で終わっていない"
    js = js[:-len("newLife();")]
    harness = open(os.path.join(ROOT, "tools", "sim_harness.js"), encoding="utf-8").read()
    path = os.path.join(tmp, "sim.js")
    open(path, "w", encoding="utf-8").write((SEEDED % seed if seed is not None else "") + STUB + js + harness)
    return path


def pct(a, p):
    return a[min(len(a) - 1, int(len(a) * p))]


def summarize(r):
    L, N = r["lives"], r["N"]
    ages = sorted(x["age"] for x in L)
    money = sorted(x["money"] for x in L)
    rate = lambda f: sum(1 for x in L if f(x)) / N * 100
    tracks = Counter(x["track"] for x in L if x["track"])
    used = r["used"]
    unused = [i for i in r["decIds"] if i not in used]
    return {
        "N": N,
        "age": {"avg": sum(ages) / N, "p10": pct(ages, .1), "med": pct(ages, .5), "p90": pct(ages, .9)},
        "money": {"p10": pct(money, .1), "p25": pct(money, .25), "med": pct(money, .5), "p75": pct(money, .75),
                  "p90": pct(money, .9), "neg%": rate(lambda x: x["money"] < 0), "1億以上%": rate(lambda x: x["money"] >= 10000)},
        "rate%": {
            "虹ルート": rate(lambda x: x["rainbow"]),
            "自己破産": rate(lambda x: x["bankrupt"]),
            "ひきこもり(1年以上)": rate(lambda x: x["hikiAny"]),
            "ひきこもり(10年以上)": rate(lambda x: x["hiki"]),
            "不登校": rate(lambda x: x["futoko"]),
            "最終時点で既婚": rate(lambda x: x["married"]),
            "子あり": rate(lambda x: x["kids"] > 0),
        },
        "cond_end_avg": {k: sum(x["cd"].get(k, 0) for x in L) / N for k in ("iso", "tired", "poor", "apathy")},
        "forks_avg": sum(x["forks"] for x in L) / N,
        "gen_decisions_per_life": r["genUse"] / N,
        "tracks%": {k: v / N * 100 for k, v in tracks.most_common()},
        "gen_decisions": {"total": len(r["decIds"]), "unused": len(unused)},
        "_unused_ids": unused,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=2000)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--unused", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        js = build_js(tmp, a.seed)
        out = subprocess.run(["node", js], cwd=tmp, env={**os.environ, "SIM_N": str(a.n)},
                             capture_output=True, text=True)
    if out.returncode:
        sys.exit(out.stderr)
    s = summarize(json.loads(out.stdout))
    if a.json:
        if not a.unused: s.pop("_unused_ids")
        print(json.dumps(s, ensure_ascii=False, indent=1)); return
    ag, m = s["age"], s["money"]
    print(f"人生 {s['N']} 回" + (f"  (seed={a.seed})" if a.seed is not None else ""))
    print(f"寿命      平均 {ag['avg']:.1f}  p10 {ag['p10']}  中央 {ag['med']}  p90 {ag['p90']}")
    print(f"最終資産  p10 {m['p10']:,.0f}  p25 {m['p25']:,.0f}  中央 {m['med']:,.0f}  p75 {m['p75']:,.0f}  p90 {m['p90']:,.0f} 万円")
    print(f"          マイナス {m['neg%']:.1f}%  1億以上 {m['1億以上%']:.1f}%")
    for k, v in s["rate%"].items():
        print(f"{k:<16}{v:5.1f}%")
    print("最期の傾き(平均段) " + "  ".join(f"{k} {v:.2f}" for k, v in s["cond_end_avg"].items()))
    print(f"分岐/人生 {s['forks_avg']:.1f}（うち生成分岐 {s['gen_decisions_per_life']:.1f}）  "
          f"生成分岐 {s['gen_decisions']['total']} 件中 未出現 {s['gen_decisions']['unused']} 件")
    print("虹の内訳  " + "  ".join(f"{k} {v:.1f}%" for k, v in s["tracks%"].items()))
    if a.unused:
        print("未出現: " + " ".join(s["_unused_ids"]))


if __name__ == "__main__":
    main()

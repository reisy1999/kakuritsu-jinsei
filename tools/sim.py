#!/usr/bin/env python3
"""バランス確認用シミュレーション。data/*.json を template.html に埋め込み、N 回の人生を回して集計する。

使い方:
  python3 tools/sim.py                      # 2000回 × 2方針（random / smart）を並べて表示
  python3 tools/sim.py -n 5000 --seed 1
  python3 tools/sim.py --policy smart       # 方針を1つだけ
  python3 tools/sim.py --unused             # 一度も出なかった生成分岐を、年齢と条件つきで表示
  python3 tools/sim.py --template old.html  # 別の template.html で回す（before / after 比較用）
  python3 tools/sim.py --json               # 集計を JSON で出力（比較・記録用）

方針:
  random … 払える選択肢からランダムに選ぶ
  smart  … 資金不足（22歳以上で資産が生活費1年分未満）や傾き2段以上のときは損失の期待値が最小の選択肢、
           余裕があるときは期待値（能力値の合計 + お金/20）が最大の選択肢を選ぶ
"""
import argparse, glob, json, os, subprocess, sys, tempfile
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STUB = '''const el=()=>({innerHTML:"",textContent:"",hidden:false,classList:{toggle(){},add(){}},onclick:null,prepend(){},appendChild(){},querySelectorAll(){return[]},scrollIntoView(){}});
const els={};globalThis.document={getElementById:id=>els[id]||(els[id]=el()),createElement:()=>el()};
globalThis.matchMedia=()=>({matches:true});globalThis.window={scrollTo(){}};
'''
SEEDED = '''{let a=%d>>>0;Math.random=function(){a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296}}
'''


def build_js(tmp, seed, template):
    G = {"decisions": [], "events": [], "tracks": []}
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        for k in G:
            G[k] += d.get(k, [])
    t = open(template, encoding="utf-8").read()
    js = t[t.index("<script>") + 8:t.rindex("</script>")].rstrip()
    assert js.endswith("newLife();"), "template.html の末尾が newLife(); で終わっていない"
    js = js[:-len("newLife();")]
    blob = "const GEN=" + json.dumps(G, ensure_ascii=False, separators=(",", ":")) + ";"
    a, b = js.index("/*GEN_START*/"), js.index("/*GEN_END*/")
    js = js[:a] + blob + js[b:]
    harness = open(os.path.join(ROOT, "tools", "sim_harness.js"), encoding="utf-8").read()
    path = os.path.join(tmp, "sim.js")
    open(path, "w", encoding="utf-8").write((SEEDED % seed if seed is not None else "") + STUB + js + harness)
    return path, G


def run(n, seed, policy, template):
    with tempfile.TemporaryDirectory() as tmp:
        js, G = build_js(tmp, seed, template)
        out = subprocess.run(["node", js], cwd=tmp, env={**os.environ, "SIM_N": str(n), "SIM_POLICY": policy},
                             capture_output=True, text=True)
    if out.returncode:
        sys.exit(out.stderr)
    return json.loads(out.stdout), G


def pct(a, p):
    return a[min(len(a) - 1, int(len(a) * p))]


def job_summary(L):
    """熟練と年収の分布（虹ルートの仕事は除く）"""
    J = [x["job"] for x in L]
    q = lambda a, p: sorted(a)[min(len(a) - 1, int(len(a) * p))] if a else None
    first = [j["first"] for j in J if j["first"] is not None]
    s40 = [j["sk40"] for j in J if j["sk40"] is not None]
    s60 = [j["sk60"] for j in J if j["sk60"] is not None]
    a45 = sorted((j["at45"] for j in J if j["at45"]), key=lambda z: z["skill"])
    quart = [a45[i * len(a45) // 4:(i + 1) * len(a45) // 4] for i in range(4)]
    return {"first": (q(first, .5), max(first) if first else None),
            "s40": (q(s40, .1), q(s40, .5), q(s40, .9)), "s60": (q(s60, .1), q(s60, .5), q(s60, .9)),
            "ever90%": sum(1 for j in J if j["max"] >= 90) / len(J) * 100,
            "inc45_by_quartile": [q([z["inc"] for z in g], .5) for g in quart],
            "type45%": {k: v / max(1, len(a45)) * 100 for k, v in Counter(z["type"] for z in a45).most_common()}}


def track_summary(L):
    """虹ルートごとの人数・続いた年数・終わり方・ピーク年齢・5年後の値のばらつき"""
    by = {}
    for x in L:
        tr = x.get("tr")
        if tr: by.setdefault(tr["id"], []).append((tr, x["age"]))
    out = {}
    for k, v in by.items():
        yrs = sorted(((tr["endAge"] or age) - tr["since"]) for tr, age in v)
        peaks = sorted(tr["peakAge"] for tr, _ in v if tr["peakAge"])
        tv5 = sorted(tr["tv5"] for tr, _ in v if tr["tv5"] is not None)
        out[k] = {"n": len(v), "years_med": yrs[len(yrs) // 2],
                  "fail%": sum(1 for tr, _ in v if tr["end"] == "fail") / len(v) * 100,
                  "end%": sum(1 for tr, _ in v if tr["end"] == "end") / len(v) * 100,
                  "peak_age_med": peaks[len(peaks) // 2] if peaks else None,
                  "tv5_p10_p90": (round(tv5[len(tv5) // 10]), round(tv5[len(tv5) * 9 // 10])) if len(tv5) >= 5 else None}
    return out


def summarize(r):
    L, N = r["lives"], r["N"]
    ages = sorted(x["age"] for x in L)
    money = sorted(x["money"] for x in L)
    rate = lambda f: sum(1 for x in L if f(x)) / N * 100
    used = r["used"]
    return {
        "N": N, "policy": r["policy"],
        "age": {"avg": sum(ages) / N, "p10": pct(ages, .1), "med": pct(ages, .5), "p90": pct(ages, .9)},
        "money": {"p10": pct(money, .1), "med": pct(money, .5), "p90": pct(money, .9)},
        "rate%": {
            "資産マイナスで死ぬ": rate(lambda x: x["money"] < 0),
            "自己破産": rate(lambda x: x["bankrupt"]),
            "結婚経験": rate(lambda x: x["everMarried"]),
            "子どもあり": rate(lambda x: x["kids"] > 0),
            "離婚経験（結婚した人のうち）": sum(1 for x in L if x["divorced"]) / max(1, sum(1 for x in L if x["everMarried"])) * 100,
            "虹ルート": rate(lambda x: x["rainbow"]),
            "ひきこもり(1年以上)": rate(lambda x: x["hikiAny"]),
            "ひきこもり(10年以上)": rate(lambda x: x["hiki"]),
            "不登校": rate(lambda x: x["futoko"]),
        },
        "forks_avg": sum(x["forks"] for x in L) / N,
        "gen_decisions_per_life": r["genUse"] / N,
        "generic_to_track": r["generic"]["track"],
        "generic_to_pro_art_founder": r["generic"]["special"],
        "job": job_summary(L),
        "track_detail": track_summary(L),
        "tracks%": {k: v / N * 100 for k, v in Counter(x["track"] for x in L if x["track"]).most_common()},
        "gen_total": len(r["decIds"]),
        "unused_ids": [i for i in r["decIds"] if i not in used],
    }


ROWS = [
    ("寿命 平均", lambda s: f"{s['age']['avg']:.1f}"),
    ("最終資産 中央値(万円)", lambda s: f"{s['money']['med']:,.0f}"),
    ("最終資産 p10 / p90", lambda s: f"{s['money']['p10']:,.0f} / {s['money']['p90']:,.0f}"),
    *[(k, (lambda k: lambda s: f"{s['rate%'][k]:.1f}%")(k)) for k in
      ("資産マイナスで死ぬ", "自己破産", "結婚経験", "離婚経験（結婚した人のうち）", "子どもあり", "虹ルート", "ひきこもり(1年以上)", "ひきこもり(10年以上)", "不登校")],
    ("分岐/人生（うち生成）", lambda s: f"{s['forks_avg']:.1f}（{s['gen_decisions_per_life']:.1f}）"),
    ("生成分岐 未出現", lambda s: f"{len(s['unused_ids'])} / {s['gen_total']}"),
    ("最初の仕事の熟練 中央値 / 最大", lambda s: "%s / %s" % s["job"]["first"]),
    ("熟練 40歳 p10/中央/p90", lambda s: "%s / %s / %s" % s["job"]["s40"]),
    ("熟練 60歳 p10/中央/p90", lambda s: "%s / %s / %s" % s["job"]["s60"]),
    ("熟練90以上に達した", lambda s: f"{s['job']['ever90%']:.1f}%"),
    ("45歳の年収中央値（熟練の四分位 低→高）", lambda s: " / ".join(str(round(v)) if v is not None else "-" for v in s["job"]["inc45_by_quartile"])),
    ("虹ルートの人に汎用の働き方分岐", lambda s: f"{s['generic_to_track']}回"),
    ("（参考）プロ・表現者・経営者に汎用分岐", lambda s: f"{s['generic_to_pro_art_founder']}回"),
]


def table(cols):
    """cols: [(見出し, summary)]"""
    w0 = max(len(r[0]) for r in ROWS) + 2
    head = "| 指標 | " + " | ".join(h for h, _ in cols) + " |"
    print(head)
    print("|---|" + "---|" * len(cols))
    for name, f in ROWS:
        print(f"| {name} | " + " | ".join(f(s) for _, s in cols) + " |")


def unused_report(ids, G):
    by = {x["id"]: x for x in G["decisions"]}
    for i in ids:
        x = by[i]
        print(f"  {i:<28} age {x['age'][0]}-{x['age'][1]}  requires {json.dumps(x.get('requires') or {}, ensure_ascii=False)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=2000)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--policy", choices=["random", "smart", "both"], default="both")
    ap.add_argument("--template", default=os.path.join(ROOT, "template.html"))
    ap.add_argument("--unused", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    pols = ["random", "smart"] if a.policy == "both" else [a.policy]
    res = []
    for p in pols:
        r, G = run(a.n, a.seed, p, a.template)
        res.append(summarize(r))
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1)); return
    print(f"人生 {a.n} 回" + (f"  seed={a.seed}" if a.seed is not None else "") + f"  template={os.path.relpath(a.template, ROOT)}\n")
    table([(s["policy"], s) for s in res])
    for s in res:
        print(f"\n[{s['policy']}] 45歳の職種  " + "  ".join(f"{k} {v:.0f}%" for k, v in s["job"]["type45%"].items()))
        print(f"[{s['policy']}] 虹ルート別  " + "  ".join(
            f"{k}: {v['n']}人 {v['years_med']}年 失敗{v['fail%']:.0f}% 区切り{v['end%']:.0f}%"
            + (f" ピーク{v['peak_age_med']}歳" if v['peak_age_med'] else "") + (f" 5年後{v['tv5_p10_p90']}" if v['tv5_p10_p90'] else "")
            for k, v in sorted(s["track_detail"].items(), key=lambda kv: -kv[1]["n"])))
        print(f"[{s['policy']}] 虹の内訳  " + "  ".join(f"{k} {v:.1f}%" for k, v in s["tracks%"].items()))
    if a.unused:
        both = set.intersection(*(set(s["unused_ids"]) for s in res))
        print(f"\nどの方針でも一度も出なかった生成分岐: {len(both)} 件")
        unused_report([i for i in res[0]["unused_ids"] if i in both], G)


if __name__ == "__main__":
    main()

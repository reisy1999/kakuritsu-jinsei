#!/usr/bin/env python3
"""確率人生 生成データのバリデータ。使い方: python3 validate.py data/xxx.json [...]"""
import json, sys, re

STATS = {"health", "happy", "know", "bond", "luck"}
FX_KEYS = STATS | {"money", "income_mul"}
STATUS = {"school", "futoko", "college", "work", "jobless", "hikikomori", "retired"}
CONDS = {"iso", "tired", "poor", "apathy"}
GOALS = {"tech", "sport", "art", "stable"}
KINDS = {"corp", "public", "irregular", "founder", "pro", "art"}
REQ_KEYS = {"status", "married", "kids_min", "money_min", "money_max", "stat_min", "stat_max", "cond_min", "cond_max",
            "parents_alive", "goal", "track", "flags_any", "flags_none", "year_min", "year_max"}
SET_KEYS = {"status", "job", "married", "kids_delta", "flags", "cond", "press", "track", "bankrupt"}
BANNED = ["自殺", "自傷", "リストカット", "死にたい", "風俗", "売春", "援助交際", "覚醒剤", "大麻", "万引き", "窃盗", "強盗", "逮捕", "前科", "拒食", "過食", "嘔吐"]

def main(paths):
    total_err = 0
    seen = {}
    for p in paths:
        errs = []
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print(f"[{p}] JSON parse error: {e}"); total_err += 1; continue

        def E(where, msg): errs.append(f"{where}: {msg}")

        def chk_fx(where, fx, kind):
            if not isinstance(fx, dict): E(where, "fx must be object"); return
            for k, v in fx.items():
                if k not in FX_KEYS: E(where, f"unknown fx key {k}")
                elif not isinstance(v, (int, float)): E(where, f"fx {k} not number")
            st = {k: v for k, v in fx.items() if k in STATS}
            if kind == "good" and any(v < 0 for v in st.values()) and sum(st.values()) <= 0: E(where, "good event has net negative stats")
            if kind == "good" and (any(v > 4 for v in st.values()) or sum(st.values()) > 5): E(where, "good event stats too large (+4 each, total +5)")
            if kind == "bad" and (any(v < -6 for v in st.values()) or sum(st.values()) < -8): E(where, "bad event stats too large (-6 each, total -8)")
            if kind == "bad" and sum(st.values()) > 0: E(where, "bad event net positive")
            if kind == "normal" and st and (all(v > 0 for v in st.values()) or all(v < 0 for v in st.values())) and len(st) > 1:
                E(where, "normal event should mix up and down")
            if kind in ("choice", "outcome") and any(abs(v) > 15 for v in st.values()): E(where, "stat change > 15")
            if "income_mul" in fx and not (0.5 <= fx["income_mul"] <= 2.0): E(where, "income_mul out of 0.5-2.0")

        def chk_req(where, r):
            if r is None: return
            if not isinstance(r, dict): E(where, "requires must be object"); return
            for k, v in r.items():
                if k not in REQ_KEYS: E(where, f"unknown requires key {k}")
            for s in r.get("status", []) or []:
                if s not in STATUS: E(where, f"unknown status {s}")
            for g in r.get("goal", []) or []:
                if g not in GOALS: E(where, f"unknown goal {g}")
            for ck in ("cond_min", "cond_max"):
                for k in (r.get(ck) or {}):
                    if k not in CONDS: E(where, f"unknown cond {k}")
            for ck in ("stat_min", "stat_max"):
                for k in (r.get(ck) or {}):
                    if k not in STATS: E(where, f"unknown stat {k}")
            for yk in ("year_min", "year_max"):
                if yk in r and not (isinstance(r[yk], int) and 1975 <= r[yk] <= 2110): E(where, f"{yk} must be a year 1975-2110")
            if isinstance(r.get("year_min"), int) and isinstance(r.get("year_max"), int) and r["year_min"] > r["year_max"]: E(where, "year_min > year_max")

        def chk_set(where, s):
            if s is None: return
            for k in s:
                if k not in SET_KEYS: E(where, f"unknown set key {k}")
            if "status" in s and s["status"] not in STATUS: E(where, f"unknown status {s['status']}")
            if "job" in s:
                j = s["job"]
                for k in ("name", "income", "grow", "kind"):
                    if k not in j: E(where, f"job missing {k}")
                if j.get("kind") not in KINDS: E(where, f"unknown job kind {j.get('kind')}")
            for ck in ("cond", "press"):
                for k in (s.get(ck) or {}):
                    if k not in CONDS: E(where, f"unknown {ck} {k}")

        def chk_text(where, t, mx):
            if not isinstance(t, str) or not t.strip(): E(where, "empty text"); return
            if len(t) > mx: E(where, f"text too long ({len(t)}>{mx})")
            for b in BANNED:
                if b in t: E(where, f"banned word {b}")

        def chk_id(where, i):
            if not isinstance(i, str) or not re.match(r"^[a-z0-9]+(_[a-z0-9]+)*_\d{2}$", i): E(where, f"bad id {i}")
            if i in seen: E(where, f"duplicate id {i} (also in {seen[i]})")
            seen[i] = p

        def chk_age(where, a):
            if not (isinstance(a, list) and len(a) == 2 and 0 <= a[0] <= a[1] <= 110): E(where, f"bad age {a}")
            return a if isinstance(a, list) and len(a) == 2 else [0, 110]

        def chk_decision(i, x):
            w = f"decision[{i}] {x.get('id')}"
            chk_id(w, x.get("id")); age = chk_age(w, x.get("age"))
            chk_req(w, x.get("requires")); chk_text(w + ".title", x.get("title"), 16); chk_text(w + ".text", x.get("text"), 70)
            ch = x.get("choices", [])
            if not (3 <= len(ch) <= 4): E(w, f"choices must be 3-4 (got {len(ch)})")
            labels = set()
            for j, c in enumerate(ch):
                cw = f"{w}.choice[{j}]"
                chk_text(cw + ".label", c.get("label"), 20)
                if c.get("label") in labels: E(cw, "duplicate label")
                labels.add(c.get("label"))
                cost = (c.get("cost") or {}).get("money", 0)
                if cost > 0: E(cw, "cost must be <= 0")
                if cost and age[1] < 18: E(cw, "children cannot pay cost")
                fx = c.get("fx", {}); chk_fx(cw, fx, "choice")
                if fx.get("money", 0) < 0: E(cw, "spending must go in cost, not fx")
                r = c.get("roll")
                if not r: E(cw, "missing roll"); continue
                chk_text(cw + ".roll.name", r.get("name"), 16)
                for s in r.get("stats", []):
                    if s not in STATS: E(cw, f"unknown roll stat {s}")
                if not r.get("stats"): E(cw, "roll.stats empty")
                if not isinstance(r.get("difficulty"), (int, float)): E(cw, "difficulty missing")
                for t in ("good", "mid", "bad"):
                    o = r.get(t)
                    if not o: E(cw, f"missing {t}"); continue
                    chk_text(f"{cw}.{t}.label", o.get("label"), 20); chk_text(f"{cw}.{t}.text", o.get("text"), 60)
                    chk_fx(f"{cw}.{t}", o.get("fx", {}), "outcome"); chk_set(f"{cw}.{t}", o.get("set"))
                    if age[1] < 18 and (o.get("fx", {}).get("money", 0) not in (0,) and age[0] < 15): E(f"{cw}.{t}", "children money change")
            return

        def chk_event(i, x):
            w = f"event[{i}] {x.get('id')}"
            chk_id(w, x.get("id")); age = chk_age(w, x.get("age")); chk_req(w, x.get("requires"))
            if x.get("tier") not in ("good", "normal", "bad"): E(w, f"bad tier {x.get('tier')}")
            chk_text(w, x.get("text"), 60); chk_fx(w, x.get("fx", {}), x.get("tier")); chk_set(w, x.get("set"))
            m = x.get("fx", {}).get("money", 0)
            if age[1] < 15 and m: E(w, "children money change")
            if x.get("spend") and m >= 0: E(w, "spend event must have negative money")

        for i, x in enumerate(d.get("decisions", [])): chk_decision(i, x)
        for i, x in enumerate(d.get("events", [])): chk_event(i, x)
        for i, t in enumerate(d.get("tracks", [])):
            w = f"track[{i}] {t.get('id')}"
            for k in ("id", "name", "gate", "chance"):
                if k not in t: E(w, f"missing {k}")
            g = t.get("gate", {})
            if "age" not in g: E(w, "gate.age missing")
            if not (g.get("stat_min")): E(w, "gate.stat_min required (虹は能力条件必須)")
            for yk in ("year_min", "year_max"):
                if yk in g and not (isinstance(g[yk], int) and 1975 <= g[yk] <= 2110): E(w, f"gate.{yk} must be a year 1975-2110")
            ch = t.get("chance", {})
            for k in ("name", "stats", "difficulty", "hit", "miss"):
                if k not in ch: E(w, f"chance missing {k}")
            if "hit" in ch: chk_set(w + ".hit", {k: v for k, v in ch["hit"].items() if k in ("job",)})
        tids = {t.get("id") for t in d.get("tracks", [])}
        for x in d.get("decisions", []) + d.get("events", []):
            tr = (x.get("requires") or {}).get("track")
            if tr and d.get("tracks") is not None and tr not in tids: E(x.get("id"), f"unknown track {tr}")

        nd, ne = len(d.get("decisions", [])), len(d.get("events", []))
        print(f"[{p}] decisions={nd} events={ne} tracks={len(d.get('tracks', []))} errors={len(errs)}")
        for e in errs[:80]: print("  -", e)
        if len(errs) > 80: print(f"  ... and {len(errs)-80} more")
        total_err += len(errs)
    sys.exit(1 if total_err else 0)

if __name__ == "__main__":
    main(sys.argv[1:])

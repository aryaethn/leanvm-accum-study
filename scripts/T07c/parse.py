#!/usr/bin/env python3
import re, glob, os, statistics as st, csv, sys
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "results", "T07c")  # bundle-relative (edited from absolute path)
ANSI = re.compile(r"\x1b\[[0-9;]*m")
EXPECT = {("base",4):766603,("base",5):953421,("base",6):1140247,("v6",4):668803,("v6",5):822968,("v6",6):976882}
def mib(s):
    m = re.search(r"used = ([\d.]+)M", s); return float(m.group(1)) if m else None
rows = []
for f in sorted(glob.glob(f"{R}/runs/*_p*.log")):
    name, p = re.match(r".*/(.+)_p(\d)\.log", f).groups()
    t = ANSI.sub("", open(f, errors="replace").read())
    if "### therm_end" not in t: continue
    d = dict(name=name, passno=int(p))
    sw0 = mib(re.search(r"### swap_start: (.*)", t).group(1)); sw1 = mib(re.search(r"### swap_end: (.*)", t).group(1))
    d["swap0"], d["dswap"] = sw0, round(sw1 - sw0, 2)
    th = re.findall(r"### therm_(?:start|end): (.*)", t)
    lim = [x for x in th if "Speed_Limit" in x or "Scheduler_Limit" in x]
    d["therm"] = "none" if not any(re.search(r"CPU_Speed_Limit\s*=\s*(\d+)", x) and int(re.search(r"CPU_Speed_Limit\s*=\s*(\d+)", x).group(1)) < 100 for x in th) else "LIMIT: " + "; ".join(lim)
    if "No thermal warning level has been recorded" not in th[0]: d["therm"] += " (warning recorded: " + th[0][:80] + ")"
    d["exit"] = re.search(r"### exit: (\d+)", t).group(1)
    m = re.search(r"cycles \(VM steps\)\s*:\s*([\d,]+)", t); d["cycles"] = int(m.group(1).replace(",", ""))
    m = re.search(r"proving time\s*:.*peak memory ([\d.]+) GiB", t); d["leanvm_peak_GiB"] = float(m.group(1))
    m = re.search(r"(\d+)\s+peak memory footprint", t); d["footprint_GiB"] = round(int(m.group(1)) / 2**30, 3)
    m = re.search(r"verifying\s*:\s*([\d.]+ ?\w+)", t); d["verify"] = ("ok (" + m.group(1) + ", exit " + d["exit"] + ")") if m and d["exit"] == "0" else "FAIL"
    m = re.search(r"proof size\s*:\s*([\d.]+) KiB", t); d["proof_KiB"] = float(m.group(1))
    # three proving times
    if name.startswith("leaf"):
        m = re.search(r"passes\s*:\s*([\d.]+) s\s+([\d.]+) s\s+([\d.]+) s", t); times = [float(x) for x in m.groups()]
        m = re.search(r"TOTAL_COMMITTED 2\^([\d.]+)", t); d["tc_log2"] = float(m.group(1))
        d["mu"] = "%d (=ceil log2 TC, derived)" % -(-int(__import__("math").ceil(d["tc_log2"])))
        d["tc"] = d["lanes"] = ""
    else:
        a = re.search(r"passes\s*:\s*([\d.]+) s", t); b = re.findall(r"^\s*([\d.]+) s(?!\w*s)", t, re.M)
        b = re.findall(r"^[ ]*([\d.]+) s(?=INFO|\s*$)", t, re.M)
        times = [float(a.group(1))] + [float(x) for x in b]
        node = re.findall(r"kind=node cycles=(\d+) mu=(\d+) n_lanes=(\d+) committed_len=(\d+) placed=(\d+)", t)
        leaf = re.findall(r"kind=leaf cycles=(\d+) mu=(\d+) n_lanes=(\d+) committed_len=(\d+) placed=(\d+)", t)
        d["node_cycle_set"] = sorted(set(int(x[0]) for x in node))
        n = node[-1]; d["mu"], d["lanes"], d["tc"] = int(n[1]), int(n[2]), int(n[4])
        d["node_distinct"] = sorted(set(x[1:] for x in node))
        d["leaf_mu_lanes"] = sorted(set((int(x[1]), int(x[2])) for x in leaf))
        d["leaf_cycles_range"] = (min(int(x[0]) for x in leaf), max(int(x[0]) for x in leaf)) if leaf else None
        d["leaf_tc"] = sorted(set(int(x[4]) for x in leaf))
    d["times"] = times
    d["median"] = round(st.median(times), 3)
    rows.append(d)
import json
json.dump(rows, open(f"{R}/parsed.json", "w"), indent=1, default=str)
with open(f"{R}/per_run.md", "w") as o:
    o.write("| name | pass | cycles | TC | lanes | mu | t1 | t2 | t3 | median s | leanVM peak GiB | footprint GiB | swap start MiB | swap delta MiB | thermal | verify |\n|" + "---|" * 16 + "\n")
    for d in sorted(rows, key=lambda x: (x["name"], x["passno"])):
        t = d["times"]
        flag = " **FLAG**" if abs(d["dswap"]) > 64 else ""
        o.write(f"| {d['name']} | {d['passno']} | {d['cycles']:,} | {d['tc']} | {d['lanes']} | {d['mu']} | {t[0]} | {t[1]} | {t[2]} | {d['median']} | {d['leanvm_peak_GiB']} | {d['footprint_GiB']} | {d['swap0']} | {d['dswap']}{flag} | {d['therm']} | {d['verify']} |\n")
with open(f"{R}/pooled.md", "w") as o:
    o.write("| config | n runs x repeats | pooled median s | min s | max s | median of pass-1 | median of pass-2 |\n|---|---|---|---|---|---|---|\n")
    for name in dict.fromkeys(d["name"] for d in sorted(rows, key=lambda x: x["name"])):
        rr = [d for d in rows if d["name"] == name]; allt = [x for d in rr for x in d["times"]]
        pm = lambda k: round(st.median([x for d in rr if d["passno"] == k for x in d["times"]]), 3) if any(d["passno"] == k for d in rr) else "-"
        o.write(f"| {name} | {len(allt)} | {round(st.median(allt),3)} | {min(allt)} | {max(allt)} | {pm(1)} | {pm(2)} |\n")
# checks
for d in rows:
    if "node_cycle_set" in d:
        v, n = re.match(r"(base|v6)_n(\d)", d["name"]).groups()
        if d["name"].count("_") == 1:
            ok = d["node_cycle_set"] == [EXPECT[(v, int(n))]] and d["cycles"] == EXPECT[(v, int(n))]
            print(d["name"], d["passno"], "cycles match T07b:", ok, d["node_cycle_set"], "node(mu,lanes,cl,placed) distinct:", d["node_distinct"])
        print("   leaf", d["leaf_mu_lanes"], d["leaf_cycles_range"], d["leaf_tc"])

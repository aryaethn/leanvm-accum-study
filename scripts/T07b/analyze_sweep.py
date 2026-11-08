#!/usr/bin/env python3
"""T07b: count table and capacity table from sweep/*.log."""
import csv
import math
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))  # repository root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_tables import parse, recompute, ORDER  # noqa: E402

D = f"{ROOT}/results/T07b/sweep"
VS = ["base", "b0u", "v6", "v6u"]
UNSOUND = {"v6", "v6u"}
NS = range(2, 9)
rows = []
data = {}
for v in VS:
    for n in NS:
        r, printed, pk, txt = parse(f"{D}/{v}_n{n}.log")
        assert r is not None, (v, n)
        verify = "verifying" in txt and "panicked" not in txt
        tc, mu, taus = recompute(r)
        assert tc == r["placed"], (v, n, tc, r["placed"])
        assert mu == r["mu"], (v, n)
        data[(v, n)] = dict(r=r, taus=taus, tc=tc, mu=mu, pk=pk, verify=verify, printed=printed)
        row = dict(variant=v + ("(UNSOUND)" if v in UNSOUND else ""), n=n, cycles=r["cycles"], mu=r["mu"], tc=tc, log_tc=round(math.log2(tc), 6), n_lanes=r["n_lanes"],
                   committed_len=r["committed_len"], h=r["log_mem"], mem_used=r["mem_used"], code_len=r["code_len"], proof_kib=pk, verify=verify)
        for t in ORDER:
            row[f"{t}_rows"] = r["tables"][t]["rows"]
            row[f"{t}_tau"] = taus[t]
        rows.append(row)
out = D + "/../count_table.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("wrote", os.path.relpath(os.path.normpath(out), ROOT))
print("verify ok:", all(x["verify"] for x in rows), "runs:", len(rows))
print()
print("| variant | n | cycles | XOR | MUL | SET | DEREF | JUMP | KECCAK | h | TC | mu | lanes | KiB | verify |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for x in rows:
    cells = " | ".join(f"{x[t+'_rows']:,}/2^{x[t+'_tau']}" for t in ORDER)
    print(f"| {x['variant']} | {x['n']} | {x['cycles']:,} | {cells} | {x['h']} | 2^{x['log_tc']:.3f} | {x['mu']} | {x['n_lanes']} | {x['proof_kib']} | {'ok' if x['verify'] else 'FAIL'} |")

print()
print("# capacity (mu <= 25)")
for v in VS:
    ok = [n for n in NS if data[(v, n)]["mu"] <= 25]
    nmax = max(ok) if ok else None
    if nmax is None:
        print(v, "no n with mu<=25")
        continue
    nxt = nmax + 1
    print(f"{v}: largest n with mu<=25: {nmax} (TC 2^{math.log2(data[(v, nmax)]['tc']):.4f}, lanes {data[(v, nmax)]['r']['n_lanes']})")
    if (v, nxt) not in data:
        print("  n+1 not in sweep")
        continue
    a, b = data[(v, nmax)], data[(v, nxt)]
    changed = []
    for t in ORDER:
        if b["taus"][t] != a["taus"][t]:
            h = (1 << a["taus"][t]) - a["r"]["tables"][t]["rows"]
            changed.append((t, a["taus"][t], b["taus"][t], a["r"]["tables"][t]["rows"], h, round(100 * h / (1 << a["taus"][t]), 2), b["r"]["tables"][t]["rows"]))
    if b["r"]["log_mem"] != a["r"]["log_mem"]:
        cells = 1 << a["r"]["log_mem"]
        h = cells - a["r"]["mem_used"]
        changed.append(("MEMORY", a["r"]["log_mem"], b["r"]["log_mem"], a["r"]["mem_used"], h, round(100 * h / cells, 2), b["r"]["mem_used"]))
    print(f"  at n={nxt}: mu={b['mu']} TC 2^{math.log2(b['tc']):.4f}; tables crossing a power of two (table, tau@n, tau@n+1, rows@n, headroom rows@n, headroom % of 2^tau, rows@n+1):")
    for c in changed:
        print("   ", c)
    # the crossings that alone push TC above 2^25 at the n+1 sizes
    bumps = []
    for t in ORDER:
        if b["taus"][t] != a["taus"][t]:
            w = (15 if t in ("XOR", "MUL", "DEREF") else 14 if t == "JUMP" else 8 if t == "SET" else 26) + (64 if t == "KECCAK" else 0)
            bumps.append((t, (b["taus"][t] > a["taus"][t]) * w * ((1 << b["taus"][t]) - (1 << a["taus"][t]))))
    print("    contrib added by each crossing at n+1 (words):", bumps, "memory +", (4 * (1 << b['r']['log_mem'])) - (4 * (1 << a['r']['log_mem'])))

#!/usr/bin/env python3
"""T03: pool both timing passes (runs/, runs2/: 2 passes x 3 measured repeats = 6 per point) and
derive per-child node prove-time savings. DERIVED numbers; V1/V2 are UNSOUND variants.
usage: pooled.py OUT_CSV"""
import csv, os, statistics, sys
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'results', 'T03')
P = {}
for f in ('summary.csv', 'summary_pass2.csv'):
    for r in csv.DictReader(open(os.path.join(R, f))):
        k = (r['variant'], int(r['n_children']))
        P.setdefault(k, []).extend(float(x) for x in r['prove_s_each_repeat'].split())
T01 = {2: 0.557, 4: 1.338, 6: 2.333}
med = {k: statistics.median(v) for k, v in P.items()}
rows = []
for v in ('base', 'v1', 'v2'):
    for n in (2, 4, 6):
        xs = sorted(P[v, n])
        rows.append(dict(kind='point', variant=v, n=n, prove_s_all=' '.join(map(str, xs)), pooled_median_s=round(med[v, n], 4),
                         min_s=xs[0], max_s=xs[-1]))
def slopes(v):
    return (med[v, 6] - med[v, 2]) / 4, (med[v, 4] - med[v, 2]) / 2
bs26, bs24 = slopes('base')
t26, t24 = (T01[6] - T01[2]) / 4, (T01[4] - T01[2]) / 2
print(f"pooled medians: " + '; '.join(f"{v} n{n} {med[v, n]:.3f}" for v in ('base', 'v1', 'v2') for n in (2, 4, 6)))
print(f"base slope n2-6 {bs26*1e3:.1f} ms/child, n2-4 {bs24*1e3:.1f}; T01 n2-6 {t26*1e3:.1f}, n2-4 {t24*1e3:.1f}")
for v in ('v1', 'v2'):
    s26, s24 = slopes(v)
    d = dict(kind='derived', variant=v, slope_n2_6_ms=round(s26 * 1e3, 1), slope_n2_4_ms=round(s24 * 1e3, 1),
             saved_n2_6_ms=round((bs26 - s26) * 1e3, 1), saved_frac_n2_6=round((bs26 - s26) / bs26, 3),
             saved_n2_4_ms=round((bs24 - s24) * 1e3, 1), saved_frac_n2_4=round((bs24 - s24) / bs24, 3),
             saved_vs_T01_n2_6_ms=round((t26 - s26) * 1e3, 1), saved_frac_vs_T01_n2_6=round((t26 - s26) / t26, 3),
             saved_vs_T01_n2_4_ms=round((t24 - s24) * 1e3, 1), saved_frac_vs_T01_n2_4=round((t24 - s24) / t24, 3))
    rows.append(d); print(d)
keys = []
for r in rows:
    for k in r:
        if k not in keys: keys.append(k)
with open(sys.argv[1], 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)

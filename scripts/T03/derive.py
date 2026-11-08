#!/usr/bin/env python3
"""T03 step 5: summary.csv and DERIVED per-child savings of the UNSOUND variants V1, V2.

usage: derive.py RUNS_DIR OUT_SUMMARY_CSV OUT_DERIVED_CSV
Logs are run.sh outputs named <variant>_n<n>.log, variant in base / v1 / v2.

Slopes are least-squares over n = 2, 4, 6. With equally spaced n this equals (y6 - y2) / 4: the
n = 4 point does not move the slope; it is reported as a linearity check (residual at n = 4).
Prove time is the median of the 3 measured passes. KECCAK counts are 2^x from the printed
per-opcode line (x has 3 decimals, so about +-0.04% each); exact KECCAK counts come from the
profiler attribution (attribution.csv), not from here.
"""
import sys, os, re, csv, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_runs import row as parse_row

PER_CHILD_BASE_CYCLES = 186807.5  # exact, from the profiler (slope n=2 -> n=4); T01 rounded: 186.8k
T01 = {2: dict(cycles=392988, prove=0.557), 4: dict(cycles=766603, prove=1.338), 6: dict(cycles=1140247, prove=2.333)}
LABEL = {'base': 'baseline (df7d122, sound)', 'v1': 'V1 UNSOUND (skip e1)', 'v2': 'V2 UNSOUND (skip e1+e2+e4)'}


def lsq(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    s = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return s, my - s * mx


def keccak_of(line):
    m = re.search(r'KECCAK 2\^([\d.]+)', line or '')
    return 2 ** float(m.group(1)) if m else None


def main():
    runs, out_sum, out_der = sys.argv[1:4]
    rows = []
    for f in sorted(os.listdir(runs)):
        if not f.endswith('.log'): continue
        p = os.path.join(runs, f)
        r = parse_row(p)
        t = open(p, errors='replace').read()
        v = f.split('_')[0]
        r = dict(variant=v, label=LABEL[v], sound='no' if v != 'base' else 'yes', **r)
        r['verify_result'] = 'FAILED' if 'panicked' in t else ('ok' if re.search(r'verifying\s*:', t) else 'no output')
        r['keccak_count_from_log2'] = round(keccak_of(r['per_opcode_line']), 1)
        rows.append(r)
    with open(out_sum, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    by = {(r['variant'], int(r['n_children'])): r for r in rows}
    ns = (2, 4, 6)
    fit = {}
    for v in ('base', 'v1', 'v2'):
        if not all((v, n) in by for n in ns): continue
        cyc = [int(by[v, n]['cycles'].replace(',', '')) for n in ns]
        kec = [keccak_of(by[v, n]['per_opcode_line']) for n in ns]
        prv = [float(by[v, n]['prove_s_median']) for n in ns]
        fit[v] = dict(cyc=cyc, kec=kec, prv=prv, cs=lsq(ns, cyc), ks=lsq(ns, kec), ps=lsq(ns, prv))
    t01p = lsq(ns, [T01[n]['prove'] for n in ns])
    t01c = lsq(ns, [T01[n]['cycles'] for n in ns])
    der = []
    print(f"T01 baseline: cycles slope {t01c[0]:.1f}/child, prove slope {t01p[0]*1e3:.1f} ms/child")
    for v, f in fit.items():
        res4 = f['cyc'][1] - (f['cs'][0] * 4 + f['cs'][1])
        print(f"{v}: cycles {f['cyc']} slope {f['cs'][0]:.1f} (n=4 residual {res4:.1f}); KECCAK~ {[round(x) for x in f['kec']]} "
              f"slope {f['ks'][0]:.1f}; prove medians {f['prv']} slope {f['ps'][0]*1e3:.1f} ms/child")
    for v in ('v1', 'v2'):
        if v not in fit: continue
        f = fit[v]
        d = dict(variant=v, label=LABEL[v])
        d['cycles_slope_variant'] = round(f['cs'][0], 1)
        d['cycles_saved_per_child'] = round(t01c[0] - f['cs'][0], 1)
        d['cycles_saved_frac_of_186807'] = round((t01c[0] - f['cs'][0]) / PER_CHILD_BASE_CYCLES, 4)
        d['keccak_slope_variant'] = round(f['ks'][0], 1)
        if 'base' in fit:
            d['keccak_saved_per_child_from_log2'] = round(fit['base']['ks'][0] - f['ks'][0], 1)
            d['keccak_saved_frac'] = round((fit['base']['ks'][0] - f['ks'][0]) / fit['base']['ks'][0], 4)
        d['prove_slope_variant_ms'] = round(f['ps'][0] * 1e3, 1)
        d['prove_saved_per_child_ms_vs_T01'] = round((t01p[0] - f['ps'][0]) * 1e3, 1)
        d['prove_saved_frac_vs_T01'] = round((t01p[0] - f['ps'][0]) / t01p[0], 4)
        if 'base' in fit:
            b = fit['base']['ps'][0]
            d['prove_slope_base_same_session_ms'] = round(b * 1e3, 1)
            d['prove_saved_per_child_ms_vs_same_session'] = round((b - f['ps'][0]) * 1e3, 1)
            d['prove_saved_frac_vs_same_session'] = round((b - f['ps'][0]) / b, 4)
            # the n=2 -> n=4 slope avoids the n=6 point, which pages on this 8 GiB machine
            b24 = (fit['base']['prv'][1] - fit['base']['prv'][0]) / 2
            v24 = (f['prv'][1] - f['prv'][0]) / 2
            d['prove_saved_per_child_ms_n2_n4_same_session'] = round((b24 - v24) * 1e3, 1)
            d['prove_saved_frac_n2_n4_same_session'] = round((b24 - v24) / b24, 4)
        der.append(d)
    if der:
        with open(out_der, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(der[0])); w.writeheader(); w.writerows(der)
        for d in der: print(d)


if __name__ == '__main__':
    main()

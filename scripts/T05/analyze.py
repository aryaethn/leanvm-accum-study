#!/usr/bin/env python3
"""T05 steps 5 and 7: run table, pooled medians and DERIVED savings of the UNSOUND variants V3, V4.

usage: analyze.py            (changes to results/T05; reads runs/ and runs2/, writes the csv/md files)

Per log (run.sh output, one per variant x n x pass): parsed by T03's parse_runs.row, plus
  node_mu_trace  = (base encode log_domain of the node's traced pass) + 4. At rate 1/4 the L0 tree
                   depth is log_msg_cols + log_inv_rate = (mu - 6) + 2 (T04 section 2a), so
                   mu = log_domain + 4. Cross-checked against
  node_mu_tc     = max(15, ceil(TOTAL_COMMITTED exponent)) (crates/verifier/src/layout.rs:547).
  verify_result  = ok if the CLI printed 'verifying' (it runs sig.verify().expect(..),
                   bins/leanvm/src/benchmark.rs:196) and nothing panicked.
Pooled medians: 2 passes x 3 measured repeats = 6 per (variant, n). Slopes over n = 2, 4, 6 are
least squares, which for equally spaced n equals (y6 - y2) / 4; the n = 2 -> 4 slope is also given.
All savings are DERIVED (differences of measured medians or of printed cycle counts).
"""
import os, sys, re, csv, statistics, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'T03'))
from parse_runs import row as parse_row

ANSI = re.compile(r'\x1b\[[0-9;]*m')
LABEL = {'base': 'baseline (df7d122, sound)', 'v3': 'V3 UNSOUND (L0 only)', 'v4': 'V4 UNSOUND (L0+L1)'}
NS = (2, 4, 6)
T03_BASE = {2: 0.605, 4: 1.406, 6: 2.247}
EXACT_KECCAK_SAVED_PER_CHILD = {'v3': 3914 / 2, 'v4': 2288 / 2}  # profiled n=2 (v3_check.txt, v4_check.txt)


def keccak_of(line):
    m = re.search(r'KECCAK 2\^([\d.]+)', line or '')
    return 2 ** float(m.group(1)) if m else None


def lsq(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


def one(path, pas):
    r = parse_row(path)
    t = ANSI.sub('', open(path, errors='replace').read())
    v = os.path.basename(path).split('_')[0]
    m = re.findall(r'kind: "base encode" \| log_domain: (\d+)', t)
    tc = float(r['total_committed_log2'])
    out = dict(variant=v, label=LABEL[v], sound='no' if v != 'base' else 'yes', n=int(r['n_children']), pass_=pas)
    out.update(r)
    out['node_base_encode_log_domain'] = m[-1] if m else ''
    out['node_mu_trace'] = int(m[-1]) + 4 if m else ''
    out['node_mu_total_committed'] = max(15, math.ceil(tc))
    out['mu_consistent'] = 'yes' if m and int(m[-1]) + 4 == out['node_mu_total_committed'] else 'NO'
    out['verify_result'] = 'FAILED' if 'panicked' in t else ('ok' if re.search(r'verifying\s*:', t) else 'no output')
    out['keccak_count_from_log2'] = round(keccak_of(r['per_opcode_line']), 1)
    return out


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'results', 'T05'))
    rows = []
    for pas, d in ((1, 'runs'), (2, 'runs2')):
        for f in sorted(os.listdir(d)):
            if f.endswith('.log'):
                rows.append(one(os.path.join(d, f), pas))
    rows.sort(key=lambda r: (r['pass_'], r['n'], list(LABEL).index(r['variant'])))
    if not rows: sys.exit('no raw logs in results/T05/runs (raw T05 logs are not bundled); tables left unchanged')
    with open('summary.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    # ---- run table ----
    L = ['| variant | n | pass | cycles | TOTAL_COMMITTED | node mu (trace / TC) | proof KiB | prove s (3 repeats) | median s | leanVM peak GiB | OS peak footprint GiB | swap delta MiB | verify | flags |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        L.append(f"| {LABEL[r['variant']]} | {r['n']} | {r['pass_']} | {r['cycles']} | 2^{r['total_committed_log2']} | {r['node_mu_trace']} / {r['node_mu_total_committed']} | {r['proof_kib']} | {r['prove_s_each_repeat']} | {r['prove_s_median']} | {r['leanvm_peak_gib']} | {r['os_peak_footprint_gib']} | {r['swap_delta_mib']} | {r['verify_result']} ({r['verify_ms']} ms) | {r['flags']} |")
    L.append('\nPer-opcode lines (`details`), per variant and n, both passes:\n')
    for r in rows:
        L.append(f"- {r['variant']} n={r['n']} pass {r['pass_']}: `{r['per_opcode_line']}`")
    open('run_table.md', 'w').write('\n'.join(L) + '\n')

    # ---- pooled medians ----
    P, C, K, MU = {}, {}, {}, {}
    for r in rows:
        k = (r['variant'], r['n'])
        P.setdefault(k, []).extend(float(x) for x in r['prove_s_each_repeat'].split())
        C.setdefault(k, set()).add(int(r['cycles'].replace(',', '')))
        K.setdefault(k, []).append(keccak_of(r['per_opcode_line']))
        MU.setdefault(k, set()).add(r['node_mu_trace'])
    med = {k: statistics.median(v) for k, v in P.items()}
    pooled = []
    for v in LABEL:
        for n in NS:
            xs = sorted(P[v, n])
            pooled.append(dict(variant=v, label=LABEL[v], n=n, prove_s_all=' '.join(map(str, xs)), pooled_median_s=round(med[v, n], 4),
                               min_s=xs[0], max_s=xs[-1], cycles=' / '.join(map(str, sorted(C[v, n]))), node_mu=' / '.join(map(str, sorted(MU[v, n])))))
    with open('prove_pooled.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(pooled[0])); w.writeheader(); w.writerows(pooled)

    # ---- derived ----
    cyc = {k: statistics.mean(v) for k, v in C.items()}
    kec = {k: statistics.mean(v) for k, v in K.items()}
    sl = lambda d, v: lsq(NS, [d[v, n] for n in NS])
    sl24 = lambda d, v: (d[v, 4] - d[v, 2]) / 2
    der = []
    for v in ('v3', 'v4'):
        d = dict(variant=v, label=LABEL[v])
        d['cycles_slope_base'] = round(sl(cyc, 'base'), 1); d['cycles_slope_variant'] = round(sl(cyc, v), 1)
        d['cycles_saved_per_child'] = round(sl(cyc, 'base') - sl(cyc, v), 1)
        d['cycles_saved_frac_of_base_slope'] = round((sl(cyc, 'base') - sl(cyc, v)) / sl(cyc, 'base'), 4)
        d['keccak_saved_per_child_from_log2_slope'] = round(sl(kec, 'base') - sl(kec, v), 1)
        d['keccak_saved_per_child_exact_profile_n2'] = EXACT_KECCAK_SAVED_PER_CHILD[v]
        d['prove_slope_base_ms'] = round(sl(med, 'base') * 1e3, 1); d['prove_slope_variant_ms'] = round(sl(med, v) * 1e3, 1)
        d['prove_saved_per_child_ms'] = round((sl(med, 'base') - sl(med, v)) * 1e3, 1)
        d['prove_saved_frac'] = round((sl(med, 'base') - sl(med, v)) / sl(med, 'base'), 4)
        d['prove_saved_per_child_ms_n2_n4'] = round((sl24(med, 'base') - sl24(med, v)) * 1e3, 1)
        d['prove_saved_frac_n2_n4'] = round((sl24(med, 'base') - sl24(med, v)) / sl24(med, 'base'), 4)
        d['n6_prove_base_s'] = round(med['base', 6], 4); d['n6_prove_variant_s'] = round(med[v, 6], 4)
        d['n6_prove_saved_s'] = round(med['base', 6] - med[v, 6], 4)
        d['n6_prove_saved_frac'] = round((med['base', 6] - med[v, 6]) / med['base', 6], 4)
        d['mu_base_n2_4_6'] = ' '.join('/'.join(map(str, sorted(MU['base', n]))) for n in NS)
        d['mu_variant_n2_4_6'] = ' '.join('/'.join(map(str, sorted(MU[v, n]))) for n in NS)
        d['n6_mu_step_vs_base'] = 'yes' if MU[v, 6] != MU['base', 6] else 'no'
        der.append(d)
    with open('derived.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(der[0])); w.writeheader(); w.writerows(der)

    print('pooled medians (s): ' + '; '.join(f"{v} n{n} {med[v, n]:.3f}" for v in LABEL for n in NS))
    print('cycles: ' + '; '.join(f"{v} n{n} {sorted(C[v, n])}" for v in LABEL for n in NS))
    print('node mu: ' + '; '.join(f"{v} n{n} {sorted(MU[v, n])}" for v in LABEL for n in NS))
    for r in rows:
        if r['variant'] == 'base' and r['n'] == 2:
            m = float(r['prove_s_median'])
            print(f"drift base n=2 pass {r['pass_']}: median {m:.3f} s vs 0.605 s: {100 * (m - 0.605) / 0.605:+.1f}%  swap delta {r['swap_delta_mib']} MiB")
    print('base vs T03 pooled medians: ' + '; '.join(f"n{n} {med['base', n]:.3f} vs {T03_BASE[n]} ({100 * (med['base', n] - T03_BASE[n]) / T03_BASE[n]:+.1f}%)" for n in NS))
    for d in der:
        print(d)
    print('mu consistency (trace vs TOTAL_COMMITTED): ' + ('all consistent' if all(r['mu_consistent'] == 'yes' for r in rows) else str([(r['variant'], r['n'], r['pass_']) for r in rows if r['mu_consistent'] != 'yes'])))
    print('verify: ' + ', '.join(sorted({r['verify_result'] for r in rows})))


if __name__ == '__main__':
    main()

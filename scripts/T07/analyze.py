#!/usr/bin/env python3
"""T07 steps 3-5: run table, n=8 row, pooled medians and DERIVED quantities for baseline vs V5.
V5 is UNSOUND (measurement-only emulation of the batched L1 opening B'-L1, research/d3-v5).

usage: analyze.py      (changes to results/T07; reads runs/, runs2/, runs8/; writes csv/md files)

Per log (run.sh output): parsed by T03's parse_runs.row, plus
  swap_before_mib  = used swap when the run started (run.sh '# swap_before')
  node_mu_trace    = (last 'base encode' log_domain in the trace, i.e. the node's) + 4
                     (rate 1/4: L0 depth = (mu - 6) + 2, T04/T05), cross-checked against
  node_mu_tc       = max(15, ceil(TOTAL_COMMITTED exponent)).
  verify_result    = ok if the CLI printed 'verifying' (sig.verify().expect(..)) and nothing panicked.
Pooled medians: 2 passes x 3 measured repeats = 6 per (variant, n). Per-child slopes over n = 2, 4, 6
are least squares (= (y6 - y2) / 4 for equally spaced n). Everything in derived.csv is DERIVED.
"""
import os, sys, re, csv, statistics, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'T03'))
from parse_runs import row as parse_row, swap_used

ANSI = re.compile(r'\x1b\[[0-9;]*m')
LABEL = {'base': 'baseline (df7d122, sound)', 'v5': 'V5 UNSOUND (B\'-L1 emulation)'}
NS = (2, 4, 6)
T05_BASE = {2: 0.5535, 4: 1.275, 6: 1.945}            # T05 pooled medians (paging present)
T05_CYC = {2: 392988, 4: 766603, 6: 1140247}
PROFILED_N2 = dict(cycles_saved=30063, keccak_saved=1158)   # v5_check.txt (child 1 at n=2)
# Projection inputs given by the task (seconds).
LEAF_S, LEAF_OPEN_REMOVED_S, BATCHED_OPEN_S, N_LEAVES = 1.026, 0.103, 0.11, 6


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
    sb = re.search(r'# swap_before: (.*)', t).group(1)
    out = dict(variant=v, label=LABEL[v], sound='no' if v != 'base' else 'yes', n=int(r['n_children']), pass_=pas,
               swap_before_mib=round(swap_used(sb)))
    out.update(r)
    out['node_base_encode_log_domain'] = m[-1] if m else ''
    out['node_mu_trace'] = int(m[-1]) + 4 if m else ''
    out['node_mu_total_committed'] = max(15, math.ceil(tc))
    out['mu_consistent'] = 'yes' if m and int(m[-1]) + 4 == out['node_mu_total_committed'] else 'NO'
    out['verify_result'] = 'FAILED' if 'panicked' in t else ('ok' if re.search(r'verifying\s*:', t) else 'no output')
    out['keccak_count_from_log2'] = round(keccak_of(r['per_opcode_line']), 1)
    return out


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'results', 'T07'))
    rows = []
    for pas, d in ((1, 'runs'), (2, 'runs2'), ('n8', 'runs8')):
        if not os.path.isdir(d): continue
        for f in sorted(os.listdir(d)):
            if f.endswith('.log'):
                rows.append(one(os.path.join(d, f), pas))
    key = lambda r: (str(r['pass_']), r['n'], list(LABEL).index(r['variant']))
    rows.sort(key=key)
    with open('summary.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    main_rows = [r for r in rows if r['pass_'] in (1, 2)]
    n8 = [r for r in rows if r['pass_'] == 'n8']

    # ---- run table ----
    L = ['| variant | n | pass | cycles | TOTAL_COMMITTED | node mu (trace / TC rule) | proof KiB | prove s (3 repeats) | median s | leanVM peak GiB | OS footprint GiB | swap at start MiB | swap Δ MiB | verify | flags |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in main_rows:
        L.append(f"| {LABEL[r['variant']]} | {r['n']} | {r['pass_']} | {r['cycles']} | 2^{r['total_committed_log2']} | {r['node_mu_trace']} / {r['node_mu_total_committed']} | {r['proof_kib']} | {r['prove_s_each_repeat']} | {r['prove_s_median']} | {r['leanvm_peak_gib']} | {r['os_peak_footprint_gib']} | {r['swap_before_mib']} | {r['swap_delta_mib']:+d} | {r['verify_result']} ({r['verify_ms']} ms) | {r['flags']}; swap at start {r['swap_before_mib']} MiB |")
    L.append('\nn = 8, `--repeat 1` (prove time is paging-bound here; not used):\n')
    L.append('| variant | n | cycles | TOTAL_COMMITTED | node mu (trace / TC rule) | proof KiB | prove s (paging-bound) | OS footprint GiB | swap at start MiB | swap Δ MiB | verify |')
    L.append('|---|---|---|---|---|---|---|---|---|---|---|')
    for r in n8:
        L.append(f"| {LABEL[r['variant']]} | 8 | {r['cycles']} | 2^{r['total_committed_log2']} | {r['node_mu_trace']} / {r['node_mu_total_committed']} | {r['proof_kib']} | {r['prove_s_each_repeat']} (paging-bound) | {r['os_peak_footprint_gib']} | {r['swap_before_mib']} | {r['swap_delta_mib']:+d} | {r['verify_result']} ({r['verify_ms']} ms) |")
    L.append('\nPer-opcode lines (`details`):\n')
    for r in rows:
        L.append(f"- {r['variant']} n={r['n']} pass {r['pass_']}: `{r['per_opcode_line']}`")
    open('run_table.md', 'w').write('\n'.join(L) + '\n')

    # ---- pooled medians ----
    P, C, K, MU = {}, {}, {}, {}
    for r in main_rows:
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

    # ---- derived (DERIVED) ----
    cyc = {k: statistics.mean(v) for k, v in C.items()}
    kec = {k: statistics.mean(v) for k, v in K.items()}
    sl = lambda d, v: lsq(NS, [d[v, n] for n in NS])
    der = [('cycles per child, baseline slope n=2,4,6', round(sl(cyc, 'base'), 1)),
           ('cycles per child, V5 slope n=2,4,6 (children >= 1)', round(sl(cyc, 'v5'), 1)),
           ('cycles saved per child (slope difference)', round(sl(cyc, 'base') - sl(cyc, 'v5'), 1)),
           ('cycles saved per child, share of baseline slope', round((sl(cyc, 'base') - sl(cyc, 'v5')) / sl(cyc, 'base'), 4)),
           ('cycles saved per child, profiled n=2 (child 1, exact)', PROFILED_N2['cycles_saved']),
           ('KECCAK saved per child (slope of printed 2^x; about +-0.04% each)', round(sl(kec, 'base') - sl(kec, 'v5'), 1)),
           ('KECCAK saved per child, profiled n=2 (exact)', PROFILED_N2['keccak_saved'])]
    for n in NS:
        der.append((f'pooled median prove s, baseline n={n}', round(med['base', n], 4)))
        der.append((f'pooled median prove s, V5 n={n}', round(med['v5', n], 4)))
        der.append((f'prove s saved (baseline - V5), n={n}', round(med['base', n] - med['v5', n], 4)))
        der.append((f'prove s saved share, n={n}', round((med['base', n] - med['v5', n]) / med['base', n], 4)))
    der.append(('prove ms per child, baseline slope n=2,4,6', round(sl(med, 'base') * 1e3, 1)))
    der.append(('prove ms per child, V5 slope n=2,4,6', round(sl(med, 'v5') * 1e3, 1)))
    der.append(('prove ms saved per child (slope difference)', round((sl(med, 'base') - sl(med, 'v5')) * 1e3, 1)))
    for v in LABEL:
        der.append((f'node mu {v} n=2/4/6', ' / '.join('/'.join(map(str, sorted(MU[v, n]))) for n in NS)))
    der.append(('V5 n=6 node mu', '/'.join(map(str, sorted(MU['v5', 6])))))
    leaf = LEAF_S - LEAF_OPEN_REMOVED_S
    M = med['v5', 6]
    dl = leaf + BATCHED_OPEN_S + M
    cpu = N_LEAVES * leaf + BATCHED_OPEN_S + M
    der.append(('projection: leaf s = 1.026 - 0.103', round(leaf, 4)))
    der.append(('projection: merge s = V5 n=6 pooled median (measured)', round(M, 4)))
    der.append(('projection: deadline s = leaf + batched native opening + merge = (1.026 - 0.103) + 0.11 + M', round(dl, 4)))
    der.append(('projection: CPU s per slot = 6 x leaf + batched native opening + merge = 6 x (1.026 - 0.103) + 0.11 + M', round(cpu, 4)))
    Mb = med['base', 6]
    der.append(('context: baseline deadline s = 1.026 + baseline n=6 median', round(LEAF_S + Mb, 4)))
    der.append(('context: baseline CPU s per slot = 6 x 1.026 + baseline n=6 median', round(N_LEAVES * LEAF_S + Mb, 4)))
    with open('derived.csv', 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['quantity (DERIVED)', 'value']); w.writerows(der)

    print('pooled medians (s): ' + '; '.join(f"{v} n{n} {med[v, n]:.4f}" for v in LABEL for n in NS))
    print('cycles: ' + '; '.join(f"{v} n{n} {sorted(C[v, n])}" for v in LABEL for n in NS))
    print('base cycles reproduce T05: ' + str(all(C['base', n] == {T05_CYC[n]} for n in NS)))
    print('base vs T05 pooled medians: ' + '; '.join(f"n{n} {med['base', n]:.4f} vs {T05_BASE[n]} ({100 * (med['base', n] - T05_BASE[n]) / T05_BASE[n]:+.1f}%)" for n in NS))
    for q, v in der:
        print(f'  {q}: {v}')
    print('mu consistency (trace vs TOTAL_COMMITTED rule): ' + ('all consistent' if all(r['mu_consistent'] == 'yes' for r in rows) else str([(r['variant'], r['n'], r['pass_']) for r in rows if r['mu_consistent'] != 'yes'])))
    print('verify: ' + ', '.join(f"{r['variant']} n{r['n']} p{r['pass_']}={r['verify_result']}" for r in rows))
    print('swap at start / delta (MiB): ' + ', '.join(f"{r['variant']} n{r['n']} p{r['pass_']} {r['swap_before_mib']}/{r['swap_delta_mib']:+d}" for r in rows))


if __name__ == '__main__':
    main()

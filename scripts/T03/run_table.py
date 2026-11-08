#!/usr/bin/env python3
"""Markdown run table from summary.csv (pass 1) and summary_pass2.csv (pass 2). usage: run_table.py > run_table.md"""
import csv, os
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'results', 'T03')
print('| variant | n | pass | cycles | TOTAL_COMMITTED | proof KiB | prove s (3 passes) | median s | leanVM peak GiB | OS peak footprint GiB | swap delta MiB | verify | flags |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
ops = {}
for p, f in ((1, 'summary.csv'), (2, 'summary_pass2.csv')):
    for r in csv.DictReader(open(os.path.join(R, f))):
        ops[(r['variant'], r['n_children'])] = r['per_opcode_line']
        lab = {'base': 'baseline', 'v1': 'V1 (UNSOUND)', 'v2': 'V2 (UNSOUND)'}[r['variant']]
        print(f"| {lab} | {r['n_children']} | {p} | {r['cycles']} | 2^{r['total_committed_log2']} | {r['proof_kib']} | {r['prove_s_each_repeat']} | {r['prove_s_median']} | {r['leanvm_peak_gib']} | {r['os_peak_footprint_gib']} | {r['swap_delta_mib']} | {r['verify_result']} ({r['verify_ms']} ms) | {r['flags']} |")
print('\nPer-opcode lines (identical in both passes):\n')
for (v, n), line in sorted(ops.items(), key=lambda x: (['base', 'v1', 'v2'].index(x[0][0]), int(x[0][1]))):
    print(f"- {v} n={n}: `{line}`")

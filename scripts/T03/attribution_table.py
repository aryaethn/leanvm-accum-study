#!/usr/bin/env python3
"""T03 step 2 output: exact per-child cycle attribution (slope n=2 -> n=4 of the baseline profiles).

usage: attribution_table.py BASE_N2.json BASE_N4.json OUT_CSV
Inputs are attribute.py --json outputs of the two baseline DBG_PROF_DUMP profiles (one run each;
cycles are deterministic). Per-child = (n4 - n2) / 2 for every bucket, so fixed per-node work
cancels. Writes one row per bucket and one per stage group, with cycles, share of the per-child
total, KECCAK opcodes and Fiat-Shamir-helper cycles per child.
"""
import json, sys, csv, collections

GROUP = {  # bucket prefix -> stage of the T03 definitions
    'a': '(a) transcript replay + FS (verify_sub own)', 'e': '(a) transcript in open_stacked (level roots, setup)',
    'b': '(b) bus GKR', 'c': '(c) table / constraint sumcheck', 'd': '(d) Keccak GKR / reduction',
    'e1': '(e1) Merkle hashing', 'e1e2': '(e1/e2) lane packing of opened rows',
    'e2': '(e2) folding + consistency at queried points', 'e3': '(e3) evaluation-claim parts',
    'e4': '(e4) final polynomial', 'eq': '(eq) query sampling + query PoW',
    'outside verify_sub: main': 'node, outside verify_sub (per-child part of main)',
    'outside verify_sub: __jump_tables': 'node, jump-table prologue (fixed)',
}


def tot(d, pred=lambda k: True):
    return sum(v for k, v in d.items() if pred(k))


def main():
    a, b, out = sys.argv[1:4]
    A, B = json.load(open(a)), json.load(open(b))
    per_child_total = (B['grand'] - A['grand']) / 2
    rows, groups = [], collections.defaultdict(lambda: [0.0, 0.0, 0.0])
    for k in sorted(set(A['buckets']) | set(B['buckets'])):
        x, y = A['buckets'].get(k, {}), B['buckets'].get(k, {})
        c = (tot(y) - tot(x)) / 2
        kc = (tot(y, lambda o: o.startswith('KECCAK')) - tot(x, lambda o: o.startswith('KECCAK'))) / 2
        fs = (tot(y, lambda o: o.endswith('|FS')) - tot(x, lambda o: o.endswith('|FS'))) / 2
        g = GROUP.get(k) or GROUP[k.split(':')[0]]
        rows.append(dict(kind='bucket', stage=g, bucket=k, cycles_per_child=round(c, 1),
                         share_pct=round(100 * c / per_child_total, 2), keccak_per_child=round(kc, 1),
                         fs_helper_cycles_per_child=round(fs, 1), n2_cycles=round(tot(x), 1), n4_cycles=round(tot(y), 1)))
        groups[g][0] += c; groups[g][1] += kc; groups[g][2] += fs
    for g, (c, kc, fs) in groups.items():
        rows.append(dict(kind='stage', stage=g, bucket='', cycles_per_child=round(c, 1),
                         share_pct=round(100 * c / per_child_total, 2), keccak_per_child=round(kc, 1),
                         fs_helper_cycles_per_child=round(fs, 1), n2_cycles='', n4_cycles=''))
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"per-child total (slope n2->n4): {per_child_total:.1f}; n2 {A['grand']:.0f}, n4 {B['grand']:.0f}")
    print(f"{'stage':52s} {'cyc/child':>10s} {'share':>7s} {'KECCAK':>8s} {'FS-help':>8s}")
    for g in sorted(groups, key=lambda g: g):
        c, kc, fs = groups[g]
        print(f"{g:52s} {c:10.1f} {100 * c / per_child_total:6.2f}% {kc:8.1f} {fs:8.1f}")
    for r in rows:
        if r['kind'] == 'bucket':
            print(f"   {r['bucket']:44s} {r['cycles_per_child']:10.1f} {r['share_pct']:6.2f}% {r['keccak_per_child']:8.1f}")


if __name__ == '__main__':
    main()

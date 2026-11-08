#!/usr/bin/env python3
"""T07 step 2: itemized check of the profiled UNSOUND variant V5 against the expected per-child saving.

usage: compare_v5.py BASE_N2_lv.json V5_N2_lv.json PER_LEVEL_LONG.csv OUT.csv

At n=2, child 0 runs the full opening and child 1 the reduced one, so (baseline - V5) per cell
is child 1's saving in that cell, minus child 0's gating overhead.

Expected set E (the task's 33.4k): every per-child cell (T05 slope table) at L2, L3, L4 and the
tail, plus the L1 cells other than Merkle cap, leaf+path, lane packing and query rows.
For each cell of E, "kept" = expected - delta is child 1's work that V5 still runs in that cell
(transcript work, or arithmetic V5 does not gate). Cells outside E should not move; their delta
is listed (gating overhead, realised query positions of different leaf proofs, label moves).
"""
import json, sys, csv, collections

KEEP_L1 = {'e1:Merkle cap', 'e1:Merkle leaf+path', 'e1e2:lane packing', 'e2:query rows'}


def in_E(bucket, level):
    if level in ('L2', 'L3', 'L4', 'tail'):
        return True
    return level == 'L1' and bucket not in KEEP_L1


def cells(j):
    out = {}
    for k, v in j['buckets'].items():
        b, _, lv = k.partition('@')
        out[(b, lv or '-')] = (sum(v.values()), sum(x for o, x in v.items() if o.startswith('KECCAK')))
    return out


def main():
    bj, vj, long_csv, out = sys.argv[1:5]
    B, V = json.load(open(bj)), json.load(open(vj))
    cb, cv = cells(B), cells(V)
    pc = {(r['bucket'], r['level']): (float(r['cycles_per_child']), float(r['keccak_per_child']))
          for r in csv.DictReader(open(long_csv))}
    rows = []
    E = Ek = 0.0
    kept, other = [], []
    for key in sorted(set(cb) | set(cv) | {k for k in pc if in_E(*k)}, key=lambda k: (k[1], k[0])):
        b0, kb = cb.get(key, (0.0, 0.0)); v0, kv = cv.get(key, (0.0, 0.0))
        d, dk = b0 - v0, kb - kv
        e_c, e_k = pc.get(key, (0.0, 0.0)) if in_E(*key) else (0.0, 0.0)
        r = dict(bucket=key[0], level=key[1], base_n2=round(b0, 1), v5_n2=round(v0, 1), delta=round(d, 1),
                 keccak_delta=round(dk, 1), in_E=int(in_E(*key)), expected_per_child=e_c,
                 kept_in_child1=round(e_c - d, 1) if in_E(*key) else '')
        rows.append(r)
        if in_E(*key):
            E += e_c; Ek += e_k
            if abs(e_c - d) > 1e-9: kept.append((key, e_c, d, e_c - d, e_k - dk))
        elif abs(d) > 1e-9:
            other.append((key, d, dk))
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    jt = 'outside verify_sub: __jump_tables'
    pro = cb.get((jt, '-'), (0, 0))[0] - cv.get((jt, '-'), (0, 0))[0]
    meas = B['steps'] - V['steps']
    mk = sum(x[1] for x in cb.values()) - sum(x[1] for x in cv.values())
    print(f"node steps: baseline {B['steps']}, V5 {V['steps']}; measured saving {meas} (child 1)")
    print(f"fixed prologue (__jump_tables) change: {pro:.1f}; measured saving excl. prologue: {meas - pro:.1f}")
    print(f"expected E (1 x per-child T05 slope cells): {E:.1f} cycles, KECCAK {Ek:.1f}")
    print(f"measured / expected: {100 * (meas - pro) / E:.3f}%   measured - expected: {meas - pro - E:+.1f}")
    print(f"KECCAK saved: measured {mk:.1f}")
    print("\ncells of E with work kept in child 1 (expected per child, delta at n=2, kept = expected - delta, KECCAK kept):")
    tk = 0
    for key, e_c, d, k, kk in kept:
        tk += k
        print(f"   {'@'.join(key):42s} expected {e_c:9.1f}  delta {d:9.1f}  kept {k:+9.1f}  K {kk:+6.1f}")
    print(f"   sum kept: {tk:+.1f}")
    print("\ncells outside E that moved (delta = base - V5; negative = V5 costs more):")
    to = 0
    for key, d, dk in sorted(other, key=lambda x: x[1]):
        to += d
        print(f"   {'@'.join(key):42s} delta {d:+9.1f}  K {dk:+6.1f}")
    print(f"   sum: {to:+.1f}")
    print(f"\ncheck: expected {E:.1f} - kept {tk:.1f} + outside {to:+.1f} = {E - tk + to:.1f} vs measured excl. prologue {meas - pro:.1f}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""T05 step 4: check a profiled UNSOUND variant (V3: K=1, V4: K=2) against the step-1 attribution.

usage: compare_variant.py BASE_N2_lv.json VAR_N2_lv.json K PER_LEVEL_LONG.csv OUT.csv

Removed set R(K), by the variant definition (scripts/make_variant.py):
  levels L_k, k >= K : Merkle cap, leaf+path, lane packing, query rows, row eq weights,
                       PoW check (eq:query grinding), query decode (eq:query decode)
  all levels         : residual (e2:residual)
  tail               : final-message evaluation (e4:final message@tail); final check (e4@-)
Prints, per (bucket, level) cell at n=2: baseline, variant, delta. Then
  predicted (exact)    = sum of baseline n=2 cells in R(K)
  predicted (step 1)   = 2 x per-child cells in R(K) from the slope table (per_level_long.csv)
  measured             = baseline n=2 steps - variant n=2 steps, minus the fixed prologue change.
"""
import json, sys, csv, collections

STRIP = {'e1:Merkle cap', 'e1:Merkle leaf+path', 'e1e2:lane packing', 'e2:query rows',
         'e2:row eq weights', 'eq:query grinding', 'eq:query decode'}


def removed(bucket, level, K):
    if bucket in STRIP and level.startswith('L') and int(level[1:]) >= K:
        return True
    if bucket == 'e2:residual (query weights)':
        return True
    if (bucket, level) in (('e4:final message', 'tail'), ('e4:final check', '-')):
        return True
    return False


def cells(j):
    out = {}
    for k, v in j['buckets'].items():
        b, _, lv = k.partition('@')
        out[(b, lv or '-')] = (sum(v.values()), sum(x for o, x in v.items() if o.startswith('KECCAK')))
    return out


def main():
    bj, vj, K, long_csv, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
    B, V = json.load(open(bj)), json.load(open(vj))
    cb, cv = cells(B), cells(V)
    per_child = {(r['bucket'], r['level']): (float(r['cycles_per_child']), float(r['keccak_per_child'])) for r in csv.DictReader(open(long_csv))}
    rows = []
    pred_exact = pred_k = pred_step1 = pred_step1_k = 0.0
    other = collections.Counter()
    for key in sorted(set(cb) | set(cv)):
        b0, k0 = cb.get(key, (0.0, 0.0)); v0, kv = cv.get(key, (0.0, 0.0))
        rm = removed(*key, K)
        rows.append(dict(bucket=key[0], level=key[1], base_n2=round(b0, 1), variant_n2=round(v0, 1),
                         delta=round(b0 - v0, 1), keccak_delta=round(k0 - kv, 1), in_removed_set=int(rm)))
        if rm:
            pred_exact += b0; pred_k += k0
            pc = per_child.get(key, (0.0, 0.0)); pred_step1 += 2 * pc[0]; pred_step1_k += 2 * pc[1]
            if v0: other['removed cell not empty in variant: ' + '@'.join(key)] += v0
        elif abs(b0 - v0) > 1e-9:
            other['@'.join(key)] += b0 - v0
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    jt = 'outside verify_sub: __jump_tables'
    pro = cb.get((jt, '-'), (0, 0))[0] - cv.get((jt, '-'), (0, 0))[0]
    meas = B['steps'] - V['steps']
    mk = sum(x[1] for x in cb.values()) - sum(x[1] for x in cv.values())
    print(f"K={K}: node steps base {B['steps']} variant {V['steps']}  measured saving {meas}")
    print(f"  fixed prologue (__jump_tables) change: {pro:.1f}")
    print(f"  measured saving excl. prologue: {meas - pro:.1f}  (per child {(meas - pro) / 2:.1f})")
    print(f"  predicted, exact baseline n=2 cells in R(K): {pred_exact:.1f}  (KECCAK {pred_k:.1f})")
    print(f"  predicted, 2 x step-1 per-child slope cells in R(K): {pred_step1:.1f}  (KECCAK {pred_step1_k:.1f})")
    print(f"  measured / step-1 prediction: {100 * (meas - pro) / pred_step1:.3f}%   measured - step1: {meas - pro - pred_step1:+.1f}")
    print(f"  KECCAK removed: measured {mk:.1f}")
    print("  cells outside R(K) that changed (base - variant), and removed cells left non-empty:")
    for k, v in sorted(other.items(), key=lambda x: -abs(x[1])):
        print(f"     {v:+10.1f}  {k}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""T07 step 2: group the V5 per-cell residuals (v5_vs_base_cells.csv) into the itemized difference
between the measured child-1 saving and the expected 33,381.5 (T05 per-child cells)."""
import csv, collections, os
G = collections.OrderedDict((g, [0.0, 0.0, []]) for g in (
    'A transcript kept (fold rounds, squeezes, OOD point/value reads, level roots, nonce absorb, final-message read)',
    'B non-transcript work kept by design (point rotation, L1 row eq weights, level batching arithmetic, L1 advice windows)',
    'C V5 gating: branch tests, join cells, xc plumbing',
    'D realised-query-position noise (different leaf proofs) and +-1 residual cells'))
k = list(G)
def grp(b, lv):
    if b in ('e3:sumcheck rounds', 'eq:query sampling', 'e:level roots') or (b == 'e4:final message' and lv == 'L4'):
        return k[0]
    if b == 'e3:OOD' and lv in ('L1', 'L2', 'L3'): return k[0]          # next level's OOD point + value reads
    if b == 'eq:query grinding': return k[0]                              # nonce absorb (22 cycles a level)
    if b in ('e3:point rotation', 'e3:level batching') or (b == 'e2:row eq weights' and lv == 'L1') or (b == 'eq:query decode' and lv == 'L1'):
        return k[1]
    if b == 'v5:gating' or (b == 'e2:query rows' and lv in ('L2', 'L3', 'L4')) or (b == 'e3:OOD' and lv == 'tail') or lv == '-':
        return k[2]
    return k[3]
tot = 0
for r in csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'results', 'T07', 'v5_vs_base_cells.csv'))):
    x = float(r['kept_in_child1']) if r['in_E'] == '1' else -float(r['delta'])   # contribution to (expected - measured)
    if abs(x) < 1e-9: continue
    g = grp(r['bucket'], r['level']); G[g][0] += x; G[g][2].append(f"{r['bucket']}@{r['level']} {x:+.1f}"); tot += x
for g, (x, _, items) in G.items():
    print(f"{x:+9.1f}  {g}\n           " + '; '.join(items))
print(f"{tot:+9.1f}  total = expected 33381.5 - measured 30063 = {33381.5 - 30063:+.1f}")

#!/usr/bin/env python3
"""T05 step 1: per-WHIR-level attribution per child (slope n=2 -> n=4 of the baseline profiles).

usage: per_level_table.py BASE_N2_lv.json BASE_N4_lv.json OUT_DIR

Inputs: attribute_lv.py --json outputs of the T03 baseline node dumps (one run each; cycles are
deterministic). Per child = (n4 - n2) / 2 for every (bucket, level) cell.
Writes OUT_DIR/per_level_long.csv (bucket, level, cycles, KECCAK per child),
OUT_DIR/per_level_pivot.csv (levels x components) and prints both plus the checks:
  * the level split sums back to each T03 bucket (results/T03/attribution.csv);
  * KECCAK per level against T04's analytic values (results/T04/pcs_facts.md section 5a).
Convention: level k = iteration k of open_stacked's level loop, plus the level-k residual rows,
plus the OOD eq term of the level-k OOD sample. Iteration k (k < 4) also reads the NEXT
level's root and OOD sample (the T04 table counts those OOD squeezes on level k as well).
"""
import json, sys, csv, collections, os

PER_CHILD_TOTAL_T03 = 186807.5
T04_KECCAK = {'L0': 2171.1, 'L1': 845.4, 'L2': 524.2, 'L3': 378.4, 'L4': 280.0, 'tail': 3.0}

COMP = [  # (column, bucket) in table order
    ('Merkle cap', 'e1:Merkle cap'), ('leaf+path hash', 'e1:Merkle leaf+path'),
    ('lane packing', 'e1e2:lane packing'), ('query rows', 'e2:query rows'),
    ('row eq weights', 'e2:row eq weights'), ('residual', 'e2:residual (query weights)'),
    ('query squeezes', 'eq:query sampling'), ('query decode', 'eq:query decode'), ('PoW', 'eq:query grinding'),
    ('fold sumcheck', 'e3:sumcheck rounds'), ('OOD', 'e3:OOD'), ('level roots', 'e:level roots'),
    ('level batching', 'e3:level batching'), ('final message', 'e4:final message'),
    ('point rotation', 'e3:point rotation'), ('setup', 'e:setup'),
]
LEVELS = ['setup', 'L0', 'L1', 'L2', 'L3', 'L4', 'tail']


def tot(d, pred=lambda k: True):
    return sum(v for k, v in d.items() if pred(k))


def main():
    a, b, out = sys.argv[1:4]
    A, B = json.load(open(a)), json.load(open(b))
    per_child = (B['grand'] - A['grand']) / 2
    cells = {}
    for k in sorted(set(A['buckets']) | set(B['buckets'])):
        x, y = A['buckets'].get(k, {}), B['buckets'].get(k, {})
        c = (tot(y) - tot(x)) / 2
        kc = (tot(y, lambda o: o.startswith('KECCAK')) - tot(x, lambda o: o.startswith('KECCAK'))) / 2
        bucket, _, lvl = k.partition('@')
        cells[(bucket, lvl or '-')] = (c, kc)
    with open(os.path.join(out, 'per_level_long.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['bucket', 'level', 'cycles_per_child', 'keccak_per_child'])
        for (bk, lv), (c, kc) in sorted(cells.items()):
            w.writerow([bk, lv, round(c, 2), round(kc, 2)])
    print(f"per-child total (slope n2->n4): {per_child:.1f} (T03: {PER_CHILD_TOTAL_T03})")

    # --- check 1: level split sums back to the T03 bucket per child ---
    t03 = {r['bucket']: float(r['cycles_per_child']) for r in csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'results', 'T03', 'attribution.csv'))) if r['kind'] == 'bucket'}
    byb = collections.defaultdict(float)
    for (bk, lv), (c, kc) in cells.items():
        byb['eq:query sampling' if bk == 'eq:query decode' else bk] += c  # T03 had them as one bucket
    worst = max(abs(byb[k] - t03.get(k, 0)) for k in set(byb) | set(t03))
    print(f"check: max |sum over levels - T03 bucket| per child = {worst:.3f} cycles over {len(byb)} buckets")

    # --- pivot ---
    rows = []
    for lv in LEVELS:
        r = {'level': lv}
        cyc = kec = 0.0
        for col, bk in COMP:
            c, kc = cells.get((bk, lv), (0.0, 0.0))
            r[col] = round(c, 1); cyc += c; kec += kc
        r['total cycles'] = round(cyc, 1)
        r['share of 186807.5 %'] = round(100 * cyc / PER_CHILD_TOTAL_T03, 2)
        r['KECCAK'] = round(kec, 1)
        r['T04 analytic KECCAK'] = T04_KECCAK.get(lv, '')
        r['KECCAK - T04'] = round(kec - T04_KECCAK[lv], 1) if lv in T04_KECCAK else ''
        rows.append(r)
    sumr = {'level': 'sum (opening, in open_stacked)'}
    for col in [c for c, _ in COMP] + ['total cycles', 'KECCAK']:
        sumr[col] = round(sum(r[col] for r in rows), 1)
    sumr['share of 186807.5 %'] = round(100 * sumr['total cycles'] / PER_CHILD_TOTAL_T03, 2)
    sumr['T04 analytic KECCAK'] = round(sum(T04_KECCAK.values()), 1)
    sumr['KECCAK - T04'] = round(sumr['KECCAK'] - sum(T04_KECCAK.values()), 1)
    rows.append(sumr)
    # opening-related but not level-specific (outside open_stacked)
    for bk in ['e3:terminal weights', 'e3:ring-switch front+claim batch', 'e3:placement+config certify', 'e3:open dispatch', 'e4:final check']:
        c, kc = cells.get((bk, '-'), (0.0, 0.0))
        rows.append({'level': f'not level-specific: {bk}', 'total cycles': round(c, 1), 'share of 186807.5 %': round(100 * c / PER_CHILD_TOTAL_T03, 2), 'KECCAK': round(kc, 1)})
    fields = ['level'] + [c for c, _ in COMP] + ['total cycles', 'share of 186807.5 %', 'KECCAK', 'T04 analytic KECCAK', 'KECCAK - T04']
    with open(os.path.join(out, 'per_level_pivot.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(' | '.join(f"{r.get(k, '')}" for k in fields))

    # --- check 2: T03 opening buckets total vs the level table sum ---
    open_b = [bk for _, bk in COMP]
    t03_open = sum(t03.get(k, 0) for k in set(open_b))
    print(f"check: level-table sum {sumr['total cycles']:.1f} vs T03 opening buckets {t03_open:.1f} "
          f"({100 * (sumr['total cycles'] - t03_open) / t03_open:+.4f}%)")


if __name__ == '__main__':
    main()

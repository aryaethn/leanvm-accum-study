#!/usr/bin/env python3
"""T05 step 6: native prover WHIR opening cost per level, from leanVM --tracing span trees.

usage: parse_open.py OUT_CSV LABEL=LOG [LABEL=LOG ...]

For each log (one traced pass each), reads the 'Prove' tree:
  * 'Commit' stage child 'NTT kind: "base encode"': the L0 oracle commit (outside 'PCS open');
  * every child of 'PCS open', in order (crates/pcs/src/stack_open.rs:162-216, crates/pcs/src/whir.rs:1029-1213):
      Ring switch, Basis, Sumcheck (rounds 0..k0), Commit level 1, Open/Induce/Introduce level 0,
      then per recursive level i: Sumcheck, Commit level i+2, Open/Induce/Introduce level i+1,
      and finally 'Final level' (L4 open + induce + introduce + the tail rounds).
Level attribution (oracle convention: level k = all prover work on oracle L_k):
  L_k: the Sumcheck span that folds L_k (the k-th Sumcheck span), Commit level k (k >= 1; L0's is the
       base-encode commit outside PCS open), Open/Induce/Introduce level k. 'Basis' (the combined
       initial weight that the L0 sumcheck runs on) is put on L0. 'Final level' holds L4's
       open/induce/introduce and the tail rounds: reported as 'L4 final+tail'.
  Not level-specific: Ring switch. Untraced remainder = PCS open - sum of its children (PoW grinding
  for all 5 levels, query sampling, OOD sends): the tree has no timestamps, so it cannot be split.
"""
import re, sys, csv

ANSI = re.compile(r'\x1b\[[0-9;]*m')
UNIT = {'s': 1.0, 'ms': 1e-3, 'µs': 1e-6, 'us': 1e-6, 'ns': 1e-9}
LINE = re.compile(r'^(?P<pre>.*?)[┝┕]━ (?P<name>[^\[]+?) \[ (?P<v>[\d.]+)(?P<u>s|ms|µs|us|ns) \|[^\]]*\](?P<attr>.*)$')


def parse(path):
    lines = [ANSI.sub('', l).rstrip('\n') for l in open(path, errors='replace')]
    nodes = []
    for l in lines:
        m = LINE.match(l)
        if m:
            depth = len(m.group('pre'))
            nodes.append(dict(depth=depth, name=m.group('name').strip(), sec=float(m.group('v')) * UNIT[m.group('u')], attr=m.group('attr').strip()))
    i = next(k for k, n in enumerate(nodes) if n['name'] == 'PCS open')
    d0 = nodes[i]['depth']
    kids = []
    j = i + 1
    while j < len(nodes) and nodes[j]['depth'] > d0:
        n = nodes[j]
        if kids and n['depth'] > kids[-1]['depth']:
            kids[-1].setdefault('sub', []).append(n)
        else:
            kids.append(dict(n))
        j += 1
    # the L0 commit: the 'Commit' span (NTT + Merkle) whose child NTT is the base encode
    base = None
    for k, n in enumerate(nodes):
        if 'base encode' in n['attr']:
            par = next(p for p in reversed(nodes[:k]) if p['depth'] < n['depth'])
            base = dict(par, attr=n['attr']); break
    return nodes[i], kids, base


def main():
    out = sys.argv[1]
    rows = []
    for arg in sys.argv[2:]:
        label, path = arg.split('=', 1)
        top, kids, base = parse(path)
        acc = {}
        def add(level, comp, sec):
            acc.setdefault(level, {}).setdefault(comp, 0.0)
            acc[level][comp] += sec
        n_sc = 0
        child_sum = 0.0
        for k in kids:
            child_sum += k['sec']
            lv = re.search(r'level: (\d+)', k['attr'])
            if k['name'] == 'Sumcheck':
                rounds = [int(x) for s in k.get('sub', []) for x in re.findall(r'round: (\d+)', s['attr'])]
                add(f'L{n_sc}', f"sumcheck rounds {min(rounds)}-{max(rounds)}" if rounds else 'sumcheck', k['sec'])
                n_sc += 1
            elif k['name'] in ('Commit', 'Open', 'Induce', 'Introduce'):
                add(f"L{lv.group(1)}", k['name'].lower(), k['sec'])
            elif k['name'] == 'Basis':
                add('L0', 'basis', k['sec'])
            elif k['name'] == 'Final level':
                add('L4', 'final level (L4 open+induce+introduce, tail rounds)', k['sec'])
            else:
                add('-', k['name'], k['sec'])
        if base:
            add('L0', 'commit (base encode, outside PCS open)', base['sec'])
        add('-', 'untraced remainder (PoW x5, query sampling, OOD)', top['sec'] - child_sum)
        for lvl in sorted(acc, key=lambda x: (x == '-', x)):
            for comp, sec in acc[lvl].items():
                rows.append(dict(run=label, log=path, level=lvl, component=comp, ms=round(sec * 1e3, 4)))
        rows.append(dict(run=label, log=path, level='PCS open total', component='', ms=round(top['sec'] * 1e3, 4)))
        if base:
            rows.append(dict(run=label, log=path, level='L0 commit (base encode)', component=base['attr'], ms=round(base['sec'] * 1e3, 4)))
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['run']:14s} {r['level']:24s} {r['component']:56s} {r['ms']:10.3f} ms")
    # pivot: per run, per level (oracle convention), PCS-open part and with the L0 base commit
    runs = list(dict.fromkeys(r['run'] for r in rows))
    lv = ['L0', 'L1', 'L2', 'L3', 'L4', '-']
    piv = []
    for run in runs:
        rr = [r for r in rows if r['run'] == run]
        d = {'run': run}
        for l in lv:
            d[f'{l} in PCS open ms'] = round(sum(r['ms'] for r in rr if r['level'] == l and 'outside PCS open' not in r['component']), 3)
            d[f'{l} commit ms'] = round(sum(r['ms'] for r in rr if r['level'] == l and r['component'].startswith('commit')), 3)
            d[f'{l} non-commit ms'] = round(sum(r['ms'] for r in rr if r['level'] == l and not r['component'].startswith('commit')), 3)
        d['PCS open total ms'] = next(r['ms'] for r in rr if r['level'] == 'PCS open total')
        d['L0 base commit ms (outside PCS open)'] = next((r['ms'] for r in rr if r['level'] == 'L0 commit (base encode)'), '')
        piv.append(d)
    groups = {}
    for d in piv:
        groups.setdefault(d['run'].split('_')[0], []).append(d)
    for g, ds in groups.items():
        m = {'run': f'{g} MEAN of {len(ds)}'}
        for k in ds[0]:
            if k != 'run': m[k] = round(sum(x[k] for x in ds) / len(ds), 3)
        piv.append(m)
    with open(out.replace('.csv', '_pivot.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(piv[0])); w.writeheader(); w.writerows(piv)
    print()
    for d in piv:
        print(d['run'], {k: v for k, v in d.items() if k != 'run'})


if __name__ == '__main__':
    main()

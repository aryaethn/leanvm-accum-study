#!/usr/bin/env python3
"""Per-stage prover breakdown from a leanvm --tracing log.

usage: parse_trace.py LOG [LOG ...] [--csv stages.csv]

Reads tracing-forest output (ANSI codes stripped; trace lines may be glued to
other output, so lines are located by regex, not by line start).

Traced pass
-----------
The printed "passes" line gives each measured pass; the traced pass is the LAST
one. Its total time (denominator for all percentages) is that last pass time.
Pass-level spans are: the depth-1 children of a root span named
"aggregation"/"Fibonacci" if one exists, else the depth-0 spans (recursion logs
have no root). Their durations are matched to stages below; whatever remains of
the pass (residual of Prove not covered by its children, the other pass-level
spans, and any untraced gap vs the printed pass time) is "other".

Span -> stage mapping (direct children of the pass-level "Prove" span)
    Execute program      -> execute
    Build witness        -> witness build   (also the node-level "Build witness")
    Commit               -> commit          (NTT + Merkle; sub-rows commit:NTT, commit:Merkle)
    Prove bus            -> bus GKR
    Prove constraints    -> constraint sumcheck
    Keccak reduction     -> Keccak GKR/reduction
    PCS open             -> PCS open (stacked WHIR)
Pass-level spans outside Prove:
    Replay children      -> replay children   (recursion: child proofs replayed in the VM input)
    Build witness        -> witness build
    everything else      -> other (Batch deferred claims, Recompute deferred claims,
                            Statement digest, LeanDA commit, ...)
"""
import re, sys, csv, os

ANSI = re.compile(r'\x1b\[[0-9;]*m')
SPAN = re.compile(r'INFO {5}((?:[│ ]|[┝┕]━ )*)([^\[\n\r]*?) \[ ?([\d.]+)(ns|µs|ms|s) \| ([\d.]+)%')
UNIT = {'ns': 1e-9, 'µs': 1e-6, 'ms': 1e-3, 's': 1.0}

STAGES = ['execute', 'witness build', 'commit', 'bus GKR', 'constraint sumcheck',
          'Keccak GKR/reduction', 'PCS open', 'replay children', 'other']
PROVE_MAP = {'Execute program': 'execute', 'Build witness': 'witness build', 'Commit': 'commit',
             'Prove bus': 'bus GKR', 'Prove constraints': 'constraint sumcheck',
             'Keccak reduction': 'Keccak GKR/reduction', 'PCS open': 'PCS open'}
NODE_MAP = {'Replay children': 'replay children', 'Build witness': 'witness build'}


def clean(text):
    return ANSI.sub('', text)


def parse_spans(text):
    """Return a forest of dict(name, secs, children, extra) from the trace lines."""
    roots, stack = [], []
    for m in SPAN.finditer(text):
        prefix, name, val, unit, _pct = m.groups()
        depth = len(prefix) // 3
        node = dict(name=name.strip(), secs=float(val) * UNIT[unit], children=[], depth=depth)
        while stack and stack[-1]['depth'] >= depth:
            stack.pop()
        (stack[-1]['children'] if stack else roots).append(node)
        stack.append(node)
    return roots


def printed_passes(text):
    m = re.search(r'passes\s*:\s*([^\n]*)', text)
    ps = [float(x) for x in re.findall(r'([\d.]+) s(?![a-z])', m.group(1))] if m else []
    # recursion: the traced (last) pass time is printed on a line of its own
    # (trace output interleaves with the "passes" line)
    m2 = re.search(r'\n +([\d.]+) s *\n', text)
    if m2 and (not ps or len(ps) < 3):
        ps.append(float(m2.group(1)))
    return ps


def breakdown(path):
    text = clean(open(path, errors='replace').read().replace('\r', '\n'))
    roots = parse_spans(text)
    passes = printed_passes(text)
    # pass-level spans
    roots_named = [r for r in roots if r['name'] in ('aggregation', 'Fibonacci')]
    pass_spans = roots_named[0]['children'] if roots_named else roots
    pass_total = passes[-1] if passes else sum(s['secs'] for s in pass_spans)
    secs = {s: 0.0 for s in STAGES}
    other_parts = {}
    sub = {'commit:NTT': 0.0, 'commit:Merkle': 0.0}
    for sp in pass_spans:
        if sp['name'] == 'Prove':
            covered = 0.0
            for ch in sp['children']:
                st = PROVE_MAP.get(ch['name'])
                if st:
                    secs[st] += ch['secs']; covered += ch['secs']
                    if ch['name'] == 'Commit':
                        for g in ch['children']:
                            if g['name'] == 'NTT': sub['commit:NTT'] += g['secs']
                            if g['name'] == 'Merkle': sub['commit:Merkle'] += g['secs']
                else:
                    other_parts['Prove/' + ch['name']] = other_parts.get('Prove/' + ch['name'], 0) + ch['secs']
            other_parts['Prove residual (not in a child span)'] = sp['secs'] - covered - sum(
                v for k, v in other_parts.items() if k.startswith('Prove/'))
        elif sp['name'] in NODE_MAP:
            secs[NODE_MAP[sp['name']]] += sp['secs']
        else:
            other_parts[sp['name']] = other_parts.get(sp['name'], 0) + sp['secs']
    mapped = sum(v for k, v in secs.items() if k != 'other')
    secs['other'] = max(pass_total - mapped, 0.0)
    gap = pass_total - mapped - sum(other_parts.values())
    other_parts['untraced gap vs printed pass time'] = gap
    return dict(path=path, pass_total=pass_total, secs=secs, sub=sub, other_parts=other_parts,
                passes=passes, mapped_pct=100 * mapped / pass_total if pass_total else 0)


def main():
    args = sys.argv[1:]
    out = None
    if '--csv' in args:
        i = args.index('--csv'); out = args[i + 1]; del args[i:i + 2]
    rows = []
    for p in args:
        b = breakdown(p)
        name = os.path.basename(os.path.dirname(os.path.abspath(p))) + '/' + os.path.basename(p)[:-4]
        print(f"\n== {name}: traced (last) pass {b['pass_total']:.4f} s; printed passes {b['passes']}; "
              f"mapped stages cover {b['mapped_pct']:.1f}%")
        for s in STAGES:
            v = b['secs'][s]
            print(f"  {s:24s} {v:9.4f} s  {100 * v / b['pass_total']:6.2f}%")
        for k, v in b['sub'].items():
            print(f"    ({k:22s} {v:9.4f} s  {100 * v / b['pass_total']:6.2f}%)")
        print("  'other' made of: " + '; '.join(f"{k} {v*1e3:.2f} ms" for k, v in b['other_parts'].items() if abs(v) > 1e-9))
        for s in STAGES:
            rows.append(dict(log=name, stage=s, secs=round(b['secs'][s], 6),
                             pct=round(100 * b['secs'][s] / b['pass_total'], 3), pass_total_s=b['pass_total'],
                             note=('; '.join(f"{k} {v*1e3:.2f} ms" for k, v in b['other_parts'].items() if abs(v) > 1e-9)
                                   if s == 'other' else '')))
        for k, v in b['sub'].items():
            rows.append(dict(log=name, stage=k, secs=round(v, 6), pct=round(100 * v / b['pass_total'], 3),
                             pass_total_s=b['pass_total'], note='sub-stage of commit (not additive)'))
    if out:
        mode = 'w'
        with open(out, mode, newline='') as f:
            w = csv.DictWriter(f, fieldnames=['log', 'stage', 'secs', 'pct', 'pass_total_s', 'note'])
            w.writeheader(); w.writerows(rows)


if __name__ == '__main__':
    main()

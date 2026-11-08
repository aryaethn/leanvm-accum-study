#!/usr/bin/env python3
"""Summarise leanvm run logs (written by run.sh) into summary.csv rows.
usage: parse_runs.py OUT.csv LOG [LOG ...]   (a column 'variant' is taken from the log's cmd path)"""
import re, sys, csv, os, statistics
ANSI = re.compile(r'\x1b\[[0-9;]*m')

def passes_of(t):
    m = re.search(r'passes\s*:\s*([^\n]*)', t)
    ps = [float(x) for x in re.findall(r'([\d.]+) s(?![a-z])', m.group(1))] if m else []
    if len(ps) < 3:   # recursion: last (traced) pass is printed on its own line
        m2 = re.search(r'\n +([\d.]+) s *\n', t)
        if m2: ps.append(float(m2.group(1)))
    return ps

def swap_used(line): return float(re.search(r'used = ([\d.]+)M', line).group(1))

def row(path):
    t = ANSI.sub('', open(path, errors='replace').read()).replace('\r', '\n')
    t = re.sub(r'[^\n]*generating leanXMSS signers[^\n]*', '', t)
    g = lambda p: (re.search(p, t) or [None, None])[1]
    cmd = g(r'# cmd: (.*)')
    ps = passes_of(t)
    sb, sa = g(r'# swap_before: (.*)'), g(r'# swap_after: (.*)')
    d = round(swap_used(sa) - swap_used(sb))
    power = g(r'# power: (.*)') or ''
    flags = ['AC' if 'discharging' not in power else 'BATTERY']
    if d > 256: flags.append('memory-pressured')
    n = re.search(r'--n (\d+)', cmd); xm = re.search(r'--xmss (\d+)', cmd); ml = re.search(r'--xmss-per-leaf (\d+)', cmd)
    lr = re.search(r'--leaf-log-inv-rate (\d+)', cmd); r = re.search(r'--log-inv-rate (\d+)', cmd)
    return dict(
        log=os.path.basename(path)[:-4], binary=('rebuild' if 'target-rebuild' in cmd else 'baseline'),
        workload=cmd.split('leanvm ')[-1].split()[0], n_children=n.group(1) if n else '',
        size=(xm or ml).group(1) if (xm or ml) else '', leaf_rate=lr.group(1) if lr else '',
        outer_rate=r.group(1) if r else '', params=cmd.split('leanvm ', 1)[-1].replace(' --tracing', ''),
        cycles=g(r'cycles \(VM steps\)\s*:\s*([\d,]+)'), per_opcode_line=g(r'details\s*:\s*([^\n]*)'),
        total_committed_log2=g(r'TOTAL_COMMITTED 2\^([\d.]+)'), proof_kib=g(r'proof size\s*:\s*([\d.]+) KiB'),
        prove_s_each_repeat=' '.join(map(str, ps)), prove_s_median=statistics.median(ps) if ps else '',
        printed_mean=g(r'proving(?: time)?\s*:\s*([^\n]*?)\s{2,}'), leanvm_peak_gib=g(r'peak memory ([\d.]+) GiB'),
        os_max_rss_gib=round(int(g(r'(\d+)\s+maximum resident set size')) / 2**30, 3),
        os_peak_footprint_gib=round(int(g(r'(\d+)\s+peak memory footprint')) / 2**30, 3),
        swap_delta_mib=d, verify_ms=g(r'verifying\s*:\s*([\d.]+) ms'), wall_s=g(r'([\d.]+) real'),
        flags='; '.join(flags))

if __name__ == '__main__':
    out, logs = sys.argv[1], sys.argv[2:]
    rows = [row(p) for p in logs]
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(r['log'], r['cycles'], r['total_committed_log2'], r['proof_kib'], r['prove_s_each_repeat'], r['prove_s_median'],
              r['leanvm_peak_gib'], r['os_max_rss_gib'], r['os_peak_footprint_gib'], r['swap_delta_mib'], r['verify_ms'], r['wall_s'], r['flags'], sep=' | ')

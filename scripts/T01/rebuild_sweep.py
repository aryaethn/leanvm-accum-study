#!/usr/bin/env python3
"""T01 step 4d/4e: baseline drift check, then variant aggregate sweep with footprint prediction (stop > 9.5 GiB)."""
import subprocess, time, os, re
H = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))  # repository root
R = H + '/results/T01'; S = H + '/scripts/T01/run.sh'
BASE = H + '/upstream/leanMultisig/target/release/leanvm'
VAR = H + '/upstream/leanMultisig/target-rebuild/release/leanvm'
LIMIT = 9.5 * 2**30
def footprint(name):
    t = open(f'{R}/{name}.log').read()
    return int(re.search(r'(\d+)\s+peak memory footprint', t).group(1))
def run(binary, name, n):
    time.sleep(30)
    subprocess.run([S, R, binary, name, 'aggregate', '--xmss', str(n), '--log-inv-rate', '2', '--repeat', '3', '--tracing'])
    return footprint(name)
run(BASE, 'drift_baseline_aggregate_xmss250_lir2', 250); print('drift done', flush=True)
last = None
for n in (250, 500, 1000, 1500):
    if last:
        pred = last[1] * n / last[0]
        if pred > LIMIT:
            msg = f'SKIP variant N={n}: predicted footprint {pred/2**30:.2f} GiB > 9.5 GiB'
            print(msg, flush=True); open(R + '/skipped.txt', 'a').write(msg + '\n'); break
    last = (n, run(VAR, f'rebuild_aggregate_xmss{n}_lir2', n))
    print('variant', n, f'{last[1]/2**30:.2f} GiB', flush=True)
print('DONE')

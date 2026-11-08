#!/usr/bin/env python3
"""T03 step 4: baseline / V1 / V2 recursion sweep, interleaved per n. 30 s sleep before every run.
V1 and V2 are UNSOUND measurement-only variants (research/d3-v1, research/d3-v2)."""
import subprocess, time, os
H = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))  # repository root
S = H + '/scripts/T03/run.sh'; R = H + '/results/T03/runs2'
U = H + '/upstream/leanMultisig'
BIN = {'base': U + '/target/release/leanvm', 'v1': U + '/target-d3v1/release/leanvm', 'v2': U + '/target-d3v2/release/leanvm'}
os.makedirs(R, exist_ok=True)
for n in (2, 4, 6):
    for v in ('base', 'v1', 'v2'):
        time.sleep(30)
        subprocess.run([S, R, BIN[v], f'{v}_n{n}', 'recursion', '--n', str(n), '--xmss-per-leaf', '250',
                        '--leaf-log-inv-rate', '2', '--log-inv-rate', '2', '--repeat', '3', '--tracing'])
        print('done', v, n, time.strftime('%H:%M:%S'), flush=True)
print('DONE')

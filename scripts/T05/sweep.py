#!/usr/bin/env python3
"""T05 step 5: baseline / V3 / V4 recursion sweep, interleaved per n, two passes (runs/, runs2/).
30 s sleep before every run. V3 and V4 are UNSOUND measurement-only variants
(research/d3-v3, research/d3-v4)."""
import subprocess, time, os
H = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))  # repository root
S = H + '/scripts/T05/run.sh'
U = H + '/upstream/leanMultisig'
BIN = {'base': U + '/target/release/leanvm', 'v3': U + '/target-d3v3/release/leanvm', 'v4': U + '/target-d3v4/release/leanvm'}
for rdir in ('runs', 'runs2'):
    R = H + '/results/T05/' + rdir
    os.makedirs(R, exist_ok=True)
    for n in (2, 4, 6):
        for v in ('base', 'v3', 'v4'):
            time.sleep(30)
            subprocess.run([S, R, BIN[v], f'{v}_n{n}', 'recursion', '--n', str(n), '--xmss-per-leaf', '250',
                            '--leaf-log-inv-rate', '2', '--log-inv-rate', '2', '--repeat', '3', '--tracing'])
            print('done', rdir, v, n, time.strftime('%H:%M:%S'), flush=True)
print('DONE')

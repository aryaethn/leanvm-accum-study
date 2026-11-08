#!/usr/bin/env python3
"""T01 step 3: n-to-1 recursion sweep. 30 s sleep before every run; no stop rule (flag only)."""
import subprocess, time, os
H = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))  # repository root
S = H + '/scripts/T01/run.sh'; R = H + '/results/T01'
B = H + '/upstream/leanMultisig/target/release/leanvm'
for rate in (1, 2):
    for n in (2, 4, 6, 8):
        time.sleep(30)
        subprocess.run([S, R, B, f'recursion_n{n}_m250_leaflir2_lir{rate}', 'recursion', '--n', str(n),
                        '--xmss-per-leaf', '250', '--leaf-log-inv-rate', '2', '--log-inv-rate', str(rate),
                        '--repeat', '3', '--tracing'])
        print('done', n, rate, flush=True)
print('DONE')

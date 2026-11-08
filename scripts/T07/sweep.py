#!/usr/bin/env python3
"""T07 steps 3-4: baseline / V5 (UNSOUND) recursion sweep.
Step 3: two passes (runs/, runs2/), n in 2, 4, 6, interleaved base then v5 per n, --repeat 3 --tracing.
Step 4: n=8, base then v5, --repeat 1 --tracing (runs8/; cycles, TOTAL_COMMITTED, mu only).
30 s sleep before every run. run.sh logs the command, date, power, swap before/after."""
import subprocess, time, os
H = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))  # repository root
S = H + '/scripts/T07/run.sh'
U = H + '/upstream/leanMultisig'
BIN = {'base': U + '/target/release/leanvm', 'v5': U + '/target-d3v5/release/leanvm'}
ARGS = ['--xmss-per-leaf', '250', '--leaf-log-inv-rate', '2', '--log-inv-rate', '2', '--tracing']
plan = [(r, n, v, 3) for r in ('runs', 'runs2') for n in (2, 4, 6) for v in ('base', 'v5')]
plan += [('runs8', 8, v, 1) for v in ('base', 'v5')]
for rdir, n, v, rep in plan:
    R = H + '/results/T07/' + rdir
    os.makedirs(R, exist_ok=True)
    time.sleep(30)
    subprocess.run([S, R, BIN[v], f'{v}_n{n}', 'recursion', '--n', str(n), *ARGS[:6], '--repeat', str(rep), ARGS[6]])
    print('done', rdir, v, n, time.strftime('%H:%M:%S'), flush=True)
print('DONE', flush=True)

#!/usr/bin/env python3
"""Count sweep (T07b step 8): n=2..8 x {base, b0u, v6, v6u}, --repeat 1, DBG_TABLES=1, 5 s sleep."""
import subprocess, time, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))  # repository root
REPO = f"{ROOT}/upstream/leanMultisig"
RES = f"{ROOT}/results/T07b/sweep"
RUN = f"{ROOT}/scripts/T07b/run.sh"
BINS = {"base": "target-dbg", "b0u": "target-b0u", "v6": "target-d3v6", "v6u": "target-d3v6u"}
os.makedirs(RES, exist_ok=True)
for n in range(2, 9):
    for v, d in BINS.items():
        time.sleep(5)
        args = ["recursion", "--n", str(n), "--xmss-per-leaf", "250", "--leaf-log-inv-rate", "2", "--log-inv-rate", "2", "--repeat", "1"]
        print(f"{time.strftime('%H:%M:%S')} {v} n={n}", flush=True)
        subprocess.run([RUN, RES, f"{REPO}/{d}/release/leanvm", f"{v}_n{n}"] + args, check=True)
print("done", flush=True)

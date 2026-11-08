#!/usr/bin/env python3
"""T07b Part C: timing of n=4 and n=6 for base, B0U, V6, V6U, 2 passes interleaved, --repeat 3 --tracing,
30 s sleep before each run; swap recorded before and after every run. DBG_TABLES unset (no diagnostic prints)."""
import os
import subprocess
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))  # repository root
REPO = f"{ROOT}/upstream/leanMultisig"
OUT = f"{ROOT}/results/T07b/timing"
BINS = {"base": "target-dbg", "b0u": "target-b0u", "v6": "target-d3v6", "v6u": "target-d3v6u"}
os.makedirs(OUT, exist_ok=True)


def swap():
    return subprocess.check_output(["sysctl", "-n", "vm.swapusage"]).decode().strip()


with open(f"{OUT}/swap_log.txt", "w") as sl:
    for p in (1, 2):
        for n in (4, 6):
            for v, d in BINS.items():
                time.sleep(30)
                name = f"p{p}_{v}_n{n}"
                log = f"{OUT}/{name}.log"
                cmd = ["/usr/bin/time", "-l", f"{REPO}/{d}/release/leanvm", "recursion", "--n", str(n), "--xmss-per-leaf", "250", "--leaf-log-inv-rate", "2", "--log-inv-rate", "2", "--repeat", "3", "--tracing"]
                s0 = swap()
                t0 = time.strftime("%H:%M:%S")
                sl.write(f"{name} start {t0} swap: {s0}\n")
                sl.flush()
                print(f"{t0} {name} swap {s0}", flush=True)
                with open(log, "w") as f:
                    f.write(f"# cmd: {' '.join(cmd)}\n# date: {time.ctime()}\n# swap_before: {s0}\n")
                    f.flush()
                    subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
                s1 = swap()
                with open(log, "a") as f:
                    f.write(f"# swap_after: {s1}\n")
                sl.write(f"{name} end {time.strftime('%H:%M:%S')} swap: {s1}\n")
                sl.flush()
print("done", flush=True)

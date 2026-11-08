#!/usr/bin/env python3
"""T07c timing driver. Usage: run_timing.py <pass> <name> [<name>...]"""
import subprocess, sys, time, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))  # repository root
B = f"{ROOT}/upstream/leanMultisig/target-dbg/release/leanvm"
V = f"{ROOT}/upstream/leanMultisig/target-d3v6/release/leanvm"
OUT = f"{ROOT}/results/T07c/runs"
def R(b, n, x=250):
    return (True, [b, "recursion", "--n", str(n), "--xmss-per-leaf", str(x), "--leaf-log-inv-rate", "2", "--log-inv-rate", "2", "--repeat", "3", "--tracing"])
CFG = {
 "leaf_250": (False, [B, "aggregate", "--xmss", "250", "--log-inv-rate", "2", "--repeat", "3"]),
 "leaf_300": (False, [B, "aggregate", "--xmss", "300", "--log-inv-rate", "2", "--repeat", "3"]),
 "base_n4": R(B,4), "v6_n4": R(V,4), "base_n5": R(B,5), "v6_n5": R(V,5),
 "base_n6": R(B,6), "v6_n6": R(V,6),
 "base_n5_300": R(B,5,300), "v6_n5_300": R(V,5,300),
}
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout.strip()
p = sys.argv[1]
for name in sys.argv[2:]:
    dbg, cmd = CFG[name]
    time.sleep(30)
    log = f"{OUT}/{name}_p{p}.log"
    with open(log, "w") as f:
        f.write("### swap_start: " + sh("sysctl vm.swapusage") + "\n")
        f.write("### therm_start: " + sh("pmset -g therm").replace("\n", " | ") + "\n")
        f.write("### cmd: " + ("DBG_TABLES=1 " if dbg else "") + " ".join(cmd).replace(ROOT + "/", "") + "\n")
        f.flush()
        env = dict(os.environ)
        if dbg: env["DBG_TABLES"] = "1"
        t0 = time.time()
        r = subprocess.run(["/usr/bin/time", "-l"] + cmd, cwd=f"{ROOT}/upstream/leanMultisig", env=env, stdout=f, stderr=subprocess.STDOUT)
        f.write(f"\n### exit: {r.returncode} wall: {time.time()-t0:.1f}s\n")
        f.write("### swap_end: " + sh("sysctl vm.swapusage") + "\n")
        f.write("### therm_end: " + sh("pmset -g therm").replace("\n", " | ") + "\n")
    print(name, p, "done", r.returncode, flush=True)

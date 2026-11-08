#!/usr/bin/env python3
"""Parse DBG_TABLES node records from run logs and recompute TOTAL_COMMITTED from the source formula.

Formula (crates/leanvm_core/src/cpu/layout.rs col_kappa_sources / witness.rs placements_of):
  TC = 4*2^h + 2^kbc + 2^(SLOT_LOG+tau_K) + sum_t w_t * 2^tau_t,
  tau_t = max(ceil log2 rows_t, floor_t);  h = padded memory log; kbc = padded bytecode log;
  mu = max(ceil log2 TC, MIN_MU=15), with the aggregation floor min_log_committed = 22 (memory doubled).
"""
import re, sys, math, csv, glob, os
W = dict(XOR=15, MUL=15, SET=8, DEREF=15, JUMP=14, KECCAK=26)
SLOT_LOG = 6
ORDER = ["XOR", "MUL", "SET", "DEREF", "JUMP", "KECCAK"]

def clog2(n):
    return 0 if n <= 1 else math.ceil(math.log2(n))

def parse(path):
    txt = open(path, errors="replace").read()
    recs = {}
    head = None
    for ln in txt.splitlines():
        if not ln.startswith("DBG_TABLES kind=node"):
            continue
        d = dict(re.findall(r"(\w+)=(\S+)", ln))
        if "cycles" in d:
            head = {k: (float(v) if "." in v else (int(v) if re.fullmatch(r"-?\d+", v) else v)) for k, v in d.items()}
            head["tables"] = {}
            head["shared"] = {}
        elif "table" in d:
            head["tables"][d["table"]] = {k: int(v) for k, v in d.items() if k not in ("table", "kind")}
        elif "shared" in d:
            head["shared"][d["shared"]] = {k: int(v) for k, v in d.items() if k not in ("shared", "kind")}
        elif "sum_contrib" in d:
            head["sum_contrib"] = int(d["sum_contrib"])
            head["placed_minus_sum"] = int(d["placed_minus_sum"])
            recs["last"] = head
    m = re.search(r"TOTAL_COMMITTED 2\^([0-9.]+)", txt)
    pkib = re.search(r"proof size\s*:\s*([0-9.]+) KiB", txt)
    return recs.get("last"), (float(m.group(1)) if m else None), (float(pkib.group(1)) if pkib else None), txt

def recompute(r):
    h = r["log_mem"]
    kbc = clog2(r["prog_len"])
    taus = {t: max(clog2(r["tables"][t]["rows"]), (9 if t == "KECCAK" else 0)) for t in ORDER}
    tc = 4 * (1 << h) + (1 << kbc) + (1 << (SLOT_LOG + taus["KECCAK"])) + sum(W[t] * (1 << taus[t]) for t in ORDER)
    mu = max(clog2(tc), 15)
    return tc, mu, taus

def line(lbl, n, r, printed):
    tc, mu, taus = recompute(r)
    tc_log = math.log2(tc)
    res = None if printed is None else tc_log - printed
    tab = " ".join(f"{t}={r['tables'][t]['rows']}/{taus[t]}" for t in ORDER)
    print(f"{lbl:10s} n={n} cycles={r['cycles']:>8} TC(printed)=2^{printed} TC(placed)={r['placed']} TC(formula)={tc} mu(rule)={mu} mu(trace)={r['mu']} lanes={r['n_lanes']} "
          f"formula-placed={tc - r['placed']} log(formula)={tc_log:.6f} formula-printed={res} | {tab} h={r['log_mem']} mem_used={r['mem_used']} kbc={clog2(r['prog_len'])} code={r['code_len']}")
    return tc

if __name__ == "__main__":
    d = sys.argv[1]
    for lbl in sys.argv[2:]:
        for n in [2, 4, 6, 8]:
            r, p, pk, _ = parse(f"{d}/{lbl}_n{n}.log")
            line(lbl, n, r, p)

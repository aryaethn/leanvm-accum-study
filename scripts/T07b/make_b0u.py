#!/usr/bin/env python3
"""T07b B0U: semantics-preserving loop unrolling in the per-child verifier path of the
recursion guest. usage: make_b0u.py GUEST_PATH

Applies exact-string edits to crates/rec_aggregation/guests/lean_ethereum.py @ df7d122:
  B0U_ARM (open_stacked m_idx = 10, i.e. rate 2, committed mu 25: the only arm this
  configuration executes for leaf children) replaces, by compile-time dispatch only,
    (1) the position-squeeze mul_range loop (L1566) by unroll(0, LIG_SQUEEZES[ml]);
    (2) the extension-row Merkle query mul_range loop of opening_queries (L1410) by unroll,
        for WHIR levels 1..4 (level 0's base-field pair loop stays a mul_range loop:
        56 iterations x 596 instructions exceed the bytecode budget).
Every other arm keeps its mul_range loops. Trip counts are compile-time constants
(LIG_SQUEEZES[ml], n_queries); no check is moved, removed or reordered; runtime cells written
by the loops keep the same addresses (xs -> GEN**i is exact).
"""
import sys

path = sys.argv[1]
s = open(path).read()
MARK = "T07b B0U (semantics-preserving unroll)"
B0U_ARM = 10
N_ARMS = 28
MAX_LEVELS = 6
QUERIES_L1_L4 = {1: 45, 2: 28, 3: 21, 4: 16}
import os as _os
# per-loop accounting builds: B0U_ONLY=sq|q1|q2|q3|q4 applies one edit (see per_loop_b0u.sh)
_ONLY = _os.environ.get("B0U_ONLY", "")
if _ONLY:
    QUERIES_L1_L4 = {int(_ONLY[1]): QUERIES_L1_L4[int(_ONLY[1])]} if _ONLY.startswith("q") else {}


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# ---- constants table: per (arm, level), the iteration count to unroll in opening_queries
# (0 = keep the runtime mul_range loop). Placed before the defs (zkDSL requires constants first).
tab = [0] * (N_ARMS * MAX_LEVELS)
for lvl, q in QUERIES_L1_L4.items():
    tab[B0U_ARM * MAX_LEVELS + lvl] = q
tab_s = "[" + ", ".join(map(str, tab)) + "]"
import re as _re
first_def = _re.search(r"^(?:@|def )", s, _re.M).start()
s = s[:first_def] + f"B0U_ARM = {B0U_ARM}\nB0U_UNROLL_ITERS = {tab_s}\n\n" + s[first_def:]

# ---- (1) L1566 position-squeeze loop ----
old_sq = """        for xs in mul_range(1, GEN ** LIG_SQUEEZES[ml]):
            # a loop body captures free names BY VALUE, so the compile-time aliases
            # are rebound here (m_idx and lvl are substituted literals)
            depth = LIG_TREE_DEPTH[m_idx * LIG_MAX_LEVELS + lvl]
            pos_off = LIG_POSITIONS_OFF[m_idx * LIG_MAX_LEVELS + lvl]
            row = sqz * xs ** FS_CELLS
            row_cap = fs_load(row, 0, 1)
            no_rate = StackBuf(8)
            row_sp, packed_word = squeeze(row_cap, no_rate, 0)
            fs_store(row * GEN ** FS_CELLS, 0, 1, row_sp)
            query_ptr = xs ** (FIELD_BITS // depth)
            cap_depth = LIG_CAP_DEPTH[m_idx * LIG_MAX_LEVELS + lvl]
            decode_query_windows(packed_word, query_positions * GEN ** pos_off * query_ptr, query_win_ptrs * GEN ** pos_off * query_ptr, win_tabs, depth, cap_depth)
"""
new_sq = old_sq if (_ONLY and _ONLY != "sq") else f"""        # {MARK}: arm B0U_ARM only; LIG_SQUEEZES[ml] is compile-time.
        if const(m_idx == B0U_ARM):
            for sq_i in unroll(0, LIG_SQUEEZES[ml]):
                row = sqz * GEN ** (sq_i * FS_CELLS)
                row_cap = fs_load(row, 0, 1)
                no_rate = StackBuf(8)
                row_sp, packed_word = squeeze(row_cap, no_rate, 0)
                fs_store(row * GEN ** FS_CELLS, 0, 1, row_sp)
                sq_ptr = GEN ** (sq_i * (FIELD_BITS // LIG_TREE_DEPTH[ml]))
                decode_query_windows(packed_word, query_positions * GEN ** LIG_POSITIONS_OFF[ml] * sq_ptr, query_win_ptrs * GEN ** LIG_POSITIONS_OFF[ml] * sq_ptr, win_tabs, LIG_TREE_DEPTH[ml], LIG_CAP_DEPTH[ml])
        else:
""" + "".join("    " + l + "\n" for l in old_sq.rstrip("\n").split("\n"))
if new_sq is not old_sq:
    rep(old_sq, new_sq)

# ---- (2) L1410 Merkle query loop ----
rep("def opening_queries(cap, flags, lam, lam_n, query_win_ptrs, row_eq_weights, n_iters_g, odd: Const, base: Const, interleave: Const, leaf_cells: Const, depth: Const, cap_depth: Const):\n",
    "def opening_queries(cap, flags, lam, lam_n, query_win_ptrs, row_eq_weights, n_iters_g, odd: Const, base: Const, interleave: Const, leaf_cells: Const, depth: Const, cap_depth: Const, unroll_n: Const):\n")
old_loop = """    for xi in mul_range(1, n_iters_g):
        if base == 1:
            bit_ptrs = query_win_ptrs * xi * xi
            d0 = opening_query(cap, flags, row_eq_weights, bit_ptrs[GEN ** odd], base, interleave, leaf_cells, depth, cap_depth)
            d1 = opening_query(cap, flags, row_eq_weights, bit_ptrs[GEN ** (odd + 1)], base, interleave, leaf_cells, depth, cap_depth)
            chain[xi * GEN] = ((chain[xi] + d0) * mu + d1) * mu
        else:
            d = opening_query(cap, flags, row_eq_weights, query_win_ptrs[xi], base, interleave, leaf_cells, depth, cap_depth)
            chain[xi * GEN] = (chain[xi] + d) * mu
"""
new_loop = f"""    # {MARK}: unroll_n != 0 only for extension-row levels of arm B0U_ARM (n_iters_g = GEN ** unroll_n).
    if const(unroll_n != 0):
        for iq in unroll(0, unroll_n):
            d = opening_query(cap, flags, row_eq_weights, query_win_ptrs[GEN ** iq], base, interleave, leaf_cells, depth, cap_depth)
            chain[GEN ** (iq + 1)] = (chain[GEN ** iq] + d) * mu
    else:
""" + "".join("    " + l + "\n" for l in old_loop.rstrip("\n").split("\n"))
rep(old_loop, new_loop)
rep("depth, cap_depth)\n\n        cap_depth = LIG_CAP_DEPTH[ml]" if False else
    "n_queries % 2 * (1 // (lvl + 1)), 1 // (lvl + 1), interleave, LIG_LEAF_CELLS[ml], depth, cap_depth)\n",
    "n_queries % 2 * (1 // (lvl + 1)), 1 // (lvl + 1), interleave, LIG_LEAF_CELLS[ml], depth, cap_depth, B0U_UNROLL_ITERS[ml])\n")

open(path, "w").write(s)
print(f"wrote B0U to {path}")

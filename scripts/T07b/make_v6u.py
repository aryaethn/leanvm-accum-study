#!/usr/bin/env python3
"""T07b V6U (UNSOUND, measurement only): V6 + the B0U unrolling, same loops and method.
Applied to the V6 guest. Unrolls, arm 10 only:
  (1) position-squeeze loops in v6_child0 and v6_child_rest;
  (2) child 0's extension-row Merkle query loops of opening_queries at levels 1..3
      (level 4 left as a loop so the bytecode stays <= 2^19; see the report);
  (3) the level-1 query loop of v6_opening_queries_free (children >= 1, 45 iterations).
Usage: make_v6u.py GUEST_PATH
"""
import re
import sys
path = sys.argv[1]
s = open(path).read()
MARK = "T07b V6U (UNSOUND; V6 + B0U unrolling)"
L_ITERS = {1: 45, 2: 28, 3: 21}
N_ARMS, MAX_LEVELS = 28, 6
ARM = 10

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)

tab = [0] * (N_ARMS * MAX_LEVELS)
for lvl, q in L_ITERS.items():
    tab[ARM * MAX_LEVELS + lvl] = q
first_def = re.search(r"^(?:@|def )", s, re.M).start()
s = s[:first_def] + "B0U_UNROLL_ITERS = [" + ", ".join(map(str, tab)) + "]\n\n" + s[first_def:]

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
new_sq = f"""        # {MARK}: position squeezes (arm 10 functions only).
        for sq_i in unroll(0, LIG_SQUEEZES[ml]):
            row = sqz * GEN ** (sq_i * FS_CELLS)
            row_cap = fs_load(row, 0, 1)
            no_rate = StackBuf(8)
            row_sp, packed_word = squeeze(row_cap, no_rate, 0)
            fs_store(row * GEN ** FS_CELLS, 0, 1, row_sp)
            sq_ptr = GEN ** (sq_i * (FIELD_BITS // LIG_TREE_DEPTH[ml]))
            decode_query_windows(packed_word, query_positions * GEN ** LIG_POSITIONS_OFF[ml] * sq_ptr, query_win_ptrs * GEN ** LIG_POSITIONS_OFF[ml] * sq_ptr, win_tabs, LIG_TREE_DEPTH[ml], LIG_CAP_DEPTH[ml])
"""
rep(old_sq, new_sq, count=2)

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
new_loop = f"""    # {MARK}: unroll_n != 0 only for extension-row levels of arm 10's child-0 path.
    if const(unroll_n != 0):
        for iq in unroll(0, unroll_n):
            d = opening_query(cap, flags, row_eq_weights, query_win_ptrs[GEN ** iq], base, interleave, leaf_cells, depth, cap_depth)
            chain[GEN ** (iq + 1)] = (chain[GEN ** iq] + d) * mu
    else:
""" + "".join("    " + l + "\n" for l in old_loop.rstrip("\n").split("\n"))
rep(old_loop, new_loop)

# every opening_queries call passes the table entry (0 for all but child 0 / arm 10 L1..L3)
n = len(re.findall(r"opening_queries\(cap, flags, lam, lam_pow, .*, LIG_LEAF_CELLS\[ml\], depth, cap_depth\)", s))
s = re.sub(r"(opening_queries\(cap, flags, lam, lam_pow, .*, LIG_LEAF_CELLS\[ml\], depth, cap_depth)\)", r"\1, B0U_UNROLL_ITERS[ml])", s)
print(f"opening_queries call sites patched: {n}")

old_free = """    for xi in mul_range(1, n_iters_g):
        cap_q = HeapBuf(GEN ** (2 ** (cap_depth + 2)))
        flags_q = HeapBuf(GEN ** (2 ** cap_depth))
        d = opening_query(cap_q, flags_q, row_eq_weights, query_win_ptrs[xi], 0, interleave, leaf_cells, depth, cap_depth)
        chain[xi * GEN] = (chain[xi] + d) * mu
"""
new_free = f"""    # {MARK}: the 45 level-1 queries unrolled.
    for iq in unroll(0, 45):
        cap_q = HeapBuf(GEN ** (2 ** (cap_depth + 2)))
        flags_q = HeapBuf(GEN ** (2 ** cap_depth))
        d = opening_query(cap_q, flags_q, row_eq_weights, query_win_ptrs[GEN ** iq], 0, interleave, leaf_cells, depth, cap_depth)
        chain[GEN ** (iq + 1)] = (chain[GEN ** iq] + d) * mu
"""
rep(old_free, new_free)
open(path, "w").write(s)
print(f"wrote V6U to {path}")

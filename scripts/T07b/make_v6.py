#!/usr/bin/env python3
"""T07b: write the UNSOUND, measurement-only guest variant V6 (closer cost emulation of B'-L1).

usage (repo root, on a guest already patched to V5): make_v6.py GUEST_PATH

Replaces V5's open_stacked for arm V6_ARM (m_idx = 10: rate 2, mu 25, the only arm the leaves of
this configuration reach) by two paths selected at runtime by the child index xc:

  child 0 (xc == 1): the baseline open_stacked, plus T_B header + beta (child 0 once), k extra
    level-1 fold rounds (sink sponge), per-child combine work.
  children >= 1: keep level 0 in full, their own level-1 lambda, cap check and Merkle openings at
    the shared positions (windows, row eq weights via heap pointers published by child 0). They do
    no level-1+ folds, no level-root / OOD / nonce / position squeezes for L1.., no final message
    read, no residual/OOD-eq except their own level-1 OOD-eq term. Hints are popped at 0 cycles.
    Fold / tail challenges and the point are child 0's (read through shared pointers).

UNSOUND: child>=1's shared values are unchecked (the terminal check holds vacuously).
"""
import os
import re
import subprocess
import sys

path = sys.argv[1]
s = open(path).read()
U = "T07b V6 (UNSOUND, measurement only)"
ARM = 10
Q1 = 45  # LIG_QUERIES at level 1 of arm 10
BASE_REV = "df7d122abbe25cf12e5c8ae992ce6d3505f75372"
GUEST_REL = "crates/rec_aggregation/guests/lean_ethereum.py"
base = subprocess.check_output(["git", "show", f"{BASE_REV}:{GUEST_REL}"]).decode()

SHARE = {"WINS": 0, "ROWEQ": 1, "FOLDS": 2, "TAIL": 3, "POINT": 4, "POINT1": 5, "LQS": 6, "SINK": 7, "ACC": 8, "BETA": 9, "K": 10, "TERM": 11}


def rep(old, new, count=1, target=None):
    global s
    if target is not None:
        assert target.count(old) == count, (target.count(old), old[:100])
        return target.replace(old, new)
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)


# ---- baseline open_stacked text ----
sig = "def open_stacked(m_idx: Const, fs0, fs1, fs2, fs3, fs4, target, commit_root_0, commit_root_1, cursor):\n"
ret = "    return sumcheck_target, point, point1, inner_chain[GEN ** n_levels] + ood_inner, yr_at_tail\n"
a = base.index(sig)
b = base.index(ret, a) + len(ret)
fn = base[a:b]

hdr_mark = "    n_levels = LIG_N_LEVELS[m_idx]\n"
loop_mark = "    for lvl in unroll(0, n_levels):\n        ml = m_idx * LIG_MAX_LEVELS + lvl\n        n_queries = LIG_QUERIES[ml]\n        depth = LIG_TREE_DEPTH[ml]\n"
tail_mark = "    # ---- finish the sumcheck over the tail coordinates ----\n"
resid_mark = "    basis_d = HeapBuf(GEN ** (n_levels * LIG_LOG_MSG_COLS_CAP))\n"
ood_mark = "    # Explicit OOD eq bases at the same terminal point.\n"

i_hdr = fn.index(hdr_mark)
i_loop = fn.index(loop_mark)
i_tail = fn.index(tail_mark)
i_resid = fn.index(resid_mark)
i_ood = fn.index(ood_mark)
i_ret = fn.index(ret)
assert i_hdr < i_loop < i_tail < i_resid < i_ood < i_ret

header = fn[i_hdr:i_loop]
loop_body = fn[i_loop:i_tail]
resid_part = fn[i_resid:i_ood]
ood_part = fn[i_ood:i_ret]

# ---- child 0: baseline text + publishing + new work ----
ch0 = fn.replace(sig, "def v6_child0(m_idx: Const, fs0, fs1, fs2, fs3, fs4, target, commit_root_0, commit_root_1, cursor, xc, share):\n"
                 f"    # {U}: child 0 runs the full opening; it publishes level-1 pointers and runs T_B work.\n")
ch0 = rep(hdr_mark, hdr_mark + "    v6_done_start = v6_batch_start(share, fs0, fs1, fs2, fs3, fs4)\n", target=ch0)
# k extra level-1 fold rounds, after level-1's folds
ch0 = rep("""            round_quad_b = sumcheck_target + round_quad_a

        if lvl == yr_level:
            word0, fs0, fs1, fs2, fs3, fs4, msg_cursor, q_nonce = opening_final_message(""",
          """            round_quad_b = sumcheck_target + round_quad_a

        if const(lvl == 1):
            v6_done_rounds = v6_k_rounds(share, cursor)  # T07b@v6k

        if lvl == yr_level:
            word0, fs0, fs1, fs2, fs3, fs4, msg_cursor, q_nonce = opening_final_message(""", target=ch0)
# publish level-1 windows and row eq weights
ch0 = rep("        opening_row_weights(fold_challenges * GEN ** folds_off, row_eq_weights, LIG_FOLDS[ml], 1 // (lvl + 1))\n",
          "        opening_row_weights(fold_challenges * GEN ** folds_off, row_eq_weights, LIG_FOLDS[ml], 1 // (lvl + 1))\n"
          "        if const(lvl == 1):\n"
          "            share[GEN ** V6_ROWEQ] = row_eq_weights  # T07b@v6pub\n"
          "            share[GEN ** V6_WINS] = query_win_ptrs * GEN ** pos_off  # T07b@v6pub\n", target=ch0)
ch0 = rep("n_queries % 2 * (1 // (lvl + 1)), 1 // (lvl + 1), interleave, LIG_LEAF_CELLS[ml], depth, cap_depth)\n",
          "n_queries % 2 * (1 // (lvl + 1)), 1 // (lvl + 1), interleave, LIG_LEAF_CELLS[ml], depth, cap_depth)\n"
          "        if const(lvl == 1):\n"
          "            share[GEN ** V6_LQS] = level_query_sum  # T07b@v6pub\n", target=ch0)
ch0 = rep(ret, f"""    # {U}: child 0 publishes challenges and the terminal point, then the per-child combine work.
    share[GEN ** V6_FOLDS] = fold_challenges  # T07b@v6pub
    share[GEN ** V6_TAIL] = tail_challenges  # T07b@v6pub
    share[GEN ** V6_POINT] = point  # T07b@v6pub
    share[GEN ** V6_POINT1] = point1  # T07b@v6pub
    v6_done_common = v6_common(share, xc, commit_root_0, commit_root_1, share[GEN ** V6_LQS])
""" + ret, target=ch0)

# ---- children >= 1 ----
loop0 = loop_body.replace("    for lvl in unroll(0, n_levels):\n", "    for lvl in unroll(0, 1):\n", 1)
residual0 = resid_part.replace("    for lvl in unroll(0, n_levels):\n", "    for lvl in unroll(0, 1):\n").replace("fold_challenges[", "s_folds[").replace("tail_challenges[", "s_tail[")
ood1 = ood_part.replace("    for ood_lvl in unroll(1, n_levels):\n", "    for ood_lvl in unroll(1, 2):\n").replace("fold_challenges[", "s_folds[").replace("tail_challenges[", "s_tail[")

l1_block = f"""    # {U}: level 1 of a child >= 1: its own lambda, cap check and Merkle openings at the
    # positions and row weights child 0 published (no decode, no folds, no residual).
    ml1 = m_idx * LIG_MAX_LEVELS + 1
    l1_sp = fs_cap(fs0, fs1, fs2, fs3, fs4)
    no_rate = StackBuf(8)
    l1_sp, lam = squeeze(l1_sp, no_rate, 0)
    lam_pow = lam ** LIG_QUERIES[ml1]
    cap = merkle_caps * GEN ** (4 * LIG_CAP_OFF[ml1])
    flags = cap_flags * GEN ** LIG_CAP_OFF[ml1]
    root_0, root_1 = verify_merkle_cap(cap, flags, LIG_CAP_DEPTH[ml1])
    level_roots[GEN ** 2] = root_0
    level_roots[GEN ** 3] = root_1
    # The child's proof opened its own positions, so at the shared positions its hinted rows and
    # paths do not fold back to a cap: each query hashes into a fresh scratch cap and flag buffer
    # (same instruction count as the real walk; no constraint links them to the real cap).
    lqs = v6_opening_queries_free(lam, lam_pow, share[GEN ** V6_WINS], share[GEN ** V6_ROWEQ], GEN ** LIG_QUERIES[ml1], LIG_INTERLEAVE[ml1], LIG_LEAF_CELLS[ml1], LIG_TREE_DEPTH[ml1], LIG_CAP_DEPTH[ml1])
    # L2..L4: the rows and paths are popped unread, so the next child reads its own entries.
    for lvl in unroll(2, n_levels):
        ml = m_idx * LIG_MAX_LEVELS + lvl
        for q in unroll(0, LIG_QUERIES[ml]):
            skip_row = StackBuf(LIG_ROW_CAP)
            hint_witness(skip_row[0:3 * LIG_INTERLEAVE[ml]], "merkle_leaf_rows")
            skip_path = StackBuf(LIG_PATH_CAP)
            hint_witness(skip_path[0:4 * (LIG_TREE_DEPTH[ml] - LIG_CAP_DEPTH[ml])], "merkle_children")
"""

rest = f"""def v6_child_rest(m_idx: Const, fs0, fs1, fs2, fs3, fs4, target, commit_root_0, commit_root_1, cursor, xc, share):
    # {U}: children >= 1. See results/T07b/scripts/make_v6.py.
    s_folds = share[GEN ** V6_FOLDS]
    s_tail = share[GEN ** V6_TAIL]
    s_point = share[GEN ** V6_POINT]
    s_point1 = share[GEN ** V6_POINT1]
""" + header + loop0 + l1_block + residual0 + ood1 + f"""    v6_done_common = v6_common(share, xc, commit_root_0, commit_root_1, lqs)
    return 0, s_point, s_point1, inner_chain[GEN ** 1] + ood_inner, 0
"""

helpers = f"""@inline
def v6_absorb_group(sp, v0, v1, v2, v3):
    # {U}: one 4-scalar group of the per-child T_B absorb.
    rate = StackBuf(8)
    fs_pack(rate, 0, v0, DS_OBSERVE)
    fs_pack(rate, 1, v1, DS_OBSERVE)
    fs_pack(rate, 2, v2, DS_OBSERVE)
    fs_pack(rate, 3, v3, DS_OBSERVE)
    nxt = fs_perm(sp, rate, 4)
    return nxt


def v6_common(share, xc, v0, v1, v2):
    # {U}: per-child batch work (every child): T_B absorb of 4 digests + 1 element
    # (9 scalars, 3 permutations) on the sink sponge; eq(kappa, c), k E-muls; one E-mul + E-add
    # per level-1 query (45) into 45 memory accumulators; terminal combine (2 E-mul + 1 E-add).
    # Values are dummies; the operations and cells are the design's.
    k_g = share[GEN ** V6_K]
    sink = share[GEN ** V6_SINK]
    row = sink * xc ** FS_CELLS
    sp0 = fs_load(row, 0, 1)
    sp1 = v6_absorb_group(sp0, v0, v1, v2, xc)
    sp2 = v6_absorb_group(sp1, v0, v1, v2, xc)
    tail_rate = StackBuf(8)
    fs_pack(tail_rate, 0, v2, DS_OBSERVE)
    sp3 = fs_perm(sp2, tail_rate, 1)
    fs_store(row * GEN ** FS_CELLS, 0, 1, sp3)
    beta = share[GEN ** V6_BETA]
    eq_chain = HeapBuf(k_g * GEN)
    eq_chain[GEN ** 0] = 1
    for xk in mul_range(1, k_g):
        eq_chain[xk * GEN] = eq_chain[xk] * (1 + beta[xk])
    w = eq_chain[k_g]
    acc = share[GEN ** V6_ACC]
    row_acc = acc * xc ** {Q1}
    for q in unroll(0, {Q1}):
        row_acc[GEN ** ({Q1} + q)] = row_acc[GEN ** q] + w * v2
    term = share[GEN ** V6_TERM]
    term[xc] = w * v2 + v1 * v2
    return 0


def v6_batch_start(share, fs0, fs1, fs2, fs3, fs4):
    # {U}: child 0, once per batch: T_B header, then beta in E^k.
    k_g = share[GEN ** V6_K]
    sink = share[GEN ** V6_SINK]
    for j in unroll(0, FS_CELLS):
        sink[GEN ** j] = 0
    acc = share[GEN ** V6_ACC]
    for q in unroll(0, {Q1}):
        acc[GEN ** q] = 0
    cap = fs_cap(fs0, fs1, fs2, fs3, fs4)
    rate = StackBuf(8)
    fs_pack(rate, 0, k_g, DS_OBSERVE)
    hdr = fs_perm(cap, rate, 1)
    rows = HeapBuf((k_g * GEN) ** FS_CELLS)
    fs_store(rows, 0, 1, hdr)
    beta = share[GEN ** V6_BETA]
    for xk in mul_range(1, k_g):
        rd = rows * xk ** FS_CELLS
        rsp = fs_load(rd, 0, 1)
        no_rate = StackBuf(8)
        nxt, b = squeeze(rsp, no_rate, 0)
        beta[xk] = b
        fs_store(rd * GEN ** FS_CELLS, 0, 1, nxt)
    return 0


def v6_k_rounds(share, cursor):
    # {U}: k extra level-1 fold rounds (child 0) on a separate sponge, reading
    # dummy coefficients from the proof stream without advancing it.
    k_g = share[GEN ** V6_K]
    rows = HeapBuf((k_g * GEN) ** 8)
    for j in unroll(0, 8):
        rows[GEN ** j] = 0
    for xk in mul_range(1, k_g):
        rd = rows * xk ** 8
        n0, n1, n2, n3, n4, c_out, claim, c0, c2, r = opening_fold(rd[GEN ** 0], rd[GEN ** 1], rd[GEN ** 2], rd[GEN ** 3], rd[GEN ** 4], rd[GEN ** 5], rd[GEN ** 6], cursor, rd[GEN ** 7], rd[GEN ** 5], rd[GEN ** 6])
        nxt = rd * GEN ** 8
        nxt[GEN ** 0] = n0
        nxt[GEN ** 1] = n1
        nxt[GEN ** 2] = n2
        nxt[GEN ** 3] = n3
        nxt[GEN ** 4] = n4
        nxt[GEN ** 5] = c0
        nxt[GEN ** 6] = c2
        nxt[GEN ** 7] = claim
    return 0


def v6_opening_queries_free(lam, lam_n, query_win_ptrs, row_eq_weights, n_iters_g, interleave: Const, leaf_cells: Const, depth: Const, cap_depth: Const):
    # {U}: opening_queries' extension-row loop with a fresh cap / flag scratch per query,
    # so a child's own hints hashed at child 0's positions never hit write-once conflicts.
    mu = 1 / lam
    chain = HeapBuf(n_iters_g * GEN)
    chain[GEN ** 0] = 0
    for xi in mul_range(1, n_iters_g):
        cap_q = HeapBuf(GEN ** (2 ** (cap_depth + 2)))
        flags_q = HeapBuf(GEN ** (2 ** cap_depth))
        d = opening_query(cap_q, flags_q, row_eq_weights, query_win_ptrs[xi], 0, interleave, leaf_cells, depth, cap_depth)
        chain[xi * GEN] = (chain[xi] + d) * mu
    return chain[n_iters_g] * lam_n


def open_stacked(m_idx: Const, fs0, fs1, fs2, fs3, fs4, target, commit_root_0, commit_root_1, cursor, xc, share):
    # {U}: arm V6_ARM dispatches on the child index; other arms stay V5.
    r = StackBuf(5)
    if const(m_idx == V6_ARM):
        if xc == 1:
            c0, c1, c2, c3, c4 = v6_child0(m_idx, fs0, fs1, fs2, fs3, fs4, target, commit_root_0, commit_root_1, cursor, xc, share)
            r[0] = c0
            r[1] = c1
            r[2] = c2
            r[3] = c3
            r[4] = c4
        else:
            c0, c1, c2, c3, c4 = v6_child_rest(m_idx, fs0, fs1, fs2, fs3, fs4, target, commit_root_0, commit_root_1, cursor, xc, share)
            r[0] = c0
            r[1] = c1
            r[2] = c2
            r[3] = c3
            r[4] = c4
    else:
        a0, a1, a2, a3, a4 = open_stacked_v5(m_idx, fs0, fs1, fs2, fs3, fs4, target, commit_root_0, commit_root_1, cursor, xc, share)
        r[0] = a0
        r[1] = a1
        r[2] = a2
        r[3] = a3
        r[4] = a4
    return r[0], r[1], r[2], r[3], r[4]
"""

# ---- plumbing on the V5 guest ----
rep("def open_stacked(m_idx: Const, fs0, fs1, fs2, fs3, fs4, target, commit_root_0, commit_root_1, cursor, xc):\n",
    "def open_stacked_v5(m_idx: Const, fs0, fs1, fs2, fs3, fs4, target, commit_root_0, commit_root_1, cursor, xc, share):\n")
rep("lambda m_idx: open_stacked(m_idx, sp[8], sp[9], sp[10], sp[11], sp[12], target, commit_root_0, commit_root_1, cursor, xc))",
    "lambda m_idx: open_stacked(m_idx, sp[8], sp[9], sp[10], sp[11], sp[12], target, commit_root_0, commit_root_1, cursor, xc, share))")
rep("def verify_sub(pi_0, pi_1, seed_0, seed_1, g_squares, defer_out, xc):\n",
    "def verify_sub(pi_0, pi_1, seed_0, seed_1, g_squares, defer_out, xc, share):\n")
rep("verify_sub(pi_0, pi_1, seed_0, seed_1, g_squares, child_fresh * xc ** DEFER_SIZE, xc)\n",
    "verify_sub(pi_0, pi_1, seed_0, seed_1, g_squares, child_fresh * xc ** DEFER_SIZE, xc, v6_share)\n")
rep("    written[GEN ** 0] = n_raw_x_g * n_raw_s_g\n",
    f"""    written[GEN ** 0] = n_raw_x_g * n_raw_s_g
    # {U}: batch state shared by the children, in cells of one heap buffer.
    v6_share = HeapBuf(GEN ** 16)
    v6_share[GEN ** V6_K] = log2_ceil_in_the_exponent(n_children_g, g_squares, 0, SIZE_BITS)
    v6_sink = HeapBuf((n_children_g * GEN) ** FS_CELLS)
    v6_acc = HeapBuf((n_children_g * GEN) ** {Q1})
    v6_beta = HeapBuf(GEN ** 8)
    v6_term = HeapBuf(n_children_g)
    v6_share[GEN ** V6_SINK] = v6_sink
    v6_share[GEN ** V6_ACC] = v6_acc
    v6_share[GEN ** V6_BETA] = v6_beta
    v6_share[GEN ** V6_TERM] = v6_term
""")

# ---- constants before the first def, new functions before verify_sub ----
const_block = f"V6_ARM = {ARM}\n" + "".join(f"V6_{k} = {v}\n" for k, v in SHARE.items()) + "\n"
first_def = re.search(r"^(?:@|def )", s, re.M).start()
s = s[:first_def] + const_block + s[first_def:]
insert_at = s.index("def verify_sub(")
s = s[:insert_at] + helpers + "\n\n" + ch0 + "\n\n" + rest + "\n\n" + s[insert_at:]

open(path, "w").write(s)
print(f"wrote V6 to {path}")

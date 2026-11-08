#!/usr/bin/env python3
"""T07: write the UNSOUND, measurement-only guest variant V5 (emulated B'-L1 batched L1 opening).

usage: make_v5.py GUEST_PATH

Exact-string edits to crates/rec_aggregation/guests/lean_ethereum.py @ df7d122.

The child index reaches open_stacked as the runtime loop counter `xc` of main's child loop
(a g-power; child 0 has xc == 1): one extra argument on verify_sub and on open_stacked.

Child 0 (xc == 1) runs open_stacked with the baseline's semantics (it stands in for the shared
chain of the B'-L1 design). Every child with xc != 1:
  level 0  : unchanged, residual included.
  level 1  : keeps the Merkle cap check, leaf + path hashing, lane packing and query rows (and
             the row eq weights they consume). Its query windows are read as unchecked
             computed advice (hint_windows_exponent) without the decode's range checks,
             position assembly and reconstruction. Skips the PoW check, the residual and the
             OOD-eq term.
  L2..L4   : skips PoW, decode, row eq weights, cap check, openings (row and path hints are
             still popped, at zero cycles, so the global streams stay in sync), residual, OOD-eq.
  tail     : skips the final-message evaluation; returns yr_at_tail = 0 and
             sumcheck_target = 0, so the final check outside open_stacked
             (inner_sum * yr_at_tail == sumcheck_target) holds vacuously.
  Kept everywhere: every transcript absorb / squeeze (fold rounds, roots, OOD points and
  values, nonces, position squeezes, lam, final message), and the small sumcheck / batching
  arithmetic interleaved with them (gating it per round would cost a runtime branch each).
"""
import sys

path = sys.argv[1]
s = open(path).read()
U = "T07 V5 (UNSOUND, measurement only)"


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)


def indent(block, n=4):
    return "\n".join((" " * n + ln) if ln else ln for ln in block.rstrip("\n").split("\n")) + "\n"


# 0. The child index: verify_sub and open_stacked take main's loop counter xc.
rep("def verify_sub(pi_0, pi_1, seed_0, seed_1, g_squares, defer_out):\n",
    "def verify_sub(pi_0, pi_1, seed_0, seed_1, g_squares, defer_out, xc):\n"
    f"    # {U}: xc is main's child-loop counter (child 0 has xc == 1).\n")
rep("        verify_sub(pi_0, pi_1, seed_0, seed_1, g_squares, child_fresh * xc ** DEFER_SIZE)\n",
    "        verify_sub(pi_0, pi_1, seed_0, seed_1, g_squares, child_fresh * xc ** DEFER_SIZE, xc)\n")
rep("def open_stacked(m_idx: Const, fs0, fs1, fs2, fs3, fs4, target, commit_root_0, commit_root_1, cursor):\n",
    "def open_stacked(m_idx: Const, fs0, fs1, fs2, fs3, fs4, target, commit_root_0, commit_root_1, cursor, xc):\n"
    f"    # {U}: xc == 1 (child 0) runs the full opening; every other child keeps level 0\n"
    "    # and level 1's Merkle openings only (see results/T07/scripts/make_v5.py).\n")
rep("lambda m_idx: open_stacked(m_idx, sp[8], sp[9], sp[10], sp[11], sp[12], target, commit_root_0, commit_root_1, cursor))",
    "lambda m_idx: open_stacked(m_idx, sp[8], sp[9], sp[10], sp[11], sp[12], target, commit_root_0, commit_root_1, cursor, xc))")

# 1. The query PoW: checked at level 0 by every child, at levels >= 1 by child 0 only.
old_pow = """        if LIG_QUERY_GRIND_BITS[ml] != 0:
            grind_check(word0, LIG_QUERY_GRIND_BITS[ml])
        else:
            assert q_nonce == 0
"""
rep(old_pow, f"""        # {U}: levels >= 1 check the PoW in child 0 only; the
        # nonce is absorbed above by every child, so the transcript is unchanged.
        if const(lvl == 0):
""" + indent(old_pow) + """        else:
            if xc == 1:  # T07@gate
""" + indent(old_pow, 8))

# 2. Position squeezes: every child squeezes at every level. Decoding: level 0 every child;
#    levels >= 1 child 0; level 1 of the other children reads its windows as unchecked advice.
old_loop = """        for xs in mul_range(1, GEN ** LIG_SQUEEZES[ml]):
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
hinted_loop = old_loop.replace(
    "            decode_query_windows(packed_word, query_positions * GEN ** pos_off * query_ptr, query_win_ptrs * GEN ** pos_off * query_ptr, win_tabs, depth, cap_depth)\n",
    "            v5_query_windows_hinted(packed_word, query_win_ptrs * GEN ** pos_off * query_ptr, depth, cap_depth)  # T07@1578\n")
squeeze_only = """        for xs in mul_range(1, GEN ** LIG_SQUEEZES[ml]):
            row = sqz * xs ** FS_CELLS
            row_cap = fs_load(row, 0, 1)
            no_rate = StackBuf(8)
            row_sp, packed_word = squeeze(row_cap, no_rate, 0)
            fs_store(row * GEN ** FS_CELLS, 0, 1, row_sp)
"""
rep(old_loop, f"""        # {U}: every child squeezes every level's position
        # words. Child 0 decodes them at every level; the other children decode level 0,
        # take level 1's windows as unchecked advice (no decode) and do not decode L2..L4.
        if const(lvl == 0):
""" + indent(old_loop) + """        else:
            if xc == 1:  # T07@gate
""" + indent(old_loop, 8) + """            else:
                if const(lvl == 1):
""" + indent(hinted_loop, 12) + """                else:
""" + indent(squeeze_only, 12))

# 3. Row weights, cap check and openings: levels 0 and 1 every child; L2..L4 child 0 only.
old_open = """        row_eq_weights = HeapBuf(GEN ** (LIG_MAX_INTERLEAVE[m_idx]))
        opening_row_weights(fold_challenges * GEN ** folds_off, row_eq_weights, LIG_FOLDS[ml], 1 // (lvl + 1))

        cap_depth = LIG_CAP_DEPTH[ml]
        cap = merkle_caps * GEN ** (4 * LIG_CAP_OFF[ml])
        flags = cap_flags * GEN ** LIG_CAP_OFF[ml]
        root_0, root_1 = verify_merkle_cap(cap, flags, cap_depth)
        level_roots[GEN ** (2 * lvl)] = root_0
        level_roots[GEN ** (2 * lvl + 1)] = root_1

        level_query_sum = opening_queries(cap, flags, lam, lam_pow, query_win_ptrs * GEN ** pos_off, row_eq_weights, GEN ** (n_queries // (1 + 1 // (lvl + 1))), n_queries % 2 * (1 // (lvl + 1)), 1 // (lvl + 1), interleave, LIG_LEAF_CELLS[ml], depth, cap_depth)
"""
gated_open = old_open.replace("        level_query_sum = opening_queries(", "        lqs[0] = opening_queries(").rstrip("\n") + "  # T07@1606\n"
rep(old_open, f"""        # {U}: levels 0 and 1 are opened by every child; L2..L4
        # by child 0 only. A runtime branch's bindings are local, so the level's query sum
        # crosses the join in a frame cell.
        if const(lvl // 2 == 0):
""" + indent(old_open) + """        else:
            lqs = StackBuf(1)
            if xc == 1:  # T07@gate
""" + indent(gated_open, 8) + f"""            else:
                # {U}: the level's rows and paths are popped unread
                # (hint_witness costs no cycle), so the next child reads its own entries.
                cap_depth = LIG_CAP_DEPTH[ml]
                for q in unroll(0, n_queries):
                    skip_row = StackBuf(LIG_ROW_CAP)
                    hint_witness(skip_row[0:3 * interleave], "merkle_leaf_rows")
                    skip_path = StackBuf(LIG_PATH_CAP)
                    hint_witness(skip_path[0:4 * (depth - cap_depth)], "merkle_children")
                lqs[0] = 0  # T07@gate
            level_query_sum = lqs[0]  # T07@1606
""")

# 4. The final-message evaluation moves into the child-0 branch at the end (step 5).
rep("""    yr_at_tail = fold_final_msg(final_msg, tail_challenges, yr_log)
""", f"""    # {U}: the final-message evaluation runs below, in child 0 only.
""")

# 5. Residual and OOD eq: level 0's residual for every child; levels >= 1, the OOD-eq terms
#    and the final-message evaluation for child 0 only. Outputs cross the join in frame cells.
a = s.index("    basis_d = HeapBuf(GEN ** (n_levels * LIG_LOG_MSG_COLS_CAP))\n")
b = s.index("    return sumcheck_target, point, point1, inner_chain[GEN ** n_levels] + ood_inner, yr_at_tail\n")
tail = s[a:b]
i_chain = tail.index("    inner_chain = HeapBuf(GEN ** (n_levels + 1))\n")
i_ood = tail.index("    # Explicit OOD eq bases at the same terminal point.\n")
basis_loop = tail[:i_chain]          # allocations + per-level basis rows
chain_part = tail[i_chain:i_ood]     # inner_chain alloc + per-level residual chains
ood_part = tail[i_ood:]              # OOD eq bases
alloc_basis, basis_body = basis_loop.split("    for lvl in unroll(0, n_levels):\n", 1)
alloc_chain, chain_body = chain_part.split("    for lvl in unroll(0, n_levels):\n", 1)
assert "for lvl in unroll(0, n_levels)" not in basis_body + chain_body
new_tail = (alloc_basis
            + f"    # {U}: level 0's residual runs in every child.\n"
            + "    for lvl in unroll(0, 1):\n" + basis_body
            + alloc_chain
            + "    for lvl in unroll(0, 1):\n" + chain_body
            + f"""    # {U}: levels >= 1's residual, the OOD-eq terms and the
    # final-message evaluation run in child 0 only. The other children return
    # sumcheck_target = yr_at_tail = 0, so the final check outside holds vacuously.
    v5_out = StackBuf(3)
    if xc == 1:  # T07@gate
        v5_out[2] = fold_final_msg(final_msg, tail_challenges, yr_log)  # T07@1662
""" + indent("    for lvl in unroll(1, n_levels):\n" + basis_body
             + "    for lvl in unroll(1, n_levels):\n" + chain_body
             + ood_part)
            + """        v5_out[0] = sumcheck_target  # T07@gate
        v5_out[1] = inner_chain[GEN ** n_levels] + ood_inner  # T07@1764
    else:
        v5_out[0] = 0  # T07@gate
        v5_out[1] = inner_chain[GEN ** 1]  # T07@gate
        v5_out[2] = 0  # T07@gate
""")
s = s[:a] + new_tail + s[b:]
rep("    return sumcheck_target, point, point1, inner_chain[GEN ** n_levels] + ood_inner, yr_at_tail\n",
    "    return v5_out[0], point, point1, v5_out[1], v5_out[2]  # T07@1764\n")

# 6. The advice-only window read used by level 1 of children >= 1.
rep("def grind_check(word, nbits: Const):\n", f"""def v5_query_windows_hinted(squeezed_word, win_ptrs_out, depth: Const, cap_depth: Const):
    # {U}: decode_query_windows' windows as unchecked computed
    # advice: no range checks, no bit-pattern reads, no positions, no reconstruction. Stands in
    # for level-1 query windows handed over by the shared chain. Each window is hinted whole
    # (hint_windows_exponent reads across limbs), equal to decode's lo * hi^(2^cut).
    per_word = FIELD_BITS // depth
    path = depth - cap_depth
    n_pw = (path + QW - 1) // QW
    n_win = n_pw + 2
    wins = StackBuf(QUERY_WINDOWS_CAP)
    wins_ptr = addr(wins)
    for j in unroll(0, per_word):
        base = j * depth
        at0 = j * n_win
        for i in unroll(0, n_win):
            if const(i + 2 == n_win):
                off = path
                width = 1
            elif const(i + 1 == n_win):
                off = path + 1
                width = cap_depth - 1
            elif const(i + 3 == n_win):
                off = QW * i
                width = path - QW * i
            else:
                off = QW * i
                width = QW
            hint_windows_exponent(wins, squeezed_word, base + off, width, 1, at0 + i)
        win_ptrs_out[GEN ** j] = wins_ptr * GEN ** at0
    return


def grind_check(word, nbits: Const):
""")

open(path, 'w').write(s)
print(f"wrote V5 to {path}")

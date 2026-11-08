#!/usr/bin/env python3
"""T05: write the UNSOUND, measurement-only guest variants V3 (K=1) and V4 (K=2).

usage: make_variant.py GUEST_PATH K TAG

Applies exact-string edits to crates/rec_aggregation/guests/lean_ethereum.py @ df7d122.
Inside each child's open_stacked, levels lvl < K keep everything (fold rounds, query sampling and
PoW, row eq weights, Merkle cap, leaf + path hashing, lane packing, query rows). Levels lvl >= K
skip their PoW check, query-window decoding, row eq weights, cap check and query openings; their
row and path hints are still popped (zero-cycle hint_witness) so the next child reads its own
entries. The residual (all levels), the final-message evaluation and the final check are skipped.
Every prover message is still read and absorbed and every challenge squeezed (transcript unchanged).
"""
import sys

path, K, TAG = sys.argv[1], int(sys.argv[2]), sys.argv[3]
s = open(path).read()
U = f"T05 {TAG} (UNSOUND, measurement only)"


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


# 1. PoW check only at kept levels (the nonce is still absorbed above).
rep("""        if LIG_QUERY_GRIND_BITS[ml] != 0:
            grind_check(word0, LIG_QUERY_GRIND_BITS[ml])
        else:
            assert q_nonce == 0
""", f"""        # {U}: the query PoW is checked only at levels < {K}.
        # The nonce is still absorbed above, so the transcript is unchanged.
        if const(lvl // {K} == 0):
            if LIG_QUERY_GRIND_BITS[ml] != 0:
                grind_check(word0, LIG_QUERY_GRIND_BITS[ml])
            else:
                assert q_nonce == 0
""")

# 2. Query-position squeezes at every level; window decoding only at kept levels.
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
rep(old_loop, f"""        # {U}: every query-position challenge is still squeezed; the
        # squeezed words are decoded into positions and windows only at levels < {K}.
        if const(lvl // {K} == 0):
""" + "\n".join(("    " + ln) if ln else ln for ln in old_loop.rstrip("\n").split("\n")) + f"""
        else:
            for xs in mul_range(1, GEN ** LIG_SQUEEZES[ml]):
                row = sqz * xs ** FS_CELLS
                row_cap = fs_load(row, 0, 1)
                no_rate = StackBuf(8)
                row_sp, packed_word = squeeze(row_cap, no_rate, 0)
                fs_store(row * GEN ** FS_CELLS, 0, 1, row_sp)
""")

# 3. Row weights, cap check and query openings only at kept levels.
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
rep(old_open, f"""        # {U}: row eq weights, the Merkle cap check and the query
        # openings (rows, lane packing, leaf + path hashing, row folds) run only at levels < {K}.
        if const(lvl // {K} == 0):
""" + "\n".join(("    " + ln) if ln else ln for ln in old_open.rstrip("\n").split("\n")) + f"""
        else:
            # {U}: the level's rows and paths are popped unread (hint_witness costs no
            # cycle), so the next child's opening reads its own entries of the global streams.
            cap_depth = LIG_CAP_DEPTH[ml]
            for q in unroll(0, n_queries):
                skip_row = StackBuf(LIG_ROW_CAP)
                hint_witness(skip_row[0:3 * interleave], "merkle_leaf_rows")
                skip_path = StackBuf(LIG_PATH_CAP)
                hint_witness(skip_path[0:4 * (depth - cap_depth)], "merkle_children")
            level_query_sum = 0
""")

# 4. No final-message evaluation (e4); the message is still read and absorbed.
rep("""    yr_at_tail = fold_final_msg(final_msg, tail_challenges, yr_log)
""", f"""    # {U}: the final message is not evaluated (e4). It is
    # still read and absorbed above, so the transcript and every later challenge are unchanged.
    yr_at_tail = 0
""")

# 5. No residual (induced-basis weights at query positions) at any level.
a = s.index("    # ---- per-level induced bases at the single terminal point ----")
b = s.index("    # Explicit OOD eq bases at the same terminal point.")
s = s[:a] + f"""    # {U}: the per-level induced bases at the query
    # positions (the residual, e2) are not computed at any level.

""" + s[b:]
rep("""    return sumcheck_target, point, point1, inner_chain[GEN ** n_levels] + ood_inner, yr_at_tail
""", """    return sumcheck_target, point, point1, ood_inner, yr_at_tail
""")

# 6. No final check (outside open_stacked; it cannot hold without the residual), as in T03 V2.
rep("""    assert inner_sum * yr_at_tail == sumcheck_target
""", f"""    # {U}: no final-polynomial check (it needs the skipped residual and e4).
    # assert inner_sum * yr_at_tail == sumcheck_target
""")

open(path, 'w').write(s)
print(f"wrote {TAG} (K={K}) to {path}")

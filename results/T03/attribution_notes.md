# T03 attribution notes: in-circuit child verification in leanVM recursion

leanMultisig df7d122 (research/baseline). Guest: crates/rec_aggregation/guests/lean_ethereum.py.
All guest line numbers below are for df7d122. V1 and V2 are UNSOUND, measurement-only variants.

## How the guest reaches the binary

- Embedded at build time: `include_str!("../../guests/lean_ethereum.py")` (crates/rec_aggregation/src/aggregation/guest.rs:49).
- Placeholders are substituted and the guest is compiled at run time, on the first `unified_guest()` call (guest.rs:23-37). It is compiled to a fixed point on its own padded bytecode size (2^19 for all three programs here).
- In the benchmark this happens before any timing (bins/leanvm/src/benchmark.rs:172). The compile is about 0.8-1.0 s.
- The leaves (child process, benchmark.rs:185, 271-291) run the same compiled guest with no children.

## Profiling facility (exists upstream; no semantic change)

| facility | where | what |
|---|---|---|
| `DBG_PROF=1` | crates/leanvm_core/src/cpu/execute.rs:344-346, 1007-1046 | per-pc step counts; prints cycles per compiled function |
| `DBG_PROF_DUMP=path` | execute.rs:1017-1037 | writes raw per-pc counts plus the function table (`F name entry len`) |
| `DBG_DISASM=path` | guest.rs:52-66 | disassembly with function boundaries |
| `DBG_PLACEHOLDERS=path` | guest.rs:42-47 | baked guest constants |
| `Program::src_lines`, `fn_ranges` | crates/leanvm_core/src/cpu/mod.rs:116-126 | source line per pc. Pub field, but no env var dumps it. Read by proto/guest-lines through the public `rec_aggregation::aggregation::unified_guest()` |

Checks that the profiler does not change behaviour:
- Profiled node cycles equal unprofiled cycles: 392,988 at n=2 and 766,603 at n=4 (T01 and this task).
- The guest-lines function table equals the DBG_PROF_DUMP table exactly (992 / 942 / 688 functions for baseline / V1 / V2).

## Method (scripts/attribute.py)

1. **Bucket by source line.** Each pc gets a bucket from its source line (table in attribute.py, df7d122 lines). Functions holding bucketed lines are "split" functions: `verify_sub`, the `open_stacked` arms, `opening_queries` and their `__loop` helpers.
2. **Inlined code.** An `@inline` helper's pcs carry the helper's own line (lean_compiler lower/call.rs:394-405). Such a run is given to the caller statement that calls the helper, found by searching the caller source between the neighbouring bucketed pcs, then the caller def. 26 cycles at n=2 stayed ambiguous; they are inlined FS helpers at the boundaries between a:commit root, a:bus challenges and b:bus GKR.
3. **Non-inline callees.** These inherit the bucket of their call site.
   - Static calls: `SET fp[k] = g^entry` then `JUMP pc=fp[k]`.
   - `match` dispatch: `DEREF *(fp[x]*g^o2) = fp[k]`, then `JUMP pc=fp[k]`. The table is filled by the `__jump_tables` prologue.
   - Inclusive cost is pushed to call sites in proportion to call counts.
   - After this, every executed function except the roots `main` and `__jump_tables` has entry count equal to its incoming call count.
   - Callees reached from two stages are split by call counts: `assert_small_g_power`, `assert_canonical`, `eq_prefix_chain` and `eq_prefix_run__L*`, 1.5k cycles in all at n=2.
4. **Per-opcode counts** are carried along, so KECCAK per bucket is exact. "FS-helper" is a cross-cut: cycles whose line is in the sponge helpers (lean_ethereum.py:555-692).
5. **Per child** = (n=4 total − n=2 total) / 2 per bucket. Both profiles come from one run each; cycles are deterministic.
6. **Variants.** Their profiles are attributed with their own source, line-mapped back to df7d122 by difflib. The measured removals match the buckets (below).

## Location table, stages (a) to (e4)

| stage | where (lean_ethereum.py @ df7d122) |
|---|---|
| (a) transcript replay, FS | `verify_sub` 3337-3427 (seed 3337-3345, announced layout + certification 3346-3395, commitment root 3396-3411, bus challenges 3412-3427), export 3511-3517. Sponge helpers 555-692 (`fs_*`, `squeeze`) are inlined into every stage. In `open_stacked`: level-root reads 1506-1519, setup 1434-1496 |
| (b) bus GKR | call at `verify_sub` 3428-3430; `verify_bus_gkr` 1772-1944; `gkr_rounds` 1098-1121; `sumcheck_round4` 1079-1095 |
| (c) table / constraint sumcheck | call at `verify_sub` 3431-3434; `verify_tables` 2113-2539 (leaf decomposition 2178-2362, table sumcheck 2363-2524, public-input claim 2525-2539) |
| (d) Keccak GKR / reduction | call at `verify_sub` 3435-3441; `verify_keccak` 2927-3093; `keccak_layer` 2698-2879; `keccak_plain_rounds` 2882-2907 |
| (e) WHIR opening | `open_stacked` 1434-1764, dispatched per (rate, size) by the `match` at `verify_sub` 3503. Front at `verify_sub` 3442-3502; terminal `check_opening_terminal` 3238-3322 (call 3508-3510) |
| (e1) Merkle hashing | `opening_query` 1391-1393: leaf `keccak_cells` + `walk_path` call. `walk_path` 1312-1347 and `walk_window` 1297-1309. `verify_merkle_cap` 1163-1214, called at 1599-1604, where the cap root is checked against the level root. (`verify_merkle_path` 1145-1160 is defined but never called.) |
| (e1/e2) lane packing | `opening_query` 1361-1370 (`pack64x2` 530-532, an F64 range check of every opened lane, used by both the hash and the fold) |
| (e2) folding and consistency at queried points | row hint, row-by-eq-weights dot products, per-query lam chain: `opening_query` 1351-1360 + 1371-1390, `opening_queries` 1397-1419. Row eq weights: `opening_row_weights` 1272-1293, called at 1596-1597. Residual = induced-basis weights at query positions: 1691-1748 + `residual_query` 1423-1431 |
| (e3) evaluation-claim parts | sumcheck rounds: `opening_fold` 1220-1233, called at 1497-1503 and 1643-1661. OOD: `opening_ood_point` 1236-1247, answers 1520-1538, OOD eq 1749-1763. Level batching 1582-1595 and 1608-1642. Point rotation 1663-1690. Ring-switch front + claim batching `verify_sub` 3442-3490 (`ring_switch_target` 3106-3123). Placement certification 3491-3502 (`certify_placement` 3138-3182). Terminal transparent weights 3238-3321 (`column_selector` 3185-3212, `selector_tables` 3215-3235, `ring_switch_weight` 3126-3135) |
| (e4) final polynomial | read and absorb: `opening_final_message` 1250-1269, called at 1504-1505. Evaluation: `fold_final_msg` 1058-1076, called at 1662. Final equality 3322 |
| (eq) query sampling + PoW (not in a-e4) | 1539-1581: nonce absorb, `grind_check` 889-915, squeeze, `decode_query_windows` 825-886; window table 1480-1482 |

## Exact attribution per child (baseline, outer rate 2, M=250 leaves)

Per-child total is 186,807.5 cycles (slope from n=2 to n=4; T01 gave 186.8k).

| stage | cycles / child | share | KECCAK / child | FS-helper cycles / child |
|---|---:|---:|---:|---:|
| (a) transcript + FS, `verify_sub` own | 590.0 | 0.32% | 8 | 85 |
| (a) `open_stacked` level roots + setup | 228.0 | 0.12% | 0 | 94 |
| (b) bus GKR | 9,551.0 | 5.11% | 179 | 4,847 |
| (c) table / constraint sumcheck | 12,134.2 | 6.50% | 58 | 1,494 |
| (d) Keccak GKR / reduction | 35,839.0 | 19.18% | 482 | 10,684 |
| (e1) Merkle hashing | 23,174.5 | 12.41% | 4,084.5 | 0 |
| ... cap | 2,284.5 | 1.22% | 235.5 | |
| ... leaf + path | 20,890.0 | 11.18% | 3,849 | |
| (e1/e2) lane packing | 19,004.0 | 10.17% | 0 | 0 |
| (e2) folding / consistency at queries | 44,109.0 | 23.61% | 0 | 0 |
| ... query rows (dot products, chain) | 28,947.0 | 15.50% | | |
| ... residual (query weights) | 14,946.0 | 8.00% | | |
| ... row eq weights | 216.0 | 0.12% | | |
| (e3) evaluation-claim parts | 21,023.7 | 11.25% | 83 | 1,175 |
| ... terminal weights | 11,334.7 | 6.07% | | |
| ... ring-switch front + claim batch | 6,116.0 | 3.27% | | |
| ... sumcheck rounds | 1,809.0 | 0.97% | | |
| ... OOD | 829.0 | 0.44% | | |
| ... placement + config certify | 664.0 | 0.36% | | |
| ... level batching / rotation / dispatch | 271.0 | 0.15% | | |
| (e4) final polynomial | 161.0 | 0.09% | 3 | 68 |
| (eq) query sampling + PoW | 13,559.0 | 7.26% | 35 | 700 |
| node work in `main` per child (outside `verify_sub`) | 7,434.0 | 3.98% | 255.5 | 340 |

Proximity part:
- W = e1 + e2 + e4 = 67,444.5 cycles (36.10%).
- W + lane packing = 86,448.5 (46.28%).
- W + packing + query sampling/PoW = 100,007.5 (53.54%).
- e3, which an accumulator still carries, = 21,023.7 (11.25%).
- KECCAK per child is 5,188, of which e1 is 4,084.5 (78.7%).

Fixed (not per child): the `__jump_tables` prologue is 16,555 cycles in the baseline. It drops by 6,162 in V1 and V2 because the `walk_path` dispatch tables go.

## Cross-check with the variants (one profiled run each at n=2)

- **V1:** removes exactly e1 (46,303 at n=2), plus 6,162 in the prologue. It adds 354 in `e2:query rows` over the 444 query openings at n=2 (222 per child), from the `path` StackBuf that the kept hint needs inside `opening_query`. The cause was not traced further.
- **V2:** removes e1, packing, e2, `fold_final_msg` (96) and the final check (6), plus 6,162 in the prologue. Small shifts: +20 level batching, −2 terminal.
- The predicted node-cycle deltas equal the measured ones exactly: 52,111 (V1) and 178,811 (V2).

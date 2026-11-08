=== RESULT REPORT T03 ===
Status: done
Machine: Apple M2 (4P+4E cores), 8 GiB, macOS 26.5.2 (25F84), fanless, AC power (100%, charged)
Toolchain: rustc 1.99.0 (b940084d7 2026-09-28), invoked as `cargo +1.99.0`; no Lean
Repo state:
- upstream/leanMultisig. Base df7d122abbe25cf12e5c8ae992ce6d3505f75372; research/baseline unmodified and checked out, tree clean.
- New local branches: research/d3-v1 at 4fb9e000fb53017df0a45b682d33f358217df450, research/d3-v2 at 4760693a8c70d5d855e1ae97292249fd0ccd119f. Both UNSOUND, measurement only, not pushed.
- Untracked build dirs target-d3v1/ and target-d3v2/, listed in .git/info/exclude. The baseline binary in target/ was not rebuilt.
- Workspace (not a git repo): new crate proto/guest-lines; new results/T03/.

## Summary
- **Profiler.** Exact per-stage attribution was possible with no semantic change. leanVM already has a per-pc cycle profiler (`DBG_PROF`, `DBG_PROF_DUMP`, `DBG_DISASM`). The pc→source-line table (`Program::src_lines`) is read through the public `unified_guest()` by a small out-of-tree tool. Inline code, calls and `match` dispatch are resolved, so all 392,988 and 766,603 node cycles are attributed.
- **Per child (186,807.5 cycles):**
  - The WHIR proximity part W = e1 + e2 + e4 is 67.4k cycles (36.1%).
  - The lane-packing range checks shared by e1 and e2 add 19.0k, making W 86.4k (46.3%).
  - Query sampling and PoW add another 13.6k (53.5% in total).
  - e3, what an accumulator would still carry, is 21.0k (11.3%). Keccak GKR (d) is 35.8k (19.2%).
- **Merkle hashing (e1)** is 23.2k cycles/child (12.4%) but 78.7% of the KECCAK opcodes (4,084.5 of 5,188 per child).
- **Variants agree with the attribution exactly.** V1 (skip e1) saves 22,993.5 cycles/child (12.3%). V2 (skip e1+e2+e4) saves 86,343.5 (46.2%). Both node proofs verify under the CLI.
- **Prove time** falls much more than cycles do, because TOTAL_COMMITTED drops at power-of-two steps and the KECCAK table shrinks. Pooled over 2 passes × 3 repeats, per child:
  - V1 saves 107 ms (27%, slope n=2→4) to 212 ms (52%, n=2→6). This figure is noisy.
  - V2 saves 280–296 ms (70–72%), stable across passes.
- **Drift check:** pass 1 baseline n=2 was +16.5% vs T01 (0.649 vs 0.557 s), outside 15%. A second full pass gave −1.4% (0.549 s), within 15%. Cycles and proof sizes match T01 exactly in every run.

## Results

### Location table (lean_ethereum.py @ df7d122)
| stage | file:line |
|---|---|
| (a) transcript replay + FS | `verify_sub` 3337-3427 (seed 3337-3345, layout 3346-3395, commit root 3396-3411, bus challenges 3412-3427), 3511-3517. Sponge helpers 555-692, inlined everywhere. `open_stacked` level roots 1506-1519 |
| (b) bus GKR | `verify_sub` 3428-3430 → `verify_bus_gkr` 1772-1944 (`gkr_rounds` 1098-1121, `sumcheck_round4` 1079-1095) |
| (c) table sumcheck | `verify_sub` 3431-3434 → `verify_tables` 2113-2539 (leaves 2178-2362, table sumcheck 2363-2524, PI 2525-2539) |
| (d) Keccak GKR | `verify_sub` 3435-3441 → `verify_keccak` 2927-3093 (`keccak_layer` 2698-2879, `keccak_plain_rounds` 2882-2907) |
| (e) opening | `open_stacked` 1434-1764 via `match` at `verify_sub` 3503; front 3442-3502; terminal `check_opening_terminal` 3238-3322 |
| (e1) Merkle | `opening_query` 1391-1393 (leaf hash + `walk_path` 1312-1347 / `walk_window` 1297-1309); `verify_merkle_cap` 1163-1214 at 1599-1604 |
| (e1/e2) lane packing | `opening_query` 1361-1370 (`pack64x2` 530-532) |
| (e2) folds / consistency at queries | `opening_query` 1351-1360, 1371-1390; `opening_queries` 1397-1419; `opening_row_weights` 1272-1293 at 1596-1597; residual 1691-1748 + `residual_query` 1423-1431 |
| (e3) evaluation claims | `opening_fold` 1220-1233 at 1497-1503 and 1643-1661; OOD 1236-1247, 1520-1538, 1749-1763; batching 1582-1595, 1608-1642; rotation 1663-1690; ring switch + claim batch 3442-3490; placement 3491-3502; terminal weights 3238-3321 |
| (e4) final polynomial | `opening_final_message` 1250-1269 at 1504-1505; `fold_final_msg` 1058-1076 at 1662; final equality 3322 |
| (eq) query sampling + PoW | 1539-1581 (`grind_check` 889-915, `decode_query_windows` 825-886), 1480-1482 |

**How the guest reaches the binary:**
- It is embedded at build time by `include_str!` (crates/rec_aggregation/src/aggregation/guest.rs:49).
- Placeholders are substituted and the guest is compiled at run time, on the first `unified_guest()` call (guest.rs:23-37, self-referential fixed point on its padded size). That call is benchmark.rs:172, before timing.

**Profiling facility:**
- `DBG_PROF=1` prints cycles per function (crates/leanvm_core/src/cpu/execute.rs:344-346, 1007-1046).
- `DBG_PROF_DUMP=path` writes per-pc counts (execute.rs:1017-1037).
- `DBG_DISASM` and `DBG_PLACEHOLDERS` (guest.rs:42-66).
- `Program::src_lines` and `fn_ranges` (cpu/mod.rs:116-126) are not dumped by any env var; read with proto/guest-lines.

### Exact attribution (step 2): per child = (n=4 − n=2)/2, baseline, rate 2
Command: `DBG_PROF=1 DBG_PROF_DUMP=... leanvm recursion --n {2,4} --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 1`, then scripts/attribute.py and attribution_table.py.

| stage | cycles / child | share of 186,807.5 | KECCAK / child |
|---|---:|---:|---:|
| (a) transcript/FS, `verify_sub` own + `open_stacked` roots/setup | 818.0 | 0.44% | 8 |
| (b) bus GKR | 9,551.0 | 5.11% | 179 |
| (c) table sumcheck | 12,134.2 | 6.50% | 58 |
| (d) Keccak GKR | 35,839.0 | 19.18% | 482 |
| (e1) Merkle (cap 2,284.5; leaf+path 20,890) | 23,174.5 | 12.41% | 4,084.5 |
| (e1/e2) lane packing | 19,004.0 | 10.17% | 0 |
| (e2) query rows 28,947; residual 14,946; row weights 216 | 44,109.0 | 23.61% | 0 |
| (e3) terminal weights 11,334.7; ring switch + batch 6,116; sumcheck 1,809; OOD 829; placement 664; other 271 | 21,023.7 | 11.25% | 83 |
| (e4) final message read/absorb + fold 158; final check 3 | 161.0 | 0.09% | 3 |
| (eq) query sampling 12,739; PoW 820 | 13,559.0 | 7.26% | 35 |
| `main`, per-child part outside `verify_sub` | 7,434.0 | 3.98% | 255.5 |
| **W = e1+e2+e4** | **67,444.5** | **36.10%** | 4,087.5 |
| W + packing | 86,448.5 | 46.28% | |
| W + packing + eq | 100,007.5 | 53.54% | |

FS-sponge-helper cycles inside the stages (cross-cut, per child): (b) 4,847; (c) 1,494; (d) 10,684; (e3) 1,175; (eq) 700; others below 350. The 19,487 total is 10.4%.

Accuracy:
- 26 cycles at n=2 sit at an ambiguous boundary.
- About 1.5k cycles at n=2 come from callees shared by two stages and are split by call counts.
- The Merkle cap is data-dependent (2,277 at n=2/2 vs 2,284.5 slope).

### Variant diffs (UNSOUND, measurement only; results/T03/v1.diff, v2.diff)

**V1** (research/d3-v1, 4fb9e000f; +6/−6 lines):
- `opening_query` replaces the leaf `keccak_cells` and `walk_path` call with a bare `hint_witness(path..., "merkle_children")`, so the streams pop in the baseline order.
- `open_stacked` drops `verify_merkle_cap` and the two `level_roots` writes that check the cap root.

**V2** (research/d3-v2, 4760693a8; +12/−72 lines):
- `open_stacked` drops `row_eq_weights` / `opening_row_weights`, the cap check and the `opening_queries` call (`level_query_sum = 0`). The query rows and paths are not popped; no other phase reads those streams, and the VM checks only for exhaustion.
- It drops the residual block (1691-1748) and returns `ood_inner` alone. `fold_final_msg` is replaced by `yr_at_tail = 0`.
- The final assert (3322) is commented out.
- Kept: sumcheck rounds, OOD, ring switch, claim batching, terminal weights, query sampling/PoW, and the final message read and absorbed, so the transcript is unchanged.

### Run table
Command for every row:
```
/usr/bin/time -l <binary> recursion --n {2,4,6} --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 3 --tracing
```
- Binaries: target/, target-d3v1/ and target-d3v2/ under upstream/leanMultisig, `release/leanvm` in each.
- Runs were interleaved base/V1/V2 per n, with 30 s sleeps.
- Pass 1 is runs/, pass 2 is runs2/.
- Median is over the 3 measured passes.
- Footprint is the `/usr/bin/time -l` peak memory footprint of the node process (leaves run in a separate child process).

| variant | n | pass | cycles | TOTAL_COMMITTED | proof KiB | prove s (3 passes) | median s | leanVM peak GiB | footprint GiB | swap Δ MiB | verify | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2 | 1 | 392,988 | 2^23.842 | 232.6 | 0.648 0.649 0.695 | 0.649 | 1.377 | 1.43 | 58 | ok | AC |
| baseline | 4 | 1 | 766,603 | 2^24.791 | 239.9 | 1.406 1.398 1.399 | 1.399 | 2.269 | 2.399 | 356 | ok | memory-pressured |
| baseline | 6 | 1 | 1,140,247 | 2^25.036 | 227.4 | 2.17 2.068 2.061 | 2.068 | 2.986 | 3.095 | 978 | ok | memory-pressured |
| V1 UNSOUND | 2 | 1 | 340,877 | 2^23.597 | 223.6 | 0.481 0.507 0.58 | 0.507 | 1.211 | 1.262 | 204 | ok | AC |
| V1 UNSOUND | 4 | 1 | 668,497 | 2^24.567 | 230.7 | 0.849 0.96 0.878 | 0.878 | 2.03 | 2.099 | -24 | ok | AC |
| V1 UNSOUND | 6 | 1 | 996,162 | 2^24.874 | 241.0 | 1.204 1.079 0.998 | 1.079 | 2.553 | 2.582 | -40 | ok | AC |
| V2 UNSOUND | 2 | 1 | 214,177 | 2^22.822 | 211.5 | 0.29 0.291 0.292 | 0.291 | 0.795 | 0.823 | -8 | ok | AC |
| V2 UNSOUND | 4 | 1 | 415,097 | 2^23.743 | 228.2 | 0.578 0.521 0.568 | 0.568 | 1.279 | 1.317 | -104 | ok | AC |
| V2 UNSOUND | 6 | 1 | 616,062 | 2^24.12 | 217.3 | 0.75 0.748 0.749 | 0.749 | 1.674 | 1.69 | -40 | ok | AC |
| baseline | 2 | 2 | 392,988 | 2^23.842 | 232.6 | 0.544 0.561 0.549 | 0.549 | 1.402 | 1.448 | -48 | ok | AC |
| baseline | 4 | 2 | 766,603 | 2^24.791 | 239.9 | 1.418 1.447 1.407 | 1.418 | 2.283 | 2.403 | -32 | ok | AC |
| baseline | 6 | 2 | 1,140,247 | 2^25.036 | 227.4 | 2.353 2.986 2.324 | 2.353 | 2.973 | 3.096 | 956 | ok | memory-pressured |
| V1 UNSOUND | 2 | 2 | 340,877 | 2^23.597 | 223.6 | 0.478 0.463 0.47 | 0.47 | 1.229 | 1.271 | -24 | ok | AC |
| V1 UNSOUND | 4 | 2 | 668,497 | 2^24.567 | 230.7 | 1.5 1.201 1.176 | 1.201 | 1.985 | 2.102 | -282 | ok | AC |
| V1 UNSOUND | 6 | 2 | 996,162 | 2^24.874 | 241.0 | 1.609 1.342 2.006 | 1.609 | 2.441 | 2.581 | 85 | ok | AC |
| V2 UNSOUND | 2 | 2 | 214,177 | 2^22.822 | 211.5 | 0.293 0.299 0.29 | 0.293 | 0.797 | 0.822 | -8 | ok | AC |
| V2 UNSOUND | 4 | 2 | 415,097 | 2^23.743 | 228.2 | 0.494 0.515 0.548 | 0.515 | 1.274 | 1.307 | 0 | ok | AC |
| V2 UNSOUND | 6 | 2 | 616,062 | 2^24.12 | 217.3 | 0.756 0.744 0.748 | 0.748 | 1.662 | 1.692 | -8 | ok | AC |

Per-opcode lines (identical in both passes):
- base n=2: `MUL 2^17.132 (36.5%)  XOR 2^16.681 (26.7%)  DEREF 2^16.105 (17.9%)  SET 2^15.213 (9.7%)  JUMP 2^14.637 (6.5%)  KECCAK 2^13.347 (2.7%)  MEMORY 2^19.379  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842`
- base n=4: `MUL 2^18.129 (37.4%)  XOR 2^17.678 (27.3%)  DEREF 2^17.093 (18.2%)  SET 2^15.845 (7.7%)  JUMP 2^15.634 (6.6%)  KECCAK 2^14.344 (2.7%)  MEMORY 2^20.357  BYTECODE 2^18.899  TOTAL_COMMITTED 2^24.791`
- base n=6: `MUL 2^18.713 (37.7%)  XOR 2^18.262 (27.6%)  DEREF 2^17.674 (18.3%)  SET 2^16.282 (7.0%)  JUMP 2^16.218 (6.7%)  KECCAK 2^14.928 (2.7%)  MEMORY 2^20.935  BYTECODE 2^18.899  TOTAL_COMMITTED 2^25.036`
- V1 n=2: `MUL 2^17.077 (40.6%)  XOR 2^16.536 (27.9%)  DEREF 2^15.844 (17.3%)  SET 2^14.614 (7.4%)  JUMP 2^14.391 (6.3%)  KECCAK 2^11.129 (0.7%)  MEMORY 2^19.031  BYTECODE 2^18.667  TOTAL_COMMITTED 2^23.597`
- V1 n=4: `MUL 2^18.074 (41.3%)  XOR 2^17.533 (28.4%)  DEREF 2^16.83 (17.4%)  JUMP 2^15.386 (6.4%)  SET 2^15.258 (5.9%)  KECCAK 2^12.118 (0.7%)  MEMORY 2^20.012  BYTECODE 2^18.667  TOTAL_COMMITTED 2^24.567`
- V1 n=6: `MUL 2^18.658 (41.5%)  XOR 2^18.117 (28.5%)  DEREF 2^17.41 (17.5%)  JUMP 2^15.969 (6.4%)  SET 2^15.701 (5.3%)  KECCAK 2^12.7 (0.7%)  MEMORY 2^20.59  BYTECODE 2^18.667  TOTAL_COMMITTED 2^24.874`
- V2 n=2: `MUL 2^16.331 (38.5%)  DEREF 2^15.657 (24.1%)  XOR 2^15.536 (22.2%)  SET 2^14.411 (10.2%)  JUMP 2^13.064 (4.0%)  KECCAK 2^11.129 (1.0%)  MEMORY 2^18.431  BYTECODE 2^18.239  TOTAL_COMMITTED 2^22.822`
- V2 n=4: `MUL 2^17.326 (39.6%)  DEREF 2^16.641 (24.6%)  XOR 2^16.529 (22.8%)  SET 2^14.992 (7.9%)  JUMP 2^14.051 (4.1%)  KECCAK 2^12.118 (1.1%)  MEMORY 2^19.401  BYTECODE 2^18.239  TOTAL_COMMITTED 2^23.743`
- V2 n=6: `MUL 2^17.91 (40.0%)  DEREF 2^17.221 (24.8%)  XOR 2^17.112 (23.0%)  SET 2^15.406 (7.0%)  JUMP 2^14.632 (4.1%)  KECCAK 2^12.7 (1.1%)  MEMORY 2^19.976  BYTECODE 2^18.239  TOTAL_COMMITTED 2^24.12`

Drift check, baseline n=2 vs T01 (0.557 s):
- Pass 1: 0.649 s (+16.5%), outside the 15% limit.
- Pass 2: 0.549 s (−1.4%), within the limit.
- Pooled median of the 6 timings: 0.605 s (+8.6%).
- Cycles, KECCAK, TOTAL_COMMITTED and proof size equal T01 exactly.

### Derived savings (DERIVED; V1/V2 UNSOUND)
- Cycle and KECCAK slopes are least squares over n = 2, 4, 6. With equal spacing this is (y6 − y2)/4; the n=4 residual is −10 to −15 cycles.
- The baseline cycle slope is 186,814.8, against the exact profiler value of 186,807.5.
- Prove time uses pooled medians of 6 timings per point: base 0.605 / 1.406 / 2.247 s, V1 0.479 / 1.068 / 1.273 s, V2 0.291 / 0.534 / 0.748 s.
- The pooled baseline prove slope is 401.0 ms/child (n=2→4) and 410.6 ms/child (n=2→6).

| variant | cycles saved / child | of 186,807.5 | KECCAK saved / child (exact; from log2 line) | of KECCAK / child | prove saved / child, n=2→4 | prove saved / child, n=2→6 |
|---|---:|---:|---:|---:|---:|---:|
| V1 (skip e1) | 22,993.5 | 12.31% | 4,084.5; 4,084.7 | 78.7% | 106.7 ms (26.6%) | 212.2 ms (51.7%) |
| V2 (skip e1+e2+e4) | 86,343.5 | 46.22% | 4,084.5; 4,084.7 | 78.7% | 279.5 ms (69.7%) | 296.4 ms (72.2%) |

The same savings against the T01 baseline medians (0.557 / 1.338 / 2.333 s):
- V1: 96.2 ms (24.6%, n=2→4); 245.6 ms (55.3%, n=2→6).
- V2: 269.0 ms (68.9%, n=2→4); 329.8 ms (74.3%, n=2→6).

Per-pass figures, same session (derived.csv, derived_pass2.csv):
- V1, n=2→6: 211.8 ms (59.7%) / 166.3 ms (36.9%). n=2→4: 189.5 ms / 69.0 ms.
- V2, n=2→6: 240.3 ms (67.7%) / 337.3 ms (74.8%). n=2→4: 236.5 ms / 323.5 ms.

### Stage breakdown of the traced (last) pass, ms and share (scripts/parse_trace.py)
| run | pass s | commit | PCS open | Keccak reduction | bus GKR |
|---|---:|---|---|---|---|
| base n=2 (p1 / p2) | 0.695 / 0.549 | 233.0 33.5% / 176.0 32.1% | 165.0 23.7% / 154.0 28.1% | 81.8 11.8% / 76.4 13.9% | 122.0 17.6% / 70.1 12.8% |
| V1 n=2 | 0.580 / 0.470 | 203.0 35.0% / 170.0 36.2% | 159.0 27.4% / 144.0 30.6% | 32.9 5.7% / 32.2 6.9% | 98.2 16.9% / 59.3 12.6% |
| V2 n=2 | 0.292 / 0.290 | 86.9 29.8% / 93.3 32.2% | 74.5 25.5% / 77.0 26.6% | 32.5 11.1% / 32.3 11.1% | 37.7 12.9% / 39.7 13.7% |
| base n=6 | 2.061 / 2.324 | 616.0 29.9% / 845.0 36.4% | 556.0 27.0% / 559.0 24.1% | 190.0 9.2% / 226.0 9.7% | 289.0 14.0% / 395.0 17.0% |
| V1 n=6 | 0.998 / 2.006 | 368.0 36.9% / 798.0 39.8% | 332.0 33.3% / 384.0 19.1% | 54.5 5.5% / 77.4 3.9% | 140.0 14.0% / 466.0 23.2% |
| V2 n=6 | 0.749 / 0.748 | 248.0 33.1% / 247.0 33.0% | 275.0 36.7% / 271.0 36.2% | 54.6 7.3% / 54.2 7.2% | 85.2 11.4% / 83.1 11.1% |

All stages, including execute, witness, constraints, replay and other, are in stages.csv and stages_pass2.csv. The V1 n=6 pass-2 traced pass (2.006 s) is an outlier: its other two passes took 1.609 and 1.342 s.

## Commands run
1. Profiled baseline runs, binary upstream/leanMultisig/target/release/leanvm, in results/T03/prof:
   - `DBG_PROF=1 DBG_PROF_DUMP=$PWD/base_n2.prof DBG_DISASM=$PWD/base.disasm DBG_PLACEHOLDERS=$PWD/base.placeholders /usr/bin/time -l .../target/release/leanvm recursion --n 2 --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 1`
   - The same with `--n 4` and `DBG_PROF_DUMP=$PWD/base_n4.prof`.
2. The pc→line tool, in proto/guest-lines:
   - `RUSTFLAGS="-C target-cpu=native" cargo +1.99.0 build --release`, then `./target/release/guest-lines ../../results/T03/prof/{base,v1,v2}.lines`.
   - Rebuilt with each branch checked out.
3. Variant branches and builds:
   - `git checkout -b research/d3-v1 df7d122…`; edit; `CARGO_TARGET_DIR=$PWD/target-d3v1 cargo +1.99.0 build --release -p leanvm-cli` (44.8 s); `git commit` (local).
   - The same for research/d3-v2 with target-d3v2 (42.5 s).
   - `git diff df7d122 > results/T03/v{1,2}.diff`; `git checkout research/baseline`.
4. Profiled variant runs: step 1's n=2 command with the target-d3v1 and target-d3v2 binaries, `DBG_PROF_DUMP=v{1,2}_n2.prof`.
5. Attribution:
   - `python3 scripts/attribute.py <prof> <lines> <disasm> --guest guest_<v>.py --json <v>_attr.json` for base n=2, base n=4, V1 n=2 and V2 n=2.
   - `python3 scripts/attribution_table.py prof/base_n2_attr.json prof/base_n4_attr.json attribution.csv`
6. Timing sweeps:
   - `python3 scripts/sweep.py` (pass 1, runs/) and `python3 scripts/sweep2.py` (pass 2, runs2/).
   - Each run was `run.sh <dir> <binary> <v>_n<n> recursion --n {2,4,6} --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 3 --tracing`, with a 30 s sleep before each.
7. Parsing:
   - `python3 scripts/derive.py runs summary.csv derived.csv` and `python3 scripts/derive.py runs2 summary_pass2.csv derived_pass2.csv`
   - `python3 scripts/pooled.py prove_pooled.csv`
   - `python3 scripts/parse_trace.py runs/{base,v1,v2}_n{2,6}.log --csv stages.csv` (likewise for runs2 → stages_pass2.csv)
   - `python3 scripts/run_table.py > run_table.md`

## Raw output
Node per-function profile head (baseline n=2, prof/base_n2_prof.log):
```
== DBG_PROF: cycles by function (392,988 total) ==
  66,642  16.958%  __loop395            (base-field query rows: opening_query inlined, lane packing + dot products)
  43,802  11.146%  keccak_layer__L0
  16,555   4.213%  __jump_tables        (one-off prologue filling match tables)
  12,250   3.117%  walk_path__L14_L7
  10,426   2.653%  decode_query_windows__L21_L7
```
Attribution checks (prof/base_n2_attr.txt):
```
steps 392988; attributed 392988.0; roots ['__jump_tables', 'main']; verify_sub calls 2, inclusive 358701.0
entry-count mismatches (non-loop fns): 2 [('__jump_tables', 1, 0), ('main', 1, 0)]
boundary-ambiguous inlined cycles (left on previous bucket): 26
```
Variant cross-check (bucket diffs, n=2):
```
V1 total diff 52111: e1:Merkle cap 4554, e1:Merkle leaf+path 41749, e2:query rows -354, __jump_tables 6162
V2 total diff 178811: e1 4554+41749, lane packing 38008, query rows 57894, residual 29892, row eq weights 432,
                      e4 final message 96 + final check 6, level batching 20, terminal -2, __jump_tables 6162
```
Example run output (runs2/v2_n6.log):
```
recursion 6→1, over leaves of 250 leanXMSS signatures
  cycles (VM steps)           : 616,062
  proof size                  : 217.3 KiB
  verifying                   : 12.004 ms
```
Full logs: runs/, runs2/, prof/*_prof.log.

## Files changed or created
- proto/guest-lines/ (Cargo.toml, Cargo.lock seeded from upstream, src/main.rs): dumps the compiled guest's function table and pc→source line via the public `unified_guest()`.
- upstream/leanMultisig on research/d3-v1 and research/d3-v2: crates/rec_aggregation/guests/lean_ethereum.py. UNSOUND variants, local commits only.
- upstream/leanMultisig/.git/info/exclude: added target-d3v1/ and target-d3v2/.
- results/T03/T03_report.md: this report.
- results/T03/attribution_notes.md: method, location table and exact attribution.
- results/T03/attribution.csv: per-bucket and per-stage cycles/child, share, KECCAK and FS cycles.
- results/T03/summary.csv, summary_pass2.csv, run_table.md: per-run data.
- results/T03/derived.csv, derived_pass2.csv, prove_pooled.csv: derived savings.
- results/T03/stages.csv, stages_pass2.csv: stage breakdowns.
- results/T03/v1.diff, v2.diff: variant diffs against df7d122.
- results/T03/runs/, runs2/: raw run logs (cmd, date, power, swap before/after).
- results/T03/build/: variant build logs.
- results/T03/prof/: profiler dumps, disassemblies and pc→line tables (gzipped); guest sources (guest_base.py, guest_v1.py, guest_v2.py); attribution JSON and text.
- results/T03/scripts/: attribute.py, attribution_table.py, derive.py, pooled.py, run_table.py, sweep.py, sweep2.py, plus copies of T01's run.sh, parse_runs.py and parse_trace.py.

## Problems and deviations
- **Steps 2 and 3 both done.** Step 2 applied, so step 3 was formally optional. I ran both: the variants give the prove-time numbers and cross-check the attribution.
- **Second timing pass.** Pass 1's drift check missed the 15% limit (+16.5%). I ran a second full interleaved pass (+18 runs, not in the task) and report both passes plus pooled medians. Pass 2 is −1.4%.
- **Extra baseline runs.** Baseline n=4 and n=6 were run as same-session references; the task asked only for n=2.
- **Timing noise and paging:**
  - Baseline n=6 was memory-pressured in both passes (swap +978 / +956 MiB, footprint 3.10 GiB); baseline n=4 was also pressured in pass 1 (+356 MiB). This inflates n=2→6 savings, so n=2→4 is the cleaner estimate.
  - V1 n=4 and n=6 medians differ by 37–49% between passes; V2's medians agree within 1% at n=2 and n=6, and differ by 10.3% at n=4 (0.568 vs 0.515 s).
  - Prove time is not linear in n, because padded committed sizes step at powers of two. "Per-child prove time" is therefore a crude slope.
- **Prove time ≠ cycles.** Prove-time savings exceed cycle savings because TOTAL_COMMITTED and the KECCAK table shrink. V2 at n=2 halves TOTAL_COMMITTED (2^23.842 → 2^22.822). The variants' bytecode is also smaller (BYTECODE 2^18.899 → 2^18.667 / 2^18.239), which a real accumulator verifier would also get, but less cleanly.
- **Classification choices** the lead may want to re-map (all in attribution.csv):
  - Lane packing (`pack64x2` range checks of opened lanes) is reported separately, because it serves both e1 and e2.
  - Query sampling and PoW are reported as (eq): neither W nor e3. V2 keeps them, following the task literally.
  - V2 keeps the final-message read and absorb (110 cycles/child) for transcript fidelity, and removes only its evaluation and the final check.
- **Fixed cost change.** Both variants also shrink the fixed `__jump_tables` prologue by 6,162 cycles: leaf cycles go 219,994 → 213,832. This cancels in per-child slopes.
- **The 354-cycle V1 overhead** in `e2:query rows` (the path hint's StackBuf) was measured, not explained.
- **Install and network:** nothing installed; no network use beyond cargo builds of path crates. All dependencies came from the existing lockfile and cache.

## Suggested next step
Size an accumulator that defers W + packing + eq (about 100k cycles/child, 53.5%) but must still verify e3 (about 21k/child). Compare that with keeping e3 and replacing the Merkle/Keccak-heavy e1 by a cheaper hash: e1 is 78.7% of per-child KECCAK.
=== END REPORT ===

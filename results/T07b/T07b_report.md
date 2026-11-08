=== RESULT REPORT T07b ===
Status: partial (Parts A and B done, B0U misses its JUMP target, Part C skipped: swap 2,492.5 MiB >= 512 MiB)
Machine: Apple M2 MacBook Air, 4P+4E = 8 cores, 8 GiB RAM, macOS 26.5.2 (25F84), AC power, battery 100% charged
Toolchain: rustc 1.99.0 (b940084d7 2026-09-28), `-C target-cpu=native` from .cargo/config.toml. No Lean.
Repo state (upstream/leanMultisig, all local, nothing pushed; tree clean, research/baseline checked out at df7d122abbe25cf12e5c8ae992ce6d3505f75372):
- research/dbg-tables f060baa0da799261543d0c11e8ad94bba4c3c049 (baseline + DBG_TABLES print), built in target-dbg/; this is the "base" binary of the sweep
- research/b0u 0490e826d6126f02647ebeef43520e74992cc0b6 (SOUND), target-b0u/
- research/d3-v6 5da84ce0e756ba1986bfba90d830ac50416afac8 (UNSOUND), target-d3v6/; its parent 7f2cbf11690fefac2259925645d135095ffaa1f5 is V5 + DBG_TABLES (used for Part A's V5 runs, rebuilt over by V6)
- research/d3-v6u 3518e28c44375b687419f342b71a49ca5b586614 (UNSOUND), target-d3v6u/
- proto/guest-lines was rebuilt against V6; rebuild before using it on another branch.

## Summary
- **H-PAD is confirmed on counts.** TC = 4*2^h + 2^kbc + 2^(6+tau_K) + sum_t w_t*2^tau_t recomputes exactly (residual 0) in all 8 runs. At n=6, baseline (mu 26) and V5 (mu 25) differ only in JUMP (2^17 vs 2^16), and that one crossing is the whole 917,504-word gap.
- **The timing question stays open.** Part C did not run, so whether T07's n=6 gain comes from B'-L1 or from padding is not measured. One relevant count: at n=6 the words actually committed differ by only 3.0% (34.6M baseline vs 33.55M V5), because the commitment is pruned to whole lanes.
- **B0U misses the JUMP target: n=6 JUMP 75,221 against the 63,000 target.** It meets the bytecode target (508,049) and crosses no new power of two, and tests match baseline (62 pass, 3 ignored on both). 9,300 of 12,665 JUMP rows per child are `assert_in_k` checks and 1,488 are runtime `match` dispatches; all `mul_range` loops together account for only 567.
- **V6 child-1 saving is 32,870 cycles** (98.5% of 33,381.5), so a = 511.5, inside the lead's 500 to 1,000 estimate. V6 and V6U reach mu 25 at n=6; n=7 tips to mu 26 because memory crosses 2^21.
- **All 28 sweep runs verify.**

## Results

### 1. Part A: committed-size formula (line references at df7d122)
- `TOTAL_COMMITTED` is `Witness::committed_size`, the sum of `2^n_vars` over non-virtual columns (crates/leanvm_core/src/cpu/layout.rs:194-201, printed at cpu/mod.rs:421).
- Column log-sizes: layout.rs:212-240 (`col_kappa_sources`), 269-276.
- Table heights: `tau_t = max(ceil log2 rows_t, floor_t)` (layout.rs:499-501). Floors: 0, except KECCAK at log2(MIN_STEPS) = 9 (tables.rs:366, keccak.rs:37).
- Memory: `h = max(ceil log2 mem_used, 16)` (execute.rs:1064, MIN_LOG_MEM cpu/mod.rs:40), doubled until committed_log >= min_log_committed (execute.rs:1067-1070). Aggregation sets min_log_committed = MU_MIN = 22 (node.rs:323, child.rs:261). So MEMORY is padded to a power of two.
- Bytecode: the program is public, not committed. Only BFCNT is, at `2^kbc` with kbc = 19 here (padded).
- **mu = max(ceil log2 TC, MIN_MU = 15)** (witness.rs:92, pcs.rs:49).
- **Layout beyond the total:** columns tile largest first, ties by index, so offsets are aligned by construction (witness.rs:57-74). The prover commits `n_lanes = ceil(TC / 2^(mu-6))` whole lanes of `2^(mu-6)` words, and never encodes the zero tail past them (witness.rs:95, LOG_BATCH = 6 from INITIAL_FOLDING_FACTOR, pcs.rs:40). So cost within one mu scales with lanes, not with 2^mu.

Formula: TC = 4*2^h + 2^kbc + 2^(SLOT_LOG + tau_K) + sum_t w_t * 2^tau_t, SLOT_LOG = 6.

| column group | committed columns per row (w) | size per column | source |
|---|---|---|---|
| MEM_LO, MEM_HI, MEM_TOP, MFCNT | 4 | 2^h | layout.rs:14-17 |
| BFCNT | 1 | 2^kbc | layout.rs:18 |
| QKECCAK | 64 slots (50 state + 14 spare) | 2^tau_K per slot | layout.rs:27, 68 |
| XOR, MUL | 15 each | 2^tau | tables.rs:470 |
| SET | 8 | 2^tau | tables.rs:552 |
| DEREF | 15 | 2^tau | tables.rs:623 |
| JUMP | 14 | 2^tau | tables.rs:726 |
| KECCAK | 26 of 90 (50 lanes and 14 spare-slot columns are virtual) | 2^tau | tables.rs:875, layout.rs:234-238 |

The lead's fits match: DEREF 15, MUL 15, JUMP 14. At n=2, 2^18*15 + 2^16*8 = 4.456M (fit 4.45M) and 2^14*90 + 4*2^20 = 5.669M (fit 5.68M, KECCAK+QKECCAK = 90 words per row).

TC recompute (command: `DBG_TABLES=1 /usr/bin/time -l <bin> recursion --n <n> --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 1`; recompute `scripts/parse_tables.py`):

| variant | n | TC recomputed (words) | TC placed | residual | printed 2^x | log2 recomputed |
|---|---|---|---|---|---|---|
| baseline | 2 | 15,040,512 | 15,040,512 | 0 | 23.842 | 23.842350 |
| baseline | 4 | 29,032,448 | 29,032,448 | 0 | 24.791 | 24.791163 |
| baseline | 6 | 34,406,400 | 34,406,400 | 0 | 25.036 | 25.036174 |
| baseline | 8 | 57,540,608 | 57,540,608 | 0 | 25.778 | 25.778077 |
| V5 (UNSOUND) | 2 | 14,057,472 | 14,057,472 | 0 | 23.745 | 23.744834 |
| V5 (UNSOUND) | 4 | 23,134,208 | 23,134,208 | 0 | 24.464 | 24.463524 |
| V5 (UNSOUND) | 6 | 33,488,896 | 33,488,896 | 0 | 24.997 | 24.997179 |
| V5 (UNSOUND) | 8 | 45,744,128 | 45,744,128 | 0 | 25.447 | 25.447083 |

Printed-vs-recomputed differences are at most 0.0005 of an exponent (3-decimal rounding). Cycle counts reproduce T07 exactly.

**H-PAD verdict: confirmed.** At n=6 all taus and h match between baseline and V5 except JUMP (76,203 rows, 2^17; 64,891 rows, 2^16). TC(base) - TC(V5) = 14 * 2^16 = 917,504 exactly. V5 headroom is 645 JUMP rows (the lead's ~630). Lanes at n=6: baseline 33 at mu 26 (committed 34,603,008); V5 64 at mu 25 (committed 33,554,432).

### 2. B0U (SOUND), research/b0u
Generator: results/T07b/scripts/make_b0u.py. Scope: arm m_idx = 10 only (rate 2, mu 25, the only arm these leaves reach), by compile-time dispatch; all other arms keep their loops. Rationale: the 28 arms would multiply the bytecode cost far past the budget.

JUMP-row profile of child 1 (n=2 minus n=1), results/T07b/prof/jump_rank_full.txt:

| source | JUMP rows per child |
|---|---|
| `assert_in_k` (packing checks) | 9,300 |
| runtime `match` dispatch (windows, column selectors) | 1,488 |
| `return` | 616 |
| `mul_range` loops | 567 |
| other calls | 391 |
| runtime `if` | 303 |
| total | 12,665 |

Unrolled loops (line numbers at df7d122; per-loop JUMP from single-edit builds at n=2, realised positions cause a few tens of rows of noise, `scripts/per_loop_b0u.sh`):

| line | loop | trip count | bytecode added | JUMP saved per child |
|---|---|---|---|---|
| 1566 | position squeezes L0..L4 | 13, 5, 3, 3, 2 = 26 | 321 | 26 |
| 1410 | extension-row Merkle queries, L1 | 45 | 7,723 | 42 |
| 1410 | L2 | 28 | 4,816 | 21 |
| 1410 | L3 | 21 | 3,619 | 13 |
| 1410 | L4 | 16 | 2,764 | 7 |
| sum / whole B0U | | | 19,243 (488,806 -> 508,049) | 109 single-edit sum; whole-B0U 152 at n=2, 168.5 slope n=2..8 |

The rest of the constant-trip work I did not unroll: L1410 L0 (56 iterations, 596 instructions each), L1734 residual (26 iterations, 14k instructions) and L3113 (8 iterations, 657 instructions). No remaining set closes the gap: even removing every `mul_range` JUMP gives about 72.8k at n=6, and the 9,300 `assert_in_k` rows are checks that may not be removed.

Targets:

| target | result |
|---|---|
| n=6 JUMP <= 63,000 | **FAILED: 75,221** (baseline 76,203) |
| bytecode <= 516,096 | met: 508,049 |
| no table crosses a power of two that baseline does not (n=2..8) | met. Only difference: SET at n=5 is 2^16 vs 2^17, a reduction. mu is identical at every n. |

Tests: `cargo +1.99.0 test --release -p rec_aggregation -p leanvm_core`, run on df7d122 and on B0U. 62 passed, 0 failed, 3 ignored on both; per-test lines are identical (diff empty). Suites: leanvm_core 21 unit, 6 verifiers (1 ignored); rec_aggregation 38 unit (2 ignored: aggregate_round_trips_through_the_wire, aggregate_three_levels). Logs: tests_base.log, tests_b0u.log.

### 3. V6 (UNSOUND), research/d3-v6, profiled at n=2
Generator: results/T07b/scripts/make_v6.py, arm 10 only (bytecode 499,653).

Child 1 cost in V6 = (n=2 total - n=1 total) - child 0's k-dependent work = (360,847 - 206,730) - 175 = 153,942 cycles. Baseline child 1 = 392,988 - 206,176 = 186,812.

| | cycles |
|---|---|
| child 1 saving | **32,870** |
| expected | 33,381.5 - a, a = 500 to 1,000 |
| measured a | 511.5 (1.53% of 33,381.5), within the 3% band |

Added work (measured):

| item | when | cycles |
|---|---|---|
| per-child batch work `v6_common` (T_B absorb, 45 combines, terminal combine) | per child | 230 |
| eq(kappa, c) loop, k=1 | per child | 23 |
| dispatch `open_stacked__L10` | per child | 38 |
| T_B header + zeroing (`v6_batch_start`) | once, child 0 | 95 |
| beta squeeze loop, k=1 | once, child 0 | 44 |
| k extra fold rounds, k=1 (loop 61 + opening_fold 47) | once, child 0 | 108 |

Not attributed separately: about 220 of a (own level-1 lambda squeeze, re-enabled L1 OOD-eq about 76 from T07's figures, scratch caps). The added-work items above confirm by profile that the batch work executes.

Slopes n=2..8 (cycles per child): baseline 186,872.7; V6 154,037.3; V6U 151,851.7. Saved by V6: 32,835.3 per child.

Emulation limits (V6):
- A child's proof opened its own positions, so its hinted rows and paths do not hash to its cap at child 0's positions. Children >= 1 hash at the shared positions into a fresh scratch cap and flag buffer per query. Instruction counts match the real walk; the path is unconstrained, and the scratch allocation adds a little per query.
- Children >= 1 read child 0's fold and tail challenges and terminal point (the L0 residual uses them too), so the terminal check holds vacuously.
- T_B and the k fold rounds run on a separate sponge with dummy values.

### 4. Count table (28 runs; rows/2^tau per table; `DBG_TABLES=1`, `--repeat 1`, 5 s sleep; V6, V6U are UNSOUND)
Command: `DBG_TABLES=1 /usr/bin/time -l <bin> recursion --n <n> --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 1` via scripts/sweep.py, 11:09 to 11:17. Bins: target-dbg, target-b0u, target-d3v6, target-d3v6u. Every verify is ok (`sig.verify` succeeded).

| variant | n | cycles | XOR | MUL | SET | DEREF | JUMP | KECCAK | h | TC | mu | lanes | KiB | verify |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 2 | 392,988 | 105,037/2^17 | 143,592/2^18 | 37,987/2^16 | 70,472/2^17 | 25,481/2^15 | 10,419/2^14 | 20 | 2^23.842 | 24 | 58 | 232.6 | ok |
| base | 3 | 579,815 | 157,338/2^18 | 215,139/2^18 | 48,413/2^16 | 105,151/2^17 | 38,165/2^16 | 15,609/2^14 | 20 | 2^24.058 | 25 | 34 | 218.7 | ok |
| base | 4 | 766,603 | 209,641/2^18 | 286,666/2^19 | 58,848/2^16 | 139,804/2^18 | 50,849/2^16 | 20,795/2^15 | 21 | 2^24.791 | 25 | 56 | 239.9 | ok |
| base | 5 | 953,421 | 261,944/2^18 | 358,211/2^19 | 69,277/2^17 | 174,479/2^18 | 63,523/2^16 | 25,987/2^15 | 21 | 2^24.817 | 25 | 57 | 238.9 | ok |
| base | 6 | 1,140,247 | 314,246/2^19 | 429,758/2^19 | 79,708/2^17 | 209,160/2^18 | 76,203/2^17 | 31,172/2^15 | 21 | 2^25.036 | 26 | 33 | 227.4 | ok |
| base | 7 | 1,327,393 | 366,556/2^19 | 501,436/2^19 | 90,164/2^17 | 243,991/2^18 | 88,881/2^17 | 36,365/2^16 | 22 | 2^25.447 | 26 | 44 | 236.5 | ok |
| base | 8 | 1,514,224 | 418,859/2^19 | 572,981/2^20 | 100,603/2^17 | 278,676/2^19 | 101,558/2^17 | 41,547/2^16 | 22 | 2^25.778 | 26 | 55 | 248.3 | ok |
| b0u | 2 | 382,502 | 104,755/2^17 | 139,356/2^18 | 34,848/2^16 | 67,954/2^17 | 25,177/2^15 | 10,412/2^14 | 20 | 2^23.842 | 24 | 58 | 231.8 | ok |
| b0u | 3 | 564,050 | 156,915/2^18 | 208,785/2^18 | 43,700/2^16 | 101,370/2^17 | 37,677/2^16 | 15,603/2^14 | 20 | 2^24.058 | 25 | 34 | 219.5 | ok |
| b0u | 4 | 745,569 | 209,077/2^18 | 278,194/2^19 | 52,554/2^16 | 134,758/2^18 | 50,189/2^16 | 20,797/2^15 | 21 | 2^24.791 | 25 | 56 | 239.4 | ok |
| b0u | 5 | 927,148 | 261,239/2^18 | 347,621/2^19 | 61,411/2^16 | 168,176/2^18 | 62,713/2^16 | 25,988/2^15 | 21 | 2^24.791 | 25 | 56 | 239.5 | ok |
| b0u | 6 | 1,108,703 | 313,400/2^19 | 417,050/2^19 | 70,256/2^17 | 201,590/2^18 | 75,221/2^17 | 31,186/2^15 | 21 | 2^25.036 | 26 | 33 | 227.0 | ok |
| b0u | 7 | 1,290,597 | 365,569/2^19 | 486,610/2^19 | 79,143/2^17 | 235,166/2^18 | 87,734/2^17 | 36,375/2^16 | 22 | 2^25.447 | 26 | 44 | 236.8 | ok |
| b0u | 8 | 1,472,161 | 417,731/2^19 | 556,037/2^20 | 87,996/2^17 | 268,584/2^19 | 100,243/2^17 | 41,570/2^16 | 22 | 2^25.778 | 26 | 55 | 246.6 | ok |
| v6(UNSOUND) | 2 | 360,847 | 96,566/2^17 | 131,878/2^18 | 35,589/2^16 | 64,557/2^16 | 23,041/2^15 | 9,216/2^14 | 20 | 2^23.745 | 24 | 54 | 229.1 | ok |
| v6(UNSOUND) | 3 | 514,951 | 140,329/2^18 | 191,615/2^18 | 43,576/2^16 | 92,994/2^17 | 33,238/2^16 | 13,199/2^14 | 20 | 2^24.058 | 25 | 34 | 218.5 | ok |
| v6(UNSOUND) | 4 | 668,803 | 184,078/2^18 | 251,258/2^18 | 51,529/2^16 | 121,343/2^17 | 43,410/2^16 | 17,185/2^15 | 21 | 2^24.464 | 25 | 45 | 228.4 | ok |
| v6(UNSOUND) | 5 | 822,968 | 227,849/2^18 | 311,029/2^19 | 59,530/2^16 | 149,787/2^18 | 53,602/2^16 | 21,171/2^15 | 21 | 2^24.791 | 25 | 56 | 239.4 | ok |
| v6(UNSOUND) | 6 | 976,882 | 271,599/2^19 | 370,704/2^19 | 67,488/2^17 | 178,169/2^18 | 63,771/2^16 | 25,151/2^15 | 21 | 2^24.997 | 25 | 64 | 247.1 | ok |
| v6(UNSOUND) | 7 | 1,131,131 | 315,357/2^19 | 430,510/2^19 | 75,473/2^17 | 206,705/2^18 | 73,949/2^17 | 29,137/2^15 | 22 | 2^25.351 | 26 | 41 | 233.0 | ok |
| v6(UNSOUND) | 8 | 1,285,071 | 359,108/2^19 | 490,183/2^19 | 83,437/2^17 | 235,089/2^18 | 84,138/2^17 | 33,116/2^16 | 22 | 2^25.447 | 26 | 44 | 236.1 | ok |
| v6u(UNSOUND) | 2 | 354,075 | 96,382/2^17 | 129,192/2^17 | 33,452/2^16 | 62,974/2^16 | 22,862/2^15 | 9,213/2^14 | 20 | 2^23.527 | 24 | 47 | 221.9 | ok |
| v6u(UNSOUND) | 3 | 505,981 | 140,085/2^18 | 188,121/2^18 | 40,679/2^16 | 90,904/2^17 | 32,988/2^16 | 13,204/2^14 | 20 | 2^24.058 | 25 | 34 | 218.7 | ok |
| v6u(UNSOUND) | 4 | 657,651 | 183,774/2^18 | 246,956/2^18 | 47,879/2^16 | 118,750/2^17 | 43,101/2^16 | 17,191/2^15 | 21 | 2^24.464 | 25 | 45 | 228.9 | ok |
| v6u(UNSOUND) | 5 | 809,624 | 227,485/2^18 | 305,919/2^19 | 55,127/2^16 | 146,691/2^18 | 53,224/2^16 | 21,178/2^15 | 21 | 2^24.791 | 25 | 56 | 239.7 | ok |
| v6u(UNSOUND) | 6 | 961,353 | 271,175/2^19 | 364,786/2^19 | 62,333/2^16 | 174,568/2^18 | 63,333/2^16 | 25,158/2^15 | 21 | 2^24.974 | 25 | 63 | 245.2 | ok |
| v6u(UNSOUND) | 7 | 1,113,428 | 314,873/2^19 | 423,784/2^19 | 69,570/2^17 | 202,605/2^18 | 73,456/2^17 | 29,140/2^15 | 22 | 2^25.351 | 26 | 41 | 233.2 | ok |
| v6u(UNSOUND) | 8 | 1,265,185 | 358,564/2^19 | 482,649/2^19 | 76,780/2^17 | 230,486/2^18 | 83,585/2^17 | 33,121/2^16 | 22 | 2^25.447 | 26 | 44 | 236.8 | ok |

CSV: results/T07b/count_table.csv.

### 5. Capacity table (largest n with mu <= 25; n+1 crossings)
| variant | largest n, mu <= 25 | n+1: table that crosses (rows at n, headroom in rows, % of 2^tau) | what tips mu |
|---|---|---|---|
| baseline | 5 (TC 2^24.817) | XOR 261,944, 200, 0.08%; JUMP 63,523, 2,013, 3.07% | XOR alone leaves TC at 33,488,896 (mu 25); JUMP's +917,504 pushes over 2^25 |
| B0U | 5 (2^24.791) | XOR 261,239, 905, 0.35%; SET 61,411, 4,125, 6.29%; JUMP 62,713, 2,823, 4.31% | same: TC 34,406,400 at n=6 |
| V6 (UNSOUND) | 6 (2^24.997, 64 lanes) | MEMORY 1,835,923, 261,229, 12.46%; JUMP 63,771, 1,765, 2.69% | MEMORY +8.39M words |
| V6U (UNSOUND) | 6 (2^24.974, 63 lanes) | MEMORY 1,820,818, 276,334, 13.18%; SET 62,333, 3,203, 4.89%; JUMP 63,333, 2,203, 3.36% | MEMORY +8.39M words |

### 6. Part C: skipped
`sysctl vm.swapusage`: used 2,492.50 MiB of 4,096 MiB at 11:17:28; 2,444.50 MiB at 11:18:07 (results/T07b/partC_skip_swap.txt). Rule: skip at >= 512 MiB, no reboot. Swap was 0 MiB at session start, 1,688 MiB by the sweep's first run, and grew further at n=7 and n=8 (table in Raw output). No timing numbers exist for this task. The T07 n=6 attribution therefore remains open.

## Commands run
1. Read T07 report, make_v5.py, v5_itemized, CLAUDE; source reading for Part A (layout.rs, witness.rs, execute.rs, tables.rs, keccak.rs, node.rs, pcs.rs).
2. `git checkout -b research/dbg-tables df7d122...`; edit cpu/mod.rs; `CARGO_TARGET_DIR=target-dbg cargo +1.99.0 build --release -p leanvm-cli`; commit f060baa0d.
3. `git checkout -b research/d3-v6 research/d3-v5 && git cherry-pick f060baa0...`; build target-d3v6 (V5 + print); Part A runs via scripts/run.sh at n=2,4,6,8 for base and V5; `python3 scripts/parse_tables.py partA base v5`.
4. `DBG_PROF=1 DBG_PROF_DUMP=... DBG_DISASM=... <target-dbg>/release/leanvm recursion --n {1,2} ...`; `scripts/jump_rank.py`.
5. `git checkout -b research/b0u research/dbg-tables`; `python3 scripts/make_b0u.py <guest>`; build target-b0u; commit 0490e826d; `scripts/per_loop_b0u.sh`; rebuilt final B0U afterwards. Tests: scripts/run_tests.sh in detached worktrees (results/T07b/wt-{base,b0u}, removed).
6. `git checkout research/d3-v6` (V5+print); `python3 scripts/make_v6.py <guest>`; build target-d3v6; commit 5da84ce0e. Profiles n=1,2; `proto/guest-lines` rebuilt against V6.
7. `git checkout -b research/d3-v6u research/d3-v6`; `python3 scripts/make_v6u.py <guest>`; build target-d3v6u; commit 3518e28c4.
8. `python3 -u scripts/sweep.py`; `python3 scripts/analyze_sweep.py`.
9. `sysctl vm.swapusage; memory_pressure | tail -1 > partC_skip_swap.txt`. Part C not started; scripts/run_timing.py is ready.
10. `git checkout research/baseline`; worktrees removed; `git diff` saved (dbg_tables.diff, b0u.diff, v6.diff, v6u.diff); prof dumps gzipped.

## Raw output
```
# V6 n=2 / n=1 (prof/v6_n2_prof.log): cycles 360,847 / 206,730; bytecode 499,653; V6 functions (n=2): v6_child0__L10 3,141; v6_child_rest__L10 923; v6_common 460; v6_batch_start 95; open_stacked__L10 76; v6_k_rounds 28; v6_opening_queries_free 22
# k-dependent child-0 work at n=2: eq loop 23; beta loop 44; k-round loop 61; opening_fold 47 per call (1128 cycles / 24 calls at n=1)
# V6U n=2: cycles 354,075; bytecode 523,891 (397 under 2^19); proof 221.9 KiB
# B0U n=2: cycles 382,502; bytecode 508,049
# swap (MiB used, before -> after) at n=7..8: base7 1624->1624; b0u7 1616->1820; v67 1820->1804; v6u7 1788->1959; base8 1959->2519; b0u8 2463->2837; v68 2821->2677; v6u8 2653->2597
# peak footprints at n=8 (GiB): base 4.30, b0u 4.30, v6 3.58, v6u 3.58 (70% of RAM = 5.6 GiB)
```
Per-run logs: results/T07b/partA/, sweep/, tests_*.log, prof/.

## Files changed or created
- leanMultisig branches listed under Repo state. .git/info/exclude gained target-dbg/, target-b0u/, target-d3v6/, target-d3v6u/.
- results/T07b/T07b_report.md: this report.
- results/T07b/{dbg_tables,b0u,v6,v6u}.diff: diffs of the four changes.
- results/T07b/count_table.csv, sweep_analysis.txt, partA/, sweep/, partC_skip_swap.txt, sweep.out, tests_base.log, tests_b0u.log, b0u_commit.txt, v6_commit.txt, v6u_commit.txt, build/.
- results/T07b/prof/: gzipped dumps, disassemblies, line tables, jump_rank_{base,full}.txt, per_loop/ logs, guest_v6.py.
- results/T07b/scripts/: run.sh, parse_tables.py, jump_rank.py, make_b0u.py, per_loop_b0u.sh, run_tests.sh, make_v6.py, make_v6u.py, sweep.py, analyze_sweep.py, run_timing.py.
- NOTES.md: T07b entry.

## Problems and deviations
- **Part C skipped by the task's swap rule.** Consequence: the task's main question (B'-L1 or padding at n=6) has count evidence only.
- **B0U could not reach the JUMP target.** The profile shows the rows are mostly checks and runtime dispatch, not loops. The Merkle paths are already `unroll`ed window walks with runtime `match`. It unrolls only arm 10.
- **V6U deviates from "same loops":** child 0's L4 Merkle query loop stays a loop, because unrolling it would exceed 2^19 bytecode. V6U is at 523,891 (397 instructions under 2^19). Children >= 1 unroll their 45 L1 queries; child 0 unrolls L1..L3.
- **V6 is arm 10 only** (mu 25, rate 2), and other arms stay V5. Scratch caps and shared challenges are as listed in section 3.
- **Single-edit JUMP deltas are noisy** (leaves differ between builds, so realised query positions shift the `if`/`match` counts). The whole-B0U numbers are the reliable ones.
- **Part A V5 runs used research/d3-v6's parent** (7f2cbf116) because the task allows modifications only on the named branches; that binary was replaced by V6 in target-d3v6/.
- Nothing was pushed or posted, nothing outside results/ was deleted, and no environment variables or process command lines were printed.

## Suggested next step
Run Part C first, immediately after a reboot (or on Linux), since builds and the sweep pushed swap past the limit here; `scripts/run_timing.py` needs only the four existing binaries. To measure B'-L1 alone against the padding, compare V6 with baseline at n=4, where mu is equal (25) in both.
=== END REPORT ===

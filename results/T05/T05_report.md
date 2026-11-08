=== RESULT REPORT T05 ===
Status: done
Machine: Apple M2 MacBook Air (4P+4E = 8 cores), 8 GiB RAM, macOS 26.5.2 (25F84); AC power, battery 100% charged; fanless. Swap in use before the sweep: about 2.9 GiB of 4 GiB.
Toolchain: rustc 1.99.0 (b940084d7 2026-09-28) via `cargo +1.99.0`; `-C target-cpu=native` from leanMultisig's .cargo/config.toml; python3 for analysis. No Lean.
Repo state:
- upstream/leanMultisig: research/baseline = df7d122abbe25cf12e5c8ae992ce6d3505f75372, unmodified, checked out at the end, tree clean (`git status --short` empty).
- New local branches from df7d122. Both are UNSOUND and measurement only, not pushed:
  - research/d3-v3 = b117ddd778a6c79703f9344b16b11d0a437559ed (V3)
  - research/d3-v4 = 3feeae43e026541294480f507dd9e515d9df1ab9 (V4)
- Build dirs target-d3v3/ and target-d3v4/ were added to .git/info/exclude (local only).
- The baseline binary is the existing target/release/leanvm (df7d122; its cycles reproduce T03 exactly).
- proto/guest-lines: rebuilt in place against the V3 and V4 sources to dump their pc→line tables; no source change. proto/ is not a git repo.

## Summary
- **Per-level attribution is exact.** The T03 profiles (base n=2, n=4) were re-attributed with a WHIR-level label per pc. The unrolled level loops are laid out in program order, and the per-level callees are specialised per level. No new baseline runs were needed.
  - Per child, the opening (in `open_stacked`) costs 103,122.5 cycles (55.2% of 186,807.5). By level: L0 56,931.5 (30.5%), L1 18,815.5 (10.1%), L2 11,460.5 (6.1%), L3 8,874.5 (4.8%), L4 6,435.5 (3.4%), tail 335, setup 270.
  - It sums to the T03 opening buckets exactly (0.000%), and to every T03 bucket within 0.05 cycles.
  - KECCAK per level is 2,171.0 / 843.0 / 523.0 / 379.0 / 280.5 / 3, against T04's analytic 2,171.1 / 845.4 / 524.2 / 378.4 / 280.0 / 3. The largest gap is −2.4, at L1.
- **Variants.**
  - V3 (UNSOUND) keeps only L0's proximity checks per child; V4 (UNSOUND) keeps L0 and L1. Both skip the residual at every level, the final-message evaluation and the final check. The transcript is unchanged.
  - Profiled at n=2, cycles saved excluding the fixed prologue: V3 104,483 (52,241.5 per child), 100.03% of the step-1 prediction; V4 74,667 (37,333.5 per child), 99.98%.
  - Across n = 2, 4, 6 and both passes, all 18 node proofs verify under the CLI.
- **Prove-time savings (derived, pooled medians, 6 repeats per point).** Both variants come out the same, because they have identical TOTAL_COMMITTED at every n (2^23.403 / 2^24.369 / 2^24.791). Prove time follows committed size here, not cycles.
  - Per child, 2→4 slope: V3 155.0 ms (43.0%), V4 154.7 ms (42.9%).
  - The 2→6 slope gives 207 to 208 ms (about 60%), but it is inflated by a mu step: at n=6 the baseline node is mu=26 and V3 and V4 are mu=25.
  - n=6 saving: V3 0.919 s (47.3%), V4 0.912 s (46.9%).
- **Native opening (prover).** Per-level cost is almost entirely `Commit level k`, the extension-encode NTT of the folded oracle:
  - leaf (2 traces): L1 127.0, L2 56.2, L3 24.0, L4 10.3 ms;
  - 2-child node (5 traces): 59.2 / 25.9 / 11.1 / 5.0 ms.
  - L0's work inside `PCS open` is 52.1 ms (leaf) and 40.2 ms (node), mostly `Basis`. L1..L4 non-commit work is 2.5 ms or less in total.
- **Drift.** Baseline n=2 gives 0.586 s (−3.1%) in pass 1 and 0.543 s (−10.2%) in pass 2, against 0.605 s. Both are within 15%.

## Results

### 1. Per-level attribution per child (baseline, outer rate 2, 250-sig leaves). Exact, from `DBG_PROF_DUMP`; slope n=2→4 of results/T03/prof/base_n{2,4}.prof.*

Commands: `scripts/attribute_lv.py` on the T03 node dumps, then `scripts/per_level_table.py prof/base_n2_lv.json prof/base_n4_lv.json .`.

Cycles per child. "decode" is `decode_query_windows` plus `query_ptr` (lines 1576-1578), split out of T03's `eq:query sampling`; "squeezes" is the rest of that bucket.

| level | Merkle cap | leaf+path | lane packing | query rows | row eq wts | residual | squeezes | decode | PoW | fold sumcheck | OOD | level roots | batching | final msg | point rot. | setup | **total** | **share of 186,807.5** | **KECCAK** | T04 KECCAK | diff |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| setup | | | | | | | | 256 | | | | | | | | 14 | **270.0** | 0.14% | 0 | | |
| L0 | 1,050 | 10,952.5 | 10,864 | 17,678 | 60 | 9,466 | 597 | 5,369 | 167 | 445 | 195 | 55 | 33 | | | | **56,931.5** | **30.48%** | **2,171.0** | 2,171.1 | −0.1 |
| L1 | 540 | 4,084.5 | 3,330 | 4,585 | 39 | 3,059 | 246 | 2,140 | 166 | 297 | 243 | 53 | 33 | | | | **18,815.5** | **10.07%** | **843.0** | 845.4 | −2.4 |
| L2 | 276* | 2,542.5 | 2,072 | 2,867 | 39 | 1,431 | 160 | 1,326 | 166 | 297 | 200 | 53 | 31 | | | | **11,460.5** | **6.13%** | **523.0** | 524.2 | −1.2 |
| L3 | 276* | 1,879.5 | 1,554 | 2,161 | 39 | 709 | 158 | 1,395 | 166 | 297 | 156 | 53 | 31 | | | | **8,874.5** | **4.75%** | **379.0** | 378.4 | +0.6 |
| L4 | 142.5 | 1,431 | 1,184 | 1,656 | 39 | 281 | 116 | 976 | 155 | 297 | 29 | 0 | 19 | 110 | | | **6,435.5** | **3.44%** | **280.5** | 280.0 | +0.5 |
| tail | | | | | | | | | | 176 | 6 | | | 48 | 105 | | **335.0** | 0.18% | 3.0 | 3.0 | 0.0 |
| **sum** | 2,284.5 | 20,890 | 19,004 | 28,947 | 216 | 14,946 | 1,277 | 11,462 | 820 | 1,809 | 829 | 214 | 147 | 158 | 105 | 14 | **103,122.5** | **55.20%** | **4,199.5** | 4,202.1 | −2.6 |
| T03 bucket | 2,284.5 | 20,890.0 | 19,004.0 | 28,947.0 | 216.0 | 14,946.0 | 12,739.0 (both) | | 820 | 1,809.0 | 829.0 | 214 (with setup: 228) | 147 | 158 | 105 | | 103,122.5 | | | | |

Not level-specific opening parts, outside `open_stacked` (unchanged from T03): terminal weights 11,334.7; ring-switch front and claim batch 6,116.0 (6 KECCAK); placement and config certify 664.0; open dispatch 19.0; final check 3.0. Total 18,136.7 (9.71%).

Conventions and exactness:
- Level k is iteration k of `open_stacked`'s level loop (lean_ethereum.py 1497-1642 @ df7d122), plus level k's residual rows (1691-1748) and the OOD-eq term of level k's OOD sample (1749-1763).
- Iteration k also reads level k+1's root and OOD sample (L0's OOD 195 cycles / 19 KECCAK is the L1 commitment's OOD point). T04 puts these on level k as well, which is why the KECCAK columns line up.
- The final message is read in iteration L4 (110 cycles) and evaluated in the tail (48).
- \* The only data-dependent callee shared by two levels is `verify_merkle_cap__L5` (cap depth 5, used by L2 and L3). Its 552 cycles and 57.5 KECCAK per child are split 1:1 by call count, so the L2/L3 cap split is approximate to at most about ±100 cycles and ±15 KECCAK.
- The other shared callees cost the same on every call (`opening_fold`, `grind_check__L17`, `opening_row_weights__L4_L0`, `assert_canonical`), so splitting them by call count is exact.
- Every other per-level callee is specialised per level (`opening_queries__…_{depth}_{cap}`, `walk_path`, `decode_query_windows`, one `__loop` per level) and is exact.

Comparison with T04:
- Total opening KECCAK per child is 4,199.5 measured against 4,202.1 analytic (−2.6).
- The per-level differences are within the realised-versus-expected cap-node spread T04 predicted ("a few hashes"). Leaf+path counts are exactly T04's Q·(4 or 3) + Q·(depth − cap) per level: 2,016 / 765 / 476 / 336 / 256, plus the sponge permutations.

### 2. V3 and V4: what is kept per child (both UNSOUND)

| item | baseline | V3 (UNSOUND) | V4 (UNSOUND) |
|---|---|---|---|
| fold sumcheck rounds, level roots, OOD reads, nonce absorb, query squeezes, λ, level batching, all levels | yes | yes | yes |
| PoW check (`grind_check`) | L0..L4 | L0 | L0, L1 |
| query-window decode | L0..L4 | L0 | L0, L1 |
| row eq weights, Merkle cap check, leaf + path hashing, lane packing, query rows | L0..L4 | L0 | L0, L1 |
| residual (induced bases at query positions) | L0..L4 | none | none |
| final-message evaluation (`fold_final_msg`) and the final check | yes | no | no |
| row and path hints of skipped levels | popped | popped unread (`hint_witness` compiles to 0 instructions) | popped unread |
| e3 (terminal weights, OOD eq, ring-switch, placement), everything outside `open_stacked` | yes | yes (only the final `assert` removed, as in T03 V2) | yes (same) |

Diffs: results/T05/v3.diff (research/d3-v3, b117ddd77) and v4.diff (research/d3-v4, 3feeae43e). Each is one file, crates/rec_aggregation/guests/lean_ethereum.py, +62/−89. The two differ only in K (`lvl // 1` versus `lvl // 2`) and the labels. Generated by results/T05/scripts/make_variant.py.

### 3. Profiled cycle check, n=2, `--repeat 1` (`DBG_PROF=1 DBG_PROF_DUMP=... DBG_DISASM=...`)

Commands: `scripts/attribute_lv.py prof/v{3,4}_n2.prof.<pid> prof/v{3,4}.lines prof/v{3,4}.disasm --guest prof/guest_v{3,4}.py`, then `scripts/compare_variant.py`.

| | V3 (UNSOUND) | V4 (UNSOUND) |
|---|---|---|
| node cycles (baseline 392,988) | 285,389 | 316,793 |
| measured saving | 107,599 | 76,195 |
| of which fixed `__jump_tables` prologue (fewer `walk_path` dispatch tables) | 3,116 | 1,528 |
| measured saving excluding prologue | 104,483 (52,241.5 per child) | 74,667 (37,333.5 per child) |
| predicted from step 1 (2 × per-child slope cells removed) | 104,448 (52,224.0 per child) | 74,679 (37,339.5 per child) |
| measured / predicted | **100.034%** (+35) | **99.984%** (−12) |
| predicted from the exact baseline n=2 cells | 104,429 | 74,672 |
| KECCAK removed, measured vs predicted (step 1) | 3,914 vs 3,913 | 2,288 vs 2,277 |
| per-child share of 186,807.5 removed | 27.97% | 19.99% |

Residual cells (base − variant, n=2): within ±36 cycles each.
- Removed `eq:query grinding` cells keep 22 cycles per level: the nonce absorb, which is kept as transcript.
- The squeeze-only loops at skipped levels save +18 to +36 more.
- OOD moves 12 cycles between the L4 and tail labels (net 0).
- In V4, cap and path cells at L0 and L1 differ by 7 to 11 cycles, from the realised query positions of a different leaf proof.

Each variant's leaves also run fewer cycles (V3 216,878, V4 218,466, baseline 219,994). That is the same smaller prologue; the leaf does not run `open_stacked`.

### 4. Run table (step 5), `/usr/bin/time -l <bin> recursion --n {2,4,6} --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 3 --tracing`, 30 s sleep before each run, interleaved (base, V3, V4 per n), 2 passes

Prove s is the 3 measured repeats as printed; "median" is their median.
- Footprint is the OS `peak memory footprint` (GiB); leanVM peak is leanVM's printed `peak memory`.
- Swap delta is used-swap after minus before (MiB).
- Node mu is read from the trace's `base encode` log_domain plus 4. It agrees with max(15, ceil(TOTAL_COMMITTED exponent)) in all 18 runs, so mu = log_domain + 4 holds.
- Proof KiB is the node proof.
- "verify ok" means the CLI printed `verifying` after `sig.verify().expect(..)` (bins/leanvm/src/benchmark.rs:196).

| variant | n | pass | cycles | TOTAL_COMMITTED | node mu | proof KiB | prove s (3 repeats) | median s | leanVM peak GiB | footprint GiB | swap Δ MiB | verify | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2 | 1 | 392,988 | 2^23.842 | 24 | 232.6 | 0.586 0.557 0.657 | 0.586 | 1.374 | 1.429 | −40 | ok (13.868 ms) | AC |
| V3 UNSOUND | 2 | 1 | 285,389 | 2^23.403 | 24 | 217.2 | 0.464 0.47 0.463 | 0.464 | 1.263 | 1.301 | 0 | ok (12.418 ms) | AC |
| V4 UNSOUND | 2 | 1 | 316,793 | 2^23.403 | 24 | 217.0 | 0.486 0.478 0.517 | 0.486 | 1.311 | 1.344 | −8 | ok (12.938 ms) | AC |
| baseline | 4 | 1 | 766,603 | 2^24.791 | 25 | 239.9 | 1.393 1.426 1.592 | 1.426 | 2.28 | 2.4 | 414 | ok (18.173 ms) | AC; memory-pressured |
| V3 UNSOUND | 4 | 1 | 554,473 | 2^24.369 | 25 | 224.9 | 0.909 0.889 0.938 | 0.909 | 1.879 | 1.943 | −8 | ok (12.572 ms) | AC |
| V4 UNSOUND | 4 | 1 | 615,656 | 2^24.369 | 25 | 225.4 | 0.896 0.948 0.878 | 0.896 | 1.883 | 1.949 | −48 | ok (13.043 ms) | AC |
| baseline | 6 | 1 | 1,140,247 | 2^25.036 | 26 | 227.4 | 1.979 1.941 1.552 | 1.941 | 3.014 | 3.081 | 853 | ok (13.893 ms) | AC; memory-pressured |
| V3 UNSOUND | 6 | 1 | 823,619 | 2^24.791 | 25 | 240.2 | 1.029 1.036 1.023 | 1.029 | 2.362 | 2.394 | −48 | ok (14.098 ms) | AC |
| V4 UNSOUND | 6 | 1 | 914,593 | 2^24.791 | 25 | 239.8 | 1.066 1.027 1.028 | 1.028 | 2.386 | 2.401 | 0 | ok (12.857 ms) | AC |
| baseline | 2 | 2 | 392,988 | 2^23.842 | 24 | 232.6 | 0.543 0.541 0.55 | 0.543 | 1.397 | 1.426 | −8 | ok (13.718 ms) | AC |
| V3 UNSOUND | 2 | 2 | 285,389 | 2^23.403 | 24 | 217.2 | 0.463 0.456 0.46 | 0.46 | 1.294 | 1.295 | −8 | ok (12.177 ms) | AC |
| V4 UNSOUND | 2 | 2 | 316,793 | 2^23.403 | 24 | 217.0 | 0.472 0.467 0.469 | 0.469 | 1.263 | 1.301 | 0 | ok (12.734 ms) | AC |
| baseline | 4 | 2 | 766,603 | 2^24.791 | 25 | 239.9 | 1.052 1.157 1.008 | 1.052 | 2.362 | 2.397 | −24 | ok (13.724 ms) | AC |
| V3 UNSOUND | 4 | 2 | 554,473 | 2^24.369 | 25 | 224.9 | 0.854 0.86 0.846 | 0.854 | 1.943 | 1.947 | −8 | ok (12.297 ms) | AC |
| V4 UNSOUND | 4 | 2 | 615,656 | 2^24.369 | 25 | 225.4 | 0.863 0.904 0.874 | 0.874 | 1.928 | 1.954 | −8 | ok (12.801 ms) | AC |
| baseline | 6 | 2 | 1,140,247 | 2^25.036 | 26 | 227.4 | 2.223 1.902 1.949 | 1.949 | 2.973 | 3.093 | 366 | ok (13.992 ms) | AC; memory-pressured |
| V3 UNSOUND | 6 | 2 | 823,619 | 2^24.791 | 25 | 240.2 | 1.122 1.017 0.99 | 1.017 | 2.38 | 2.392 | −8 | ok (12.546 ms) | AC |
| V4 UNSOUND | 6 | 2 | 914,593 | 2^24.791 | 25 | 239.8 | 1.061 1.037 1.03 | 1.037 | 2.388 | 2.402 | −16 | ok (12.953 ms) | AC |

Per-opcode lines are identical in both passes:
- baseline n=2: `MUL 2^17.132 (36.5%)  XOR 2^16.681 (26.7%)  DEREF 2^16.105 (17.9%)  SET 2^15.213 (9.7%)  JUMP 2^14.637 (6.5%)  KECCAK 2^13.347 (2.7%)  MEMORY 2^19.379  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842`
- V3 n=2: `MUL 2^16.68 (36.8%)  XOR 2^16.164 (25.7%)  DEREF 2^15.746 (19.3%)  SET 2^14.761 (9.7%)  JUMP 2^14.118 (6.2%)  KECCAK 2^12.667 (2.3%)  MEMORY 2^19.039  BYTECODE 2^18.432  TOTAL_COMMITTED 2^23.403`
- V4 n=2: `MUL 2^16.808 (36.2%)  XOR 2^16.302 (25.5%)  DEREF 2^15.882 (19.1%)  SET 2^14.959 (10.1%)  JUMP 2^14.354 (6.6%)  KECCAK 2^12.989 (2.6%)  MEMORY 2^19.158  BYTECODE 2^18.536  TOTAL_COMMITTED 2^23.403`
- baseline n=4: `MUL 2^18.129 (37.4%)  XOR 2^17.678 (27.3%)  DEREF 2^17.093 (18.2%)  SET 2^15.845 (7.7%)  JUMP 2^15.634 (6.6%)  KECCAK 2^14.344 (2.7%)  MEMORY 2^20.357  BYTECODE 2^18.899  TOTAL_COMMITTED 2^24.791`
- V3 n=4: `MUL 2^17.676 (37.8%)  XOR 2^17.16 (26.4%)  DEREF 2^16.731 (19.6%)  SET 2^15.341 (7.5%)  JUMP 2^15.112 (6.4%)  KECCAK 2^13.664 (2.3%)  MEMORY 2^20.016  BYTECODE 2^18.432  TOTAL_COMMITTED 2^24.369`
- V4 n=4: `MUL 2^17.804 (37.2%)  XOR 2^17.298 (26.2%)  DEREF 2^16.869 (19.4%)  SET 2^15.552 (7.8%)  JUMP 2^15.347 (6.8%)  KECCAK 2^13.988 (2.6%)  MEMORY 2^20.134  BYTECODE 2^18.536  TOTAL_COMMITTED 2^24.369`
- baseline n=6: `MUL 2^18.713 (37.7%)  XOR 2^18.262 (27.6%)  DEREF 2^17.674 (18.3%)  SET 2^16.282 (7.0%)  JUMP 2^16.218 (6.7%)  KECCAK 2^14.928 (2.7%)  MEMORY 2^20.935  BYTECODE 2^18.899  TOTAL_COMMITTED 2^25.036`
- V3 n=6: `MUL 2^18.26 (38.1%)  XOR 2^17.743 (26.6%)  DEREF 2^17.311 (19.7%)  SET 2^15.754 (6.7%)  JUMP 2^15.695 (6.4%)  KECCAK 2^14.247 (2.4%)  MEMORY 2^20.593  BYTECODE 2^18.432  TOTAL_COMMITTED 2^24.791`
- V4 n=6: `MUL 2^18.388 (37.5%)  XOR 2^17.881 (26.4%)  DEREF 2^17.449 (19.6%)  SET 2^15.972 (7.0%)  JUMP 2^15.931 (6.8%)  KECCAK 2^14.572 (2.7%)  MEMORY 2^20.712  BYTECODE 2^18.536  TOTAL_COMMITTED 2^24.791`

Pooled medians, 6 repeats (results/T05/prove_pooled.csv):

| variant | n=2 | n=4 | n=6 |
|---|---|---|---|
| baseline | 0.5535 s | 1.275 s | 1.945 s |
| V3 UNSOUND | 0.463 s | 0.8745 s | 1.026 s |
| V4 UNSOUND | 0.475 s | 0.887 s | 1.0335 s |

### 5. Derived savings (DERIVED; V3 and V4 are UNSOUND)

| quantity | V3 (UNSOUND) | V4 (UNSOUND) | source |
|---|---|---|---|
| cycles saved per child (slope n=2,4,6 of printed cycles) | 52,257.2 (27.97% of 186,814.8) | 37,364.8 (20.00%) | summary.csv |
| cycles saved per child (profiled n=2, excluding prologue) | 52,241.5 | 37,333.5 | v{3,4}_check.txt |
| cycles saved per child (step-1 prediction) | 52,224.0 | 37,339.5 | per_level_long.csv |
| KECCAK saved per child (exact, profiled n=2) | 1,957.0 (37.7% of 5,188) | 1,144.0 (22.1%) | v{3,4}_check.txt |
| KECCAK saved per child (slope of the printed 2^x, about ±0.04% each) | 1,953.3 | 1,131.7 | derived.csv |
| prove time per child, baseline slope 2→6 / variant slope | 347.9 / 140.7 ms | 347.9 / 139.6 ms | derived.csv |
| prove time saved per child, slope 2→6 | 207.1 ms (59.5%), includes baseline mu step at n=6 | 208.2 ms (59.9%), same | |
| prove time saved per child, slope 2→4 (no mu step in either) | **155.0 ms (43.0%)** | **154.7 ms (42.9%)** | |
| same, per pass (pass 1 / pass 2) | 197.5 / 57.5 ms | 205 / 49.5 ms | from the medians above |
| n=6 prove time saved | 0.919 s (47.3%) | 0.912 s (46.9%) | pooled medians |
| node mu at n=2 / 4 / 6 (baseline 24 / 25 / 26) | 24 / 25 / **25** | 24 / 25 / **25** | trace |

mu-step notes:
- At n=6 both variants stay at mu=25 (TOTAL_COMMITTED 2^24.791, the same as the baseline at n=4). The baseline crossed to mu=26 (2^25.036). So the n=6 saving includes one stacked-size step: twice the opening domain (the L0 base encode is log_domain 22 against 21) and the doubled stack.
- The baseline n=6 runs were memory-pressured in both passes (swap +853 and +366 MiB, footprint 3.1 GiB). The baseline n=4 run in pass 1 was too (+414 MiB).
- The 2→4 per-child prove saving is therefore the cleaner number, but it is noisy: 57 to 198 ms per pass. That is because the baseline n=4 median was 1.426 s in pass 1 (pressured) and 1.052 s in pass 2.
- V3 and V4 have identical TOTAL_COMMITTED at every n. Their prove times differ by at most 12 ms, even though V4 runs about 15k more cycles per child. In this regime prove time follows committed size and the KECCAK table, not cycles.
- The mu boundary: baseline n=4 is 2^24.791 and V3/V4 n=6 is 2^24.791. With about 0.21 to 0.24 of exponent headroom below 2^25 at n=6, the variants would cross to mu=26 at about n = 7 to 8 (estimate, not measured).

### 6. Native prover opening cost per level (seconds from the `--tracing` span trees; no new runs except the T05 baseline n=2 traces)

Command: `scripts/parse_open.py native_open_raw.csv leaf_T00=... leaf_T01drift=... node2_T01=... node2_T03r1=... node2_T03r2=... node2_T05r1=... node2_T05r2=...`.

Spans: `PCS open` children (crates/pcs/src/stack_open.rs:162, 211; crates/pcs/src/whir.rs:1029-1213). Convention: level k = all prover work on oracle L_k.
- Sumcheck span k is the rounds that fold L_k.
- `Commit level k` builds L_k (L0's is the witness `Commit` (base encode), outside `PCS open`).
- `Open`, `Induce`, `Introduce` level k act on level k's queries.
- `Final level` holds L4's open, induce and introduce plus the 3 tail rounds.
- PoW grinding (5 × 17 bits), query sampling and OOD sends are not in any span. They appear only as the untraced remainder and cannot be split by level from the tree, which has no timestamps.
- Tracing prints 3 significant digits.

Means in ms. Leaf: 2 traces (results/T00/aggregate_xmss250_lir2.log, results/T01/drift_baseline_aggregate_xmss250_lir2.log). 2-child node: 5 traces (results/T01/recursion_n2_m250_leaflir2_lir2.log, results/T03/runs/base_n2.log, results/T03/runs2/base_n2.log, results/T05/runs/base_n2.log, results/T05/runs2/base_n2.log). Ranges are in native_open.txt.

| level | component | leaf (mu 25) ms | 2-child node (mu 24) ms |
|---|---|---|---|
| L0 | commit, base encode (outside PCS open) | 263.5 (258-269) | 210.2 (176-278) |
| L0 | Basis (combined initial weight) | 38.4 | 30.5 |
| L0 | sumcheck rounds 0-6 | 7.51 | 5.83 |
| L0 | open | 0.73 | 0.84 |
| L0 | induce | 4.16 | 2.36 |
| L0 | introduce | 1.33 | 0.62 |
| **L0 in PCS open** | | **52.13** | **40.19** |
| L1 | commit (extension encode) | 127.0 | 59.2 |
| L1 | sumcheck 7-10 + open + induce + introduce | 1.27 + 0.31 + 0.23 + 0.08 = 1.89 | 0.61 + 0.27 + 0.13 + 0.04 = 1.05 |
| **L1** | | **128.89** | **60.29** |
| **L2** | commit 56.15 + rest 0.34 / commit 25.9 + rest 0.30 | **56.49** | **26.20** |
| **L3** | commit 24.0 + 0.18 / 11.14 + 0.16 | **24.18** | **11.30** |
| **L4 (+ tail)** | commit 10.25 + sumcheck 0.006 + final level 0.122 / 4.99 + 0.006 + 0.121 | **10.38** | **5.12** |
| not level-specific | Ring switch | 0.10 | 0.10 |
| not level-specific | untraced remainder (PoW ×5, sampling, OOD) | 12.84 | 12.00 |
| | **PCS open total** | **285.0** | **155.2** |

In the guest's iteration convention, where iteration k includes `Commit level k+1`, the prover cost per iteration (in ms) is:

| iteration | leaf | 2-child node |
|---|---|---|
| L0 | 52.1 + 127.0 = 179.1 | 40.2 + 59.2 = 99.4 |
| L1 | 1.9 + 56.2 = 58.0 | 1.05 + 25.9 = 26.9 |
| L2 | 0.3 + 24.0 = 24.3 | 0.3 + 11.1 = 11.4 |
| L3 | 0.2 + 10.25 = 10.4 | 0.2 + 5.0 = 5.2 |
| L4 + tail | 0.13 | 0.13 |

## Commands run
1. Read inputs: CLAUDE.md, NOTES.md, results/T03/{attribution_notes.md, T03_report.md, v1.diff, v2.diff, scripts/*}, results/T04/pcs_facts.md; guest `open_stacked` and helpers, `crates/rec_aggregation/src/aggregation/{child.rs, hints.rs}`, `crates/leanvm_core/src/cpu/execute.rs` (hint streams), and `crates/pcs/src/{whir.rs, stack_open.rs}` (prover spans).
2. Step 1, attribution: `gzip -dc` of results/T03/prof/{base_n2.prof.39072, base_n4.prof.39688, base.lines, base.disasm}.gz into the scratchpad, then
   - `python3 scripts/attribute_lv.py <base_n2.prof.39072> <base.lines> <base.disasm> --json prof/base_n2_lv.json` (and the same for n=4)
   - `python3 scripts/per_level_table.py prof/base_n2_lv.json prof/base_n4_lv.json .`
3. V3:
   - `git checkout -b research/d3-v3 df7d122abbe25cf12e5c8ae992ce6d3505f75372`
   - `python3 ../../results/T05/scripts/make_variant.py crates/rec_aggregation/guests/lean_ethereum.py 1 V3`
   - `git commit` (b117ddd77)
   - `CARGO_TARGET_DIR=target-d3v3 cargo +1.99.0 build --release -p leanvm-cli` (45.3 s)
4. V3 profile: `DBG_PROF=1 DBG_PROF_DUMP=$PWD/v3_n2.prof DBG_DISASM=$PWD/v3.disasm /usr/bin/time -l .../target-d3v3/release/leanvm recursion --n 2 --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 1`
5. V3 line table and check:
   - `(cd proto/guest-lines && RUSTFLAGS="-C target-cpu=native" cargo +1.99.0 build --release && ./target/release/guest-lines ../../results/T05/prof/v3.lines)`
   - `python3 ../scripts/attribute_lv.py v3_n2.prof.79617 v3.lines v3.disasm --guest guest_v3.py --json v3_n2_lv.json`
   - `python3 scripts/compare_variant.py prof/base_n2_lv.json prof/v3_n2_lv.json 1 per_level_long.csv v3_vs_base_cells.csv`
6. V4: the same steps with branch research/d3-v4, K=2, target-d3v4 (44.8 s), profile dump v4_n2.prof.91764, and `compare_variant.py ... 2`. Then `git checkout research/baseline`.
7. Step 5, timing: `python3 scripts/sweep.py`. This is 2 passes × n ∈ {2,4,6} × {base, v3, v4}. Each run is `scripts/run.sh <dir> <bin> <v>_n<n> recursion --n <n> --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 3 --tracing` (`/usr/bin/time -l`, swap and power recorded before and after), with a 30 s sleep before each. Run 21:50 to 22:04.
8. `python3 scripts/analyze.py` (summary.csv, run_table.md, prove_pooled.csv, derived.csv).
9. Step 6: `python3 scripts/parse_open.py native_open_raw.csv leaf_T00=../T00/aggregate_xmss250_lir2.log leaf_T01drift=../T01/drift_baseline_aggregate_xmss250_lir2.log node2_T01=../T01/recursion_n2_m250_leaflir2_lir2.log node2_T03r1=../T03/runs/base_n2.log node2_T03r2=../T03/runs2/base_n2.log node2_T05r1=runs/base_n2.log node2_T05r2=runs2/base_n2.log`
10. `git diff df7d122 research/d3-v3 > v3.diff` (and the same for v4); `gzip -9` of the variant dumps, lines and disassembly.

## Raw output
```
# per_level.txt (step 1)
per-child total (slope n2->n4): 186807.5 (T03: 186807.5)
check: max |sum over levels - T03 bucket| per child = 0.050 cycles over 30 buckets
check: level-table sum 103122.5 vs T03 opening buckets 103122.5 (+0.0000%)
callees split over several WHIR levels by call counts (n=2, self cycles):
  2256 opening_fold {L0:12, L1..L4:8, tail:4} | 1500 grind_check__L17 {L0..L4:2} | 1043 verify_merkle_cap__L5 {L2:2, L3:2}
  256 opening_row_weights__L4_L0 {L1..L4:2} | 160 assert_canonical
# v3_check.txt
K=1: node steps base 392988 variant 285389  measured saving 107599
  fixed prologue (__jump_tables) change: 3116.0
  measured saving excl. prologue: 104483.0  (per child 52241.5)
  predicted, exact baseline n=2 cells in R(K): 104429.0  (KECCAK 3922.0)
  predicted, 2 x step-1 per-child slope cells in R(K): 104448.0  (KECCAK 3913.0)
  measured / step-1 prediction: 100.034%   measured - step1: +35.0
  KECCAK removed: measured 3914.0
# v4_check.txt
K=2: node steps base 392988 variant 316793  measured saving 76195
  fixed prologue (__jump_tables) change: 1528.0
  measured saving excl. prologue: 74667.0  (per child 37333.5)
  predicted, 2 x step-1 per-child slope cells in R(K): 74679.0  (KECCAK 2277.0)
  measured / step-1 prediction: 99.984%   measured - step1: -12.0
  KECCAK removed: measured 2288.0
# profiled runs (prof/v{3,4}_n2_prof.log)
V3: cycles (VM steps) : 285,389 = 2^18.123 | proof size 217.2 KiB | verifying 13.919 ms | 8.76 real | footprint 1404880360 B | swap 2556.38M -> 2957.50M
V4: cycles (VM steps) : 316,793 = 2^18.273 | proof size 217.0 KiB | verifying 13.482 ms | 8.74 real | footprint 1419200000 B
# analyze.py
pooled medians (s): base n2 0.554; base n4 1.275; base n6 1.945; v3 n2 0.463; v3 n4 0.875; v3 n6 1.026; v4 n2 0.475; v4 n4 0.887; v4 n6 1.034
node mu: base 24/25/26; v3 24/25/25; v4 24/25/25   (trace = TOTAL_COMMITTED rule in all 18 runs)
drift base n=2 pass 1: median 0.586 s vs 0.605 s: -3.1%  swap delta -40 MiB
drift base n=2 pass 2: median 0.543 s vs 0.605 s: -10.2%  swap delta -8 MiB
base vs T03 pooled medians: n2 0.554 vs 0.605 (-8.5%); n4 1.275 vs 1.406 (-9.3%); n6 1.945 vs 2.247 (-13.4%)
verify: ok (all 18)
```
Full logs are in results/T05/runs/*.log, runs2/*.log and prof/*_prof.log.

## Files changed or created
- upstream/leanMultisig, branch research/d3-v3 (b117ddd77) and research/d3-v4 (3feeae43e): crates/rec_aggregation/guests/lean_ethereum.py. Both UNSOUND, local commits only. .git/info/exclude gained target-d3v3/ and target-d3v4/.
- results/T05/T05_report.md: this report.
- results/T05/per_level_pivot.csv, per_level_long.csv, per_level.txt: step-1 per-level table, per child, with checks.
- results/T05/v3.diff, v4.diff: variant diffs. v3_check.txt, v4_check.txt, v{3,4}_vs_base_cells.csv: profiled check and per-cell deltas.
- results/T05/summary.csv, run_table.md, prove_pooled.csv, derived.csv: step 5 and step 7 (derived).
- results/T05/native_open_raw.csv, native_open_raw_pivot.csv, native_open.txt: step 6.
- results/T05/runs/, runs2/: 18 run logs. sweep.out: sweep timestamps. build/v{3,4}_build.log: build logs.
- results/T05/prof/: base_n{2,4}_lv.{json,txt}, v{3,4}_n2_lv.{json,txt}, v{3,4}_n2_prof.log and .swap, guest_v{3,4}.py, plus gzipped v{3,4}.disasm, v{3,4}.lines and v{3,4}_n2.prof* (node dumps are the .79617 / .91764 files; the others are the two leaves).
- results/T05/scripts/: attribute_lv.py (T03 attribute.py plus level labels, stripped-text line mapping and an `eq:query decode` sub-bucket), per_level_table.py, make_variant.py, compare_variant.py, sweep.py, run.sh (copy of T03's), analyze.py (imports T03 parse_runs.py), parse_open.py.
- NOTES.md: T05 entry.

## Problems and deviations
- **Reading of "skip all checks and openings for L1..L4".** At skipped levels I removed the PoW check (`grind_check`) and the query-window decode, besides the cap check and openings. I kept every transcript operation: the nonce absorb, the position squeezes and λ. All e3 parts stay, including the OOD-eq terms at the terminal point, as in T03 V2.
  - Consequently V3 is not V2 plus L0's openings: V2 kept PoW and decode at all levels.
  - Step 1 gives the PoW and decode costs per level (PoW about 166, decode 2,140 / 1,326 / 1,395 / 976 at L1..L4), so other choices can be recombined from the table.
- **The residual is skipped at every level, L0 included, as the task lists it.** L0's residual is 9,466 cycles per child and L1's is 3,059. A design that keeps L0 or L1 fully checked would add these back (estimate from step 1, not measured).
- **The final `assert` in `check_opening_terminal` is commented out**, outside `open_stacked`, as T03 V2 did. It cannot hold without the residual and e4. Everything else outside `open_stacked` is unchanged.
- **Skipped levels still pop their `merkle_leaf_rows` and `merkle_children` hints.** The streams are global across children (aggregation/hints.rs:56-77). Without the pops, the next child's L0 would read the previous child's L1 entries and fail the entry-length check (execute.rs:251). `hint_witness` compiles to no instruction, so this costs 0 cycles (checked: no pc carries those lines). The popped cells are still written to memory.
- **Line mapping.** T03's attribute.py maps variant lines to df7d122 lines by exact difflib match, which would misplace re-indented code. attribute_lv.py matches on stripped text and sends duplicated lines to their identical base line. The baseline attribution is unchanged by this (identical numbers to T03).
- **`eq:query sampling` is split into squeezes and decode** (lines 1576-1578 plus win_tabs 1480-1482). The sum equals T03's bucket.
- **The L2/L3 Merkle-cap split is by call count** (shared `verify_merkle_cap__L5`, data-dependent): about ±100 cycles and ±15 KECCAK between those two cells. Totals are exact.
- **Different leaves.** Each variant's leaves are proven by the variant binary (smaller prologue: 216,878 / 218,466 against 219,994 leaf cycles). The verified children are therefore not bit-identical to the baseline's children. Shape and mu (25) are the same, and node cycles were identical across both passes for each variant.
- **Prove-time noise.** Baseline n=4 pass 1 and baseline n=6 in both passes were memory-pressured (swap +414 / +853 / +366 MiB). The per-pass 2→4 savings span 50 to 205 ms per child. The pooled medians are reported as asked, with this caveat.
- **Native per level.** PoW grinding, query sampling and OOD sends (about 12 to 13 ms in all) are outside every span and are not split by level. L4's open and induce sit inside `Final level`. Tracing resolution is 3 significant digits. The recursion leaves (child process) print no trace, so the leaf figures come from the 2 `aggregate` traces only.
- Nothing was installed, pushed or posted.

## Suggested next step
Size a batched-opening design from step 1: per child, L1..L4 proximity work is 37.5k cycles and 1,953 KECCAK of the 103.1k opening, with L0 at 47.5k excluding residual. Then measure a variant that keeps L0 including its residual (about 9.5k more cycles per child) at n = 2, 4, 6, 8, so that both variant and baseline sit on the same mu at each n. On Linux this would avoid the paging seen here at n ≥ 4.
=== END REPORT ===

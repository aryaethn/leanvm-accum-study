=== RESULT REPORT T02R ===
Status: done (all required configurations measured; 3 grid cells skipped by the 6 GiB memory rule, listed below)
Machine: Apple M2 (MacBook Air, Mac14,2), 4P+4E cores, 8 GiB RAM, macOS 26.5.2, AC power, fanless
Toolchain: rustc 1.97.1 (8bab26f4f 2026-07-14), cargo 1.97.1 (stable, from upstream rust-toolchain.toml; no rustup install needed). Harness pinned to the same via proto/warp-bench/rust-toolchain.toml. No lean used.
Repo state: compsec-epfl/warp 655e7d5f61d70122d0323dede8477c74a2a725bf (2026-05-02), local branch research/warp-bench, `git status --porcelain` = empty (clean; Cargo.lock/target are git-ignored). effsc @9e55dc3a, ark-codes @62cd597d (resolved at fetch time; Cargo.lock saved as results/T02/Cargo.lock.upstream and copied into proto/warp-bench/). leanMultisig untouched. proto/ is not a git repo.

## What existed from the earlier T02 session and was reused
- Reused: upstream/warp clone at 655e7d5 and branch; results/T02/repo_facts.md (my own study, file:line cited; read and still valid); Cargo.lock.upstream; the harness crate proto/warp-bench (rewritten for the T02R spec); gate machinery was not needed again.
- Superseded T02 sweep: it had started with s=8 and ran ONE configuration (BLS L=14, l=2) before being stopped when T02R arrived. Archived in results/T02/aborted_first_sweep/ and NOT used in any table.
- Earlier T02 gate (leanvm quiet for 10 min, 18:26:09 to 18:41:11) is in results/T02/gate.log; build/test ran after it. T02R only needed the per-run `pgrep` guard (see Problems).

## Summary
- Upstream builds in 31.6 s (release) and `cargo test --release` passes 5/5. Harness runs 24 configurations (BLS12-381: 10, Goldilocks: 11, sensitivity: 3). Every verify and decide accepted; every negative check rejected (tampered shift answer and Merkle path element both give `ShiftQuery`; tampered transcript byte and tampered accumulator mu give `Target`; decider on tampered witness gives `DeciderError(BundledEvaluation)`).
- One Poseidon step = 288 constraints and 288 witness variables (raw constraints = 288 L + 1, k = 288 L + 1, 2 public variables) on both fields.
- Verification is fast and nearly independent of size: 0.9 to 2.1 ms (BLS), 0.5 to 0.74 ms (Goldilocks) for step B. Decide is flat in lA and linear in M: about 2.2 us per constraint (BLS), 0.93 us (Goldilocks).
- B-prove at M=2^16, lA=8, primary params: BLS 1157 ms, Goldilocks 275 ms (4.2x). Proof excluding statement is 110 to 220 KB, dominated by 2 x 128 Merkle paths (t=128 on the fresh tree plus t=128 on the old-accumulator tree in step B). Peak footprint at M=2^18, lA=4: BLS 4.7 GiB, Goldilocks 3.0 GiB.
- Parallelism is real despite serial warp code: CPU utilisation (user+sys)/real is 3.1 to 3.6 (BLS) and 4.1 to 4.5 (Goldilocks) cores on large runs.
- Goldilocks rows are NOT 128-bit admissible (challenges from the 64-bit base field, 64 < 128+40). BLS12-381 (255-bit) is admissible.

## Results
Parameters, all primary rows: s=2, t=128, nominal rate 1/4, n = next_pow2(4k) (RS code, k = witness vars), repeats 3, all times MEDIAN of 3 repeats in ms, single process per row run under `/usr/bin/time -l`. Step A = lA fresh, l2=0. Step B = lA-1 fresh + 1 accumulator (l = lA). Depth = Merkle hashes per path incl. sibling level = log2 n. "BLS" = admissible; "Gold" = NOT 128-bit admissible. Full machine-readable table: results/T02/summary.csv (all columns, 24 rows); raw per-repeat JSON in results/T02/sweep.jsonl.

### Probe (command: `warp-bench --probe --field F --chain-len L`; file results/T02/probe.jsonl, probe_small.jsonl)
| field | L | raw constraints | M (padded) | k (witness) | n vars | public vars |
|---|---|---|---|---|---|---|
| bls12-381 | 1 | 289 | 512 | 289 | 291 | 2 |
| bls12-381 | 2 | 577 | 1024 | 577 | 579 | 2 |
| bls12-381 | 4 | 1153 | 2048 | 1153 | 1155 | 2 |
| bls12-381 | 8 | 2305 | 4096 | 2305 | 2307 | 2 |
| goldilocks | 1,2,4,8 | 289, 577, 1153, 2305 | 512, 1024, 2048, 4096 | same as raw | 291,...,2307 | 2 |
Per-step slope = 288 constraints and 288 witness variables per Poseidon step (identical on both fields); intercept +1 constraint (final enforce_equal) and +1 variable. Chosen L: 14, 56, 227, 910 give raw 4033, 16129, 65377, 262081 constraints, i.e. M = 2^12, 2^14, 2^16, 2^18 exactly (k = raw, so k is just below M and actual rate is 0.246 to 0.250).

### Sweep: timing (medians, ms)
| field | L | M | k | lA | rate (actual) | n | depth | A-prove | A-verify | B-prove | B-verify | decide |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BLS | 14 | 2^12 | 4033 | 4 | 0.2462 | 16384 | 14 | 69.7 | 1.43 | 69.4 | 0.98 | 9.9 |
| BLS | 14 | 2^12 | 4033 | 8 | 0.2462 | 16384 | 14 | 183.1 | 1.05 | 206.7 | 2.07 | 28.3 (noisy, see flags) |
| BLS | 14 | 2^12 | 4033 | 16 | 0.2462 | 16384 | 14 | 106.5 | 1.25 | 107.0 | 1.42 | 9.3 |
| BLS | 56 | 2^14 | 16129 | 4 | 0.2461 | 65536 | 16 | 291.5 | 0.89 | 212.6 | 1.29 | 43.1 |
| BLS | 56 | 2^14 | 16129 | 8 | 0.2461 | 65536 | 16 | 289.8 | 1.10 | 274.1 | 1.25 | 35.5 |
| BLS | 56 | 2^14 | 16129 | 16 | 0.2461 | 65536 | 16 | 478.7 | 1.42 | 411.8 | 1.58 | 35.3 |
| BLS | 227 | 2^16 | 65377 | 4 | 0.2494 | 262144 | 18 | 890.5 | 1.00 | 783.1 | 1.17 | 142.4 |
| BLS | 227 | 2^16 | 65377 | 8 | 0.2494 | 262144 | 18 | 1422.2 | 1.26 | 1157.4 | 1.48 | 141.4 |
| BLS | 227 | 2^16 | 65377 | 16 | 0.2494 | 262144 | 18 | 2405.6 | 1.68 | 1915.8 | 1.88 | 144.5 |
| BLS | 910 | 2^18 | 262081 | 4 | 0.2499 | 1048576 | 20 | 5221.2 | 1.32 | 4514.6 | 1.50 | 591.4 |
| BLS | 910 | 2^18 | 262081 | 8, 16 | | | | SKIPPED (memory rule) | | | | |
| Gold | 14 | 2^12 | 4033 | 4 | 0.2462 | 16384 | 14 | 14.3 | 0.29 | 13.0 | 0.46 | 4.3 |
| Gold | 14 | 2^12 | 4033 | 8 | 0.2462 | 16384 | 14 | 20.5 | 0.33 | 17.5 | 0.49 | 4.1 |
| Gold | 14 | 2^12 | 4033 | 16 | 0.2462 | 16384 | 14 | 30.2 | 0.39 | 28.1 | 0.56 | 4.2 |
| Gold | 56 | 2^14 | 16129 | 4 | 0.2461 | 65536 | 16 | 53.4 | 0.33 | 47.7 | 0.54 | 15.3 |
| Gold | 56 | 2^14 | 16129 | 8 | 0.2461 | 65536 | 16 | 72.5 | 0.37 | 62.5 | 0.58 | 15.3 |
| Gold | 56 | 2^14 | 16129 | 16 | 0.2461 | 65536 | 16 | 103.2 | 0.43 | 92.1 | 0.61 | 15.3 |
| Gold | 227 | 2^16 | 65377 | 4 | 0.2494 | 262144 | 18 | 243.8 | 0.36 | 214.0 | 0.58 | 60.6 |
| Gold | 227 | 2^16 | 65377 | 8 | 0.2494 | 262144 | 18 | 315.4 | 0.42 | 275.3 | 0.62 | 60.5 |
| Gold | 227 | 2^16 | 65377 | 16 | 0.2494 | 262144 | 18 | 629.3 | 0.49 | 417.0 | 0.71 | 61.2 |
| Gold | 910 | 2^18 | 262081 | 4 | 0.2499 | 1048576 | 20 | 1045.7 | 0.49 | 844.0 | 0.73 | 243.5 |
| Gold | 910 | 2^18 | 262081 | 8 | 0.2499 | 1048576 | 20 | 1683.3 | 0.50 | 1123.0 | 0.74 | 242.7 |
| Gold | 910 | 2^18 | 262081 | 16 | | | | SKIPPED (memory rule, predicted 6.51 GiB) | | | | |

Commands: each row is `/usr/bin/time -l warp-bench --field F --chain-len L --lA lA --rate-inv 4 --s 2 --t 128 --repeats 3` (exact lines in results/T02/sweep.log; per-run time -l output in results/T02/runs/*.time.txt).

### Sweep: sizes (bytes; A and B)
Statement = fresh-instance public inputs + old-accumulator instance fields absorbed into the transcript, measured exactly by calling the public `absorb_instances` / `absorb_accumulated_instances` on a fresh transcript and taking the NARG length (hand-checked: BLS lA=4, step A = 4 x 2 x 32 = 256; step B = 3 x 2 x 32 + 992 = 1184). Tuple = Proof tuple via `ProofSerializer` (Compress::Yes). Excl = NARG - statement + Tuple (DERIVED; the Tuple still repeats rt_0, mu_i, nu_0, a few hundred bytes already in the NARG, which I could not separate through the public API). Paths in step B: 128 on the fresh tree + 128 on the old accumulator's tree = 256 x depth. Step A: 128 paths x depth, none on old accumulators.
| field | M | lA | A stmt | A NARG | A tuple | A excl (derived) | B stmt | B NARG | B tuple | B excl (derived) | acc instance | acc witness (rt+f+w) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BLS | 2^12 | 4 | 256 | 2496 | 77128 | 79368 | 1184 | 3392 | 136496 | 138704 | 1016 | 653392 |
| BLS | 2^12 | 8 | 512 | 3392 | 93640 | 96520 | 1440 | 4288 | 153008 | 155856 | 1016 | 653392 |
| BLS | 2^12 | 16 | 1024 | 4672 | 126664 | 130312 | 1952 | 5568 | 186032 | 189648 | 1016 | 653392 |
| BLS | 2^14 | 4 | 256 | 2752 | 85320 | 87816 | 1312 | 3776 | 152880 | 155344 | 1144 | 2613328 |
| BLS | 2^14 | 8 | 512 | 3712 | 101832 | 105032 | 1568 | 4736 | 169392 | 172560 | 1144 | 2613328 |
| BLS | 2^14 | 16 | 1024 | 5056 | 134856 | 138888 | 2080 | 6080 | 202416 | 206416 | 1144 | 2613328 |
| BLS | 2^16 | 4 | 256 | 3008 | 93512 | 96264 | 1440 | 4160 | 169264 | 171984 | 1272 | 10480720 |
| BLS | 2^16 | 8 | 512 | 4032 | 110024 | 113544 | 1696 | 5184 | 185776 | 189264 | 1272 | 10480720 |
| BLS | 2^16 | 16 | 1024 | 5440 | 143048 | 147464 | 2208 | 6592 | 218800 | 223184 | 1272 | 10480720 |
| BLS | 2^18 | 4 | 256 | 3264 | 101704 | 104712 | 1568 | 4544 | 185648 | 188624 | 1400 | 41941072 |
| Gold | 2^12 | 4 | 64 | 672 | 64648 | 65256 | 320 | 920 | 124040 | 124640 | 296 | 163384 |
| Gold | 2^12 | 8 | 128 | 896 | 68776 | 69544 | 384 | 1144 | 128168 | 128928 | 296 | 163384 |
| Gold | 2^12 | 16 | 256 | 1216 | 77032 | 77992 | 512 | 1464 | 136424 | 137376 | 296 | 163384 |
| Gold | 2^14 | 4 | 64 | 736 | 72840 | 73512 | 352 | 1016 | 140424 | 141088 | 328 | 653368 |
| Gold | 2^14 | 8 | 128 | 976 | 76968 | 77816 | 416 | 1256 | 144552 | 145392 | 328 | 653368 |
| Gold | 2^14 | 16 | 256 | 1312 | 85224 | 86280 | 544 | 1592 | 152808 | 153856 | 328 | 653368 |
| Gold | 2^16 | 4 | 64 | 800 | 81032 | 81768 | 384 | 1112 | 156808 | 157536 | 360 | 2620216 |
| Gold | 2^16 | 8 | 128 | 1056 | 85160 | 86088 | 448 | 1368 | 160936 | 161856 | 360 | 2620216 |
| Gold | 2^16 | 16 | 256 | 1408 | 93416 | 94568 | 576 | 1720 | 169192 | 170336 | 360 | 2620216 |
| Gold | 2^18 | 4 | 64 | 864 | 89224 | 90024 | 416 | 1208 | 173192 | 173984 | 392 | 10485304 |
| Gold | 2^18 | 8 | 128 | 1136 | 93352 | 94360 | 480 | 1480 | 177320 | 178320 | 392 | 10485304 |
Note: acc witness = f (n elements) + w (k elements) + root, i.e. the full codeword is part of the accumulator witness (about 4.0 x M elements). Merkle tree nodes are not counted (the serializer does not include them; the tree is held in memory by the prover/decider).

### Sweep: resources
| field | M | lA | OS peak footprint MiB | max RSS MiB | CPU util | swap delta MiB | wall s | flags |
|---|---|---|---|---|---|---|---|---|
| BLS | 2^12 | 4 | 117 | 92 | 2.05 | -40 | 3.3 | |
| BLS | 2^12 | 8 | 141 | 106 | 0.98 | +1269 | 12.9 | memory-pressured flag per rule, but see Problems (system-wide swap churn, run was only 141 MiB; timing noisy) |
| BLS | 2^12 | 16 | 167 | 168 | 3.58 | -24 | 10.1 | |
| BLS | 2^14 | 4 | 362 | 306 | 1.79 | +249 | 15.2 | |
| BLS | 2^14 | 8 | 972 | 710 | 3.49 | -32 | 20.1 | |
| BLS | 2^14 | 16 | 1468 | 927 | 3.61 | -32 | 40.5 | |
| BLS | 2^16 | 4 | 2200 | 1474 | 3.31 | -24 | 40.8 | |
| BLS | 2^16 | 8 | 2120 | 1823 | 3.47 | -24 | 82.9 | |
| BLS | 2^16 | 16 | 3373 | 2395 | 3.55 | +87 | 165.4 | |
| BLS | 2^18 | 4 | 4731 | 3039 | 3.12 | +1087 | 174.7 | memory-pressured |
| Gold | 2^12 | 4 / 8 / 16 | 46 / 54 / 71 | 48 / 56 / 73 | 4.2 / 4.35 / 4.5 | -8 / 0 / 0 | 1.7 / 3.3 / 6.9 | not 128-bit admissible |
| Gold | 2^14 | 4 / 8 / 16 | 170 / 201 / 250 | 172 / 203 / 271 | 4.25 / 4.4 / 4.5 | -40 / -32 / -16 | 6.5 / 13.5 / 27.4 | not 128-bit admissible |
| Gold | 2^16 | 4 / 8 / 16 | 1610 / 1248 / 2364 | 1110 / 1114 / 1647 | 4.25 / 4.4 / 4.3 | 0 / -24 / -240 | 26.6 / 54.5 / 106.2 | not 128-bit admissible |
| Gold | 2^18 | 4 / 8 | 3035 / 3334 | 2394 / 2462 | 4.1 / 4.25 | -16 / -56 | 109.2 / 225.2 | not 128-bit admissible |
(Peak footprint and max RSS are per process, max over its 3 repeats; they include the instance-building phase, which is untimed.) The footprint is not linear in lA (e.g. BLS 2^16: lA=4 2.2 GiB, lA=8 2.1 GiB), probably because peak memory is dominated by the Merkle tree/codeword/sumcheck tables of the largest phase, and varies with allocator behaviour; this made the linear prediction conservative.

### Sensitivity (BLS12-381, M = 2^16 (L=227), lA = 8; primary row for reference)
| set | rate / n | s | t | A-prove | A-verify | B-prove | B-verify | decide | B Tuple B | B excl stmt B | B paths (fresh+old) x depth | footprint MiB | RSS MiB | CPU | swap delta |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| primary | 1/4, 262144 | 2 | 128 | 1422 | 1.26 | 1157 | 1.48 | 141.4 | 185776 | 189264 | (128+128) x 18 | 2120 | 1823 | 3.47 | -24 |
| sens1 | 1/4, 262144 | 8 | 128 | 1519 | 1.43 | 1287 | 1.60 | 142.3 | 185968 | 189648 | (128+128) x 18 | 2038 | 1922 | 3.43 | -32 |
| sens2 | 1/4, 262144 | 2 | 189 | 1421 | 1.53 | 1125 | 1.79 | 144.8 | 274104 | 277592 | (189+189) x 18 | 2121 | 1805 | 3.46 | -48 |
| sens3 | 1/2, 131072 | 2 | 256 | 802 | 1.60 | 753 | 2.05 | 93.5 | 354736 | 358064 | (256+256) x 17 | 1697 | 1473 | 3.56 | -8 |
Takeaways (derived from the table): s 2 to 8 costs +11% B-prove, +0.1% proof bytes (only +192 B NARG, 6 extra OOD answers); t 128 to 189 costs +47% proof bytes and no visible prove-time change (within noise, B-prove 1125 vs 1157 ms); rate 1/2 with t=256 has +91% proof bytes but -35% prove time and -20% footprint (half-size codeword), i.e. rate 1/2 buys prover speed at proof-size cost. Negative checks passed in all four.

### Derived (from measured values above; labelled derived)
- B-prove ns per constraint per fresh instance = median B-prove / (raw constraints x (lA-1)). BLS: M=2^12 lA=16: 1770; M=2^14 lA=16: 1702; M=2^16 lA=16: 1954; M=2^16 lA=8: 2529; M=2^16 lA=4: 3993; M=2^18 lA=4: 5742. Goldilocks: M=2^16 lA=16: 425; lA=8: 602; lA=4: 1091; M=2^18 lA=8: 612; lA=4: 1073. (Per-instance cost falls with lA, so there is a fixed per-step component, and at large M the BLS cost per constraint rises from about 1.7 to 5.7 us at lA=4. Per fresh instance includes the cost of folding in the old accumulator, so this is not a pure marginal cost.)
- B proof-excluding-statement bytes per fresh instance (derived, = B excl / (lA-1)): BLS M=2^16: lA=4 57,328; lA=8 27,038; lA=16 14,879. M=2^18 lA=4: 62,875. Goldilocks M=2^16: 52,512 / 23,122 / 11,356. The proof is nearly constant in lA (only paths' leaf columns grow), so the per-instance cost falls as 1/(lA-1).
- B-verify Merkle hashes = paths x depth: (128+128) x 14 = 3,584 (M=2^12); x 16 = 4,096 (2^14); x 18 = 4,608 (2^16); x 20 = 5,120 (2^18); sensitivity: t=189: 378 x 18 = 6,804; rate 1/2, t=256: 512 x 17 = 8,704. (Counts hashes along the paths; excludes leaf hashing of the answers.)
- decide ns per constraint (decide / raw constraints): BLS 2162 to 2257 for M >= 2^16 and for M=2^14 lA=8,16 (2673 at M=2^14 lA=4 and 2305 to 7013 at M=2^12, noisy small runs); Goldilocks 926 to 950 for M >= 2^14. Flat in lA, as expected since decide checks one accumulator.

## Commands run
```
cd upstream/warp && cargo fetch                       # (earlier session) get Cargo.lock
cd upstream/warp && cargo build --release             # 31.6 s wall, 69.7 s user
cd upstream/warp && cargo test --release              # 5 passed, 0 failed (27.4 s incl. compile)
cd proto/warp-bench && cargo build --release          # harness
cd proto/warp-bench && target/release/warp-bench --probe --field {bls12-381,goldilocks} --chain-len {1,2,4,8}
cd proto/warp-bench && cargo build && target/debug/warp-bench --field bls12-381 --chain-len 14 --lA 4 --rate-inv 4 --s 2 --t 128 --repeats 1   # debug check
cd results/T02 && python3 -I sweep.py                 # 24 runs, each: /usr/bin/time -l target/release/warp-bench --field F --chain-len L --lA A --rate-inv R --s S --t T --repeats 3
cd results/T02 && python3 -I summarize.py             # summary.csv
git -C upstream/warp status --porcelain               # (empty)
```
Not run: `cargo bench --bench warp_rs` (not in T02R), `warp-params` (does not exist on main).

## Raw output
Test summary (results/T02/test_release.log):
```
test relations::r1cs::hashchain::relation::tests::description ... ok
test relations::r1cs::hashchain::relation::tests::sanity_1 ... ok
test relations::r1cs::hashchain::relation::tests::sanity_0 ... ok
test test::warp_test_goldilocks ... ok
test test::warp_test ... ok
test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.38s
```
Debug check (results/T02/debug_check.log): debug build of the harness, BLS L=14 (M=2^12), lA=4, rate 1/4, s=2, t=128, 1 repeat: exit 0, 0 panics, `verify_and_decide_accepted: true`, A-prove 825 ms, B-prove 811 ms (debug), so no debug_assert fired in steps A (l1=4, l2=0) or B (l1=3, l2=1). Negative checks in that run also rejected.
Negative-check outputs (identical across configurations): tamper_proof_tuple_shift_answer = rejected(Err: ShiftQuery); tamper_merkle_path_element = rejected(Err: ShiftQuery); tamper_transcript_byte (mid-NARG byte flip) = rejected(Err: Target); tamper_acc_mu = rejected(Err: Target); decide_tampered_witness = rejected(Err: DeciderError(BundledEvaluation)); untampered_verify = ACCEPTED.
Sweep log (results/T02/sweep.log): DONE/SKIP lines for all 27 decisions, plus one GUARD line:
```
18:58:53 GUARD: other task process present, waiting 30s: 33303 /Library/Developer/CommandLineTools/usr/libexec/git-core/git remote-https origin https://github.com/leanEthereum/l...
18:59:23 RUN --field bls12-381 --chain-len 910 --lA 4 ...
```
Skipped (results/T02/skipped.txt): bls12-381 L910 lA8 (predicted 9.24 GiB), bls12-381 L910 lA16 (18.48 GiB), goldilocks L910 lA16 (6.51 GiB). No configuration was skipped by the 180 s time rule (largest B-prove was 4.5 s).
Per-repeat times for every phase are in results/T02/sweep.jsonl (`result.times_ms`); one example (BLS L=14 lA=4 smoke test) is shown in the transcript.

## Files changed or created
- proto/warp-bench/{Cargo.toml, Cargo.lock, rust-toolchain.toml, src/main.rs}: harness (public API of `warp` only; no upstream code copied).
- results/T02/repo_facts.md: license, toolchain, deps, API notes (a)-(f) with file:line.
- results/T02/{sweep.py, summarize.py, sweep.jsonl, summary.csv, sweep.log, skipped.txt, probe.jsonl, probe_small.jsonl, build_release.log, test_release.log, debug_check.log, runs/*, Cargo.lock.upstream, gate*.log, gate.sh}.
- results/T02/aborted_first_sweep/: superseded T02 partial sweep (1 run, s=8).
- results/T02/T02R_report.md: this report. NOTES.md: appended T02R entry.
- upstream/warp: no source changes (porcelain empty).

## Problems and deviations
- **Task grid vs. harness**: lA in {4, 8, 16} as specified; step B = (lA-1) fresh + 1 accumulator keeps l = lA a power of two. Fresh instances are rebuilt for every repeat with distinct preimages (seeded RNG, seed 1), untimed.
- **warp-params**: not on main (only unmerged branches); so the lead's (s, t) were used as given. For reference, the branch code hard-codes s=8 as "conservative", not derived from the paper; the lead's s=2 is the primary and s=8 is sensitivity set 1.
- **Memory rule was conservative**: footprint is not linear in M x lA (BLS 2^16 lA=8 used less than lA=4), so the linear extrapolation from the nearest measured run skipped BLS M=2^18 lA=8, 16 (predicted 9.2 and 18.5 GiB) and Goldilocks M=2^18 lA=16 (predicted 6.51 GiB, only just over). True footprints are probably lower, but BLS M=2^18 lA=4 already used 4.7 GiB with +1087 MiB swap, so BLS lA=8 at 2^18 would likely be memory-pressured. The Goldilocks 2^18 lA=16 cell could be run on request, it will most likely fit (3.3 GiB at lA=8).
- **Swap deltas are noisy**: `vm.swapusage` is system-wide and the machine already had 2.6 to 4 GiB swap in use before the runs. BLS M=2^12 lA=8 shows +1269 MiB although the process peaked at 141 MiB; its CPU utilisation of 0.98 and slower times (A-prove 183 ms vs 107 ms for lA=16) show it was disturbed by something else (likely system swapping/compression). By the stated rule it is "memory-pressured", but its timings are suspect; I did not rerun it. Treat BLS 2^12 lA=8 timings and the 2^18 lA=4 (+1087 MiB) row with caution; the 2^18 row's footprint 4.7 GiB on an 8 GiB machine means paging may inflate its time.
- **Guard event**: at 18:58:53 a `git remote-https` process for the leanEthereum repo (something from the T01 side, not a leanvm binary) matched the `pgrep` pattern; the driver waited about 30 s until it disappeared, then ran. No timed run overlapped any matching process.
- **Statement/proof overlap**: "excl statement" is derived as NARG - statement + Tuple; the Tuple repeats rt_0, mu_i, nu_0 that are also in the NARG (about 32 + 32 x lA + 32 bytes for BLS), so excl is over-counted by a few hundred bytes at most. The NARG contains only the statement and the field-element sumcheck/OOD messages; all Merkle paths and shift answers are in the Tuple. Total proof the verifier consumes = NARG + Tuple.
- Steps from the superseded T02 not repeated: criterion bench (`cargo bench --bench warp_rs`) and `warp-params` were not part of T02R and were not run.

## Suggested next step
Decide whether the lead wants (a) the one missing Goldilocks M=2^18 lA=16 cell and a BLS M=2^18 lA=8 run (expect paging), and (b) a single-thread run (restrict rayon via RAYON_NUM_THREADS=1) to separate algorithmic cost from the 3 to 4.5 effective cores before comparing with leanVM, whose own measurements use all cores.
=== END REPORT ===

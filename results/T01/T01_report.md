# RESULT REPORT T01

```
=== RESULT REPORT T01 ===
Status: done
```

**Machine:** Apple M2, 8 cores (4 performance + 4 efficiency), 8 GiB RAM, macOS 26.5.2 (25F84), Darwin 25.5.0 arm64, fanless MacBook Air. AC power, charging, for every T01 run (battery 97% at the start of the task, 98% at the end).
**Toolchain:** rustc 1.99.0 (b940084d7 2026-09-28) via `cargo +1.99.0`. No Lean used.
**Repo state:** `upstream/leanMultisig`.
- `research/baseline` at `df7d122abbe25cf12e5c8ae992ce6d3505f75372`: unmodified, `git status --porcelain` empty, no diff from the pinned commit. It is the branch checked out now.
- `research/rebuild-over-store` at `cee5d1c7ad4af84675eed9ca42c566cf7fd689ca`: local only, not pushed; `git status --porcelain` empty.
- `target-rebuild/` (variant build output) is untracked; I added it to the repo-local `.git/info/exclude` (not a tracked file) so `git status` stays clean on both branches.

## Summary

- **Stage breakdown (step 1):** in all 7 requested T00 logs the mapped stages cover 95.4% to 99.2% of the traced pass. Commit (NTT), PCS open and the Keccak reduction are each about a quarter of an aggregate pass. In recursion the bus GKR rises to about 16%, and child replay is only about 3%.
- **Recursion internals (step 2):** leaf proofs are made in a re-executed copy of the same binary, once per run, and are not cached on disk. The printed time covers only the parent's node-level `aggregate_with_stats` call. The T00 recursion memory rows therefore **omit the leaf-proving process**. Run alone, the M=900 leaf-proving process peaks at a 7.28 GiB footprint, against 1.15 GiB in the T00 recursion row.
- **n-to-1 (step 3):** n = 2, 4, 6, 8 at both outer rates ran. Cycles are linear in n, about 186.8k per child plus about 19.4k fixed. Proving time is near linear up to n=6 and degrades at n=8 once the machine pages (outer rate 2: 18.5 s median).
- **Rebuild variant (step 4):** `REBUILD_OVER_STORE` is a single constant, and forcing it to `true` is a one-line change. All four sizes (250, 500, 1000, 1500) ran. Cycles, committed size and proof size are identical to T00 at every size.
  - N=1000 drops from 45.4 s to 10.8 s (4.2x faster) and N=1500 from 94.4 s to 58.0 s (1.6x faster).
  - The footprint falls from 7.34 to 4.67 GiB (N=1000) and from 9.54 to 7.46 GiB (N=1500).
  - N=1500 now just fits under 8 GiB of RAM, but it still pages (swap +2,128 MiB, 200 s wall, 37x slower than the README's 1.554 s on an M4 Max).
- **Drift check (4d):** baseline N=250 median 0.982 s against T00's 1.026 s, 4.3% lower, within the 15% bound.

## Results

All runs: AC power, 30 s pause before each, `/usr/bin/time -l`, `--repeat 3`, `--tracing`. "Median" is computed by me from the printed per-pass times (`--repeat` prints each pass and the mean with a 95% CI, not a median). Memory: OS peak footprint is the primary metric. "memory-pressured" means swap used grew by more than 256 MiB; no run was stopped for it.

### 1. Stage breakdown of the seven T00 logs (step 1)

Cells are seconds (percent of the traced pass). The traced pass is the last measured pass and its total is the last printed pass time. Per-run logs: `results/T00/*.log`. Parser: `results/T01/scripts/parse_trace.py`. Data: `results/T01/stages.csv`.

| stage | agg N=50 | agg N=100 | agg N=250 | agg N=500 | rec M=50 | rec M=250 | rec M=900 |
|---|---|---|---|---|---|---|---|
| execute | 0.018 (6.2%) | 0.025 (5.1%) | 0.044 (4.3%) | 0.139 (4.9%) | 0.017 (4.1%) | 0.023 (5.3%) | 0.022 (5.2%) |
| witness build | 0.006 (2.1%) | 0.009 (1.9%) | 0.021 (2.0%) | 0.052 (1.8%) | 0.012 (2.9%) | 0.014 (3.4%) | 0.013 (3.0%) |
| commit | 0.069 (24.3%) | 0.129 (26.1%) | 0.269 (26.2%) | 0.807 (28.4%) | 0.091 (22.0%) | 0.093 (21.7%) | 0.096 (22.4%) |
| bus GKR | 0.027 (9.5%) | 0.043 (8.6%) | 0.123 (12.0%) | 0.375 (13.2%) | 0.071 (17.0%) | 0.068 (15.8%) | 0.070 (16.4%) |
| constraint sumcheck | 0.004 (1.4%) | 0.007 (1.3%) | 0.012 (1.2%) | 0.026 (0.9%) | 0.017 (4.0%) | 0.017 (3.9%) | 0.017 (3.9%) |
| Keccak GKR/reduction | 0.073 (25.8%) | 0.124 (25.1%) | 0.269 (26.2%) | 0.520 (18.3%) | 0.070 (16.9%) | 0.076 (17.7%) | 0.087 (20.4%) |
| PCS open | 0.073 (26.0%) | 0.145 (29.3%) | 0.280 (27.3%) | 0.878 (30.9%) | 0.117 (28.1%) | 0.116 (27.1%) | 0.105 (24.6%) |
| replay children | 0.000 (0.0%) | 0.000 (0.0%) | 0.000 (0.0%) | 0.000 (0.0%) | 0.015 (3.6%) | 0.015 (3.4%) | 0.011 (2.7%) |
| other | 0.013 (4.6%) | 0.013 (2.7%) | 0.008 (0.8%) | 0.046 (1.6%) | 0.006 (1.3%) | 0.007 (1.6%) | 0.006 (1.4%) |
| (commit: NTT part) | 0.068 (24.3%) | 0.129 (26.1%) | 0.268 (26.1%) | 0.807 (28.4%) | 0.091 (22.0%) | 0.093 (21.7%) | 0.096 (22.4%) |
| **traced pass total s** | 0.282 | 0.495 | 1.026 | 2.843 | 0.416 | 0.428 | 0.427 |
| mapped coverage % | 95.4 | 97.3 | 99.2 | 98.4 | 98.7 | 98.4 | 98.6 |

**Span-to-stage mapping used** (spans from `crates/leanvm_core/src/cpu/mod.rs:437,448,470,488,491,522,527` and `crates/rec_aggregation/src/aggregation/node.rs:121,146,278`, `proof.rs:199,205`):

| stage | trace span (direct child of the pass-level `Prove` span unless noted) |
|---|---|
| execute | `Execute program` |
| witness build | `Build witness` inside `Prove`, plus the node-level `Build witness` (with its `Bytecode sums`) |
| commit (NTT + Merkle) | `Commit` (children `NTT`, `Merkle`; the sub-row "commit: NTT part" is the NTT child) |
| bus GKR | `Prove bus` (`Bus leaves`, `Bus GKR`, `Bus decompose`, `Bus tables`) |
| constraint sumcheck | `Prove constraints` |
| Keccak GKR / reduction | `Keccak reduction` |
| PCS open (stacked WHIR) | `PCS open` (its own inner `Commit`, `Sumcheck`, `Open`, `Induce` spans are inside it, not separate stages) |
| replay children | node-level `Replay children` (recursion only) |
| other | anything else: node-level `Batch deferred claims`, `Recompute deferred claims`, `Statement digest`, `LeanDA commit`; the part of `Prove` not covered by a child span; and any gap between the span sum and the printed pass time |

For these seven logs `other` is made of: `Recompute deferred claims` (3.4 ms in recursion; 0 in aggregation), `Batch deferred claims` (1.3 to 1.5 ms, recursion), `Statement digest` (0.01 to 0.2 ms), the `Prove` residual (-0.8 to +3.9 ms; negative values are rounding in the 3-significant-figure span times), and an untraced gap of 1.1 to 13.2 ms (43.9 ms at N=500) between the span sum and the printed pass time. `stages.csv` lists these per log in its `note` column. The aggregation logs have an empty `Replay children` span (4.5 µs): no children.

How the traced pass is defined: the `aggregation` root's direct children for aggregate logs (`benchmark.rs:85`); the top-level spans for recursion logs, which have no root. In both cases the sum of these spans agrees with the printed last pass within 0.3% to 2.5% (4.7% at N=50).

### 2. Recursion internals (step 2)

All paths relative to `upstream/leanMultisig`, commit df7d122.

**(i) How leaf proofs are produced.** In a **child process**, once per recursion run, **not cached on disk**.
- `bins/leanvm/src/benchmark.rs:185` `let children = leaves_from_subprocess(n);`
- `benchmark.rs:271-291` `leaves_from_subprocess`: re-runs the same binary (`current_exe()`, `:273`) with the same arguments (`:274`) and `LEANVM_LEAVES_OUT` set (`:275`, constant at `:267`). The child's output goes to `std::env::temp_dir()/leanvm-leaves-<pid>.bin` (`:272`; `$TMPDIR`, a per-user `/var/folders/...` directory on macOS). The parent reads it (`:279`), deletes it (`:280`) and decodes the proofs (`:284-288`).
- Child branch: `benchmark.rs:175-184` returns early into `write_leaves` (`:238-264`). It proves each leaf in-process with `aggregate(...)` at `--leaf-log-inv-rate` (`:250-258`), using distinct signers per leaf (`:252`) and blob seeds (`:254`). It runs once, with no warmup and no repeat.
- What is cached on disk is only the signer set, not the proofs: `crates/rec_aggregation/src/signers_cache.rs:71-72` (`<crate>/../../target/signers-cache`, i.e. `upstream/leanMultisig/target/signers-cache`), file name at `:77-86`. The child passes `--tracing` through its arguments but returns at `:175` before tracing is initialised (`:187-189`), so leaf proving is never traced.
- Allowed `--n`: `benchmark.rs:158-161` asserts `1..=MAX_RECURSIONS`, with `MAX_RECURSIONS = 16` (`crates/rec_aggregation/src/aggregation/mod.rs:72`; also checked at `node.rs:72`). The CLI field has no range of its own (`main.rs:62-66`).

**(ii) What the printed proving time and peak memory cover.**
- Proving time: `benchmark.rs:190-193` `plan.warm_then_measure(... aggregate_with_stats(&children, vec![], vec![], &[], None, log_inv_rate) ...)`, i.e. the whole node-level `aggregate` call (replay of the children, witness building, `Prove`, deferred claims), not just `cpu::prove` (comment at `:54-56`). One discarded warmup pass, then `--repeat` measured passes (`crates/bench/src/lib.rs:185-192`). The timer wraps only the call: `Instant::now()` is after the cooldown (`lib.rs:214-215`) and `timing.push` follows (`:218`). It excludes leaf proving, leaf decoding, signer-cache generation, guest compilation (`:171-174`) and verification (`:194-196`). The printed value is the mean (`:59`), and `spread()` the 95% CI.
- Peak memory: `benchmark.rs:61` `crate::report::peak_gib()`, defined at `bins/leanvm/src/report.rs:19-21` as `bench::peak_rss_bytes()` (`crates/bench/src/lib.rs:235-245`): `getrusage(RUSAGE_SELF).ru_maxrss`. It is the **parent process's own** high-water RSS at print time, i.e. after the warmup, all measured passes and verification. It excludes the leaf-proving child by design (comment at `benchmark.rs:269-270`). It is an RSS, not a footprint, so it undercounts swapped or compressed pages.

**(iii) What "proven at log-inv-rate X" refers to.** The leaf rate (`--leaf-log-inv-rate`). `benchmark.rs:215-217` adds `proven at log-inv-rate {leaf_log_inv_rate}` to the header whenever the leaf rate differs from the outer `--log-inv-rate`. So a header saying "2" on an outer-rate-1 run is correct and not a bug. The outer rate is not printed in the header.

**(iv) Why max RSS exceeds the footprint in recursion runs (most likely reason).** The `time -l` figures describe a process tree and the program's printed figures describe one process.
- The recursion command forks a child that proves the leaves (`benchmark.rs:273-277`). The parent's own work is small (the node proof). The parent's printed peak and its OS footprint agree (T00 M=900: printed 1.104 GiB, footprint 1.15 GiB).
- My reading of the BSD/macOS `wait4` rusage semantics, which I did not verify in the OS source, is that `time -l` reports `ru_maxrss` as the maximum over the process and its reaped descendants, so the "max RSS" row is dominated by the leaf-proving process. The footprint row appears to describe the parent only.
- Direct measurement supports it: I ran the child path alone (`LEANVM_LEAVES_OUT=... recursion --n 2 --xmss-per-leaf M ...`, logs `results/T01/leafchild_m250.log` and `leafchild_m900.log`):

| leaf-proving process alone | max RSS | peak footprint | swap Δ | wall |
|---|---|---|---|---|
| n=2, M=250 | 1.49 GiB | 2.02 GiB | +145 MiB | 4.0 s |
| n=2, M=900 | 1.92 GiB | **7.28 GiB** | +4,595 MiB | 59.8 s |

  Against the T00 recursion rows (parent only, footprint 1.15 GiB at both sizes), this process is 1.8x (M=250) and 6.3x (M=900) larger. That also answers the "footprint far below what a 900-signature leaf needs" puzzle: the leaf cost is simply not in the parent's rows.
- **What I could not reproduce:** the combined-run max RSS (1.90 GiB at M=250, 3.01 GiB at M=900) does not equal the child-alone max RSS (1.49, 1.92 GiB). RSS of a process that is being paged is unstable (T00 aggregate N=1000 and N=1500 show 3.09 and 2.52 GiB for the same reason), so I treat the attribution as likely, not proven.

### 3. n-to-1 recursion sweep (step 3)

Commands: `/usr/bin/time -l target/release/leanvm recursion --n {2,4,6,8} --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate {1,2} --repeat 3 --tracing` (baseline binary, `research/baseline`). The OS footprint, max RSS and leanVM peak describe different things here: footprint and leanVM peak are the parent (node proof) and max RSS also reflects the leaf process (see (iv)). Leaf-proving time is not in "prove s". Wall time includes leaf proving. Data: `results/T01/summary.csv`.

| n | outer rate | cycles | per-opcode line | TOTAL_COMMITTED (log2 words) | proof KiB | prove s (each pass) | median s | leanVM peak GiB | OS max RSS GiB | OS peak footprint GiB | swap Δ MiB | verify ms | wall s | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 1 | 392,988 | MUL 2^17.132 (36.5%)  XOR 2^16.681 (26.7%)  DEREF 2^16.105 (17.9%)  SET 2^15.213 (9.7%)  JUMP 2^14.637 (6.5%)  KECCAK 2^13.347 (2.7%)  MEMORY 2^19.379  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842 | 2^23.842 | 321.4 | 0.445 0.426 0.437 | 0.437 | 1.119 | 1.822 | 1.153 | -200 | 14.263 | 12.43 | AC |
| 4 | 1 | 766,603 | MUL 2^18.129 (37.4%)  XOR 2^17.678 (27.3%)  DEREF 2^17.093 (18.2%)  SET 2^15.845 (7.7%)  JUMP 2^15.634 (6.6%)  KECCAK 2^14.344 (2.7%)  MEMORY 2^20.357  BYTECODE 2^18.899  TOTAL_COMMITTED 2^24.791 | 2^24.791 | 331.0 | 0.924 1.06 0.897 | 0.924 | 1.871 | 1.871 | 1.909 | -120 | 15.572 | 16.20 | AC |
| 6 | 1 | 1,140,247 | MUL 2^18.713 (37.7%)  XOR 2^18.262 (27.6%)  DEREF 2^17.674 (18.3%)  SET 2^16.282 (7.0%)  JUMP 2^16.218 (6.7%)  KECCAK 2^14.928 (2.7%)  MEMORY 2^20.935  BYTECODE 2^18.899  TOTAL_COMMITTED 2^25.036 | 2^25.036 | 303.8 | 1.488 1.691 1.571 | 1.571 | 2.303 | 2.303 | 2.365 | 25 | 14.84 | 21.23 | AC |
| 8 | 1 | 1,514,224 | MUL 2^19.128 (37.8%)  XOR 2^18.676 (27.7%)  DEREF 2^18.088 (18.4%)  JUMP 2^16.632 (6.7%)  SET 2^16.618 (6.6%)  KECCAK 2^15.342 (2.7%)  MEMORY 2^21.346  BYTECODE 2^18.899  TOTAL_COMMITTED 2^25.778 | 2^25.778 | 343.6 | 2.78 3.728 2.941 | 2.941 | 2.751 | 2.751 | 3.53 | 564 | 18.896 | 36.61 | AC; memory-pressured |
| 2 | 2 | 392,988 | MUL 2^17.132 (36.5%)  XOR 2^16.681 (26.7%)  DEREF 2^16.105 (17.9%)  SET 2^15.213 (9.7%)  JUMP 2^14.637 (6.5%)  KECCAK 2^13.347 (2.7%)  MEMORY 2^19.379  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842 | 2^23.842 | 232.6 | 0.557 0.556 0.569 | 0.557 | 1.427 | 1.931 | 1.453 | -40 | 13.498 | 12.60 | AC |
| 4 | 2 | 766,603 | MUL 2^18.129 (37.4%)  XOR 2^17.678 (27.3%)  DEREF 2^17.093 (18.2%)  SET 2^15.845 (7.7%)  JUMP 2^15.634 (6.6%)  KECCAK 2^14.344 (2.7%)  MEMORY 2^20.357  BYTECODE 2^18.899  TOTAL_COMMITTED 2^24.791 | 2^24.791 | 239.9 | 1.242 1.338 1.467 | 1.338 | 2.311 | 2.311 | 2.399 | -80 | 14.238 | 17.45 | AC |
| 6 | 2 | 1,140,247 | MUL 2^18.713 (37.7%)  XOR 2^18.262 (27.6%)  DEREF 2^17.674 (18.3%)  SET 2^16.282 (7.0%)  JUMP 2^16.218 (6.7%)  KECCAK 2^14.928 (2.7%)  MEMORY 2^20.935  BYTECODE 2^18.899  TOTAL_COMMITTED 2^25.036 | 2^25.036 | 227.4 | 2.333 2.092 2.863 | 2.333 | 2.967 | 2.967 | 3.098 | 689 | 40.576 | 26.73 | AC; memory-pressured |
| 8 | 2 | 1,514,224 | MUL 2^19.128 (37.8%)  XOR 2^18.676 (27.7%)  DEREF 2^18.088 (18.4%)  JUMP 2^16.632 (6.7%)  SET 2^16.618 (6.6%)  KECCAK 2^15.342 (2.7%)  MEMORY 2^21.346  BYTECODE 2^18.899  TOTAL_COMMITTED 2^25.778 | 2^25.778 | 248.3 | 14.749 24.451 18.506 | 18.506 | 2.673 | 2.673 | 4.352 | 993 | 35.177 | 78.81 | AC; memory-pressured |

Observations: cycles = 392,988 plus about 186.8k per additional child (n=4: 766,603; n=6: 1,140,247; n=8: 1,514,224), identical for both outer rates, as expected. Median at outer rate 1 is 0.437, 0.924, 1.571 and 2.941 s for n = 2, 4, 6, 8: per-child cost rises from 0.22 to 0.37 s at n=8, where the swap flag is set. At outer rate 2 the cost is 0.557, 1.338, 2.333 and 18.506 s; the n=8 passes (14.7, 24.5, 18.5 s) are paging-dominated and spread widely (±56.6% CI), so that point is a memory-limit measurement rather than a protocol cost. Stage shares at n=8 (table below) shift to bus GKR (43.5% at outer rate 1) and, with outer rate 2, to commit (45.3%).

Stage breakdown for the n-sweep (same parser; data in `stages.csv`):

| stage | n=2, outer 1 | n=4, outer 1 | n=6, outer 1 | n=8, outer 1 | n=2, outer 2 | n=4, outer 2 | n=6, outer 2 | n=8, outer 2 |
|---|---|---|---|---|---|---|---|---|
| execute | 0.022 (5.1%) | 0.061 (6.8%) | 0.069 (4.4%) | 0.099 (3.4%) | 0.021 (3.6%) | 0.050 (3.4%) | 0.059 (2.1%) | 0.683 (3.7%) |
| witness build | 0.014 (3.3%) | 0.045 (5.0%) | 0.108 (6.9%) | 0.182 (6.2%) | 0.015 (2.6%) | 0.107 (7.3%) | 0.066 (2.3%) | 0.434 (2.3%) |
| commit | 0.093 (21.4%) | 0.191 (21.3%) | 0.330 (21.0%) | 0.513 (17.4%) | 0.187 (32.9%) | 0.460 (31.4%) | 1.180 (41.2%) | 8.380 (45.3%) |
| bus GKR | 0.070 (15.9%) | 0.182 (20.3%) | 0.404 (25.7%) | 1.280 (43.5%) | 0.074 (12.9%) | 0.258 (17.6%) | 0.536 (18.7%) | 4.510 (24.4%) |
| constraint sumcheck | 0.017 (3.8%) | 0.032 (3.6%) | 0.041 (2.6%) | 0.078 (2.6%) | 0.018 (3.2%) | 0.059 (4.0%) | 0.054 (1.9%) | 0.158 (0.9%) |
| Keccak GKR/reduction | 0.079 (18.1%) | 0.142 (15.8%) | 0.190 (12.1%) | 0.267 (9.1%) | 0.080 (14.0%) | 0.141 (9.6%) | 0.210 (7.3%) | 0.329 (1.8%) |
| PCS open | 0.115 (26.3%) | 0.211 (23.5%) | 0.354 (22.5%) | 0.454 (15.4%) | 0.152 (26.7%) | 0.350 (23.9%) | 0.707 (24.7%) | 3.610 (19.5%) |
| replay children | 0.021 (4.7%) | 0.008 (0.9%) | 0.029 (1.8%) | 0.032 (1.1%) | 0.017 (3.0%) | 0.015 (1.0%) | 0.028 (1.0%) | 0.068 (0.4%) |
| other | 0.006 (1.5%) | 0.025 (2.8%) | 0.047 (3.0%) | 0.036 (1.2%) | 0.007 (1.2%) | 0.028 (1.9%) | 0.023 (0.8%) | 0.334 (1.8%) |
| (commit: NTT part) | 0.093 (21.3%) | 0.191 (21.3%) | 0.330 (21.0%) | 0.513 (17.4%) | 0.187 (32.9%) | 0.460 (31.4%) | 1.180 (41.2%) | 8.380 (45.3%) |
| **traced pass total s** | 0.437 | 0.897 | 1.571 | 2.941 | 0.569 | 1.467 | 2.863 | 18.506 |
| mapped coverage % | 98.5 | 97.2 | 97.0 | 98.8 | 98.8 | 98.1 | 99.2 | 98.2 |

### 4. Codeword-rebuild variant (step 4)

**4a. `REBUILD_OVER_STORE`: definition and semantics.**
- Definition: `crates/primitives/src/lib.rs:103`: `pub const REBUILD_OVER_STORE: bool = !cfg!(all(target_arch = "aarch64", target_os = "macos"));`. The doc comment at `:98-102` says: x86 and every non-Apple target rebuild what a later step reads, since store traffic costs more than the rebuilding products; on Apple silicon the prover stores. `AGENTS.md:117` says the same and names this constant as the single per-machine switch. So it is `true` (rebuild) everywhere except Apple silicon macOS, where it is `false` (store).
- It is read at exactly two places, both in `crates/pcs/src/whir.rs`:
  - `whir.rs:149-155`, the base-field commit (`commit`): `Keep::Whole` when the constant is `false` (the whole codeword is kept); when `true`, `Keep::Nothing` if the codeword exceeds `KEEP_CODEWORD_MAX_BYTES` (1 GiB, `:108`, test at `:151`), else `Keep::BeforeDeep`. The doc at `:102-108` says that above the cap the codeword dominates the peak, so the commit keeps none and encodes half of the cosets at a time.
  - `whir.rs:242-243`, the extension-field commit (`ligero_commit_ext`): `defer_deep = REBUILD_OVER_STORE`, passed to `encode_interleaved_with` (`crates/pcs/src/ntt/encode.rs:127-140`), so the deep NTT layer is finished in scratch and not written back.
- The `Keep` variants and `defer_deep` are plain code in `crates/pcs/src/ntt/encode.rs:23,86-140,188-229`, not architecture-gated, and the NTT tests exercise all three `Keep` values (`ntt/tests.rs:269`). So forcing the constant is a single, trivial switch and the other value is already the production path on non-Apple targets.

**4b. Exact diff** (branch `research/rebuild-over-store`, local commit `cee5d1c7ad4af84675eed9ca42c566cf7fd689ca`, one file, 1 insertion, 1 deletion, vs `df7d122abbe25cf12e5c8ae992ce6d3505f75372`):

```diff
--- a/crates/primitives/src/lib.rs
+++ b/crates/primitives/src/lib.rs
@@ -103 +103 @@
-pub const REBUILD_OVER_STORE: bool = !cfg!(all(target_arch = "aarch64", target_os = "macos"));
+pub const REBUILD_OVER_STORE: bool = true; // T01 experiment: force the rebuild path (was: !cfg!(all(target_arch = "aarch64", target_os = "macos")))
```

**4c. Build:** `CARGO_TARGET_DIR=target-rebuild cargo +1.99.0 build --release -p leanvm-cli`, 44.4 s wall, binary `upstream/leanMultisig/target-rebuild/release/leanvm` (differs from the baseline binary; `md5` 32ed45a8… vs 5653211e…). The baseline binary in `target/` was untouched. Log: `results/T01/build_rebuild.log`.

**4d. Drift check** (`aggregate --xmss 250 --log-inv-rate 2 --repeat 3 --tracing`, baseline binary):

| | T00 (AC) | T01 drift run | change |
|---|---|---|---|
| passes (s) | 1.248, 0.989, 1.026 | 1.073, 0.964, 0.982 | |
| median (s) | 1.026 | 0.982 | **-4.3%** (within 15%) |
| cycles / committed / proof | 219,994 / 2^24.103 / 220.0 KiB | same | identical |
| OS peak footprint | 2.03 GiB | 2.03 GiB | same |

**4e. Side-by-side, N = 250 / 500 / 1000 / 1500** (`aggregate --xmss N --log-inv-rate 2 --repeat 3 --tracing`; variant binary vs the T00 baseline AC runs; median of 3 passes). No size was skipped: predicted footprints (last footprint x size ratio) were 4.2 GiB for N=500, 6.5 GiB for N=1000 and 7.0 GiB for N=1500, all under the 9.5 GiB limit.

| N | baseline median s | variant median s | speed-up | baseline footprint GiB | variant footprint GiB | baseline swap Δ MiB | variant swap Δ MiB | variant wall s | cycles = TOTAL_COMMITTED = proof size as T00 |
|---|---|---|---|---|---|---|---|---|---|
| 250 | 1.026 | 1.024 | 1.00x | 2.03 | 2.08 | +83 | -8 | 12.65 | yes (219,994; 2^24.103; 220.0 KiB) |
| 500 | 2.843 | 2.872 | 0.99x | 3.94 | 3.267 | +1497 | +291 | 19.64 | yes (421,410; 2^25.082; 228.2 KiB) |
| 1000 | 45.371 | 10.806 | 4.20x | 7.34 | 4.674 | +3324 | +1307 | 48.42 | yes (824,204; 2^26.05; 238.2 KiB) |
| 1500 | 94.444 | 57.969 | 1.63x | 9.54 | 7.456 | +4942 | +2128 | 199.82 | yes (1,227,023; 2^26.993; 265.1 KiB) |

**4f. Identity and verification.** For all four variant runs, the cycle count, per-opcode line, TOTAL_COMMITTED and proof size are identical to the T00 values (compared programmatically against `results/T00/summary.csv`), and the proof verified (the benchmark panics on a failed `verify`; verify times 10.2, 11.7, 29.7 and 48.3 ms). No differences to flag.

Raw variant figures, for reference (leanVM printed peak is RSS-based and so understates under paging):

| N | passes (s) | leanVM peak GiB | OS max RSS GiB | verify ms |
|---|---|---|---|---|
| 250 | 1.107, 1.024, 0.997 | 1.829 | 1.829 | 10.212 |
| 500 | 3.041, 2.872, 2.733 | 2.720 | 2.720 | 11.652 |
| 1000 | 12.467, 9.139, 10.806 | 2.530 | 2.530 | 29.694 |
| 1500 | 54.842, 57.969, 63.265 | 2.965 | 2.965 | 48.290 |

**Stage breakdown of the variant** (seconds, percent of the traced pass). The requested N=250 run, the baseline drift run beside it, and the larger sizes:

| stage | baseline N=250 (drift run) | variant N=250 | variant N=500 | variant N=1000 | variant N=1500 |
|---|---|---|---|---|---|
| execute | 0.042 (4.2%) | 0.043 (4.3%) | 0.136 (5.0%) | 0.463 (4.3%) | 4.120 (6.5%) |
| witness build | 0.016 (1.6%) | 0.016 (1.6%) | 0.062 (2.3%) | 0.488 (4.5%) | 1.075 (1.7%) |
| commit | 0.258 (26.3%) | 0.257 (25.8%) | 0.712 (26.1%) | 1.640 (15.2%) | 8.620 (13.6%) |
| bus GKR | 0.079 (8.1%) | 0.076 (7.7%) | 0.218 (8.0%) | 1.140 (10.6%) | 18.000 (28.5%) |
| constraint sumcheck | 0.013 (1.4%) | 0.012 (1.2%) | 0.029 (1.0%) | 0.059 (0.5%) | 0.683 (1.1%) |
| Keccak GKR/reduction | 0.278 (28.3%) | 0.265 (26.6%) | 0.509 (18.6%) | 1.140 (10.6%) | 4.490 (7.1%) |
| PCS open | 0.290 (29.5%) | 0.319 (32.0%) | 1.000 (36.6%) | 5.800 (53.7%) | 25.900 (40.9%) |
| replay children | 0.000 (0.0%) | 0.000 (0.0%) | 0.000 (0.0%) | 0.000 (0.0%) | 0.000 (0.0%) |
| other | 0.006 (0.6%) | 0.008 (0.8%) | 0.067 (2.5%) | 0.076 (0.7%) | 0.377 (0.6%) |
| (commit: NTT part) | 0.258 (26.3%) | 0.257 (25.8%) | 0.712 (26.1%) | 1.640 (15.2%) | 8.620 (13.6%) |
| **traced pass total s** | 0.982 | 0.997 | 2.733 | 10.806 | 63.265 |
| mapped coverage % | 99.4 | 99.2 | 97.5 | 99.3 | 99.4 |

At N=250 the variant's profile is the baseline's: commit 25.8% against 26.3%, PCS open 32.0% against 29.5%. The N=250 total is 0.997 s against 0.982 s. At N=1000 and N=1500 the shares move to PCS open (53.7%, 40.9%) and, at N=1500, to the bus GKR (28.5%); those passes still page, so the shares reflect memory stalls as much as the algorithm.

**Reading of the result (fit in 8 GiB).** The rebuild path saves memory only when the codeword is large. The footprint is unchanged at N=250 (2.08 against 2.03 GiB) and only 17% lower at N=500, then 36% lower at N=1000 and 22% lower at N=1500. With the cap at `whir.rs:108`, the `Keep::Nothing` branch is the one that can matter above 1 GiB of codeword; I did not instrument which branch each size takes, so the link between the cap and the N=1000 gain is a hypothesis from code reading. N=1500 is 7.46 GiB against 8 GiB of RAM: it fits in the sense of staying under RAM, but with the OS and open applications it still grew swap by 2,128 MiB and took 199.8 s wall, with a median pass of 58.0 s. N=1000 is the largest size that runs in a reasonable time here (10.8 s median).

## Commands run

```
# Step 0
cp <scratchpad>/run.sh <scratchpad>/sweep_ac.py /tmp/parse.py results/T00/scripts/     # all three still existed
mkdir -p results/T01/scripts
# Step 1 (no new runs)
python3 -I results/T01/scripts/parse_trace.py <19 logs> --csv results/T01/stages.csv
# Step 2: read-only, plus two direct runs of the leaf-proving path
LEANVM_LEAVES_OUT=<scratchpad>/leaves{250,900}.bin /usr/bin/time -l target/release/leanvm recursion --n 2 --xmss-per-leaf {250,900} --leaf-log-inv-rate 2 --log-inv-rate 1 --repeat 3
# Step 3 (results/T01/scripts/nsweep.py; 30 s pause before each)
/usr/bin/time -l target/release/leanvm recursion --n {2,4,6,8} --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate {1,2} --repeat 3 --tracing
# Step 4
git -C upstream/leanMultisig checkout -b research/rebuild-over-store df7d122abbe25cf12e5c8ae992ce6d3505f75372
sed -i '' ... crates/primitives/src/lib.rs        # the one-line change
git commit -m "experiment: force REBUILD_OVER_STORE = true on Apple silicon (local, T01)"      # cee5d1c7
CARGO_TARGET_DIR=target-rebuild cargo +1.99.0 build --release -p leanvm-cli
git checkout research/baseline
# Steps 4d/4e (results/T01/scripts/rebuild_sweep.py; 30 s pause before each)
/usr/bin/time -l target/release/leanvm aggregate --xmss 250 --log-inv-rate 2 --repeat 3 --tracing                  # baseline drift check
/usr/bin/time -l target-rebuild/release/leanvm aggregate --xmss {250,500,1000,1500} --log-inv-rate 2 --repeat 3 --tracing
# Step 6
git -C upstream/leanMultisig status --porcelain       # on both branches: empty
python3 -I results/T01/scripts/parse_runs.py results/T01/summary.csv <13 logs>
```

## Raw output

Complete logs: `results/T01/*.log` (command, date, power, swap before and after, trace tree, result block, `time -l`). Key blocks:

```
aggregate --xmss 1500 --log-inv-rate 2 --repeat 3   (variant binary, AC)
  cycles (VM steps)           : 1,227,023 = 2^20.227
    details                   : XOR 2^18.099 (22.9%)  KECCAK 2^18.094 (22.8%)  MUL 2^17.955 (20.7%)  SET 2^17.46 (14.7%)  DEREF 2^17.38 (13.9%)  JUMP 2^15.91 (5.0%)  MEMORY 2^23.147  BYTECODE 2^18.899  TOTAL_COMMITTED 2^26.993
  proof size                  : 265.1 KiB
  proving time                : 58.692 s ± 16.1%      peak memory 2.965 GiB
  verifying                   : 48.29 ms
      199.82 real       160.28 user        88.67 sys
          3183214592  maximum resident set size
          8005998688  peak memory footprint
# swap_before used 4695.50M -> swap_after used 6823.38M

recursion 8→1, over leaves of 250 leanXMSS signatures, proven at log-inv-rate 2   (outer rate 2)
  cycles (VM steps)           : 1,514,224 = 2^20.53
  proof size                  : 248.3 KiB
  proving time                : 19.235 s ± 56.6%      peak memory 2.673 GiB
  verifying                   : 35.177 ms
       78.81 real
          2869608448  maximum resident set size
          4672868120  peak memory footprint
```

## Files changed or created

- `results/T01/T01_report.md`: this report.
- `results/T01/summary.csv`: 13 new runs (8 n-sweep, 1 drift, 4 variant), one row each.
- `results/T01/stages.csv`: per-stage rows for 20 logs (the 7 requested T00 logs, the 8 n-sweep runs, the drift run and the 4 variant runs).
- `results/T01/*.log`: raw logs of every new run, plus `leafchild_m250.log`, `leafchild_m900.log` (step 2 diagnostics) and `build_rebuild.log`.
- `results/T01/scripts/`: `parse_trace.py`, `parse_runs.py`, `run.sh`, `nsweep.py`, `rebuild_sweep.py`.
- `results/T00/scripts/`: copies of the T00 driver scripts (`run.sh`, `sweep_ac.py`, `parse.py`).
- `NOTES.md`: dated T01 entry added.
- `upstream/leanMultisig`: local branch `research/rebuild-over-store` (one commit) and untracked `target-rebuild/` (excluded via `.git/info/exclude`). `research/baseline` unchanged.

## Problems and deviations

- **Prediction rule:** the first variant run (N=250) has nothing to predict from; the later sizes were predicted from the previous run's footprint, and all stayed under 9.5 GiB, so none was skipped.
- **`stages.csv` has 20 logs, not 7,** because I also parsed the T01 runs. The 7 requested T00 logs are all present.
- **Stage coverage is 95.4% at its lowest** (aggregate N=50, due to a 13.2 ms untraced gap on a 0.282 s pass). The other six T00 logs are at 97.3% or higher, and the T01 logs at 97.0% or higher.
- **`Replay children` is empty for aggregation** and the stage is reported as 0; it is only meaningful for recursion.
- **Step 2 (iv) is an inference, not a proof,** as described above. I did not read the macOS kernel `wait4` rusage code, and the combined-run max RSS was not reproduced exactly by the child-alone runs.
- **Memory-pressured runs continue to carry paging noise:** n=6 and n=8 recursion at outer rate 2, n=8 at outer rate 1, and variant N >= 500. Their times reflect this machine's limit.
- **Statements about which `Keep` branch each size takes are from reading the code, not instrumentation.**
- **Signer cache growth:** the n=8 runs needed 2,000 signers, more than the previous cache held, so the first n=8 run generated about 200 more (one-time, in the unmeasured child process, cached under `target/signers-cache`).

## Suggested next step

For a clean size-versus-time curve on this machine, use the variant binary for N >= 1000 and quote its numbers only with the footprint beside them. To test the `Keep::Nothing` hypothesis and to see how much of the N=1500 time is paging, run the variant on a Linux box with at least 16 GiB, where the rebuild path is the default and the README's 1.554 s can be compared directly. Separately, the T00 recursion memory rows should be restated with the leaf-proving process included (or the leaf cost reported on its own, as above).

=== END REPORT ===

# RESULT REPORT T00

```
=== RESULT REPORT T00 ===
Status: done
```

**Machine:** Apple M2, 8 cores (4 performance + 4 efficiency), 8 GiB RAM, macOS 26.5.2 (25F84), Darwin 25.5.0 arm64, fanless MacBook Air. **AC power** for the final sweep (battery 27% to 92% while charging).
**Toolchain:** rustc 1.99.0 (b940084d7 2026-09-28) via `cargo +1.99.0` (default toolchain remains 1.88.0). Lean 4.34.1 / Lake 5.0.0 on PATH (the leanervm project pins the same); ArkLib pins Lean 4.35.0. No Lean code built in this task.
**Repo state:** `upstream/leanMultisig`, branch `research/baseline`, commit `df7d122abbe25cf12e5c8ae992ce6d3505f75372`. Default-branch HEAD at clone time: `69fb2482c0a0945ae1cebb841267a77d28a6644c` (2026-11-07). `git status --porcelain`: empty (no tracked changes). No other repos touched. `NOTES.md` is a new file in the workspace root.

## Summary

- Workspace, machine record, build, CLI discovery, timing discovery and the **full sweep** are done on **AC power**: fibonacci n=200000; aggregate N = 50, 100, 250, 500, 1000, 1500; recursion M = 50, 100, 250, 500, 900.
- **Aggregate N=1500 reproduces the README reference exactly** in cycles (1,227,023), TOTAL_COMMITTED (2^26.993) and proof size (265.1 KiB).
- **Recursion M=900 does not match the README reference**: 438,675 cycles and 322.1 KiB here, against 542,049 cycles and 216.9 KiB. See "Reference-number comparison".
- **This 8 GiB machine pages heavily at N >= 500.** N=1000 takes 45 s and N=1500 takes 94 s per proof (median), against 1.554 s on the reference M4 Max. The OS peak memory footprint at N=1500 is 9.54 GiB, which exceeds RAM. Do not read those times as protocol cost.
- leanVM's own "peak memory" and the OS max RSS understate the true footprint once pages are swapped or compressed (N=1500: 2.52 GiB printed, 9.54 GiB footprint). Use the OS peak memory footprint column for memory comparisons.
- A first run on battery is kept in `results/T00/battery_run/` (4 aggregate and 4 recursion sizes, stopped by the swap rule). It is superseded by the AC run.

## Results

BUDGET: the task formula gives 4.8 GiB (60% of 8 GiB). After the user plugged in the machine, the user set the budget to the full 8 GiB for the rerun, so the AC run used BUDGET = 8 GiB. Its only stop rule was the predicted-peak check (last peak x size ratio, from OS max RSS), and no size was skipped. Swap growth above 256 MiB is **flagged "memory-pressured" but did not stop the sweep**. That departs from the task's stop rule and is deliberate, at the user's instruction to complete the task.

**What `--repeat` reports:** a `passes` line with every measured pass's time, plus the mean with a 95% confidence interval. No median and no best. The "median" column is computed by me from the printed per-pass times, and the printed means agree with them. For recursion, the third pass time is printed on its own line, because trace output interleaves. `--tracing` is on in every run and only the last pass is traced.

Every row's command is `/usr/bin/time -l target/release/leanvm <params>` run from the workspace, with a 30 s pause before it. The last row, `diag`, is an extra diagnostic and not part of the task's sweep.

### AC-power runs (`results/T00/summary.csv`)

| workload | params | cycles | committed log2 words | proof KiB | prove s (each repeat) | median s | printed mean ± 95% CI | leanVM peak GiB | OS max RSS GiB | OS peak footprint GiB | swap Δ MiB | wall s | verify ms | flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fibonacci | `--n 200000 --log-inv-rate 1 --repeat 3` | 204,016 | 22.271 | 260.7 | 0.195 0.154 0.158 | 0.158 | 0.169 s ± 30.2% | 0.306 | 0.31 | 0.31 | -16 | 6.77 | 8.432 | AC |
| aggregate | `--xmss 50 --log-inv-rate 2 --repeat 3` | 58,630 | 22.262 | 195.8 | 0.29 0.279 0.282 | 0.282 | 0.284 s ± 4.5% | 0.65 | 0.65 | 0.67 | 0 | 8.41 | 9.88 | AC |
| aggregate | `--xmss 100 --log-inv-rate 2 --repeat 3` | 99,063 | 23.145 | 211.2 | 0.519 0.491 0.495 | 0.495 | 0.502 s ± 6.8% | 0.947 | 0.95 | 1.18 | 0 | 9.27 | 10.194 | AC |
| aggregate | `--xmss 250 --log-inv-rate 2 --repeat 3` | 219,994 | 24.103 | 220.0 | 1.248 0.989 1.026 | 1.026 | 1.088 s ± 28.6% | 1.632 | 1.63 | 2.03 | 83 | 11.90 | 10.351 | AC |
| aggregate | `--xmss 500 --log-inv-rate 2 --repeat 3` | 421,410 | 25.082 | 228.2 | 2.936 2.58 2.843 | 2.843 | 2.786 s ± 14.7% | 2.671 | 2.67 | 3.94 | 1497 | 19.03 | 20.046 | AC; memory-pressured |
| aggregate | `--xmss 1000 --log-inv-rate 2 --repeat 3` | 824,204 | 26.05 | 238.2 | 48.817 45.371 37.258 | 45.371 | 43.815 s ± 30.1% | 3.095 | 3.09 | 7.34 | 3324 | 153.24 | 252.791 | AC; memory-pressured |
| aggregate | `--xmss 1500 --log-inv-rate 2 --repeat 3` | 1,227,023 | 26.993 | 265.1 | 98.906 94.444 82.964 | 94.444 | 92.104 s ± 19.9% | 2.524 | 2.52 | 9.54 | 4942 | 325.55 | 47.833 | AC; memory-pressured |
| recursion | `--n 2 --xmss-per-leaf 50 --leaf-log-inv-rate 2 --log-inv-rate 1 --repeat 3` | 353,221 | 23.745 | 314.9 | 0.396 0.397 0.416 | 0.397 | 0.403 s ± 6.2% | 1.056 | 1.06 | 1.05 | -80 | 10.36 | 14.07 | AC |
| recursion | `--n 2 --xmss-per-leaf 100 --leaf-log-inv-rate 2 --log-inv-rate 1 --repeat 3` | 378,004 | 23.842 | 322.0 | 0.424 0.425 0.419 | 0.424 | 0.423 s ± 1.7% | 1.151 | 1.20 | 1.15 | -24 | 10.78 | 14.186 | AC |
| recursion | `--n 2 --xmss-per-leaf 250 --leaf-log-inv-rate 2 --log-inv-rate 1 --repeat 3` | 392,988 | 23.842 | 321.4 | 0.426 0.422 0.428 | 0.426 | 0.425 s ± 1.5% | 1.121 | 1.90 | 1.15 | -16 | 12.00 | 14.309 | AC |
| recursion | `--n 2 --xmss-per-leaf 500 --leaf-log-inv-rate 2 --log-inv-rate 1 --repeat 3` | 411,709 | 23.842 | 322.1 | 0.424 0.416 0.418 | 0.418 | 0.419 s ± 2.2% | 1.103 | 2.33 | 1.14 | 401 | 16.02 | 14.88 | AC; memory-pressured |
| recursion | `--n 2 --xmss-per-leaf 900 --leaf-log-inv-rate 2 --log-inv-rate 1 --repeat 3` | 438,675 | 23.842 | 322.1 | 0.445 0.435 0.427 | 0.435 | 0.436 s ± 4.6% | 1.104 | 3.01 | 1.15 | 274 | 63.61 | 19.274 | AC; memory-pressured |
| diag | `--n 2 --xmss-per-leaf 900 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 3` | 438,675 | 23.842 | 232.4 | 0.607 0.583 0.595 | 0.595 | 0.595 s ± 4.5% | 1.396 | 2.34 | 1.43 | 1903 | 58.58 | 22.878 | AC; memory-pressured |

### Per-opcode lines

| run | per-opcode line |
|---|---|
| fibonacci_n200000_lir1 | MUL 2^17.623 (98.9%)  SET 2^9.972 (0.5%)  DEREF 2^9.66 (0.4%)  JUMP 2^7.665 (0.1%)  XOR 2^7.644 (0.1%)  MEMORY 2^17.637  BYTECODE 2^10.017  TOTAL_COMMITTED 2^22.271 |
| aggregate_xmss50_lir2 | SET 2^14.459 (38.4%)  XOR 2^13.213 (16.2%)  KECCAK 2^13.188 (15.9%)  MUL 2^13.086 (14.8%)  DEREF 2^12.658 (11.0%)  JUMP 2^11.047 (3.6%)  MEMORY 2^18.321  BYTECODE 2^18.899  TOTAL_COMMITTED 2^22.262 |
| aggregate_xmss100_lir2 | SET 2^14.772 (28.2%)  XOR 2^14.202 (19.0%)  KECCAK 2^14.187 (18.8%)  MUL 2^14.071 (17.4%)  DEREF 2^13.574 (12.3%)  JUMP 2^12.025 (4.2%)  MEMORY 2^19.28  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.145 |
| aggregate_xmss250_lir2 | XOR 2^15.518 (21.3%)  KECCAK 2^15.509 (21.2%)  SET 2^15.435 (20.1%)  MUL 2^15.379 (19.4%)  DEREF 2^14.833 (13.3%)  JUMP 2^13.333 (4.7%)  MEMORY 2^20.576  BYTECODE 2^18.899  TOTAL_COMMITTED 2^24.103 |
| aggregate_xmss500_lir2 | XOR 2^16.516 (22.2%)  KECCAK 2^16.509 (22.1%)  MUL 2^16.374 (20.2%)  SET 2^16.126 (17.0%)  DEREF 2^15.81 (13.6%)  JUMP 2^14.328 (4.9%)  MEMORY 2^21.568  BYTECODE 2^18.899  TOTAL_COMMITTED 2^25.082 |
| aggregate_xmss1000_lir2 | XOR 2^17.515 (22.7%)  KECCAK 2^17.509 (22.6%)  MUL 2^17.371 (20.6%)  SET 2^16.942 (15.3%)  DEREF 2^16.799 (13.8%)  JUMP 2^15.326 (5.0%)  MEMORY 2^22.563  BYTECODE 2^18.899  TOTAL_COMMITTED 2^26.05 |
| aggregate_xmss1500_lir2 | XOR 2^18.099 (22.9%)  KECCAK 2^18.094 (22.8%)  MUL 2^17.955 (20.7%)  SET 2^17.46 (14.7%)  DEREF 2^17.38 (13.9%)  JUMP 2^15.91 (5.0%)  MEMORY 2^23.147  BYTECODE 2^18.899  TOTAL_COMMITTED 2^26.993 |
| recursion_n2_m50_leaflir2_lir1 | MUL 2^17.004 (37.2%)  XOR 2^16.531 (26.8%)  DEREF 2^15.878 (17.1%)  SET 2^15.103 (10.0%)  JUMP 2^14.497 (6.5%)  KECCAK 2^13.059 (2.4%)  MEMORY 2^19.224  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.745 |
| recursion_n2_m100_leaflir2_lir1 | MUL 2^17.094 (37.0%)  XOR 2^16.616 (26.6%)  DEREF 2^16.007 (17.4%)  SET 2^15.182 (9.8%)  JUMP 2^14.609 (6.6%)  KECCAK 2^13.231 (2.5%)  MEMORY 2^19.321  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842 |
| recursion_n2_m250_leaflir2_lir1 | MUL 2^17.132 (36.5%)  XOR 2^16.681 (26.7%)  DEREF 2^16.105 (17.9%)  SET 2^15.213 (9.7%)  JUMP 2^14.637 (6.5%)  KECCAK 2^13.347 (2.7%)  MEMORY 2^19.379  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842 |
| recursion_n2_m500_leaflir2_lir1 | MUL 2^17.178 (36.0%)  XOR 2^16.764 (27.0%)  DEREF 2^16.221 (18.6%)  SET 2^15.232 (9.3%)  JUMP 2^14.658 (6.3%)  KECCAK 2^13.477 (2.8%)  MEMORY 2^19.45  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842 |
| recursion_n2_m900_leaflir2_lir1 | MUL 2^17.234 (35.1%)  XOR 2^16.874 (27.4%)  DEREF 2^16.394 (19.6%)  SET 2^15.264 (9.0%)  JUMP 2^14.68 (6.0%)  KECCAK 2^13.628 (2.9%)  MEMORY 2^19.545  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842 |
| diag_recursion_n2_m900_leaflir2_lir2 | MUL 2^17.234 (35.1%)  XOR 2^16.874 (27.4%)  DEREF 2^16.394 (19.6%)  SET 2^15.264 (9.0%)  JUMP 2^14.68 (6.0%)  KECCAK 2^13.628 (2.9%)  MEMORY 2^19.545  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842 |

### Skipped sizes

None in the AC run. Every size in the task's lists ran, and each predicted peak stayed under 8 GiB. Skip rule: predicted peak = last peak x (next size / last size), compared against BUDGET. In the earlier battery run (BUDGET 4.8 GiB, original swap rule) the sweeps stopped after aggregate N=50 and recursion M=500, and I ran aggregate 100, 250 and 500 as a flagged deviation. Those logs and their `summary.csv` are in `results/T00/battery_run/` and are superseded.

### Reference-number comparison (step 9)

| quantity | README reference (M4 Max) | this run | verdict |
|---|---|---|---|
| aggregate 1500, rate 1/4: cycles | 1,227,023 | 1,227,023 | match |
| TOTAL_COMMITTED | 2^26.99 | 2^26.993 | match |
| proof size | 265.1 KiB | 265.1 KiB | match |
| proving time | 1.554 s | 94.4 s median (mean 92.1 s, passes 98.9, 94.4, 83.0) | not comparable: this machine pages (swap +4,942 MiB, 91.9 s system time) |
| peak memory | 9.646 GiB | leanVM printed 2.524 GiB; OS max RSS 2.52 GiB; **OS peak footprint 9.54 GiB** | footprint is consistent with the reference. The printed peak understates under paging |
| verify | 7 to 9 ms | 47.8 ms | slowed by paging; N<=250 runs show 9.9 to 10.4 ms |
| recursion 2-to-1, leaves of 900: cycles | 542,049 | **438,675** | **MISMATCH** |
| recursion proof size | 216.9 KiB | **322.1 KiB** (outer log-inv-rate 1); 232.4 KiB with outer log-inv-rate 2 (diag run) | **MISMATCH** |
| recursion TOTAL_COMMITTED | 2^24.02 | 2^23.842 | **MISMATCH** |
| recursion proving time | 0.309 s | 0.435 s median | different machine, not a protocol claim |
| recursion peak memory | 2.315 GiB | leanVM printed 1.104 GiB; footprint 1.15 GiB | differs, with the cycle mismatch |

- The recursion cycle count does not depend on the outer rate (the diag run gives 438,675 again), so the outer log-inv-rate does not explain the cycle mismatch. It moves the proof size toward the reference (322.1 to 232.4 KiB) but does not reach 216.9.
- The README's recursion block is internally inconsistent: its command says `--xmss-per-leaf 1500`, while its sample output says leaves of 900 and has no "proven at log-inv-rate 2" in the header, which my binary prints. **Hypothesis, not verified:** the README's recursion numbers predate the code at commit df7d122. I did not test other commits (the task forbids source changes, and I did not check out other commits). The 0.21 s headline figure was not checked.

### Per-stage timing and other findings

- **CLI flag mapping (assumed to real):** none needed. All flags exist as written: `aggregate --xmss --log-inv-rate --repeat`; `recursion --n --xmss-per-leaf --leaf-log-inv-rate --log-inv-rate --repeat`; `fibonacci --n --log-inv-rate --repeat`. Extra flags: `--tracing`, `--cooldown` (idle seconds before each measured pass, default 2, left at default). `hash` exists too (`--log-n`).
- **Build:** `cargo +1.99.0 build --release -p leanvm-cli`, no extra features, wall time 57.6 s (`build.log`). `.cargo/config.toml` already sets `rustflags = ["-C", "target-cpu=native"]`, kept. There is no `rust-toolchain` file. The default 1.88.0 fails at `crates/primitives/src/bit_fold.rs:93` (`isolate_lowest_one`, E0599); 1.96.1 fails with E0658 (rust-lang issue 136909, still feature-gated). 1.99.0 was already installed through rustup, and nothing was installed. CI uses `dtolnay/rust-toolchain@stable`.
- **Per-stage timing options found (step 6):** `--tracing` prints a hierarchical timing tree via `tracing-forest` (`bins/leanvm/src/main.rs:23-25`, init at `main.rs:114-115`, `crates/bench/src/trace.rs:108-115`). `RUST_LOG` adjusts verbosity. Only the last measured pass is traced (`bins/leanvm/src/benchmark.rs:95,107,191-195`; `fibonacci.rs:24-28`; `crates/bench/src/trace.rs:77-99`). Peak memory is printed by `crate::report::peak_gib()` (`benchmark.rs:58`, `fibonacci.rs:43`), implemented over `peak_rss_bytes` (`crates/bench/src/lib.rs:235`), which is RSS-based. Recursion prints no separate leaf-proving time; only the trace tree (for example "Replay children") and "generated N leanXMSS in X s" (signer generation, cached to disk) appear. The recursion log's cycle line is the recursion node only.
- **Power and throttling:** AC power, charging, throughout. No rising pass times in any run. Passes fall across repeats in the paging-bound runs (N=1000: 48.8, 45.4, 37.3 s; N=1500: 98.9, 94.4, 83.0 s), which looks like warmup or swap settling and not throttling. The small runs are flat (recursion M=250: 0.426, 0.422, 0.428 s).
- **macOS caveat:** on Apple silicon leanVM stores its whole codeword (`REBUILD_OVER_STORE` is false), so memory here is higher than on Linux. That is why N=1000 (OS footprint 7.34 GiB) and N=1500 (9.54 GiB) exceed what this 8 GiB machine can hold in RAM.
- **Memory-measure caveat for the budget rule:** I applied the prediction rule on OS max RSS. Under paging, max RSS falls (N=1000: 3.09 GiB; N=1500: 2.52 GiB) and does not track the true footprint, so the rule would have under-predicted. The AC sweep ran anyway under the user's 8 GiB budget.
- **Swap deltas** are noisy: macOS resizes the swap total during the run (4096 to 9216 MiB seen), and other applications were open. Treat the flag as indicative only.

## Commands run

```
cd ~/Desktop/accum-research && mkdir -p upstream proto lean results/T00
sysctl -n machdep.cpu.brand_string; sysctl hw.ncpu hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu hw.memsize
sw_vers; uname -a; pmset -g batt; sysctl vm.swapusage; rustc -Vv; cargo -V; rustup show; lean --version; lake --version   # -> machine.txt
git clone https://github.com/leanEthereum/leanMultisig upstream/leanMultisig
git -C upstream/leanMultisig checkout df7d122abbe25cf12e5c8ae992ce6d3505f75372 && git checkout -b research/baseline
cargo build --release -p leanvm-cli              # rustc 1.88.0: failed
cargo +1.96.1 build --release -p leanvm-cli      # failed
cargo +1.99.0 build --release -p leanvm-cli      # ok, 57.6 s
target/release/leanvm --help; target/release/leanvm <aggregate|recursion|fibonacci|hash> --help   # -> cli_help.txt
# battery run (superseded, results/T00/battery_run/): fibonacci, aggregate 50, recursion 50..500, aggregate 100/250/500
# AC run (30 s sleep before each; each under /usr/bin/time -l, all with --tracing):
leanvm fibonacci --n 200000 --log-inv-rate 1 --repeat 3
leanvm aggregate --xmss N --log-inv-rate 2 --repeat 3                       # N = 50 100 250 500 1000 1500
leanvm recursion --n 2 --xmss-per-leaf M --leaf-log-inv-rate 2 --log-inv-rate 1 --repeat 3   # M = 50 100 250 500 900
leanvm recursion --n 2 --xmss-per-leaf 900 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 3   # diagnostic only
git -C upstream/leanMultisig status --porcelain      # empty
```

Driver scripts: `run.sh`, `sweep_ac.py` in the session scratchpad (`/private/tmp/claude-501/-Users-<USER>-Desktop-accum-research/343ace69-c62e-4dfe-bd40-c1cc2876adfc/scratchpad/`). The parser is `/tmp/parse.py`.

## Raw output

Complete logs, one per run, are in `results/T00/*.log`. Each holds the command, date, swap before and after, power line, trace tree, results block and `time -l` output. Key blocks:

```
aggregate --xmss 1500 --log-inv-rate 2 --repeat 3   (AC power)
  cycles (VM steps)           : 1,227,023 = 2^20.227
    details                   : XOR 2^18.099 (22.9%)  KECCAK 2^18.094 (22.8%)  MUL 2^17.955 (20.7%)  SET 2^17.46 (14.7%)  DEREF 2^17.38 (13.9%)  JUMP 2^15.91 (5.0%)  MEMORY 2^23.147  BYTECODE 2^18.899  TOTAL_COMMITTED 2^26.993
  proof size                  : 265.1 KiB
  proving time                : 92.104 s ± 19.9%      peak memory 2.524 GiB
  verifying                   : 47.833 ms
      325.55 real       261.60 user        91.90 sys
          10248560368  peak memory footprint

recursion 2→1, over leaves of 900 leanXMSS signatures, proven at log-inv-rate 2
  cycles (VM steps)           : 438,675 = 2^18.743
    details                   : MUL 2^17.234 (35.1%)  XOR 2^16.874 (27.4%)  DEREF 2^16.394 (19.6%)  SET 2^15.264 (9.0%)  JUMP 2^14.68 (6.0%)  KECCAK 2^13.628 (2.9%)  MEMORY 2^19.545  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842
  proof size                  : 322.1 KiB
  proving time                : 0.436 s ± 4.6%      peak memory 1.104 GiB
  verifying                   : 19.274 ms
```

## Files changed or created

- `results/T00/machine.txt`: machine, power and swap record, toolchain, BUDGET (battery and AC notes).
- `results/T00/cli_help.txt`: `--help` for the binary and each subcommand.
- `results/T00/summary.csv`: one row per AC run, with extra columns for OS peak footprint, wall time and printed mean.
- `results/T00/*.log`: raw AC-run logs; `build.log`, `head_default.txt`.
- `results/T00/battery_run/`: logs, `summary.csv` and `skipped.txt` from the earlier battery run (kept, not deleted).
- `results/T00/T00_report.md`: this report.
- `NOTES.md`: new, dated T00 entry.
- `upstream/leanMultisig/`: clone, local branch `research/baseline`; `target/` is untracked and ignored.

## Problems and deviations

- **Toolchain:** the repo needs a newer rustc than the default 1.88. Built with the already-installed 1.99.0 for this task only.
- **Budget and stop rule:** the AC run used BUDGET = 8 GiB at the user's instruction, not the task's 60% rule, and did not stop on swap growth. The swap flag is indicative only.
- **Tracing in every run** may slightly skew the last pass. In the small runs the last pass was no slower than the others.
- **Paging distorts N >= 500 timings** (see the reference table). They show this machine's limits, not leanVM's cost.
- **Recursion mismatch** against the README is unexplained (see above).
- **Fibonacci** was run at the task's n=200000, not the README's 2,000,000.
- **Parsing:** the third recursion pass time comes from the separate line in the log, and the diag row's third pass was patched in by hand (0.595 s, matching the printed mean).

## Suggested next step

For the research comparison use the N <= 250 aggregate and M <= 900 recursion numbers from this machine. Get N=1000/1500 timings from a Linux box with at least 16 GiB, since this machine pages from N=500 upward. Separately, check whether a newer commit than df7d122 reproduces the README's recursion figure (542,049 cycles), before anyone quotes recursion cost against it.

=== END REPORT ===

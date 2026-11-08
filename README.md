# leanVM accumulation study: reproducibility bundle

License: MIT OR Apache-2.0 (`LICENSE-MIT`, `LICENSE-APACHE`), for this repository's own files. The upstream-derived diffs are covered by `NOTICE-leanVM`.

Write-up: ethresear.ch post (link to be added)

## What the study is

A comparison of hash-based accumulation (WARP / Arc style folding) against leanVM's
recursion for post-quantum signature aggregation. This bundle covers the leanVM side:
cost breakdowns of leanVM's recursion (`recursion` and `aggregate` subcommands of
`leanvm-cli`), where proving time and trace size go, and what "what-if" guest-program
variants would save. Task IDs T00 to T07d are the study's work units; each has a report
in `results/<task>/`.

## WARNING: UNSOUND variants

The `d3-*` variants (branches `d3-v1` to `d3-v6u`, diffs `diffs/d3-v*.diff`) are **UNSOUND and for cost
measurement only**. They skip or emulate verification work (Merkle hashing, WHIR proximity checks, ...) to
measure what that work costs. They are not secure verifiers and must never be used as one.
The SOUND diffs are `dbg-tables` (env-gated table-size print), `b0u` (loop unrolling) and
`rebuild-over-store` (flips the `REBUILD_OVER_STORE` constant).

## Pinned commits

- leanMultisig: https://github.com/leanEthereum/leanMultisig, base `df7d122abbe25cf12e5c8ae992ce6d3505f75372`.
- Diffs are `git diff df7d122 <branch>`:

| diff | source branch @ commit | sound? |
|---|---|---|
| diffs/dbg-tables.diff | research/dbg-tables @ f060baa0d | yes |
| diffs/b0u.diff | research/b0u @ 0490e826d | yes |
| diffs/rebuild-over-store.diff | research/rebuild-over-store @ cee5d1c7a | yes |
| diffs/d3-v1.diff | research/d3-v1 @ 4fb9e000f | UNSOUND |
| diffs/d3-v2.diff | research/d3-v2 @ 4760693a8 | UNSOUND |
| diffs/d3-v3.diff | research/d3-v3 @ b117ddd77 | UNSOUND |
| diffs/d3-v4.diff | research/d3-v4 @ 3feeae43e | UNSOUND |
| diffs/d3-v5.diff | research/d3-v5 @ 2f78ff13c | UNSOUND |
| diffs/d3-v6.diff | research/d3-v6 @ 5da84ce0e | UNSOUND |
| diffs/d3-v6u.diff | research/d3-v6u @ 3518e28c4 | UNSOUND |

Each applies cleanly (`git apply --check`) to df7d122. `d3-v6` and `d3-v6u` also contain the
`dbg-tables` change (the `DBG_TABLES` print); `b0u` does too.
- compsec-epfl/warp, pinned `655e7d5`: **not included** (it has no licence). Any WARP
  measurement (T02) needs that repository at 655e7d5, cloned separately; the harness that
  drove it is not part of this bundle.

## Machine and toolchain

Apple M2 (4 performance + 4 efficiency cores), 8 GiB RAM, macOS 26.5.2 (Darwin 25.5.0),
`rustc 1.99.0 (b940084d7 2026-09-28)`, built with `cargo +1.99.0`. leanMultisig pins
`-C target-cpu=native` in its `.cargo/config.toml`. All runs shared the machine with about
1.5 to 1.8 GiB of swap in use (T07c/T07d), so timings carry paging noise; cycle counts,
table sizes and proof sizes do not depend on it. On Apple silicon leanVM stores its whole
codeword (`REBUILD_OVER_STORE` false), so memory differs from Linux. Details: `results/T00/machine.txt`.

## Building a variant

```
git clone https://github.com/leanEthereum/leanMultisig upstream/leanMultisig && cd upstream/leanMultisig
git checkout -b my-variant df7d122abbe25cf12e5c8ae992ce6d3505f75372
git apply ../../diffs/<variant>.diff
cargo +1.99.0 build --release -p leanvm-cli      # binary: target/release/leanvm
```

Use a separate `CARGO_TARGET_DIR` per variant if you want several binaries side by side
(the study used `target-dbg` for dbg-tables, `target-d3v6` for d3-v6, and so on).
In T07c/T07d, "baseline" is the **dbg-tables** build and "V6" is the **d3-v6** build.

## Layout

- `diffs/`: the ten diffs above. `NOTICE-leanVM`: upstream licence texts.
- `scripts/T*/`: our analysis and driver scripts. They resolve every path from the repository
  root and can be run from any directory. Drivers expect leanMultisig at `upstream/leanMultisig`
  inside this repository (the same place the `proto/` crates look). The reports were written when
  the scripts lived in `results/<task>/scripts/`; those are now `scripts/<task>/`. Paths in raw
  log headers are as recorded at run time.
- `proto/guest-lines`, `proto/whir-params`: small standalone Rust diagnostics using only the public API of
  leanMultisig by path (`../../upstream/leanMultisig`); their `Cargo.lock` files seed from upstream's.
- `results/T00` to `T07d`: reports, parsed tables (CSV/MD/JSON), diffs as run. Raw logs are
  included only for T07, T07b (`partA`, `sweep`), T07c and T07d.
- Not included: profiler dumps, disassemblies, line tables, build outputs and binaries, raw logs for
  T00 to T06, `proto/warp-bench`, `results/T02/repo_facts.md`, `.jsonl` sweeps from T02.

## Commands behind the T07c tables

All runs: from `upstream/leanMultisig`, 30 s sleep before each, wrapped in `/usr/bin/time -l`.
B = dbg-tables binary, V = d3-v6 binary. Logs: `results/T07c/runs/<name>_p<pass>.log`;
the first `### cmd:` line of each log holds the exact command.

```
python3 scripts/T07c/run_timing.py 1 leaf_250 leaf_300 base_n4 v6_n4 base_n5 v6_n5 base_n6 v6_n6 base_n5_300
python3 scripts/T07c/run_timing.py 1 v6_n5_300
python3 scripts/T07c/run_timing.py 2 v6_n5_300 base_n5_300 v6_n6 base_n6 v6_n5 base_n5 v6_n4 base_n4 leaf_300 leaf_250
python3 -I scripts/T07c/parse.py          # writes per_run.md, pooled.md (pooled median table), parsed.json
```

Underlying commands: `B aggregate --xmss {250|300} --log-inv-rate 2 --repeat 3` and
`DBG_TABLES=1 {B|V} recursion --n N --xmss-per-leaf {250|300} --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 3 --tracing`
for (config: n) = base_n4/v6_n4: 4; base_n5/v6_n5: 5; base_n6/v6_n6: 6 (250 per leaf);
base_n5_300/v6_n5_300: 5 (300 per leaf). Tables: `results/T07c/pooled.md` (pooled medians over
6 repeats = 2 passes x 3), `per_run.md`.

## Commands behind the T07d tables

Stage table (Part A; reads the T07c logs only; 2 traced proves per configuration):
```
python3 -I scripts/T07d/stages.py                  # -> results/T07d/stages.json
cd results/T07d && python3 -I ../../scripts/T07d/table.py > stage_table.md
```
Aggregate counts (Part B), N = 350, 400, 375 in that order:
```
DBG_TABLES=1 /usr/bin/time -l <B> aggregate --xmss N --log-inv-rate 2 --repeat 1
```
Recursion counts at N* = 350 (base n = 5, 6 with B; V6 n = 6, 7 with V):
```
DBG_TABLES=1 /usr/bin/time -l <bin> recursion --n n --xmss-per-leaf 350 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 1 --tracing
cd results/T07d && python3 -I ../../scripts/T07d/rec.py        # per-table row/tau extraction
```
Logs: `results/T07d/runs/`. Narrative and numbers: `results/T07d/REPORT.md`, `stage_table.md`.
Verification has no explicit "OK" line; success was taken as a printed `verifying` time plus exit 0.

## Earlier tasks (T00 to T07b)

Each `results/<task>/<task>_report.md` lists its own commands; drivers are in `scripts/<task>/`.
Machine state (swap, thermal) was logged before and after sweeps from T07 on.

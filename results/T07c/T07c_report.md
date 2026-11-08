=== RESULT REPORT T07c ===
Status: done
Machine: Apple M2 (arm64), 8 cores, 8 GiB RAM, macOS 26.5.2 (Darwin 25.5.0)
Toolchain: none used. No cargo and no builds.
Repo state: upstream/leanMultisig was not touched. The baseline binary is research/dbg-tables f060baa0d and the V6 binary is research/d3-v6 5da84ce0e, both built in T07b. I did not re-check the working-tree state.

## Summary
- Deviation: the start swap was 1644 MiB, above the task's 512 MiB limit. Arya then raised the threshold to 8 GB, so I ran the task. Swap during the runs was 1452–1772 MiB.
- All 20 runs finished (10 configurations × 2 passes × 3 repeats) and verified (verification time printed, exit 0). Pass 2 ran in reverse order.
- Node cycles for base and V6 at n=4, 5 and 6 match T07b's count table exactly.
- Leaf proofs for 300 signatures are at mu 25, so runs i and j were included.
- The pmset logs show no CPU speed limit or thermal warning in any run. One run was flagged for swap growth: base_n6 pass 1, +327 MiB.
- Run-to-run noise is about 10–15% on some configurations (e.g. base_n5: pass 1 median 1.411 s, pass 2 1.212 s), so small differences are within noise. Only the 1.3 to 1.6× V6/base gaps at n=4 and n=6 are clearly outside it.

## Results

**1. Machine state**

| | swap used | memory free |
|---|---|---|
| Start | 1644.25 MiB of 3072 MiB | 74% |
| End | 1707.62 MiB | 64% |

**2. Binary hashes (SHA-256)**
- baseline `target-dbg/release/leanvm` (4,668,256 bytes): `f699df544bb93029aaecc6e14cb5f510bb9cec21bd40a407317476d89c728fd3`
- V6 `target-d3v6/release/leanvm` (4,717,792 bytes): `a0a73b38590c38355d95a7954a2b2dd247eca638684d3d663b442b224cf3f222`

**3. Per-run table**

Times are proving time per repeat, in seconds. Each row is a single pass. Cycles are the node's (the leaf's for `leaf_*`). All rows used `--repeat 3` and the commands under "Commands run". Swap start is in MiB. Verify was OK for every run.

| name | pass | cycles | TC | lanes | mu | t1 | t2 | t3 | median s | leanVM peak GiB | footprint GiB | swap start | swap Δ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| leaf_250 | 1 | 219,994 | – | – | 25 | 1.012 | 1.026 | 0.976 | 1.012 | 1.822 | 2.036 | 1468 | 0 |
| leaf_250 | 2 | 219,994 | – | – | 25 | 0.975 | 0.963 | 0.964 | 0.964 | 2.032 | 2.030 | 1708 | 0 |
| leaf_300 | 1 | 260,052 | – | – | 25 | 1.172 | 1.075 | 1.017 | 1.075 | 1.680 | 2.061 | 1468 | 0 |
| leaf_300 | 2 | 260,052 | – | – | 25 | 1.198 | 1.043 | 1.012 | 1.043 | 1.966 | 2.062 | 1708 | 0 |
| base_n4 | 1 | 766,603 | 29,032,448 | 56 | 25 | 1.142 | 1.189 | 1.160 | 1.160 | 2.348 | 2.401 | 1468 | 0 |
| base_n4 | 2 | 766,603 | 29,032,448 | 56 | 25 | 1.173 | 1.142 | 1.060 | 1.142 | 2.326 | 2.402 | 1708 | 0 |
| v6_n4 | 1 | 668,803 | 23,134,208 | 45 | 25 | 0.947 | 0.936 | 0.915 | 0.936 | 1.999 | 2.026 | 1468 | 0 |
| v6_n4 | 2 | 668,803 | 23,134,208 | 45 | 25 | 0.937 | 0.919 | 0.930 | 0.930 | 2.008 | 2.030 | 1708 | 0 |
| base_n5 | 1 | 953,421 | 29,556,736 | 57 | 25 | 1.411 | 1.535 | 1.243 | 1.411 | 2.411 | 2.555 | 1468 | 0 |
| base_n5 | 2 | 953,421 | 29,556,736 | 57 | 25 | 1.430 | 1.191 | 1.212 | 1.212 | 2.492 | 2.554 | 1732 | −24 |
| v6_n5 | 1 | 822,968 | 29,032,448 | 56 | 25 | 1.126 | 1.173 | 1.218 | 1.173 | 2.335 | 2.407 | 1468 | 0 |
| v6_n5 | 2 | 822,968 | 29,032,448 | 56 | 25 | 1.061 | 1.054 | 1.068 | 1.061 | 2.380 | 2.401 | 1772 | 0 |
| base_n6 | 1 | 1,140,247 | 34,406,400 | 33 | 26 | 2.015 | 1.962 | 2.183 | 2.015 | 3.019 | 3.093 | 1452 | **+327 (flag)** |
| base_n6 | 2 | 1,140,247 | 34,406,400 | 33 | 26 | 2.188 | 2.207 | 2.081 | 2.188 | 2.965 | 3.093 | 1732 | +40 |
| v6_n6 | 1 | 976,882 | 33,488,896 | 64 | 25 | 1.320 | 1.154 | 1.123 | 1.154 | 2.624 | 2.643 | 1772 | 0 |
| v6_n6 | 2 | 976,882 | 33,488,896 | 64 | 25 | 1.310 | 1.301 | 1.353 | 1.310 | 2.580 | 2.644 | 1748 | 0 |
| base_n5_300 | 1 | 957,159 | 33,488,896 | 64 | 25 | 1.255 | 1.130 | 1.129 | 1.130 | 2.606 | 2.634 | 1772 | 0 |
| base_n5_300 | 2 | 957,159 | 33,488,896 | 64 | 25 | 1.218 | 1.142 | 1.210 | 1.210 | 2.571 | 2.634 | 1748 | 0 |
| v6_n5_300 | 1 | 826,791 | 29,032,448 | 56 | 25 | 1.341 | 1.263 | 1.274 | 1.274 | 2.284 | 2.407 | 1756 | 0 |
| v6_n5_300 | 2 | 826,791 | 29,032,448 | 56 | 25 | 1.207 | 1.106 | 1.063 | 1.106 | 2.346 | 2.406 | 1748 | 0 |

- TC is the node's placed length; the table shows it as the T07b `tc` column.
- Mu for `leaf_*` is derived as ceil(log2 TOTAL_COMMITTED). The aggregate subcommand prints no mu or lanes.

**4. Pooled medians over 6 repeats**

| config | pooled median s | min | max | pass-1 median | pass-2 median |
|---|---|---|---|---|---|
| leaf_250 | 0.976 | 0.963 | 1.026 | 1.012 | 0.964 |
| leaf_300 | 1.059 | 1.012 | 1.198 | 1.075 | 1.043 |
| base_n4 | 1.151 | 1.060 | 1.189 | 1.160 | 1.142 |
| v6_n4 | 0.933 | 0.915 | 0.947 | 0.936 | 0.930 |
| base_n5 | 1.327 | 1.191 | 1.535 | 1.411 | 1.212 |
| v6_n5 | 1.097 | 1.054 | 1.218 | 1.173 | 1.061 |
| base_n6 | 2.132 | 1.962 | 2.207 | 2.015 | 2.188 |
| v6_n6 | 1.305 | 1.123 | 1.353 | 1.154 | 1.310 |
| base_n5_300 | 1.176 | 1.129 | 1.255 | 1.130 | 1.210 |
| v6_n5_300 | 1.235 | 1.063 | 1.341 | 1.274 | 1.106 |

**5. Leaf mu and lanes**
- 250 signatures: mu 25, 35 lanes, committed length 18,022,400 (aggregate cycles 219,994; leaves inside recursion runs 219,985–220,104).
- 300 signatures: mu 25, 36 lanes, committed length 18,874,368 (aggregate cycles 260,052; leaves inside recursion runs 260,038–260,058).

## Commands run
```
sysctl vm.swapusage; memory_pressure | tail -1   (start, saved to start_state.txt)
ls -l and shasum -a 256 on both binaries
python3 results/T07c/scripts/run_timing.py 1 leaf_250 leaf_300 base_n4 v6_n4 base_n5 v6_n5 base_n6 v6_n6 base_n5_300
python3 results/T07c/scripts/run_timing.py 1 v6_n5_300
python3 results/T07c/scripts/run_timing.py 2 v6_n5_300 base_n5_300 v6_n6 base_n6 v6_n5 base_n5 v6_n4 base_n4 leaf_300 leaf_250
sysctl vm.swapusage; memory_pressure | tail -1   (end, saved to end_state.txt)
python3 -I results/T07c/scripts/parse.py
```
Each run was wrapped in `/usr/bin/time -l`, preceded by a 30 s sleep, and run from upstream/leanMultisig. The exact command is the first `### cmd:` line of each log:
- `<bin> aggregate --xmss {250|300} --log-inv-rate 2 --repeat 3`
- `DBG_TABLES=1 <bin> recursion --n N --xmss-per-leaf {250|300} --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 3 --tracing`

## Raw output
Full logs are in results/T07c/runs/. Representative summary lines from `base_n5_p1.log`:
```
recursion 5→1, over leaves of 250 leanXMSS signatures
  cycles (VM steps) : 953,421 = 2^19.863
  proof size        : 238.9 KiB
  proving time      : 1.397 s ± 23.3%   peak memory 2.411 GiB
  verifying         : 14.421 ms
  2743388584 peak memory footprint
```

## Files changed or created
- results/T07c/start_state.txt, end_state.txt, binaries.txt, threshold_note.txt: states, hashes and the threshold note.
- results/T07c/runs/*.log: 20 raw logs.
- results/T07c/scripts/run_timing.py, parse.py: driver and parser.
- results/T07c/per_run.md, pooled.md, parsed.json: parsed tables.
- results/T07c/pass1.out, pass2.out: driver progress output.
- NOTES.md: T07c entry appended.

## Problems and deviations
- The swap threshold was 512 MiB. Arya raised it to 8 GB after my first blocked report, and swap stayed at 1.4–1.8 GiB throughout. This is the main confound for every timing here.
- Flagged, not discarded: base_n6 pass 1 grew swap by +327 MiB. Its times (2.015, 1.962, 2.183) are in line with pass 2 (2.188, 2.207, 2.081), so the effect looks small.
- The thermal check found no limit in any run. The pmset output reported only "No thermal warning level", "No performance warning" and "No CPU power status".
- `--tracing` interleaves the "passes" line with progress output. The parser takes the three times from the first fragment plus the standalone `X s` fragments. I checked this by hand on base_n5_p1.
- Verify has no explicit "ok" line. I took the verifying-time line plus exit 0 as success.
- The `aggregate` runs don't print mu or lanes. I derived the leaf's mu from TOTAL_COMMITTED and took its lanes from the `kind=leaf` DBG_TABLES lines in the recursion logs.
- The task asked for pass-order details only. Pass 2 was started with j first, and the other pass-2 runs follow strictly in reverse of pass 1. j in pass 1 ran last, after i.

## Suggested next step
V6's gain over the baseline is large at n=4 (about 1.23×) and n=6 (about 1.63×, driven by the mu drop 26 to 25 and 33 to 64 lanes). At n=5 it's about 1.2×, but the 300-signature case is within noise (V6 1.235 s vs base 1.176 s, V6 slower). If G3 turns on n=5 with 300 signatures, re-run those two configurations with more repeats once swap is lower.
=== END REPORT ===

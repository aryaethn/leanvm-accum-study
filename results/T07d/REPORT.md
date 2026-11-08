=== RESULT REPORT T07d ===
Status: done (Part A has one deviation: 2 traced proves per configuration, not 6)
Machine: Apple M2, 8 cores, 8 GiB RAM, macOS 26.5.2 (Darwin 25.5.0)
Toolchain: none used. No cargo or rustc was run, and no repository was built or modified.
Repo state: upstream/leanMultisig was not touched. Binaries used, identified by sha256 prefix:
- baseline `target-dbg/release/leanvm`: `f699df544bb9…` (research/dbg-tables f060baa0d)
- V6 `target-d3v6/release/leanvm`: `a0a73b38590c…` (research/d3-v6 5da84ce0e; UNSOUND, measurement only)

## Summary
- Each T07c log holds one traced Prove tree, not three, so each configuration has 2 traced proves. "Median" below is the median of those 2, which equals their mean.
- The mu-26 node costs +845 ms over the mu-25 node (1975 vs 1130 ms, ×1.75). Of the roughly 845 ms by which the stage differences sum:
  - WHIR levels L0 to L3 account for about 290 ms (the L0–L3 diffs, ratios 2.0 to 2.5).
  - Commit accounts for 260 ms (×1.71).
  - Bus, other than GKR, accounts for 140 ms (×3.2).
  - Execute accounts for 90 ms (×3.2).
  - Bus GKR accounts for 38 ms (×1.4).
- Keccak reduction (×1.14), table sumcheck (×1.07) and ring switch/claim batching (×0.98) stay roughly flat.
- N* = 350. A 350-signature leaf is mu 25 (TC 28,311,552, 54 lanes). Leaves of 375 and 400 signatures are mu 26. The boundary lies between 351 and 374 at the 25-step resolution I used.
- The four recursion runs at N* completed with exit 0. The leaves were mu 25, so the V6 runs went ahead.
- Swap was 1523.56M of 3072M used at the start of Part B, so I proceeded as instructed.

## Results

### 1. Span-name mapping
All spans are from the node's `Prove` tree. The leaves run in a child process and print no Prove tree, so there is nothing to separate.

| Stage | Span(s) |
|---|---|
| execute | Execute program |
| witness build | Build witness (inside Prove) |
| commit | top-level Commit (NTT "base encode" + Merkle) |
| bus GKR | Prove bus › Bus GKR |
| bus other (my addition) | Prove bus minus Bus GKR (Bus leaves, Bus decompose, Bus tables) |
| table sumcheck | Prove constraints |
| Keccak reduction | Keccak reduction |
| ring switch + claim batching | PCS open: Ring switch + Basis + the first Sumcheck (rounds 0 to 6, before the first Commit) |
| WHIR Lk | Commit (level k+1, "extension encode") + Open k + Induce k + Introduce k + the following Sumcheck |
| final/tail | Final level |
| untraced | Prove total minus the sum of its top-level children |

Mapping judgments you may want to check:
- **No L4:** only levels 1 to 4 are committed, so there are iterations L0 to L3 plus Final level. No L4 iteration exists in either mu.
- **Claim batching:** I assumed Basis and the first sumcheck are the claim-batching stage.
- **Bus split:** the task has no stage for "Bus leaves", which is large at mu 26, so I added "bus other".
- **Outside the Prove span:** these are not counted in the Prove total. The stage tables below don't include them.

| Span | Base mu 25 | Base mu 26 |
|---|---|---|
| Replay children | 18.6 to 23.8 ms | 19.7 to 27.5 ms |
| Outer Build witness | 11 ms | 38 to 89 ms |
| Batch deferred claims | about 2 ms | about 2 ms |

### 2. Stage medians (ms, median of 2 traced proves)
Command: `python3 -I results/T07d/stages.py`, then `table.py`. The table is also in `results/T07d/stage_table.md`.

| Stage | n5_300 (mu 25) | n6 (mu 26) | n6 − n5 | Ratio n6/n5 | V6 n6 (mu 25, reference) |
|---|---|---|---|---|---|
| execute | 41.1 | 130.9 | +89.8 | 3.18 | 48.5 |
| witness build | 16.9 | 24.8 | +7.8 | 1.46 | 15.1 |
| commit (encode+Merkle) | 365.5 | 625.5 | +260.0 | 1.71 | 413.5 |
| bus GKR | 94.8 | 132.5 | +37.7 | 1.40 | 95.0 |
| bus other | 63.2 | 203.5 | +140.3 | 3.22 | 69.0 |
| table sumcheck | 36.9 | 39.2 | +2.4 | 1.07 | 37.0 |
| Keccak reduction | 168.5 | 192.5 | +24.0 | 1.14 | 173.0 |
| ring switch + claim batching | 84.8 | 82.9 | −1.9 | 0.98 | 79.4 |
| WHIR L0 | 141.2 | 297.0 | +155.8 | 2.10 | 140.1 |
| WHIR L1 | 58.1 | 146.0 | +87.8 | 2.51 | 64.8 |
| WHIR L2 | 28.1 | 61.0 | +32.8 | 2.17 | 28.0 |
| WHIR L3 | 12.7 | 25.7 | +13.1 | 2.03 | 12.6 |
| final/tail | 0.2 | 0.2 | −0.1 | 0.73 | 0.1 |
| untraced | 0.6 | 0.1 | −0.5 | 0.17 | −0.6 |
| **TOTAL (Prove span)** | **1130** | **1975** | **+845** | **1.75** | 1185 |

Per-trace untraced time is within ±3 ms of zero, so the trace covers the whole Prove span. The stage differences sum to 849 ms against 845 ms for the totals; the gap comes from taking medians per stage.

### 4. Ratios against the references
The references are committed words ×1.031 and 2^mu ×2.0.

- **Stages closer to 2.0 (ratio above about 1.52):** execute (3.18), commit (1.71), bus other (3.22), and WHIR L0 to L3 (2.10, 2.51, 2.17, 2.03).
- **Stages closer to 1.031:** witness build (1.46), bus GKR (1.40), table sumcheck (1.07), Keccak reduction (1.14), ring switch/batching (0.98).
- **Execute and bus other** exceed 2 by more than their cycle growth explains. Cycles grow only ×1.19, and no raw figure here explains the excess.
- **Execute is noisy:** it is 169 ms in the first trace and 93 ms in the second, so treat it as unreliable.
- **Commit is under-pro-rated:** the base-encode NTT is 22 vs 22 log-domain, and its time ratio is 1.71, not 2.

### 3. Aggregate counts
Command: `DBG_TABLES=1 /usr/bin/time -l <baseline> aggregate --xmss N --log-inv-rate 2 --repeat 1`.
- **TC:** I used `committed_len`, which equals lanes × 2^(mu−6).
- **Prove time:** single cold repeat, informational only.

| N | cycles | TC | mu | lanes | footprint (B) | prove s |
|---|---|---|---|---|---|---|
| 350 | 300,484 | 28,311,552 | 25 | 54 | 3,290,696,488 | 2.07 |
| 375 | 320,729 | 34,603,008 | 26 | 33 | 3,971,108,032 | 2.59 |
| 400 | 340,919 | 35,651,584 | 26 | 34 | 4,029,205,768 | 2.62 |

The run order was 350, 400 (mu 26, so the sweep stopped), then 375 as the single bisection step. Peak footprint stayed at or below 4.03 GB, about 47% of RAM, under the 70% limit.

### 5. Recursion counts at N* = 350
Command: `DBG_TABLES=1 /usr/bin/time -l <bin> recursion --n n --xmss-per-leaf 350 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 1 --tracing`.

All leaves are mu 25 with 54 lanes. Prove times are informational only. Every run exited 0, and the program printed a "verifying" time. It prints no explicit OK line, so I took exit 0 as passing verification.

| Run | cycles | TC | mu | lanes | h (log_mem) | proof KiB | verify ms | prove s | footprint B |
|---|---|---|---|---|---|---|---|---|---|
| base n5 | 964,798 | 33,554,432 | 25 | 64 | 22 | 245.4 | 14.7 | 1.163 | 2,822,900,136 |
| base n6 | 1,153,742 | 34,603,008 | 26 | 33 | 22 | 227.0 | 16.0 | 1.637 | 3,322,121,024 |
| V6 n6 | 990,396 | 33,554,432 | 25 | 64 | 22 | 245.8 | 15.6 | 1.150 | 2,831,174,080 |
| V6 n7 | 1,146,455 | 42,991,616 | 26 | 41 | 22 | 232.3 | 16.3 | 2.403 | 3,691,318,344 |

Per-table rows (tau in parentheses):

| Run | XOR | MUL | SET | DEREF | JUMP | KECCAK |
|---|---|---|---|---|---|---|
| base n5 | 266,280 (19) | 359,903 (19) | 69,402 (17) | 179,205 (18) | 63,549 (16) | 26,459 (15) |
| base n6 | 319,447 (19) | 431,730 (19) | 79,840 (17) | 214,756 (18) | 76,218 (17) | 31,751 (15) |
| V6 n6 | 276,800 (19) | 372,676 (19) | 67,619 (17) | 183,775 (18) | 63,795 (16) | 25,731 (15) |
| V6 n7 | 321,414 (19) | 432,633 (19) | 75,591 (17) | 213,035 (18) | 73,976 (17) | 29,806 (15) |

Shared-column n_vars are 21 for MEM_LO, MEM_HI, MEM_TOP and MFCNT, 19 for BFCNT, and 21 for QKECCAK. The exception is V6 n7, where the first four are 22. The `h` column is `log_mem`. I took it to be what the task calls "h", but I did not confirm that.

### 5 (swap state at the start of Part B)
- `sysctl vm.swapusage`: total = 3072.00M, used = 1523.56M, free = 1548.44M (encrypted).
- `memory_pressure | tail -1`: System-wide memory free percentage: 73%.
- **Flag:** swap was already about 1.5 GB in use before any Part B run, so Part B timings may include swap effects. Counts are unaffected.

## Commands run
- Part A: `python3 -I results/T07d/stages.py`, then `python3 -I results/T07d/table.py`. They read `results/T07c/runs/*.log` only.
- Part B swap check: `sysctl vm.swapusage; memory_pressure | tail -1`.
- Part B aggregates, in order: `DBG_TABLES=1 /usr/bin/time -l upstream/leanMultisig/target-dbg/release/leanvm aggregate --xmss N --log-inv-rate 2 --repeat 1` for N = 350, 400, 375.
- Part B recursion, base: `DBG_TABLES=1 /usr/bin/time -l target-dbg/release/leanvm recursion --n {5,6} --xmss-per-leaf 350 --leaf-log-inv-rate 2 --log-inv-rate 2 --repeat 1 --tracing`.
- Part B recursion, V6: the same command with `target-d3v6/release/leanvm` and `--n {6,7}`.
- Table extraction: `python3 -I results/T07d/rec.py`.

## Raw output
Logs are in `results/T07d/runs/`. Each includes the `/usr/bin/time -l` block.

## Files changed or created
- `results/T07d/stages.py`: span-tree parser and stage mapping.
- `results/T07d/stages.json`: per-trace stage values.
- `results/T07d/table.py`: median, diff and ratio table.
- `results/T07d/stage_table.md`: the Part A stage table.
- `results/T07d/rec.py`: extractor for the recursion count tables.
- `results/T07d/runs/`: `agg_350.log`, `agg_375.log`, `agg_400.log`, `base_n5_350.log`, `base_n6_350.log`, `v6_n6_350.log`, `v6_n7_350.log`, `partB_swap_start.txt`.
- `NOTES.md`: appended the T07d entry.

## Problems and deviations
- **Median over 2, not 6:** the T07c logs hold one traced Prove tree each (the one for the second of the three repeats), so Part A has 2 samples per configuration. The mu-26 versus mu-25 ratios rest on those 2, and execute differs between them by 169 vs 93 ms.
- **Confound in the n6 versus n5 comparison:** n6 has 250-signature leaves and n5 has 300, so cycle counts differ as well as mu (957,159 vs 1,140,247).
- **Mapping assumptions:** no L4 exists, and claim batching is assumed to be Basis plus the first sumcheck (see §1). The "bus other" row is my addition.
- **Boundary resolution:** I ran one bisection step (375). N* is accurate only to the 25-step grid, so it is 350 among the tested values.
- **Prove-time comparability:** the aggregate prove times are single cold repeats, and swap was already about 1.5 GB in use.

## Suggested next step
- Verify the mu-26 stage attribution with a controlled mu-25 versus mu-26 pair at the same cycle count, ideally with `--repeat` of 3 or more and tracing on every repeat.
- Probe the "bus other" and execute excess at mu 26.
=== END REPORT ===

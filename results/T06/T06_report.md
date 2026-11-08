=== RESULT REPORT T06 ===
Status: done
Machine: Apple M2 (4P+4E, 8 cores), 8 GiB RAM, macOS 26.5.2 (25F84)
Toolchain: rustc 1.99.0 (b940084d7 2026-09-28), cargo 1.99.0 (5f94df478 2026-08-27); no Lean
Repo state:
- upstream/leanMultisig @ df7d122abbe25cf12e5c8ae992ce6d3505f75372, branch research/baseline, clean (unmodified; only `cargo test` run there)
- upstream/leanMultisig-t06 (git worktree of the same repo), branch research/t06-params @ 448a2c17c (local commit, parent df7d122ab), clean
- proto/whir-params: new crate (workspace is not a git repo)

## Summary
- **Answer.** Widening the first fold by k = 1..3 (L0 cut 7/8/9, or L1 cut 5/6/7) **changes no query count, no OOD count and no grinding level** at mu = 24..28, rate 1/4, when the rest of the ladder (every level's code) stays unchanged. Every eta, m, list size, MCA exponent a, proximity-gap, query and algebraic term is bit-identical to today's ladder.
- **The one term that moves** is the OOD term, through log2(mu) with mu = cols + interleaving exponent: -0.05 to -0.17 bits at L0 (L0 cut), -0.06 to -0.22 bits at L1 (L1 cut). Its margin is 40 to 50 bits.
- **Caveat: upstream's ladder rule.** Its own fixed rule (initial RS-domain reduction 3, `validate()` enforces it) makes "first fold 6+k" imply L1 rate 5+k, i.e. a 2^k-longer L1 codeword. Under that rule queries below L0 do change (mu=25: k=1 [112,38,25,19,15], k=2 [112,32,23,18,14], k=3 [112,28,21,16,14]). Keeping the ladder unchanged is rejected by `validate()` on that rate pin only; every soundness check passes.
- **Step 1.** No soundness term in `whir_config.rs` takes the fold factor or the row count as input. The interleaving exponent enters only `mu` in the OOD term (WC:618, 568-576). The code says this is deliberate and cites Jo 2026/891 Thm 4.4 (WC:431-433, 682).
- **Step 2.** Upstream's own `print_whir_query_counts`, run for all 56 (rate, size) pairs, gives eta and m per level. Rate 1/4, mu = 25: m = 162/43/40/7/9, eta = 3.086e-3 / 4.111e-3 / 1.562e-3 / 3.144e-3 / 8.12e-4.
- **Probe validation.** The probe reproduces the production derivation bit for bit (queries and eta bits, 56 configs, all rates) and the verifier's `WHIR_QUERIES` table. The probe's base eta and m match the upstream test print (26 of 26 levels).

## Results

### A. Soundness-term dependency table (step 1)
WC = `crates/pcs/src/whir_config.rs`, RS = `crates/pcs/src/ring_switch.rs`. Full version with every citation: `results/T06/dependency_table.md`.

| Term | Code | rate | code dim (cols) | block len n | eta / m | fold k_i or rows 2^ilv | mu = cols + ilv | prev queries | grinding | q = 2^192 |
|---|---|---|---|---|---|---|---|---|---|---|
| Proximity gap 192 - log2 a (BCHKS25 4.6) | WC:434-447, 455-458, 629 | Y | Y | Y | Y | **no** | no | no | no (no fold grinding) | Y |
| Query Q*log2(1/(1-gamma)), Q = ceil(111/per_q) | WC:462-466, 636-643 | Y | Y | cap Q <= n only | Y | **no** | no | no | Y (128-17) | no |
| Grinding (17, constant) | WC:60, 887, 920 | - | - | - | - | **no** | - | - | - | - |
| List size L = 1/(2 eta sqrt(rho)) | WC:497-503 | Y | Y | no | Y | **no** (stated, WC:478-489) | no | no | no | no |
| OOD bits, s >= 1: s(192 - log2 mu) - (2 log2 L - 1) | WC:568-576 | Y | Y | no | Y | **only via log2 mu** | Y | no | no | Y |
| OOD role at L0, s = 0: 192 - log2 L - log2 mu | WC:571-572 | Y | Y | no | Y | **only via log2 mu** | Y | no | no | Y |
| OOD count (smallest s in 1..8; 0 at L0) | WC:645-652 | Y | Y | no | Y | only via log2 mu | Y | no | no | Y |
| Algebraic 192 - log2 max(D_rs, prev_q + s, 2) - log2 L | WC:524-536 | Y | Y | no | Y | **no** | no | Y, dominated by D_rs = 2^31+2^15+2^7+2^3+2^1+1 (RS:76-79) | no | Y |
| Ladder rule rate_{i+1} = rate_i + k_i - 3 (then - 1); not a soundness term | WC:292-301, pinned at WC:757-781 | Y | | | | **Y: k_0 sets rate_1** | | | | |

What this table says, in order:
- **Interleaving.** The interleaving exponent (`ilv`) is this level's fold factor (`k_levels[i]`, WC:909, 916-917).
- **Under max (RBR, what the code targets).** Each fold challenge is its own RBR entry, 2L/|E| + eps (TEX thm:rbr). Under the max, extra folds cost nothing.
- **Under a sum (interactive soundness).** k extra folds would add k equal terms, at most log2(1 + 3/6) = 0.58 bits for k <= 3 at L0. The code does not compute this.

### B. Upstream per-level eta / m, rate 1/4 (step 2)
Command: `WHIR_LOG_INV_RATE=2 WHIR_NUM_VARS=<mu> cargo +1.99.0 test --release -p pcs print_whir_query_counts -- --ignored --nocapture`, run in upstream/leanMultisig (research/baseline). Values are deterministic, so repeat count does not apply. All rates 1..4 and sizes 15..28 are in `upstream_print_whir_query_counts.txt`.

| mu | L0 (rate 1/4) | L1 (1/32) | L2 (1/256) | L3 (1/2048) | L4 (1/16384) | L5 (1/131072) |
|---|---|---|---|---|---|---|
| 24 | Q 112, eta 3.086413866e-3, m 162 | 45, 4.110960475e-3, 43 | 28, 1.561736874e-3, 40 | 21, 3.653962292e-3, 6 | 16, 1.353164693e-3, 5 | |
| 25 | 112, 3.086416810e-3, 162 | 45, 4.111023206e-3, 43 | 28, 1.562118484e-3, 40 | 21, 3.144371560e-3, 7 | 16, 8.119916204e-4, 9 | |
| 26 | 112, 3.086418281e-3, 162 | 45, 4.111054572e-3, 43 | 28, 1.562309253e-3, 40 | 21, 3.150555187e-3, 7 | 16, 5.818785075e-4, 13 | |
| 27 | 112, 3.086419017e-3, 162 | 45, 4.111070255e-3, 43 | 28, 1.562404630e-3, 40 | 21, 3.153642454e-3, 7 | 16, 4.523212244e-4, 17 | |
| 28 | 112, 3.086419385e-3, 162 | 45, 4.111078096e-3, 43 | 28, 1.562452316e-3, 40 | 21, 3.155184955e-3, 7 | 16, 3.875612272e-4, 20 | 13, 2.657866474e-4, 9 |

Plain stacking past the layout window, for contrast (mu 29..31, same test, `upstream_print_whir_query_counts_mu29_31.txt`):
- L0 goes to **113 queries, m = 82**: the pg term depends on n, and n grows with mu.
- Interleaved widening keeps n fixed and stays at 112 up to mu' = 31.

### C. Sweep (step 3). Command: `cargo +1.99.0 run --release -- ../../results/T06` in proto/whir-params

Shapes. mu is the per-child stack size; n = 2^k children.
- `L0cut`: L0 interleaving 6+k, total variables mu+k, every level's code unchanged.
- `L0cut_rule`: upstream's own ladder for first fold 6+k on mu+k variables (L1 rate 5+k).
- `L1cut`: L0 per child unchanged, L1 interleaving 4+k.
- `L1cut_nq`: same, but L1's batch carries n*112 claims.

Grinding is 17 bits at every level of every case. OOD is [0,1,1,1,1] (mu=28: [0,1,1,1,1,1]) in every case.

Query counts per level:

| shape | k (n) | folds | mu=24 | mu=25 | mu=26 | mu=27 | mu=28 |
|---|---|---|---|---|---|---|---|
| base (today) | 0 (1) | 6,4,4,4,4 | 112,45,28,21,16 | 112,45,28,21,16 | 112,45,28,21,16 | 112,45,28,21,16 | 112,45,28,21,16,13 |
| L0cut | 1 (2) | 7,4,4,4,4 | same | same | same | same | same |
| L0cut | 2 (4) | 8,4,4,4,4 | same | same | same | same | same |
| L0cut | 3 (8) | 9,4,4,4,4 | same | same | same | same | same |
| L1cut and L1cut_nq | 1 (2) | 6,5,4,4,4 | same | same | same | same | same |
| L1cut and L1cut_nq | 2 (4) | 6,6,4,4,4 | same | same | same | same | same |
| L1cut and L1cut_nq | 3 (8) | 6,7,4,4,4 | same | same | same | same | same |
| L0cut_rule (rates 2,5+k,8+k,..) | 1 (2) | 7,4,4,4,4 | 112,38,25,19,15 | 112,38,25,19,15 | 112,38,25,19,15 | 112,38,25,19,15 | 112,38,25,19,15,13 |
| L0cut_rule | 2 (4) | 8,4,4,4,4 | 112,32,23,18,14 | 112,32,23,18,14 | 112,32,23,18,14 | 112,32,23,18,15 | 112,32,23,18,15,12 |
| L0cut_rule | 3 (8) | 9,4,4,4,4 | 112,28,21,16,13 | 112,28,21,16,14 | 112,28,21,17,14 | 112,28,21,17,14 | 112,29,21,17,14,12 |

Only term that differs from base in L0cut, L1cut and L1cut_nq (diff of every CSV field, all mu):

| shape | level | k=1 | k=2 | k=3 |
|---|---|---|---|---|
| L0cut | L0 OOD-role bits (base about 178.9-179.1) | -0.051..-0.059 | -0.100..-0.115 | -0.147..-0.170 |
| L1cut, L1cut_nq | L1 OOD bits (base about 169.7-170.0) | -0.064..-0.078 | -0.126..-0.152 | -0.184..-0.222 |
| L1cut_nq | L1 batch row, doc-literal (J-1)L/\|E\|, informational | -0.99 | -1.99 | -2.99 (172.76, margin 44.8) |

The code's algebraic term is unchanged in L1cut_nq because the ring-switch degree (2^31) dominates n*112 <= 896.

Per-level terms in bits. All 85 cases are in `sweep.out` and `sweep.csv`. Representative tables:

base, mu = 25 (identical to L0cut mu=25 for every k, except the L0 OOD bits: 178.960 / 178.905 / 178.853 for k = 1/2/3):

| L | fold | log_inv_rate | cols | Q | OOD | grind | eta | m | log2 L | pg | fold row (2L+a) | query | query+grind | OOD bits | algebraic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6 | 2 | 19 | 112 | 0 | 17 | 3.086417e-3 | 162 | 8.340 | 131.863 | 131.863 | 111.006 | 128.006 | 179.016 | 152.660 |
| 1 | 4 | 5 | 15 | 45 | 1 | 17 | 4.111023e-3 | 43 | 9.426 | 137.870 | 137.870 | 111.008 | 128.008 | 169.899 | 151.574 |
| 2 | 4 | 8 | 11 | 28 | 1 | 17 | 1.562118e-3 | 40 | 12.323 | 134.885 | 134.885 | 111.012 | 128.012 | 164.448 | 148.677 |
| 3 | 4 | 11 | 7 | 21 | 1 | 17 | 3.144372e-3 | 7 | 12.819 | 143.534 | 143.534 | 111.573 | 128.573 | 163.903 | 148.181 |
| 4 | 4 | 14 | 3 | 16 | 1 | 17 | 8.119916e-4 | 9 | 16.363 | 138.056 | 138.056 | 111.109 | 128.109 | 157.468 | 144.637 |

L1cut_nq, mu = 25, k = 3 (L1 fold 7, prev_q = 896). Same as base except L1: OOD bits 169.688, mu_vars 22.

L0cut_rule, mu = 25, k = 3 (upstream's rule; validate ok):

| L | fold | log_inv_rate | cols | Q | OOD | grind | eta | m | log2 L | pg | query+grind | OOD bits | algebraic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 9 | 2 | 19 | 112 | 0 | 17 | 3.086417e-3 | 162 | 8.340 | 131.863 | 128.006 | 178.853 | 152.660 |
| 1 | 4 | 8 | 15 | 28 | 1 | 17 | 1.562476e-3 | 40 | 12.322 | 130.886 | 128.003 | 164.108 | 148.678 |
| 2 | 4 | 11 | 11 | 21 | 1 | 17 | 3.155956e-3 | 7 | 12.808 | 139.549 | 128.462 | 163.477 | 148.192 |
| 3 | 4 | 14 | 7 | 16 | 1 | 17 | 3.705677e-4 | 21 | 17.404 | 128.437 | 128.017 | 154.733 | 143.596 |
| 4 | 4 | 17 | 3 | 14 | 1 | 17 | 8.612472e-4 | 3 | 17.778 | 137.759 | 131.538 | 154.637 | 143.222 |

Minimum over all cases of each term:
- pg: 128.86 (base, L0cut, L1cut); 128.44 (L0cut_rule)
- query+grind: 128.004 / 128.003
- OOD: 151.2 / 148.4
- algebraic: 141.4 / 140.0

`validate()` results:
- passes: base, L0cut k=0, all L0cut_rule
- fails, on the rate pin only: L0cut k >= 1, "L1: log_inv_rate (5) does not reduce the preceding RS domain by 3 bit(s); expected 5+k"
- not applicable: L1cut, since there are n separate L0 commitments

**Yes/no:** does widening the first fold by k = 1..3 change any query count, OOD count or grinding level?
- **No**, with the rest of the ladder (all later codes) unchanged: L0 cut and L1 cut, mu = 24..28, rate 1/4.
- **Yes, below L0**, if instead you apply upstream's ladder rule as coded. Its fixed initial reduction 3 lengthens the L1 code by 2^k; L0 is still 112 / 0 / 17.

### D. Theorem paraphrases (step 4)
Full text: `results/T06/theorems.md`. TEX = `doc/leanvm/body/b-polynomial-commitment-scheme.tex`. The papers themselves were not read.

**BCHKS25 Thm 4.6** (ePrint 2025/2055; annex `thm:mca-johnson`, TEX:176-185; WC:421-458)
- Statement. RS code over E with block length n, *slightly reduced* rate rho = (k-1)/n, radius gamma < 1 - sqrt(rho), slack eta = 1 - sqrt(rho) - gamma, and m = max(ceil(sqrt(rho)/eta), 3). For every **two-row** word, the probability over a uniform fold challenge in E that "the fold agrees with the code on some set of size (1-gamma)n but the word does not agree with the interleaved code on that set" is at most a/|E|, with a = [2(m+1/2)^5 + 3(m+1/2) gamma rho]/(3 rho^{3/2}) * n + (m+1/2)/sqrt(rho).
- Dependence: on n, rho and eta only.
- No dependence on: rows (stated for two), number of folded variables, or generator degree. The fold is an affine line; in char 2 the annex's (1-s, s) is equivalent (TEX:158 footnote).
- leanVM uses the **list** parameter ceil(sqrt(rho)/eta), not the non-list ceil(sqrt(rho)/(2 eta)) of Thm 1.5 (WC:449-455). It uses |E| = 2^192 at every level, including L0.

**Jo, ePrint 2026/891 Thm 4.4** (annex `lem:fold-list`, TEX:189-205; WC:431-433, 682)
- Statement, as the annex quotes it. For a code linear over F, and a fold whose two coefficients are functions of a seed drawn uniformly from a set of at most |F| elements, the MCA error of **every row interleaving** equals that of the code itself, at every radius.
- Hypotheses, as leanVM checks them: RS[E,S,k] is E-linear even though S is in K; the seed is the fold challenge drawn from E; the coefficients are (1-s, s).
- Consequence (`lem:fold-list`). For a 2^ell-row word, the chance that one fold changes the list is at most the same epsilon. "The bound does not grow with ell"; a row-wise union would cost 2^(ell-1) eps.
- Rows: no dependence. Folded variables: none per challenge, with one RBR entry 2L/|E| + eps per fold challenge (TEX:144, 251). Generator degree: only degree 1 (affine line, seed set E) is used.

**Johnson bound** (TEX:64-65, 299-319; WC:478-503). The list at radius 1 - sqrt(rho) - eta has at most 1/(2 eta sqrt(rho)) members. It holds for any alphabet, so it is independent of interleaving.

**thm:rbr** (TEX:139-152). Per-message errors:
- batch: (J_i - 1) L_i/|E|
- fold: 2L_i/|E| + eps_i, per challenge
- OOD: C(L_i, 2) nu_i/|E|, where nu_i counts variables including the interleaving ones
- query: (1 - gamma_i)^{t_i}
- final: t/|E|
- tail: 2/|E|

The RBR error is the max of these; interactive soundness would be their sum.

## Commands run
```
# quiet check (T05 finished): pgrep -fl leanvm every 10 s for 300 s, 22:13-22:18 +03, no hits  -> results/T06/quiet_check.txt
cd upstream/leanMultisig   # research/baseline, df7d122ab
for r in 2 1 3 4; for n in 15..28:
  WHIR_LOG_INV_RATE=$r WHIR_NUM_VARS=$n cargo +1.99.0 test --release -p pcs print_whir_query_counts -- --ignored --nocapture
for n in 29 30 31: WHIR_LOG_INV_RATE=2 WHIR_NUM_VARS=$n cargo +1.99.0 test --release -p pcs print_whir_query_counts -- --ignored --nocapture
git worktree add -b research/t06-params ../leanMultisig-t06 df7d122abbe25cf12e5c8ae992ce6d3505f75372
# (add crates/pcs/src/whir_config/t06_probe.rs; append `pub mod t06_probe;` to whir_config.rs)
git -C upstream/leanMultisig-t06 commit  -> 448a2c17c
cd proto/whir-params
cargo +1.99.0 test --release            # 3 passed
cargo +1.99.0 run --release -- ../../results/T06 > ../../results/T06/sweep.out
git -C upstream/leanMultisig-t06 diff df7d122ab HEAD > results/T06/t06-params.diff
```

## Raw output
```
$ WHIR_LOG_INV_RATE=2 WHIR_NUM_VARS=25 cargo +1.99.0 test --release -p pcs print_whir_query_counts -- --ignored --nocapture
num_vars=25, rate=1/4
L0: rate=1/4, queries=112, eta=3.086416809646e-3, m=162
L1: rate=1/32, queries=45, eta=4.111023206459e-3, m=43
L2: rate=1/256, queries=28, eta=1.562118483696e-3, m=40
L3: rate=1/2,048, queries=21, eta=3.144371559594e-3, m=7
L4: rate=1/16,384, queries=16, eta=8.119916203937e-4, m=9
test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 28 filtered out

$ cargo +1.99.0 test --release      (proto/whir-params)
test tests::widened_l0_keeps_l0_code ... ok
test tests::deterministic ... ok
test tests::probe_reproduces_production_and_table ... ok
test result: ok. 3 passed; 0 failed

$ cargo +1.99.0 run --release -- ../../results/T06   (first line)
cross-check (rates 1..4, log_n 15..28, 56 configs): probe == production derivation (queries, eta bits) == verifier WHIR_QUERIES, validate() ok: ALL PASS
```
The full sweep output is in `results/T06/sweep.out` (875 lines).

## Files changed or created
- upstream/leanMultisig-t06/ : new git worktree, branch research/t06-params (local only, not pushed)
- upstream/leanMultisig-t06/crates/pcs/src/whir_config/t06_probe.rs : new probe module (177 lines); calls the unchanged private search and term functions
- upstream/leanMultisig-t06/crates/pcs/src/whir_config.rs : +3 lines (`pub mod t06_probe;`); full diff in results/T06/t06-params.diff
- proto/whir-params/{Cargo.toml, Cargo.lock, src/main.rs} : sweep driver, cross-check and 3 tests (Cargo.lock seeded from upstream)
- results/T06/T06_report.md : this report
- results/T06/dependency_table.md : step 1 table with full citations
- results/T06/theorems.md : step 4 paraphrases
- results/T06/upstream_print_whir_query_counts.txt : step 2, upstream test output, rates 1..4 x sizes 15..28
- results/T06/upstream_print_whir_query_counts_mu29_31.txt : plain-stacking contrast
- results/T06/sweep.out, sweep.csv, sweep.stderr : step 3 output (per level: fold, rate, cols, mu_vars, prev_q, Q, OOD, grind, eta, m, gamma, L, a, every term in bits, delta vs base, validate)
- results/T06/quiet_check.txt : end of the 5-minute idle check
- NOTES.md : T06 entry

## Problems and deviations
1. **Public API was not enough.** The fold factor is a const (WC:67), and `optimize_johnson_level`, the term functions and `eta` are private. I made the minimal change on new local branch research/t06-params: one `pub mod` line plus a child module, with no production logic touched. It lives in a separate worktree, so the main clone never left research/baseline.
2. **"Rest of ladder unchanged" is not a configuration upstream can produce as coded.** `validate()` (WC:757-781) and the verifier's `derive_config` (verifier/src/whir.rs:37-50) both hard-code fold 6 and initial reduction 3. I therefore report two readings:
   - `L0cut`: ladder unchanged. All soundness checks pass; only the rate pin fails.
   - `L0cut_rule`: upstream's rule. It validates, but L1 is 2^k longer.
   Making `L0cut` real would need verifier and guest changes plus a `WHIR_QUERIES` regeneration.
3. **mu' = mu + k reaches 31, beyond the layout window** (MAX_MU = 28, verifier/src/layout.rs:87-88). The parameter analysis has no such cap; the implementation does.
4. **What the parameter code cannot see (protocol-level points, not checked here):**
   - L0 uses OOD = 0, justified by "the opening's own post-commit evaluation claim" (WC:318-320, 562-567). For n stacked children, their L0 roots and claim points come from separate earlier proofs. Whether the list-union argument (L*mu/|F|) carries over to the stacked word needs a protocol argument.
   - MCA additionally needs the fold challenges sampled after all n roots are fixed.
   - In the L1 cut, the batch J_1 really is about n*112 claims. I modelled that (`L1cut_nq`); it is absorbed by the 2^31 ring-switch degree.
5. **The upstream test prints only queries, eta and m.** The term bits come from the probe, which equals the production code bit for bit (cross-check above).

## Suggested next step
Write down the protocol argument for L0 binding and MCA when n children's separately committed L0 words are stacked (item 4). The parameters say widening is free; the open question is whether the OOD = 0 justification and the fold-challenge ordering carry over. Then decide between L0cut (ladder unchanged, which needs verifier, guest and table changes) and L1cut, which leaves the L0 machinery untouched.
=== END REPORT ===

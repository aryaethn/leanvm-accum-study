# T06 step 1: what each soundness term depends on

Sources: `WC` = `upstream/leanMultisig/crates/pcs/src/whir_config.rs` at df7d122ab (unchanged on research/baseline); `RS` = `crates/pcs/src/ring_switch.rs`.

## Inputs of the per-level search

`optimize_johnson_level(level, log_inv_rate, log_msg_cols, log_num_interleaved, target_bits, query_grinding_bits, prev_queries)` (WC:607-675), called once per level from `derive_config_with_log_inv_rate` (WC:906-924). The per-level inputs come from the ladder `derive_ladder_shape` (WC:292-301 over WC:252-286):

- `rate = log_inv_rates[i]`
- `cols = log_msg_cols[i]`, the code dimension exponent kappa_i = variables left after this level's fold
- `ilv = k_levels[i]`, this level's fold factor, which is also its interleaving exponent (WC:909, 916-917)
- `prev_queries = levels[i-1].queries`, or 0 at L0 (WC:549-552, 910)

Derived quantities inside the search:

- `rho = reduced_rate(rate, cols) = (2^cols - 1) / 2^(cols + rate)` (WC:416-419)
- `n = block_len = 2^(cols + rate)` (WC:444, 619)
- `mu = cols + ilv` (WC:618). **This is the only place `ilv` (the fold factor, i.e. the row-count exponent) enters any term.**
- For each candidate m = 3..4096, `eta = sqrt(rho)/m`, nudged by one ulp (WC:592-601, 622-623)
- `gamma = 1 - sqrt(rho) - eta`
- `L = 1/(2 eta sqrt(rho))`
- `q = 2^192`: the constant `ANALYSIS_LOG_Q` (WC:410), the same at every level

Selection: minimise `queries`; ties keep the smallest m (WC:665). Pruning: stop as soon as pg < 128 (WC:632-634), and skip a candidate if `queries > block_len` (WC:641-643).

## Dependency table

Legend: Y = depends on it; - = does not. "Fold k_i" means this level's own fold, the fold of the first level being widened. "Rows" means interleaving 2^ilv. At every level of the production ladder these two are the same number (`ilv = k_levels[i]`, WC:909).

| Term (bits) | Formula as coded | Code | rate | cols (code dim) | block len n | eta (m) | fold k_i / rows 2^ilv | mu (= cols + ilv) | prev_queries | grinding | field q | ring-switch degree |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Proximity gap / MCA, "pg" | `192 - log2 a`, a from BCHKS25 Thm 4.6 | WC:434-447 (a), 455-458 (m), 629 | Y | Y (via rho, n) | Y | Y | **-** | - | - | - (fold-challenge grinding is none) | Y | - |
| Query | `Q * log2(1/(1-gamma))`; `Q = ceil((128-17)/per_q)` | WC:462-466, 636-643; check WC:819-829 | Y | Y (rho) | only the cap `Q <= n` (WC:641) | Y | **-** | - | - | Y (target 128 - 17 = 111, WC:617) | - | - |
| Grinding (query phase) | constant 17 | WC:60, 887, 920 | - | - | - | - | **-** | - | - | n/a | - | - |
| List size L (feeds pg-adjacent terms, OOD and algebraic) | `log2(1/(2 eta sqrt(rho)))` | WC:497-503 | Y | Y | - | Y | **-** (stated independent of interleaving, WC:478-489) | - | - | - | - | - |
| OOD, level >= 1, s samples | `s(192 - log2 mu) - (2 log2 L - 1)` | WC:568-576; s chosen at WC:645-652 | Y (L) | Y (L, mu) | - | Y | **Y, only through log2(mu)** | Y | - | - | Y | - |
| OOD-role at L0 (s = 0) | `192 - log2 L - log2 mu` | WC:571-572 | Y | Y | - | Y | **Y, only through log2(mu)** | Y | - | - | Y | - |
| OOD sample count | smallest s in 1..8 with OOD >= 128; forced 0 at L0 | WC:645-652 | Y | Y | - | Y | **Y, via log2(mu)** (the margin is large, see sweep) | Y | - | - | Y | - |
| Algebraic (batch row + the 2L part of the fold row) | `192 - log2(max(D_rs, prev_q + s, 2)) - log2 L` | WC:524-536; check WC:842-851 | Y (L) | Y (L) | - | Y | **-** | - | Y, but dominated: D_rs = 2^31 + 2^15 + 2^7 + 2^3 + 2^1 + 1 (RS:76-79) is far above prev_q + s | - | Y | Y |
| Ladder geometry (not a soundness term, but it moves every term below L0) | `rate_{i+1} = rate_i + k_i - 3` after L0, `- 1` after that | WC:292-301; pinned by `validate` at WC:757-781 | Y | Y | Y | - | **Y: the first fold k_0 sets rate_1 = rate_0 + k_0 - 3** | - | - | - | - | - |

## Answers to step 1

- **Does any soundness term grow with the first fold factor or with the row count?**
  - No proximity-gap, query, grinding, list-size or algebraic term contains `ilv` or `k_i` (table above).
  - The only per-level dependence is `log2(mu)` in the OOD term, with `mu = cols + ilv`. Going from 6 to 9 on mu = 25 changes it from log2 25 to log2 28 = 0.16 bits per sample at L0. That is negligible next to a margin of tens of bits (measured in the sweep).
  - The code says this independence is deliberate: the "Why" at WC:682 and the doc comment at WC:431-433 both cite Jo 2026/891 Thm 4.4 / `lem:fold-list`.
- **Indirect dependence through the ladder.** With the production rule (fixed initial domain reduction 3, `RS_DOMAIN_INITIAL_REDUCTION_FACTOR`, WC:73; enforced by `validate`, WC:761-781), a first fold of 6 + k gives L1 rate 5 + k. The L1 codeword is then 2^k times longer and every later rate moves by k as well, so queries at L1 and below change. This comes from the ladder rule, not from any soundness term.
  - Keeping "the rest of the ladder unchanged" (L1 rate 5) means an initial reduction of 3 + k. `validate()` rejects that as coded. The soundness terms themselves would not object.
- **Number of fold challenges.** Each fold challenge is a separate RBR entry of size `2L/|E| + eps` (TEX `thm:rbr`). Under the max (RBR, which is what the code targets: WC:25-27, 870-875) k extra folds add nothing. Under a sum (interactive soundness), they add k more equal terms, i.e. log2(1 + k/6) bits of loss at L0, at most 1 bit for k <= 3. The code does not compute that sum.
- **Rate.** Every term depends on it through rho, L and n.
- **Margin eta.** Every term except the grinding constant depends on it. It is chosen per level, so a change in rate, cols or (through OOD) mu can move it.
- **Field size.** The constant 192 enters pg, OOD and algebraic. Query and grinding do not depend on it.

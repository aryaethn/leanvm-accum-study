# T04: leanVM PCS opening structure, soundness parameters, in-circuit hashing, deferred claims

Pinned commit: leanMultisig `df7d122abbe25cf12e5c8ae992ce6d3505f75372`, branch `research/baseline`, tree clean (`git status --short` empty before and after; nothing edited in `upstream/`).
Method: file reading and grep only. No cargo, no builds, no benchmarks (T03 was running). `target*/` excluded from every search.
Paths below are relative to `upstream/leanMultisig/`. `W:` = `crates/verifier/src/whir.rs`, `WC:` = `crates/pcs/src/whir_config.rs`, `G:` = `crates/rec_aggregation/guests/lean_ethereum.py`, `AG:` = `crates/rec_aggregation/src/aggregation/`.

Evidence tags used in every table:
- **[E]** exact, read from code or from a tool-printed number.
- **[X]** expectation over uniformly random query positions, computed by hand from a closed form (no program was run).
- **[D]** derived by hand from code plus shapes that are printed in the T00/T01 logs.
- **[I]** inferred: needs a shape that no log prints (bus depth, table evaluation count). Flagged as estimate.

---------------------------------------------------------------------------------------------------

## 0. Shapes used (where the numbers come from)

| Object | Leaf (child), 250 XMSS, rate 1/4 | Merge node, 2 children, rate 1/4 | Source |
|---|---|---|---|
| Placed words (`TOTAL_COMMITTED`) | 2^24.103 = 18.02 M | 2^23.842 = 14.7 M | results/T00/aggregate_xmss250_lir2.log:154; results/T01/recursion_n2_m250_leaflir2_lir2.log (details line) |
| Stack size `mu = log_n = ceil(log2 placed)` | 25 | 24 | `crates/verifier/src/layout.rs:547` (`MIN_STACKED_LOG.max(total_log)`, window 15..=28 at `layout.rs:87-88`); the guest dispatches on it over 22..=28 (`AG child.rs:261-262`) |
| Lane blocks carrying data | 35 of 64 (placed / 2^19 = 34.4 -> 35; encoder row padded to 40) | 58 of 64 (placed / 2^18 = 57.3 -> 58; row 64) | `crates/pcs/src/whir.rs:129-141`; NTT log line `lanes: 40` / `lanes: 64` |
| L0 NTT log-domain | 21 | 20 | trace `kind: "base encode" log_domain: 21 lanes: 40` (leaf), `20 / 64` (node) |

Leaf = `aggregate(&[], 250 sigs, .., leaf_log_inv_rate=2)` (`bins/leanvm/src/benchmark.rs:250-258`), the same call as `leanvm aggregate --xmss 250 --log-inv-rate 2`, so the T00 aggregate log is the leaf's shape. The recursion benchmark's leaf keys differ from the `aggregate` benchmark's, so row counts could differ slightly; `mu = 25` is robust (2^24.103 sits well inside [2^24, 2^25]).

---------------------------------------------------------------------------------------------------

## 1. Committed objects of one leaf proof

**There is exactly one witness commitment per proof**: the stacked polynomial `q`. Every column of every table, the memory limbs and the Keccak states are placed inside it and all claims are discharged by a single WHIR opening.
- Stacking: `doc/leanvm/body/04-committing-the-witness.tex:5-25`; placement `crates/verifier/src/layout.rs:481-574`; one opening `crates/verifier/src/lib.rs:125-149` (`verify_stacked_opening`) and `lib.rs:326-335`.
- Symbol field: `K = GF(2^64)` for the committed message, `E = GF(2^192)` for challenges, folded witnesses and deeper-level codewords (`crates/pcs/src/whir.rs:6-22`).

### 1a. What is inside `q` (leaf, 250 XMSS) [D, cross-checked against measured total]

Heights are `ceil(log2 rows)` from the printed row counts (XOR 2^15.518, MUL 2^15.379, SET 2^15.435, DEREF 2^14.833, JUMP 2^13.333, KECCAK 2^15.509, MEMORY 2^20.576, BYTECODE 2^18.899).

| Polynomial (K-valued multilinear) | Count x size | Words | Source |
|---|---|---|---|
| MEMORY_0, MEMORY_1, MEMORY_2 (the three K limbs of each F192 memory cell) | 3 x 2^21 | 6,291,456 | `layout.rs:93-98`, `kappas` at `layout.rs:524-531`; log_memory = 21 |
| MEMORY_FINAL_COUNTERS | 1 x 2^21 | 2,097,152 | same |
| BYTECODE_FINAL_COUNTERS | 1 x 2^19 | 524,288 | same (`log_bytecode` = 19, since BYTECODE_VARS = 23 = 19 + 4) |
| q_keccak (bit-packed Keccak states, 64 bits per K word; also hosts 14 spare-slot KECCAK-table columns) | 2^(16 + 6) | 4,194,304 | `layout.rs:523`, slot bits = ceil(log2 50) = 6; `layout.rs:343-367` |
| XOR table, 15 columns | 15 x 2^16 | 983,040 | `ARITH_COLUMNS` `layout.rs:371` |
| MUL table, 15 columns | 15 x 2^16 | 983,040 | same |
| SET table, 8 columns | 8 x 2^16 | 524,288 | `SET_COLUMNS` `layout.rs:372` |
| DEREF table, 15 columns | 15 x 2^15 | 491,520 | `DEREF_COLUMNS` `layout.rs:374` |
| JUMP table, 14 columns | 14 x 2^14 | 229,376 | `JUMP_COLUMNS` `layout.rs:376` |
| KECCAK table's remaining committed columns (40 head+count columns, 14 ride q_keccak spare slots; 50 value lanes are not committed as columns) | 26 x 2^16 | 1,703,936 | `layout.rs:538-545`, `qkeccak_slot` |
| **Sum** | | **18,022,400** (= 2^24.103 within rounding of the printed exponent) | matches `TOTAL_COMMITTED` 2^24.103 |

The sum reproducing the tool's own `TOTAL_COMMITTED` is the check that the column accounting is right. The blocks are laid out largest first (`stack_offsets`), zero padded to `2^mu`; the zero tail is whole lanes of the L0 commitment and is never encoded or sent (`pcs/src/whir.rs:111-127`).

### 1b. The Merkle commitments of the WHIR opening (leaf, rate 1/4, mu = 25) [D]

| Commitment | What is committed | Symbols | Interleaving `m` (lanes per Merkle leaf) | Leaf bytes | Domain (leaves) | Code rate | Source |
|---|---|---|---|---|---|---|---|
| L0 | the stacked `q` | K = GF(2^64) | 2^6 = 64 lanes (35 carry data) | 512 (zero prefix hashed too) | 2^21 | 1/4 | `W:185-200`, `pcs whir.rs:129-170` |
| L1 | `q` folded by 6 (19 variables) | E = GF(2^192), 3 K-words each | 2^4 = 16 | 384 | 2^20 | 1/32 | `W:37-50`, `pcs whir.rs:218-254` |
| L2 | folded by 4 more (15 variables) | E | 16 | 384 | 2^19 | 1/256 | same |
| L3 | (11 variables) | E | 16 | 384 | 2^18 | 1/2048 | same |
| L4 | (7 variables) | E | 16 | 384 | 2^17 | 1/16384 | same |
| residual `yr` | 3 variables left after 22 folds | E, sent in the clear | n/a | n/a | 8 elements | n/a | `W:173-175`, `WC:86` |

Merge node (mu = 24): L0 domain 2^20, L1..L4 2^19, 2^18, 2^17, 2^16 (matches the printed NTT logs `20,19,18,17,16`), residual 4 elements. Rate-1/2 node (`--log-inv-rate 1`): ladder rates 1,4,7,10,13 and domains 2^19 .. 2^15 (matches the lir1 log `19,18,17,16,15`).

Rates follow `log_inv_rate[i+1] = log_inv_rate[i] + k_i - reduction`, reduction 3 after the initial 6-fold and 1 after each 4-fold (`W:41-46`, `WC:288-301`); fold factors 6 then 4 (`WC:67-68`); folding stops once at most 5 variables remain (`WC:86`).

### 1c. Where ring switching sits

- The Keccak GKR (24 rounds in 2 segments of depth 12) ends in claims on **bits**: 64 slice claims `s_i` of the bit-MLE of q_keccak at an E-point (`crates/verifier/src/keccak.rs:1-10`; guest `verify_keccak` `G:2927-3093`, slices read at `G:3066-3072`).
- Ring switching (Diamond-Posen): six challenges build a composed F2-linear map Phi (shifts 32,16,8,4,2,1). The 64 slice claims become **one** claim `<rs_eq_ind, q_keccak> = T` on the packed K-polynomial, i.e. on the q_keccak region of the stack. Verifier `crates/verifier/src/ring_switch.rs:1-54`; native call site `crates/verifier/src/lib.rs:316-326`; prover `crates/pcs/src/ring_switch.rs:1-60`; guest `G:3448-3467` (target) and `G:3126` (weight).
- That claim leads the batch (takes lambda^0, weight scaled by the q_keccak placement selector, `lib.rs:322-327`); every other column claim (bus decomposition, table sumcheck evaluations, public-input limbs, Keccak output claim) follows with powers of the same challenge (`G:3476-3489`). One WHIR run then proves the whole combined claim (`crates/pcs/src/stack_open.rs:1-60`).

---------------------------------------------------------------------------------------------------

## 2. WHIR / Ligerito opening, per round

**Parameters are tabulated, not recomputed, in the verifier.** `W:18-23` hard-codes `WHIR_QUERIES[log_inv_rate-1][log_n-15]`; `W:51-52` checks the entry's length equals the ladder length. A test pins the table against the Rust search (`crates/leanvm_core/tests/verifiers/whir_query_table.rs:1-70`, "WHIR_QUERIES is stale, regenerate it"). The guest takes the same numbers from `pcs::whir::config_for_rate` (`AG child.rs:26-37`), and the Rust search is `WC:884-940` (`derive_config_with_log_inv_rate`) calling `WC:607-675` (`optimize_johnson_level`).

Row used for rate 1/4 is `W:20` (the second row, `log_inv_rate = 2`), index `log_n - 15`: mu = 25 -> index 10, mu = 24 -> index 9; both give `[112, 45, 28, 21, 16]` (five levels, as the ladder predicts).

OOD samples: 0 at L0, exactly 1 at every deeper level, asserted for all rates and sizes 22..28 + LOG_PACKING by the test at `WC:976-1004` (`assert_eq!(level.ood_samples, 1)`, `assert_eq!(level.grinding_bits, QUERY_GRINDING_BITS)`). Grinding is 17 bits on every level including the last (`WC:60`, `W:15,184`).

### 2a. Leaf (mu = 25, rate 1/4)

| Level | Fold k | log rate | log msg cols | Tree depth (= NTT log-domain) | Queries | OOD | Grind bits | Guest cap depth | Path hashes / query | Leaf words (bytes) | Positions / squeeze | Squeezes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 6 | 2 | 19 | 21 | 112 | 0 | 17 | 7 | 14 | 64 K-words (512) | 9 | 13 |
| L1 | 4 | 5 | 15 | 20 | 45 | 1 | 17 | 6 | 14 | 48 K-words (384) | 9 | 5 |
| L2 | 4 | 8 | 11 | 19 | 28 | 1 | 17 | 5 | 14 | 48 (384) | 10 | 3 |
| L3 | 4 | 11 | 7 | 18 | 21 | 1 | 17 | 5 | 13 | 48 (384) | 10 | 3 |
| L4 | 4 | 14 | 3 | 17 | 16 | 1 | 17 | 4 | 13 | 48 (384) | 11 | 2 |
| final | 3 residual vars | | | | `yr` = 8 E elements sent in clear | | | | | | | |

Formulas: tree depth = `log_msg_cols + log_inv_rate` (`W:185`, `WC:146-148`); cap depth = `min(ceil(log2 queries), depth)` (`AG child.rs:39-41`); path hashes = depth - cap depth (`child.rs:188`); positions per squeeze = `floor(192 / depth)` (`W:72`, `child.rs:30`); squeezes = `ceil(queries / positions_per_squeeze)` (`AG placeholders.rs:610`). Total folds 6+4+4+4+4 = 22; residual 25 - 22 = 3.

### 2b. Merge node, 2 children (mu = 24, rate 1/4)  [as a future child of a parent node]

| Level | Fold k | log rate | log msg cols | Depth | Queries | OOD | Grind | Cap depth | Path hashes / query | Leaf words (bytes) | Positions / squeeze | Squeezes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 6 | 2 | 18 | 20 | 112 | 0 | 17 | 7 | 13 | 64 (512) | 9 | 13 |
| L1 | 4 | 5 | 14 | 19 | 45 | 1 | 17 | 6 | 13 | 48 (384) | 10 | 5 |
| L2 | 4 | 8 | 10 | 18 | 28 | 1 | 17 | 5 | 13 | 48 (384) | 10 | 3 |
| L3 | 4 | 11 | 6 | 17 | 21 | 1 | 17 | 5 | 12 | 48 (384) | 11 | 2 |
| L4 | 4 | 14 | 2 | 16 | 16 | 1 | 17 | 4 | 12 | 48 (384) | 12 | 2 |
| final | 2 residual vars | | | | `yr` = 4 E elements | | | | | | | |

Rate-1/2 node (`--log-inv-rate 1`, mu = 24): queries `[224, 56, 32, 23, 17]` from `W:19` index 9; ladder rates 1,4,7,10,13; same fold schedule.

Proof carries L0 rows of only 35 (leaf) / 58 (node) words, the zero prefix is reconstructed (`crates/verifier/src/merkle.rs:94-100`; row width from `W:195-197`). The guest still hashes the full 512-byte image (`G:1591-1595` comment, `G:1364-1368`).

### 2c. Two different "caps"

- **Guest cap** (protocol-visible, used for the in-circuit cost): the top `cap_depth` levels of each level's tree are hinted as a shared node set, authenticated once per level by `verify_merkle_cap` (`G:1163-1214`), then each query hashes only `depth - cap_depth` levels (`G:1312-1347`). Queries are not deduplicated in the guest.
- **`CutTree`** (prover memory only, not a protocol parameter): trees of at least 2^12 leaves do not store the lowest `CUT = 4` levels, which are recomputed from rows on opening (`crates/pcs/src/merkle.rs:297-312`).

---------------------------------------------------------------------------------------------------

## 3. Soundness regime

| Item | Finding | Source |
|---|---|---|
| Regime | **Johnson list decoding with explicit slack eta** (proximity radius `gamma = 1 - sqrt(rho) - eta`), plus out-of-domain binding. **Not** unique decoding: the UDR helpers (`udr_queries`, `udr_per_query_bits_asymptotic`, `default_config`) exist only under `#[cfg(test)]`. No proximity-gap conjecture is used. | `WC:307-326`, `WC:161-176, 472-476` (test-only) |
| Proximity-gap theorem | BCHKS25 Theorem 4.6 (list correlated agreement), in the PCS annex as `thm:mca-johnson`; exceptional set `a = [2(m+1/2)^5 + 3(m+1/2) gamma rho] / (3 rho^{3/2}) * n + (m+1/2)/sqrt(rho)`, `m = max(ceil(sqrt(rho)/eta), 3)`. Uses the *list* parameter (a factor 2 worse than the non-list Thm 1.5; noted at `WC:449-455`). | `WC:421-458`; `doc/leanvm/body/b-polynomial-commitment-scheme.tex:176` |
| Interleaving | fold error of a 2^l-row word equals the two-row MCA error (affine-line MCA invariant under row interleaving), citing Jo, ePrint 2026/891 Thm 4.4, annex `lem:fold-list` | `WC:431-433`; tex:190-201 |
| List size | `L <= 1/(2 eta sqrt(rho))` (Johnson bound for the interleaved code, independent of interleaving) | `WC:478-503`; tex:64-65 |
| Overall analysis | Round-by-round (RBR) soundness: every verifier-challenge transition must individually clear 128 bits; the Fiat-Shamir error per random-oracle query is the MAX of the entries, not their sum. This is not a claim that the sum of all interactive failure probabilities is below 2^-128. | `WC:25-27, 36-38, 870-875, 899-904` |
| Target bits | `SECURITY_BITS = 128` (`WC:38`); analysis field `q = 2^192` (`WC:410`) | |
| Query-phase grinding | 17 bits per level, applied after the level's root is observed and before query positions are sampled; the query count only has to close `128 - 17 = 111` bits. Verified by `grind_check(17)` at every level (`W:184`; guest `G:889-915, 1555-1558`). | `WC:57-60` |
| Fold-challenge grinding | **None** (the eta search keeps `log2(q/a)` above 128 by itself) | `WC:314-318, 628-634` |
| Query count rule | `queries = ceil(111 / per_q)`, `per_q = log2(1/(sqrt(rho)+eta))` (`rho` is the *reduced* rate `(2^c - 1)/2^(c+r)`) | `WC:462-466, 636-643` |
| Margin eta | Not a constant: chosen **per level** by a discrete search over `m = 3..4096` (`JOHNSON_ETA_SEARCH_MAX_M`), minimising queries subject to: proximity-gap >= 128 bits, OOD >= 128 bits, list-unioned algebraic term >= 128 bits (degree = max(ring-switch degree, previous queries + OOD, 2)). Ties keep the smallest `m`. `eta` values are not printed anywhere I could read (they would need `print_whir_query_counts`, a cargo test). | `WC:607-675` |
| OOD | explicit samples at levels >= 1 (smallest `s` in 1..8 with `s(192 - log2 mu) - (2 log2 L - 1) >= 128`; the test asserts s = 1); at L0 the opening's own post-commit evaluation claim plays the OOD role (`L mu/q`), so `ood = 0` and the PCS alone is only list-binding | `WC:554-576, 645-652`; tex:4 |
| Hand sanity check (my arithmetic, not program output) [X-class, labelled estimate] | L0 at rate 1/4: 112 queries needs `per_q >= 111/112 = 0.991`, i.e. `eta` of order 2-3 x 10^-3 (`m` roughly 160..270); at that `m` the BCHKS25 term `a` is about 2^60..2^64 against `q = 2^192`, comfortably 128+ bits. Consistent with the tabulated 112. | `WC:434-447` |
| Paper cross-check | eprint 2026/2424 Section 7 says leanVM uses Johnson-bound guarantees: consistent with the code above. README states "128-bit ROM (64-bit QROM) soundness" and "no proximity gap conjecture" (`README.md:47-48`): consistent with a proven Johnson-regime analysis. I did not re-derive the proof. | |

One caveat worth passing on: "128-bit" here is a per-transition RBR target (128 bits for each of: batching, fold/proximity-gap, OOD, query+17 grinding), which is the right notion for the ROM Fiat-Shamir argument but is not 128 bits of total interactive soundness. The accumulation scheme's own parameters should state which notion it matches.

---------------------------------------------------------------------------------------------------

## 4. Hashing costs

### 4a. Keccak-256 as a Merkle hash

All Merkle hashing is Keccak-256 (rate 136 B, `0x01 .. 0x80` padding): `primitives::hash::hash` natively (`crates/fiat_shamir/src/merkle.rs:24-38`), identical to the verifier's `keccak_hash` (`crates/verifier/src/hash.rs:8, 79-97`). Permutations per call = `floor(len/136) + 1`. One `KECCAK` VM instruction = one permutation (`crates/lean_compiler/zkDSL.md:451-462`: "136 bytes a KECCAK instruction").

| Call | Input bytes | Keccak-f per call | Source |
|---|---|---|---|
| 2-to-1 node `H(left || right)` | 64 | **1** | `merkle.rs:37-42` (verifier), `fiat_shamir/merkle.rs:31-38` |
| L0 leaf (64 K-words) | 512 | **4** (3 full blocks + 104 B) | `W:194`; guest `LIG_LEAF_CELLS` = 32 cells x 16 B (`AG placeholders.rs:766-779`) |
| L>=1 leaf (16 lanes x 3 K-words) | 384 | **3** (2 full + 112 B) | same, 24 cells |
| Digest | 32 B, carried as two 128-bit halves | | `fiat_shamir/merkle.rs:16-22` |

There is no separate leaf/node domain tag; the only separation is length (leaf images 384/512 B vs node preimages 64 B).

### 4b. Fiat-Shamir sponge (`crates/fiat_shamir`, mirrored by `crates/verifier/src/transcript.rs:32-90` and guest `G:592-688`)

- Keccak-f[1600] duplex in overwrite mode. Rate = lanes 0..16 (128 B), capacity = lanes 16..25 (lane 16 is Keccak-256 rate but the transcript keeps it).
- Absorb: an E element (192 bit) occupies **4 lanes** (3 limbs + a domain tag: `DS_OBSERVE = 1`, `DS_POW_NONCE = 4`), so up to 4 scalars wait and a permutation takes all of them: **0.25 permutation per absorbed scalar**, one permutation when the 5th scalar arrives.
- Squeeze: **every challenge costs one permutation** of its own (taking whatever waits); the challenge is the first 3 lanes of the output. A sumcheck round that receives 2-3 coefficients and returns a challenge therefore costs exactly 1 permutation.
- Init: 1 permutation (IV and public input). Grinding: nonce absorbed with its own tag then one squeeze; verifier cost 1 permutation, prover about 2^17 expected.
- Query positions: one squeeze yields `floor(192/depth)` positions (`W:70-85`).

---------------------------------------------------------------------------------------------------

## 5. Guest accounting (one leaf child verified inside a node)

Where each cost sits in the guest (all in `G`):

| Cost | Location |
|---|---|
| `verify_sub` (one child, mirrors `crates/verifier`) | 3325-3517 |
| `open_stacked` (the WHIR opening, one arm per (rate, mu)) | 1434-1764 |
| Fold rounds (1 squeeze each) | `opening_fold` 1220-1233, loop 1497-1502 |
| OOD point (1 squeeze per coordinate) | `opening_ood_point` 1236-1247, call 1525-1530 |
| Final message + nonce | `opening_final_message` 1250-1269, call 1505 |
| Grind check | `grind_check` 889-915, call 1555-1556 |
| Query-position squeezes + window decode | 1560-1580, `decode_query_windows` 825-886 |
| Batching challenge lambda (1 squeeze/level) | 1587-1590 |
| Cap authentication (`verify_merkle_cap`) | 1163-1214, call 1602 |
| Per-query leaf hash (`keccak_cells`) | `opening_query` 1391-1393 |
| Per-query path hashing (`keccak` per level) | `walk_window` 1296-1309, `walk_path` 1312-1347, `opening_queries` 1397-1419 |
| Tail sumcheck rounds | 1643-1660 |
| Rest of verify_sub | bus GKR `verify_bus_gkr` 1772-1944; tables `verify_tables` 2113-~2540; Keccak GKR `verify_keccak` 2927-3093 / `keccak_layer` 2698-2879; ring switch 3448-3476 |
| Per-child cost in `main` | claim-list digest 4101-4122 (mono walk 4170-4201), child statement digest 3973-4004 (call 4550), `aggregate_claims` 4585-4689 |

### 5a. Analytic KECCAK count of the WHIR opening, per round (leaf, mu = 25, rate 1/4)

Columns: leaf hashing = Q x (4 or 3); path hashing = Q x (depth - cap); cap = expected number of distinct internal cap nodes hashed [X]: `sum_{j=0}^{c-1} 2^j (1 - (1 - 2^-j)^Q)` for cap depth `c` (root always hashed; a node is hashed only if flagged; `G:1200-1208`); sponge = fold squeezes + OOD-point squeezes + 1 nonce/grind permutation + query squeezes + 1 lambda (+ final-message permutations at L4).

| Level | Q | Leaf hash | Path hashes | Cap hashes [X] | Merkle subtotal | Sponge perms [E] | Level total |
|---|---|---|---|---|---|---|---|
| L0 | 112 | 448 (4 x 112) | 1568 (14 x 112) | 115.1 (max 127) | 2131.1 | 6 + 19 + 1 + 13 + 1 = 40 | **2171.1** |
| L1 | 45 | 135 | 630 | 54.4 (max 63) | 819.4 | 4 + 15 + 1 + 5 + 1 = 26 | **845.4** |
| L2 | 28 | 84 | 392 | 28.2 (max 31) | 504.2 | 4 + 11 + 1 + 3 + 1 = 20 | **524.2** |
| L3 | 21 | 63 | 273 | 26.4 (max 31) | 362.4 | 4 + 7 + 1 + 3 + 1 = 16 | **378.4** |
| L4 | 16 | 48 | 208 | 14.0 (max 15) | 270.0 | 4 + 3 (final msg 2 + nonce 1) + 2 + 1 = 10 | **280.0** |
| tail sumcheck (3 residual variables) | | | | | | 3 | **3** |
| **Opening total** | 222 queries | 778 | 3071 | 238.1 | **4087.1** | **115** | **4202.1** |

Sponge arithmetic: folds 6+4+4+4+4 = 22; OOD points 19+15+11+7 = 52 (dimension = log msg cols of the level, `G:1528`); OOD nonce permutations 4; final message 2 + 1 (yr_len 8, `G:1258-1268`); query squeezes 13+5+3+3+2 = 26; lambda 5; tail 3. 22+52+4+3+26+5+3 = 115.

Expected-cap arithmetic (hand-evaluated, e.g. L0, c = 7, Q = 112: j = 0..6 -> 1, 2, 4, 8, 15.99, 31.09, 53.03). The realised value is random per proof; I estimate its standard deviation at a few hashes across all five levels.

Same accounting for a **2-child node as a child** (mu = 24, rate 1/4): leaf+path = 4x112 + 3x(45+28+21+16) + 13x(112+45+28) + 12x(21+16) = 448 + 330 + 2405 + 444 = 3627; caps ~238.1; sponge 22 + 48 + 4 + 2 + 25 + 5 + 2 = 108; **total ~3973** [E/X].

### 5b. Reconciliation against the measured 5,185 KECCAK per child

Measured: KECCAK opcodes 2^13.347 (n=2), 2^14.344 (n=4), 2^14.928 (n=6), 2^15.342 (n=8) from results/T01 (`details` lines), giving (hand arithmetic) (2^15.342 - 2^13.347)/6 = 5,186 and (2^14.344 - 2^13.347)/2 = 5,187 per added child: matches the quoted 5,185 to within the 3-decimal rounding of the printed exponents (about +/-3 per child). The 5,185 itself was supplied in the task and I could not re-derive its last digits; the logs only print powers of two.

| Component (per added 250-XMSS child) | KECCAK | Tag | Basis |
|---|---|---|---|
| WHIR opening: leaf + path hashing | 3,849 | E | 5a |
| WHIR opening: cap authentication | 238.1 | X | 5a |
| WHIR opening: sponge (folds, OOD, nonces, squeezes, lambda, tail) | 115 | E | 5a |
| **PCS subtotal** | **4,202.1** | | |
| Child's claim-list digest rebuilt in the node: 250 claims x 64 B = 16,000 B | 118 | E | `G:4101-4201`; `floor(16000/136)+1` |
| This node's own claim-list digest, per child's share: 250 x 64 / 136 | 117.6 | E | `G:4468`, `statement.rs:32-36` |
| Child statement digest: (8 + 3 x 12) cells x 16 B = 704 B | 6 | E | `G:3973-4004, 4550`; `AG placeholders.rs:831-846` |
| `aggregate_claims` per child: 1 pending-rate perm + 12 for 52 padded words | 13 | E | `G:4611-4639` (DEFER_SIZE = 24, AGG_CHILD_PAD = 2) |
| verify_sub prelude (seed, announced sizes, root, 4 bus alphas, beta) | 8 | E | `G:3340-3426` |
| Bus GKR: binary layer 3 + radix-4 layers 11 x 5 + rounds sum (2j-1) = 121 | 179 | I | `G:1772-1944`; assumes bus depth mu_bus = 23 (see below) |
| Table sumcheck: 16 rounds + ~162 observed evaluation words / 4 + ~3 | ~60 | I (estimate) | `bus.rs:218-`, `G:2113-`; word count from table widths |
| Keccak GKR: 12 layers x 37 + prelude 6 + outputs 6 + inputs 10 + slices 16 | 482 | D | `G:2698-3093`; shape: tau_keccak = 16, y = 13, 47 product words, 11 local bits |
| Ring-switch challenges + lambda_cl | 6 | E | `G:3452-3476` |
| **Non-PCS subtotal** | **989.6** | | |
| **Analytic total** | **5,191.7** | | |
| Measured | 5,185 | | |
| **Residual (measured - analytic)** | **-6.7 (-0.13%)** | | |

How much to trust the near-zero residual: the PCS part and the five exact non-PCS rows (together about 4,500 of the 5,185) have no free parameters, apart from the expected cap size. The residual is small because the remaining ~735 (verify_sub's non-opening transcript) matches, but that line includes two inferred items: bus depth `mu_bus = log2_ceil(sum of push block sizes) = 23` (derived from push blocks: memory 2^21 + bytecode 2^19 + XOR/MUL 5 x 2^16 each + SET 3 x 2^16 + DEREF 5 x 2^15 + JUMP 5 x 2^14 + KECCAK 28 x 2^16 = 84.75 x 2^16 = 2^22.4, `layout.rs:107-440`, `bus.rs:107`) and the ~60 table-phase estimate. If either is off, the other would have to be off by the opposite amount, so treat the residual as "consistent to within about +/-30", not as proof that no hashing is missing. What the numbers do establish: **about 81% of the per-child KECCAK count (4,202 of 5,185) is the child's WHIR opening, and about 92% of that is Merkle leaf and path hashing (3,849) with the cap and sponge small.** Folding challenges, OOD points and query squeezes are only 115 permutations.

Per-round shares of the 5,185: L0 41.9%, L1 16.3%, L2 10.1%, L3 7.3%, L4 5.4%, tail 0.1%; non-PCS 19.1%.

### 5c. Cycle context (not KECCAK)

Measured 186.8k cycles per child (T01). 5,185 KECCAK instructions are only 2.7% of cycles (T01 `details`: KECCAK 2^13.347 = 2.7% at n=2); most cycles are MUL/XOR/DEREF in query decoding, row folding and residual evaluation. The hashing count above is the *committed-table* load (KECCAK table rows, hence q_keccak and the Keccak-GKR), not the cycle driver.

---------------------------------------------------------------------------------------------------

## 6. Deferred claims

### 6a. What each trace span does (`AG node.rs`, `proof.rs`, `deferred.rs`)

**"Replay children"** (`node.rs:121-144`). For each child the node calls `verifier::replay_unchecked` (`crates/verifier/src/lib.rs:176-178`, `walk(.., checked = false)`) on a single thread per child. This walks the child's transcript and reads out a `Summary` (announced sizes, `log_inv_rate`, the bytecode evaluation *point*, the Keccak scalar range, every query's Merkle path) **without checking anything**: no sumcheck, GKR, WHIR terminal, PoW, Merkle root or bytecode evaluation is verified (`lib.rs:173-178`; `transcript.rs:113-117`). It exists only to build the guest's witness (`child.rs:64-256`). Children are assumed verified by the caller (`node.rs:44-45, 114-120`); a bad child fails inside the guest, which verifies every child in the VM.

**"Batch deferred claims"** (`node.rs:273-284` -> `deferred.rs:244-352`, `aggregate_deferred_claims`; ~1.4 ms in T01). Each child brings **two** claims on the *stacked bytecode* polynomial: the **fresh** claim its verification raised (the bytecode point from the bus GKR, `summary.bytecode_point`, `node.rs:219-226`; value computed by `bytecode_sums`/`bytecode_value`, `deferred.rs:145-191`) and the **carried** claim the child itself deferred (`child.defer`). With `2n` claims, one challenge `lam` from a fresh transcript (`deferred.rs:255-276`, `RECURSION_AGG_LABEL`) batches them with powers `lam^(2i)`, `lam^(2i+1)`, and a single product sumcheck over `BYTECODE_VARS = 23` variables (10 low rounds on precomputed sums, 13 on the full row table, `deferred.rs:307-339`) reduces the lot to **one** claim `(r_bc, v_bc)` which the node stores as its own `defer` and publishes in its statement (`node.rs:318`). The guest mirrors it word for word (`G:4585-4689`, `aggregate_claims`) and checks the sumcheck terminal `bc_running == bytecode_star * bc_wsum` (`G:4684`) and that `bytecode_star` is whatever the claim reduces to; the prover supplies the value hint `bc_star_hint`.

**"Recompute deferred claims"** (`proof.rs:194-211`, `EthereumProof::verify`, ~3.4 ms in T01). Whoever finally verifies a *received* aggregate (the root consumer, natively) re-evaluates the stacked bytecode MLE at the transmitted point (`DeferredClaim::recompute_scalar`, `deferred.rs:50-60`, a pass over the 2^23-entry table) and requires it to equal the claim in the statement. The wire format carries only the point; the value is recomputed on parse (`proof.rs:116-123, 159-176`), so a lying value changes the statement the proof must satisfy rather than the claim anyone checks.

### 6b. What is deferred, from which polynomial, checked by whom

| Question | Answer | Citation |
|---|---|---|
| Which claims are deferred? | Evaluation claims of the **stacked bytecode** polynomial at points `(zeta_lo, alpha)` raised by the bus: one fresh + one carried per child | `deferred.rs:21-34`, `node.rs:217-226`, `G:3511-3516` |
| From which polynomial? | The **public, fixed** stacked bytecode table of the aggregation guest (`stacked_bytecode()`, `deferred.rs:112-115`). **Not** a child's committed witness `q`, and not any prover-committed polynomial. | `deferred.rs:109-115` |
| How batched? | Random linear combination (powers of one challenge) of all `2n` claims, reduced by one 23-variable sumcheck to a single claim | `deferred.rs:244-352`, `G:4585-4689` |
| Who discharges it? | Not in-circuit: the parent defers it again in its own public statement (`statement_digest(.., defer)`, `G:4578`); the final consumer **recomputes the evaluation natively** (`proof.rs:199-204`). A leaf defers the all-zeros point whose value is just the table's first entry (`deferred.rs:34-39, 69-76`; `G:4566-4574`). | |
| Where does the sumcheck check happen? | In the guest (`G:4684`), i.e. in-circuit, for the *batching*; only the final single evaluation is native | |

### 6c. Does the merge node already batch the children's PCS openings into fewer openings?

**NO.**

- Each child's stacked WHIR opening is verified **in full, in-circuit**, once per child, by `open_stacked` inside `verify_sub` (`G:3503`, `G:1434-1764`; call at `G:4554`): every fold, OOD claim, all five levels' queries with leaf hashes, Merkle paths, cap authentication, the induced-weight/residual evaluation and the terminal check (`check_opening_terminal`, `G:3509`). The 4,202 permutations in 5b are exactly that cost, and it grows linearly with n (186.8k cycles and ~5,185 KECCAK per added child, T01).
- The only quantity deferred and batched is the evaluation of a **public bytecode polynomial**, which is a different kind of object. It never touches the children's committed witnesses or PCS openings. Batching it removes the need for each child to evaluate the 2^23 bytecode table in-circuit; it does not reduce the number of WHIR openings the node verifies.
- The node's own proof has its own single opening (its stack), proven natively by the node prover, not batched with anything.
- Consequence for the accumulation design: replacing the n in-circuit WHIR verifications by deferred/accumulated claims (the WARP/Arc idea) would remove the 81% of per-child KECCAK work (and the associated MUL/XOR/DEREF decode cycles) that leanVM currently pays; nothing in the pinned commit does this.

---------------------------------------------------------------------------------------------------

## 7. What could not be found or was not done

- `eta` per level and the realised `m`: not printed anywhere readable without running the cargo test `print_whir_query_counts` (`WC:1006-1037`). Order of magnitude hand-checked only.
- Bus depth `mu_bus`, table evaluation word count `N_COL_EVALS`, `N_FRESH`: placeholders computed at guest compile time (`AG placeholders.rs`), not logged; `mu_bus = 23` and ~60 table permutations are inferred (5b).
- Realised cap node counts: random per proof; only the expectation is given.
- The residual of -6.7 should be re-checked once T03 releases the machine: instrument or count KECCAK per `verify_sub` phase and the realised cap hashes (a single trace run with a counter, no code change to leanVM semantics).
- No Rust or Python was executed; all arithmetic was done by hand and is reproducible from the formulas given.

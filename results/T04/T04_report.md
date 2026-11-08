=== RESULT REPORT T04 ===
Status: done
Machine: Apple M2 (4 performance + 4 efficiency cores, 8 total), 8 GiB RAM, macOS 26.5.2 (Darwin 25.5.0, arm64). Taken from results/T00/machine.txt. Nothing heavy ran on it during this task.
Toolchain: none used. No cargo, rustc, lake or Python was run (T03 was benchmarking). All arithmetic was done by hand. (Installed default rustc is 1.88.0 per T00; irrelevant here.)
Repo state: leanMultisig `df7d122abbe25cf12e5c8ae992ce6d3505f75372`, branch `research/baseline`, working tree clean before and after (`git status --short` empty). Nothing edited in `upstream/`. Workspace files written: `results/T04/pcs_facts.md`, `results/T04/T04_report.md`, and an appended entry in `NOTES.md`.

Evidence tags used below: **[E]** exact, read from code or a tool-printed number. **[X]** expectation over random query positions, computed by hand from a closed form. **[D]** derived by hand from code plus shapes printed in the T00/T01 logs. **[I]** inferred, needs a shape no log prints (estimate).
Path abbreviations: `W` = `crates/verifier/src/whir.rs`, `WC` = `crates/pcs/src/whir_config.rs`, `G` = `crates/rec_aggregation/guests/lean_ethereum.py`, `AG` = `crates/rec_aggregation/src/aggregation/`.

## Summary
- Each proof has exactly one stacked witness commitment `q` and one WHIR opening. Leaf (250 XMSS): mu = 25. Two-child node: mu = 24. The leaf's column sum is 18.02 M words, matching the tool's own `TOTAL_COMMITTED` 2^24.103.
- Rate-1/4 openings have 5 levels, folds 6,4,4,4,4. Queries are `[112,45,28,21,16]` for both mu = 24 and mu = 25. OOD samples: 0 at L0, 1 at L1..L4. Query-phase grinding: 17 bits at every level. No fold-challenge grinding.
- Soundness regime: Johnson list decoding with per-level slack eta (BCHKS25 Thm 4.6) plus OOD binding, round-by-round 128-bit target (each transition individually, not a total). Unique-decoding code exists only under `#[cfg(test)]`.
- Of the measured 5,185 KECCAK per child, about 4,202 (81%) are the child's WHIR opening: 3,849 leaf and path hashes, about 238 cap hashes [X], 115 sponge permutations. Analytic total 5,191.7 vs measured 5,185, residual -6.7 (-0.13%); I would put the uncertainty at about +/-30 because two inputs are inferred.
- Deferred claims are evaluations of the public stacked bytecode polynomial only (two per child, batched by one 23-variable sumcheck, discharged natively by the final verifier). **The merge node does NOT batch the children's PCS openings: each is verified in full, in-circuit.**

## Results

### R1. Committed objects (step 1)

Shapes used:

| Object | Leaf (child), 250 XMSS, rate 1/4 | Merge node, 2 children, rate 1/4 | Source |
|---|---|---|---|
| Placed words (`TOTAL_COMMITTED`) | 2^24.103 = 18.02 M | 2^23.842 = 14.7 M | results/T00/aggregate_xmss250_lir2.log:154; results/T01/recursion_n2_m250_leaflir2_lir2.log |
| Stack size mu = log_n | 25 | 24 | `crates/verifier/src/layout.rs:547`, window 15..=28 at `:87-88` |
| Lane blocks carrying data (of 64) | 35 (encoder row padded to 40) | 58 (row 64) | `crates/pcs/src/whir.rs:129-141`; trace `lanes: 40` / `lanes: 64` |
| L0 NTT log-domain | 21 | 20 | trace `kind: "base encode"` |

Contents of the stacked polynomial `q`, leaf, 250 XMSS [D]:

| Polynomial (K-valued multilinear) | Count x size | Words | Source |
|---|---|---|---|
| MEMORY_0..2 (three K limbs of each F192 memory cell) | 3 x 2^21 | 6,291,456 | `layout.rs:93-98, 524-531` |
| MEMORY_FINAL_COUNTERS | 1 x 2^21 | 2,097,152 | same |
| BYTECODE_FINAL_COUNTERS | 1 x 2^19 | 524,288 | same |
| q_keccak (bit-packed Keccak states, 64 bits per K word; also hosts 14 spare-slot KECCAK-table columns) | 2^(16+6) | 4,194,304 | `layout.rs:523, 343-367` |
| XOR table, 15 columns | 15 x 2^16 | 983,040 | `layout.rs:371` |
| MUL table, 15 columns | 15 x 2^16 | 983,040 | `layout.rs:371` |
| SET table, 8 columns | 8 x 2^16 | 524,288 | `layout.rs:372` |
| DEREF table, 15 columns | 15 x 2^15 | 491,520 | `layout.rs:374` |
| JUMP table, 14 columns | 14 x 2^14 | 229,376 | `layout.rs:376` |
| KECCAK table's other committed columns (26 blocks) | 26 x 2^16 | 1,703,936 | `layout.rs:538-545` |
| **Sum** | | **18,022,400** | matches 2^24.103 |

Merkle commitments of the WHIR opening, leaf (mu = 25, rate 1/4) [D]:

| Commit | Content | Symbols | Interleaving m (lanes per Merkle leaf) | Leaf bytes | Domain (leaves) | Rate |
|---|---|---|---|---|---|---|
| L0 | stacked `q` | GF(2^64) | 64 (35 carry data) | 512 | 2^21 | 1/4 |
| L1 | `q` folded by 6 (19 variables) | GF(2^192), 3 words each | 16 | 384 | 2^20 | 2^-5 |
| L2 | folded by 4 more | GF(2^192) | 16 | 384 | 2^19 | 2^-8 |
| L3 | folded by 4 more | GF(2^192) | 16 | 384 | 2^18 | 2^-11 |
| L4 | folded by 4 more | GF(2^192) | 16 | 384 | 2^17 | 2^-14 |
| `yr` | residual, 3 variables left | GF(2^192), in the clear | – | – | 8 elements | – |

Node (mu = 24): domains 2^20, 2^19, 2^18, 2^17, 2^16; residual 4 elements. Rate-1/2 node: ladder rates 1,4,7,10,13, domains 2^19..2^15 (matches the printed NTT logs).

Ring switching: the Keccak GKR (24 rounds, 2 segments of depth 12) ends in 64 bit-slice claims of the bit-MLE of q_keccak (`crates/verifier/src/keccak.rs:1-10`; guest `G:2927-3093`). Ring switching (`crates/verifier/src/ring_switch.rs:1-54`, call site `crates/verifier/src/lib.rs:316-326`, prover `crates/pcs/src/ring_switch.rs`, guest `G:3448-3467`) turns them into one claim `<rs_eq_ind, q_keccak> = T` on the packed K polynomial, i.e. on the q_keccak region of the stack. That claim leads the batch (power lambda^0, weighted by the placement selector, `lib.rs:322-327`); all other column claims follow with powers of the same challenge (`G:3476-3489`), and one WHIR run proves the combined claim (`crates/pcs/src/stack_open.rs:1-60`).

### R2. Per-round opening (step 2)

Parameters are tabulated in the verifier at `W:18-23` (`WHIR_QUERIES[log_inv_rate-1][log_n-15]`), the rate-1/4 row is `W:20`. `W:51-52` checks the entry length against the ladder length. A test pins the table to the Rust search (`crates/leanvm_core/tests/verifiers/whir_query_table.rs`). The guest uses `pcs::whir::config_for_rate` (`AG child.rs:26-37`). Rust search: `WC:884-940` calling `WC:607-675`.

Leaf, mu = 25, rate 1/4:

| Level | Fold k | log rate | log msg cols | Depth | Queries | OOD | Grind bits | Guest cap depth | Path hashes / query | Leaf (bytes) | Positions / squeeze | Squeezes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 6 | 2 | 19 | 21 | 112 | 0 | 17 | 7 | 14 | 64 words (512) | 9 | 13 |
| L1 | 4 | 5 | 15 | 20 | 45 | 1 | 17 | 6 | 14 | 48 words (384) | 9 | 5 |
| L2 | 4 | 8 | 11 | 19 | 28 | 1 | 17 | 5 | 14 | 48 (384) | 10 | 3 |
| L3 | 4 | 11 | 7 | 18 | 21 | 1 | 17 | 5 | 13 | 48 (384) | 10 | 3 |
| L4 | 4 | 14 | 3 | 17 | 16 | 1 | 17 | 4 | 13 | 48 (384) | 11 | 2 |
| final | 3 residual variables | | | | `yr` = 8 elements | | | | | | | |

Merge node, 2 children, mu = 24, rate 1/4:

| Level | Fold k | log rate | log msg cols | Depth | Queries | OOD | Grind bits | Guest cap depth | Path hashes / query | Leaf (bytes) | Positions / squeeze | Squeezes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 6 | 2 | 18 | 20 | 112 | 0 | 17 | 7 | 13 | 64 words (512) | 9 | 13 |
| L1 | 4 | 5 | 14 | 19 | 45 | 1 | 17 | 6 | 13 | 48 (384) | 10 | 5 |
| L2 | 4 | 8 | 10 | 18 | 28 | 1 | 17 | 5 | 13 | 48 (384) | 10 | 3 |
| L3 | 4 | 11 | 6 | 17 | 21 | 1 | 17 | 5 | 12 | 48 (384) | 11 | 2 |
| L4 | 4 | 14 | 2 | 16 | 16 | 1 | 17 | 4 | 12 | 48 (384) | 12 | 2 |
| final | 2 residual variables | | | | `yr` = 4 elements | | | | | | | |

Rate-1/2 node (mu = 24), for reference: queries `[224,56,32,23,17]` (`W:19`), ladder rates 1,4,7,10,13.

Formulas: depth = log_msg_cols + log_inv_rate (`W:185`, `WC:146-148`); rate step = fold - reduction, reduction 3 after the first fold and 1 after each later one (`W:41-46`, `WC:288-301`); cap depth = min(ceil(log2 queries), depth) (`AG child.rs:39-41`); path hashes = depth - cap depth; positions per squeeze = floor(192/depth) (`W:72`); squeezes = ceil(queries / positions per squeeze) (`AG placeholders.rs:604`). Fold schedule `WC:67-68`; residual cap `WC:86`.

Two meanings of "cap": the guest cap is the shared top of each tree, authenticated once per level (`G:1163-1214`), queries then hash depth - cap levels (`G:1312-1347`), queries are not deduplicated. `CutTree` (`crates/pcs/src/merkle.rs:297-312`, CUT = 4, from 2^12 leaves) is a prover-memory optimisation, not a protocol parameter.

### R3. Soundness regime (step 3)

| Item | Finding | Source |
|---|---|---|
| Regime | Johnson list decoding, radius gamma = 1 - sqrt(rho) - eta, with OOD binding. Not unique decoding (UDR helpers are `#[cfg(test)]`). No proximity-gap conjecture. | `WC:307-326, 161-176, 472-476` |
| Theorem | BCHKS25 Thm 4.6 (list correlated agreement, `thm:mca-johnson`), list parameter m = max(ceil(sqrt(rho)/eta), 3) | `WC:421-458`; `doc/leanvm/body/b-polynomial-commitment-scheme.tex:176` |
| Interleaving | Fold error of a 2^l-row word equals the two-row MCA error (Jo, ePrint 2026/891 Thm 4.4) | `WC:431-433` |
| List size | L <= 1/(2 eta sqrt(rho)) | `WC:478-503` |
| Analysis | Round-by-round: every verifier-challenge transition individually >= 128 bits; the FS error per RO query is the MAX of the entries, not the sum | `WC:25-27, 36-38, 870-875, 899-904` |
| Target | SECURITY_BITS = 128; analysis field q = 2^192 | `WC:38, 410` |
| Grinding | 17 bits per level, between root and query sampling; queries close the remaining 111 bits. Checked at every level including the last. | `WC:57-60`; `W:184`; `G:889-915, 1555-1558` |
| Fold grinding | none | `WC:314-318, 628-634` |
| Query rule | queries = ceil(111 / per_q), per_q = log2(1/(sqrt(rho)+eta)), rho the reduced rate (2^c-1)/2^(c+r) | `WC:462-466, 636-643` |
| Margin eta | per level, chosen by search over m = 3..4096 minimising queries subject to proximity-gap, OOD and list-unioned algebraic terms all >= 128 bits; ties keep smallest m | `WC:607-675` |
| OOD | s samples, smallest s in 1..8 with s(192 - log2 mu) - (2 log2 L - 1) >= 128 (test asserts s = 1 for L>=1); L0 bound by the opening's own evaluation claim, so 0 | `WC:554-576, 645-652, 976-1004` |
| Cross-check | README "128-bit ROM (64-bit QROM) soundness", "no proximity gap conjecture" (`README.md:47-48`); eprint 2026/2424 §7 "Johnson-bound guarantees": both consistent with the code. I did not re-derive the proofs. | |

Hand sanity check (estimate, my arithmetic): L0 at rate 1/4 with 112 queries needs per_q >= 111/112, so eta of order 2-3e-3 (m about 160..270); the BCHKS25 term a is then about 2^60..2^64 against q = 2^192, i.e. 128+ bits. Actual eta values are not printed anywhere readable without running `print_whir_query_counts` (`WC:1006-1037`, a cargo test).

Caveat: "128-bit" is a per-transition RBR target, not 128 bits of total interactive soundness. The accumulation scheme's parameters should say which notion they match.

### R4. Hashing costs (step 4)

Keccak-256, rate 136 B, padding `0x01..0x80`; permutations per call = floor(len/136) + 1. One `KECCAK` VM instruction = one permutation (`crates/lean_compiler/zkDSL.md:451-462`). Sources: `crates/fiat_shamir/src/merkle.rs:24-38`, `crates/verifier/src/hash.rs:8, 79-97`.

| Call | Input bytes | Keccak-f per call | Source |
|---|---|---|---|
| 2-to-1 node H(left ‖ right) | 64 | 1 | `crates/verifier/src/merkle.rs:37-42` |
| L0 leaf (64 K-words) | 512 | 4 | `W:194`; `AG placeholders.rs:766-779` (32 cells x 16 B) |
| L>=1 leaf (16 lanes x 3 K-words) | 384 | 3 | same (24 cells) |
| Digest | 32 B, carried as two 128-bit halves | – | `crates/fiat_shamir/src/merkle.rs:16-22` |

No separate leaf/node domain tag; separation is by length only.

Fiat-Shamir sponge (`crates/fiat_shamir`, mirrored at `crates/verifier/src/transcript.rs:32-90` and `G:592-688`): Keccak-f[1600] duplex, overwrite mode, rate = lanes 0..16, capacity = lanes 16..25. An E element takes 4 lanes (3 limbs + tag; DS_OBSERVE = 1, DS_POW_NONCE = 4), so 4 scalars per permutation, i.e. 0.25 permutation per absorbed scalar. Every challenge is one permutation of its own (first 3 lanes of the output). Init: 1 permutation. Grinding: nonce absorbed with its own tag, then one squeeze; verifier cost 1 permutation, prover about 2^17 expected. Query positions: floor(192/depth) per squeeze.

### R5. Guest accounting and analytic KECCAK count (step 5)

Where the costs sit (all in `G`): `verify_sub` 3325-3517; `open_stacked` 1434-1764; fold rounds `opening_fold` 1220-1233 (loop 1497-1502); OOD point 1236-1247 (call 1525-1530); final message 1250-1269 (call 1505); grind check 889-915 (call 1555); query squeezes 1560-1580 and `decode_query_windows` 825-886; lambda squeeze 1587-1590; cap authentication `verify_merkle_cap` 1163-1214 (call 1602); per-query leaf hash `opening_query` 1391-1393; path hashing `walk_window` 1296-1309, `walk_path` 1312-1347, `opening_queries` 1397-1419; tail rounds 1643-1660; rest of `verify_sub`: bus GKR 1772-1944, tables 2113-~2540, Keccak GKR 2698-3093, ring switch 3448-3476; per child in `main`: claim-list digest 4101-4201, statement digest 3973-4004 (call 4550), `aggregate_claims` 4585-4689.

Per-round analytic KECCAK of the WHIR opening, leaf child, mu = 25, rate 1/4:

| Level | Q | Leaf hash [E] | Path hashes [E] | Cap hashes [X] | Merkle subtotal | Sponge perms [E] | Level total |
|---|---|---|---|---|---|---|---|
| L0 | 112 | 448 (4 x 112) | 1568 (14 x 112) | 115.1 (max 127) | 2131.1 | 6 folds + 19 OOD + 1 nonce + 13 squeezes + 1 lambda = 40 | 2171.1 |
| L1 | 45 | 135 | 630 | 54.4 (max 63) | 819.4 | 4 + 15 + 1 + 5 + 1 = 26 | 845.4 |
| L2 | 28 | 84 | 392 | 28.2 (max 31) | 504.2 | 4 + 11 + 1 + 3 + 1 = 20 | 524.2 |
| L3 | 21 | 63 | 273 | 26.4 (max 31) | 362.4 | 4 + 7 + 1 + 3 + 1 = 16 | 378.4 |
| L4 | 16 | 48 | 208 | 14.0 (max 15) | 270.0 | 4 folds + 3 final msg and nonce + 2 + 1 = 10 | 280.0 |
| tail | | | | | | 3 | 3 |
| **Opening** | 222 | 778 | 3071 | 238.1 | 4087.1 | 115 | **4202.1** |

Expected cap hashes per level: sum over j = 0..c-1 of 2^j (1 - (1 - 2^-j)^Q), c = cap depth (root always hashed, other nodes only if flagged, `G:1200-1208`). Hand-evaluated; the realised count is random per proof.
Sponge sum: folds 22, OOD points 19+15+11+7 = 52 (`G:1528`), OOD nonces 4, final message 2+1 (`G:1258-1268`), query squeezes 26, lambda 5, tail 3: total 115.

Two-child node as a child (mu = 24): leaf+path 3,627, cap about 238, sponge 108, total about 3,973.

Reconciliation against the measured per-child KECCAK. Measured KECCAK (T01 `details` lines): 2^13.347 (n=2), 2^14.344 (n=4), 2^14.928 (n=6), 2^15.342 (n=8). By hand: (2^15.342 - 2^13.347)/6 = 5,186 and (2^14.344 - 2^13.347)/2 = 5,187 per added child. The logs print only powers of two, so the quoted 5,185 is good to about +/-3 and I could not re-derive its last digits.

| Component per added 250-XMSS child | KECCAK | Tag | Basis |
|---|---|---|---|
| WHIR opening: leaf + path hashing | 3,849 | E | table above |
| WHIR opening: cap authentication | 238.1 | X | table above |
| WHIR opening: sponge | 115 | E | table above |
| **PCS subtotal** | **4,202.1** | | |
| Child's claim-list digest rebuilt (250 x 64 B = 16,000 B) | 118 | E | `G:4101-4201` |
| Node's own claim-list digest, per-child share | 117.6 | E | `G:4468` |
| Child statement digest ((8 + 3 x 12) cells x 16 B = 704 B) | 6 | E | `G:3973-4004`; `AG placeholders.rs:831-846` |
| `aggregate_claims`, per child (52 padded words) | 13 | E | `G:4611-4639` |
| `verify_sub` prelude | 8 | E | `G:3340-3426` |
| Bus GKR (binary layer 3 + 11 radix-4 layers x 5 + 121 rounds) | 179 | I | `G:1772-1944`; assumes bus depth 23 |
| Table sumcheck and evaluations (16 rounds + about 162 words / 4 + about 3) | about 60 | I | `bus.rs:218-`, `G:2113-` |
| Keccak GKR (12 layers x 37 + prelude 6 + outputs 6 + inputs 10 + slices 16) | 482 | D | `G:2698-3093`; tau = 16, 13 rounds per layer, 47 product words |
| Ring-switch challenges + lambda_cl | 6 | E | `G:3452-3476` |
| **Non-PCS subtotal** | **989.6** | | |
| **Analytic total** | **5,191.7** | | |
| Measured | 5,185 | | |
| **Residual (measured - analytic)** | **-6.7 (-0.13%)** | | |

How far to trust the small residual: the PCS rows and the exact non-PCS rows (about 4,500 of the 5,185) have no free parameters apart from the expected cap size. The remaining about 735 (non-opening `verify_sub` transcript) includes two inferred items: bus depth 23 (derived from push-block sizes: memory 2^21 + bytecode 2^19 + XOR/MUL 5 x 2^16 each + SET 3 x 2^16 + DEREF 5 x 2^15 + JUMP 5 x 2^14 + KECCAK 28 x 2^16 = 84.75 x 2^16 = 2^22.4; `layout.rs:107-440`, `bus.rs:107`) and the table-phase estimate. Treat the residual as consistent to about +/-30, not as proof that nothing is missing.

What the numbers establish: about 81% of the per-child KECCAK count (4,202 of 5,185) is the child's WHIR opening, and about 92% of that is Merkle leaf and path hashing (3,849). Shares of the 5,185: L0 41.9%, L1 16.3%, L2 10.1%, L3 7.3%, L4 5.4%, tail 0.1%, non-PCS 19.1%. KECCAK instructions are only 2.7% of the 186.8k cycles per child (T01); the cycle cost is mostly MUL/XOR/DEREF in query decoding, row folding and residual evaluation.

### R6. Deferred claims (step 6)

**Replay children** (`AG node.rs:121-144`): runs `verifier::replay_unchecked` (`crates/verifier/src/lib.rs:176-178`, `walk(.., checked = false)`) single-threaded per child. It reads a `Summary` (announced sizes, log_inv_rate, bytecode evaluation point, Keccak scalar range, every query's Merkle path) and checks nothing: no sumcheck, GKR, WHIR terminal, PoW, Merkle root or bytecode evaluation (`lib.rs:173-178`; `transcript.rs:113-117`). Its only purpose is to build the guest witness (`AG child.rs:64-256`). Children are assumed verified by the caller (`node.rs:44-45, 114-120`); a bad child fails inside the guest.

**Batch deferred claims** (`node.rs:273-284` -> `AG deferred.rs:244-352`; about 1.4 ms in T01): each child brings two claims on the stacked bytecode polynomial, the fresh one its verification raised (`node.rs:219-226`, value via `deferred.rs:145-191`) and the one it carried (`child.defer`). One challenge lam from a fresh transcript (`deferred.rs:255-276`) batches the 2n claims with powers lam^(2i), lam^(2i+1). One sumcheck over BYTECODE_VARS = 23 variables (10 low rounds on precomputed sums, 13 on the full row table, `deferred.rs:307-339`) reduces them to a single claim, stored as the node's own `defer` and published in its statement (`node.rs:318`). The guest mirrors this (`G:4585-4689`) and checks the terminal at `G:4684`.

**Recompute deferred claims** (`AG proof.rs:194-211`, `EthereumProof::verify`; about 3.4 ms in T01): the final consumer re-evaluates the 2^23-entry stacked bytecode at the transmitted point natively (`DeferredClaim::recompute_scalar`, `deferred.rs:50-60`) and requires it to equal the claim in the statement. The wire carries only the point; the value is recomputed on parse (`proof.rs:116-123, 159-176`).

| Question | Answer | Citation |
|---|---|---|
| Which claims are deferred? | Evaluations of the stacked bytecode polynomial, one fresh and one carried per child | `deferred.rs:21-34`, `node.rs:217-226`, `G:3511-3516` |
| From which polynomial? | The public, fixed stacked bytecode table of the aggregation guest (`stacked_bytecode()`), not a child's committed witness and not any prover-committed polynomial | `deferred.rs:109-115` |
| How batched? | Powers of one challenge, reduced by one 23-variable sumcheck to a single claim | `deferred.rs:244-352` |
| Who checks? | The batching sumcheck in-circuit (`G:4684`); the single resulting evaluation is re-deferred in the parent's statement and finally recomputed natively. A leaf defers the all-zeros point (value = first table entry). | `proof.rs:199-204`; `deferred.rs:34-39, 69-76`; `G:4566-4574` |

**Does the merge node already batch the children's PCS openings into fewer openings? NO.**
- Each child's stacked WHIR opening is verified in full in-circuit, once per child, by `open_stacked` inside `verify_sub` (`G:3503`, `G:1434-1764`, called at `G:4554`): all folds, OOD claims, all five levels' queries with leaf hashes, Merkle paths and cap authentication, the induced-weight and residual evaluation, and the terminal check (`G:3509`). Its cost, about 4,202 permutations (R5), grows linearly in n (186.8k cycles and about 5,185 KECCAK per added child).
- What is batched is the evaluation of a public bytecode polynomial. It never touches the children's committed witnesses or PCS openings, and batching it does not reduce the number of WHIR openings the node verifies.
- The node's own proof has its own single opening, proven natively by the node prover, batched with nothing.
- For the accumulation design: replacing the n in-circuit WHIR verifications by deferred or accumulated claims would remove about 81% of the per-child KECCAK work and the associated decode cycles. Nothing at the pinned commit does this.

## Commands run
Read-only, in this order (grouped):
1. `ls`, `cat NOTES.md`, `ls results`, `git rev-parse HEAD`, `git branch --show-current`, `git status --short`, `wc -l` on the relevant source files (workspace orientation).
2. `cat 02_RELAY_PROTOCOL.md`, `ls results/T03`, `ls results/T01`.
3. File reads of `crates/pcs/src/whir_config.rs`, `whir.rs`, `lib.rs`, `merkle.rs` (grep), `stack_open.rs`, `ring_switch.rs` (header); `crates/verifier/src/whir.rs`, `merkle.rs`, `hash.rs`, `transcript.rs`, `lib.rs`, `layout.rs`, `ring_switch.rs`, `bus.rs`, `keccak.rs`; `crates/fiat_shamir/src/merkle.rs`, `lib.rs` (grep); `crates/rec_aggregation/src/aggregation/node.rs`, `proof.rs`, `deferred.rs`, `child.rs`, `placeholders.rs`; `crates/rec_aggregation/guests/lean_ethereum.py` (many ranges); `crates/lean_compiler/zkDSL.md`, `snark_lib.py`; `doc/leanvm/body/04-committing-the-witness.tex`, `b-polynomial-commitment-scheme.tex` (grep); `README.md` (grep); `bins/leanvm/src/benchmark.rs`.
4. `grep -rn` (with `--exclude-dir='target*'`) for `MIN_STACKED_LOG|MAX_STACKED_LOG`, `keccak_cells`, `merkle_cap_depth|cap_depth`, `KECCAK_SEG_LOG|KECCAK_PROD_BITS`, etc.
5. `grep -a` with ANSI stripping on `results/T00/aggregate_xmss250_lir2.log`, `results/T01/rebuild_aggregate_xmss250_lir2.log`, `results/T01/recursion_n{2,4,6,8}_m250_leaflir2_lir{1,2}.log` for `log_domain`, `cycles`, `details`.
6. Wrote `results/T04/pcs_facts.md` and this report; appended the T04 entry to `NOTES.md` with `cat >> NOTES.md`; final `git status --short | wc -l` on `upstream/leanMultisig` returned 0.

No cargo, rustc, Python, build or benchmark was executed.

## Raw output
Only logged numbers were used as measured inputs (copied from existing logs, ANSI stripped):

```
results/T00/aggregate_xmss250_lir2.log
  NTT kind: "base encode" | log_domain: 21 | lanes: 40
  NTT kind: "extension encode" | log_domain: 20 | lanes: 16   (then 19, 18, 17)
  cycles (VM steps) : 219,994 = 2^17.747
  details : XOR 2^15.518 (21.3%)  KECCAK 2^15.509 (21.2%)  SET 2^15.435 (20.1%)  MUL 2^15.379 (19.4%)  DEREF 2^14.833 (13.3%)  JUMP 2^13.333 (4.7%)  MEMORY 2^20.576  BYTECODE 2^18.899  TOTAL_COMMITTED 2^24.103
  proof size : 220.0 KiB

results/T01/recursion_n2_m250_leaflir2_lir2.log
  NTT kind: "base encode" | log_domain: 20 | lanes: 64
  NTT kind: "extension encode" | log_domain: 19, 18, 17, 16
  cycles : 392,988 = 2^18.584
  details : MUL 2^17.132 (36.5%)  XOR 2^16.681 (26.7%)  DEREF 2^16.105 (17.9%)  SET 2^15.213 (9.7%)  JUMP 2^14.637 (6.5%)  KECCAK 2^13.347 (2.7%)  MEMORY 2^19.379  BYTECODE 2^18.899  TOTAL_COMMITTED 2^23.842
  INFO Replay children [ 16.8ms ]   Batch deferred claims [ 1.40ms ]   Bytecode batch [ 1.38ms ] vars: 23

results/T01/T01_report.md (table rows, outer rate 2)
  n=4: KECCAK 2^14.344, TOTAL_COMMITTED 2^24.791
  n=6: KECCAK 2^14.928, TOTAL_COMMITTED 2^25.036
  n=8: KECCAK 2^15.342, TOTAL_COMMITTED 2^25.778
```

Table literal at `crates/verifier/src/whir.rs:19-22` (rate 1/4 is the second row, line 20):
```
[&[111,45], &[112,45,27], &[112,45,28], &[112,45,28], &[112,45,28], &[112,45,28,20], &[112,45,28,20], &[112,45,28,21], &[112,45,28,21], &[112,45,28,21,16], &[112,45,28,21,16], &[112,45,28,21,16], &[112,45,28,21,16], &[112,45,28,21,16,13]]
index = log_n - 15  ->  mu = 24: index 9, mu = 25: index 10, both [112,45,28,21,16]
```

## Files changed or created
- `results/T04/pcs_facts.md`: full write-up of steps 1-6 with file:line citations and evidence tags.
- `results/T04/T04_report.md`: this report.
- `NOTES.md`: appended a dated T04 entry.
- Nothing in `upstream/`, `proto/` or `lean/` was touched.

## Problems and deviations
- Inferred rather than read: bus depth 23 and about 60 table-phase permutations (neither is logged). If either is off, the -6.7 residual would hide an equal and opposite error.
- The cap-hash count (238.1) is an expectation over random queries; a real proof differs by a few hashes. The sponge, leaf and path counts are exact.
- Per-level eta values were not obtained: they need the cargo test `print_whir_query_counts`, which the task forbade. Only an order-of-magnitude hand check is given.
- The recursion benchmark's leaf keys differ from the `aggregate` benchmark's, so row counts may differ slightly; mu = 25 is robust (2^24.103 is well inside [2^24, 2^25]).
- The 5,185 figure came from the task. The logs print KECCAK only as powers of two, so I could confirm it only to about +/-3.
- All arithmetic was by hand (the task allowed no program runs); the formulas are in the report so it is reproducible.

## Suggested next step
Once T03 frees the machine, run one traced recursion node with a per-phase KECCAK counter (no semantic change) to replace the inferred bus-depth and table counts with measured ones and obtain the realised cap-hash count. The design question this feeds is replacing the per-child in-circuit WHIR verification: it is about 81% of the per-child KECCAK work and nothing at the pinned commit amortises it.
=== END REPORT ===

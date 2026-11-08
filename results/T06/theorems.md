# T06 step 4: proximity theorems as leanVM uses them

Sources (paths relative to `upstream/leanMultisig/`, commit df7d122ab):
`TEX` = `doc/leanvm/body/b-polynomial-commitment-scheme.tex`, `WC` = `crates/pcs/src/whir_config.rs`, bib = `doc/leanvm/refs.bib:78-93`.
The papers themselves were not opened (not fetched, per workspace rules); everything below is the statement **as leanVM's annex and code state it**, paraphrased.

## BCHKS25 Thm 4.6 (Ben-Sasson, Carmon, Haböck, Kopparty, Saraf, "On Proximity Gaps for Reed-Solomon Codes", ePrint 2025/2055)

Annex label `thm:mca-johnson`, TEX:176-185; code `paper_thm_ca_johnson_log_a`, WC:421-447, and `johnson_m_param`, WC:449-458.

Paraphrase. Take a Reed-Solomon code over E with block length n and dimension k. Use the *slightly reduced rate* rho = (k-1)/n, because BCHKS25 parametrize by the degree bound, not the dimension (TEX:177; WC:412-419 `reduced_rate`). Pick a radius gamma in (0, 1 - sqrt(rho)), write the Johnson slack as eta = 1 - sqrt(rho) - gamma, and set the integer parameter m = max(ceil(sqrt(rho)/eta), 3). Then for **every two-row word** U, the probability over a uniform fold challenge s in E of the following event is at most a/|E|:

- "there is an agreement set S with |S| >= (1-gamma)n on which the fold U_s agrees with the code, but U itself does not agree with the interleaved code on S" (this is the mutual-correlated-agreement event),

where a = [2(m+1/2)^5 + 3(m+1/2) gamma rho] / (3 rho^{3/2}) * n + (m+1/2)/sqrt(rho).

What it depends on: n (block length), rho (reduced rate, so code dimension and block length), eta (through m and gamma). It does **not** mention:
- the number of rows: it is stated for two rows;
- the number of folded variables;
- the field size, except as the denominator |E|;
- any generator degree. The fold is the affine line U[0] + s U[1]. In characteristic 2 the annex's (1-s)U[0] + s U[1] is an invertible change of pair (TEX:158 footnote).

leanVM-specific choices:
- It uses the **list** form of m, ceil(sqrt(rho)/eta). The annex footnote and WC:449-455 point out that the non-list Thm 1.5 has ceil(sqrt(rho)/(2 eta)), and that Flock's Thm 8 quotes 4.6 with the non-list parameter. The test at WC:962-973 pins this.
- |E| = 2^192 (`ANALYSIS_LOG_Q`, WC:409-410) at **every** level, including L0. At L0 the committed symbols are K = GF(2^64), but the fold challenge is drawn from E.
- The eta search keeps 192 - log2 a >= 128 at every level, with no fold-challenge grinding (WC:313-318, 629-634).

## Jo, ePrint 2026/891, Thm 4.4 ("Interleaving Stability for Mutual Correlated Agreement and Curve Decodability")

Used in annex `lem:fold-list`, TEX:189-205. The code comment is at WC:431-433 and the "Why" comment at WC:682.

Paraphrase as the annex states it (TEX:196). Take a code that is linear over a field F, and a fold whose two coefficients are functions of a seed drawn uniformly from a set of at most |F| elements. Then the MCA error of **every row interleaving** of the code equals the MCA error of the code itself, at every radius.

leanVM checks the two hypotheses with F = E (TEX:197-200):
- RS[E, S, k] is an E-subspace even though its domain S lies in K, so every row interleaving is E-linear too.
- The seed is the fold challenge s drawn from E itself, and the coefficients are (1-s, s).

How leanVM uses it (annex `lem:fold-list`, TEX:189-194; proof at TEX:204). Take an interleaved word with 2^ell rows, ell >= 1, and fold one variable. The probability that the list of the fold differs from the fold of the list is at most the same epsilon = a/|E| as for a two-row word. The proof reads the 2^ell-row word as a two-row word over the 2^(ell-1)-fold interleaved code and applies Jo Thm 4.4 to it. The annex states this outright: **"The bound does not grow with ell"**, and a row-by-row union bound would instead cost 2^(ell-1) epsilon (TEX:196, 201).

What it depends on:
- The number of rows: **no**. The error is invariant under row interleaving.
- The number of folded variables: **no, per fold challenge**. Each of the ell_i fold challenges of a level is one RBR transition with error 2L_i/|E| + epsilon_i (TEX:144, 239-259). B_2 applies the lemma to the 2^(ell_i - j + 1)-row matrix at round j (TEX:251).
- Generator degree: the annex only uses the degree-1 (affine-line) fold with seed set E. No curve or higher-degree generator appears, so I found no generator-degree dependence anywhere in leanVM's use. Jo's title also mentions "curve decodability", which suggests the paper covers higher-degree generators as well. I have not verified that, since I did not read the paper.

## Johnson bound (annex `thm:johnson-interleaved`, TEX:64-65, proof TEX:299-319; code WC:478-503)

For every interleaved word of a rate-rho RS code and every eta in (0, 1 - sqrt(rho)), the list at radius 1 - sqrt(rho) - eta has at most 1/(2 eta sqrt(rho)) members. The proof works for any alphabet, so it holds unchanged for interleaved codes: interleaving keeps the relative distance and only enlarges the alphabet. It therefore has **no dependence on the row count** (WC:478-489). The code uses the reduced rate here as well (WC:499).

## RBR soundness theorem (annex `thm:rbr`, TEX:139-152): the per-message error table

| Verifier message | Error | Depends on |
|---|---|---|
| batch lambda, level i | (J_i - 1) L_i / \|E\| | claim count J_i (J_0 = input claims; J_i = t_{i-1} + 2), list size L_i |
| fold challenge s_j, level i | 2 L_i / \|E\| + epsilon_i | L_i, MCA epsilon_i (BCHKS25 4.6 for the level-i code); **one entry per fold, the same for every j** |
| OOD entering level i >= 1 | C(L_i, 2) * nu_i / \|E\| | L_i, nu_i = variables of the level-i multilinear (= interleaving exponent + code dimension exponent) |
| query message, level i | (1 - gamma_i)^{t_i} | gamma_i, t_i |
| final lambda | t_{r-1} / \|E\| | last query count |
| each closing round | 2 / \|E\| | none |

RBR error is the **max** of these (TEX:84, 151). Interactive soundness would be their **sum** (TEX:84). Under the sum, a level with ell_i folds contributes ell_i fold entries, so widening the first fold by k adds k more terms of size 2L_0/|E| + epsilon_0. Under the max, which is the notion leanVM targets, it adds nothing.

//! T06: does widening the first fold of a WHIR opening (stacking n = 2^k children as
//! k extra interleaving variables) change leanVM's query counts, OOD samples,
//! grinding, or any soundness term?
//!
//! All numbers come from leanVM's own search (`optimize_johnson_level`) and term
//! functions, reached through the probe module on branch research/t06-params.
//!
//! Shapes (per-child stack size `mu`, widening `k`, rate 1/4 unless noted):
//! - `base`:      production ladder of one `mu`-variable opening (folds 6,4,4,...).
//! - `L0cut`:     L0 interleaving 6+k (total variables mu+k), every code in the
//!                ladder unchanged (L0 code dim 2^(mu-6), L1.. rates 5,8,11,..).
//!                This is the "rest of the ladder unchanged" shape of the task.
//! - `L0cut_rule`: what upstream's production ladder rule itself gives for
//!                initial fold 6+k on mu+k variables: fixed initial RS-domain
//!                reduction 3, so the L1 rate becomes 5+k (L1 codeword 2^k longer).
//! - `L1cut`:     L0 per child unchanged; L1 interleaving 4+k, L2.. unchanged.
//!                prev_queries at L1 = the code's rule (one L0 query phase).
//! - `L1cut_nq`:  as L1cut, but L1's batch carries n * (L0 queries) claims
//!                (n children's L0 query phases), the honest J for stacking.

use pcs::whir_config::t06_probe::{
    LevelReport, LevelSpec, probe_levels, production_ladder, production_queries_eta, validate_probed,
};
use std::fmt::Write as _;

/// Copy of `crates/verifier/src/whir.rs:18-23` (WHIR_QUERIES[rate-1][log_n-15]).
#[rustfmt::skip]
const WHIR_QUERIES: [[&[usize]; 14]; 4] = [
    [&[222,55], &[223,56,30], &[223,56,31], &[223,56,32], &[223,56,32], &[223,56,32,22], &[223,56,32,22], &[224,56,32,23], &[224,56,32,23], &[224,56,32,23,17], &[224,56,32,23,17], &[224,56,32,23,18], &[225,56,32,23,18], &[225,56,32,23,18,14]],
    [&[111,45], &[112,45,27], &[112,45,28], &[112,45,28], &[112,45,28], &[112,45,28,20], &[112,45,28,20], &[112,45,28,21], &[112,45,28,21], &[112,45,28,21,16], &[112,45,28,21,16], &[112,45,28,21,16], &[112,45,28,21,16], &[112,45,28,21,16,13]],
    [&[75,37], &[75,37,24], &[75,37,25], &[75,38,25], &[75,38,25], &[75,38,25,18], &[75,38,25,19], &[75,38,25,19], &[75,38,25,19], &[75,38,25,19,15], &[75,38,25,19,15], &[75,38,25,19,15], &[75,38,25,19,15], &[75,38,25,19,15,13]],
    [&[56,32], &[56,32,22], &[56,32,22], &[56,32,23], &[56,32,23], &[56,32,23,17], &[56,32,23,17], &[56,32,23,18], &[56,32,23,18], &[56,32,23,18,14], &[56,32,23,18,14], &[56,32,23,18,14], &[56,32,23,18,15], &[56,32,23,18,15,12]],
];

const RATE: usize = 2;
const MUS: [usize; 5] = [24, 25, 26, 27, 28];
const KS: [usize; 4] = [0, 1, 2, 3];

fn shape_specs(shape: &str, mu: usize, k: usize) -> Result<(usize, Vec<LevelSpec>), String> {
    let mut specs = production_ladder(mu, 6, RATE)?;
    match shape {
        "base" => Ok((mu, specs)),
        "L0cut" => {
            specs[0].log_num_interleaved += k;
            Ok((mu + k, specs))
        }
        "L0cut_rule" => Ok((mu + k, production_ladder(mu + k, 6 + k, RATE)?)),
        "L1cut" | "L1cut_nq" => {
            specs[1].log_num_interleaved += k;
            if shape == "L1cut_nq" {
                let l0 = probe_levels(&specs[..1])?;
                specs[1].prev_queries_override = Some((1usize << k) * l0[0].queries);
            }
            // log_n has no single meaning here (n separate L0 commitments).
            Ok((mu, specs))
        }
        _ => Err(format!("unknown shape {shape}")),
    }
}

/// Cross-check: the probe on the production ladder must equal both the production
/// derivation (queries and eta, bit for bit) and the verifier's table.
fn cross_check(log: &mut String) -> bool {
    let mut ok = true;
    for rate in 1..=4 {
        for log_n in 15..=28 {
            let specs = production_ladder(log_n, 6, rate).unwrap();
            let rep = probe_levels(&specs).unwrap();
            let prod = production_queries_eta(log_n, rate).unwrap();
            let q: Vec<usize> = rep.iter().map(|r| r.queries).collect();
            let same_prod = rep.len() == prod.len()
                && rep
                    .iter()
                    .zip(&prod)
                    .all(|(r, p)| r.queries == p.0 && r.eta.to_bits() == p.1.to_bits());
            let same_table = q.as_slice() == WHIR_QUERIES[rate - 1][log_n - 15];
            let valid = validate_probed(log_n, &specs, &rep).is_ok();
            ok &= same_prod && same_table && valid;
            if !(same_prod && same_table && valid) {
                let _ = writeln!(
                    log,
                    "MISMATCH rate={rate} log_n={log_n}: probe {q:?} prod_eq={same_prod} table_eq={same_table} valid={valid}"
                );
            }
        }
    }
    let _ = writeln!(
        log,
        "cross-check (rates 1..4, log_n 15..28, 56 configs): probe == production derivation (queries, eta bits) == verifier WHIR_QUERIES, validate() ok: {}",
        if ok { "ALL PASS" } else { "FAILED" }
    );
    ok
}

const CSV_HEADER: &str = "shape,mu,k,n_children,mu_total,level,fold,log_inv_rate,log_msg_cols,log_num_interleaved,mu_vars,log_block_len,prev_queries,queries,ood,grind_bits,eta,m,gamma,per_query_bits,log2_list,log2_a,pg_bits,fold_row_bits,query_bits,query_plus_grind_bits,ood_bits,algebraic_bits,algebraic_degree,batch_row_doc_bits,d_queries_vs_base,d_ood_vs_base,d_grind_vs_base,validate";

fn main() {
    let mut log = String::new();
    let ok = cross_check(&mut log);
    print!("{log}");
    assert!(ok, "cross-check failed");

    let out_dir = std::env::args().nth(1).unwrap_or_else(|| ".".into());
    let mut csv = String::from(CSV_HEADER);
    csv.push('\n');
    let mut summary = String::new();

    for &mu in &MUS {
        let (_, base_specs) = shape_specs("base", mu, 0).unwrap();
        let base = probe_levels(&base_specs).unwrap();
        for shape in ["base", "L0cut", "L0cut_rule", "L1cut", "L1cut_nq"] {
            let ks: &[usize] = if shape == "base" { &[0] } else { &KS };
            for &k in ks {
                let (log_n, specs) = shape_specs(shape, mu, k).unwrap();
                let rep = match probe_levels(&specs) {
                    Ok(r) => r,
                    Err(e) => {
                        println!("{shape} mu={mu} k={k}: SEARCH FAILED: {e}");
                        continue;
                    }
                };
                let validate = if shape.starts_with("L1cut") {
                    "n/a (n separate L0 commitments)".to_string()
                } else {
                    match validate_probed(log_n, &specs, &rep) {
                        Ok(()) => "ok".into(),
                        Err(e) => format!("FAIL: {e}"),
                    }
                };
                print_case(shape, mu, k, log_n, &rep, &base, &validate);
                let mut any_change = rep.len() != base.len();
                for (i, r) in rep.iter().enumerate() {
                    let b = base.get(i);
                    let (dq, dood, dg) = match b {
                        Some(b) => (
                            r.queries as i64 - b.queries as i64,
                            r.ood_samples as i64 - b.ood_samples as i64,
                            r.grinding_bits as i64 - b.grinding_bits as i64,
                        ),
                        None => (i64::MAX, i64::MAX, i64::MAX),
                    };
                    any_change |= dq != 0 || dood != 0 || dg != 0;
                    let _ = writeln!(
                        csv,
                        "{shape},{mu},{k},{},{log_n},{},{},{},{},{},{},{},{},{},{},{},{:.12e},{},{:.12},{:.12},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{},{:.6},{dq},{dood},{dg},\"{}\"",
                        1usize << k,
                        r.level,
                        r.fold,
                        r.log_inv_rate,
                        r.log_msg_cols,
                        r.log_num_interleaved,
                        r.mu_vars,
                        r.log_block_len,
                        r.prev_queries,
                        r.queries,
                        r.ood_samples,
                        r.grinding_bits,
                        r.eta,
                        r.m_param,
                        r.gamma,
                        r.per_query_bits,
                        r.log2_list,
                        r.log2_a,
                        r.pg_bits,
                        r.fold_row_bits,
                        r.query_bits,
                        r.query_plus_grind_bits,
                        r.ood_bits,
                        r.algebraic_bits,
                        r.algebraic_degree,
                        r.batch_row_doc_bits,
                        validate.replace('"', "'"),
                    );
                }
                let q: Vec<usize> = rep.iter().map(|r| r.queries).collect();
                let ood: Vec<usize> = rep.iter().map(|r| r.ood_samples).collect();
                let g: Vec<usize> = rep.iter().map(|r| r.grinding_bits).collect();
                let folds: Vec<usize> = rep.iter().map(|r| r.fold).collect();
                let rates: Vec<usize> = rep.iter().map(|r| r.log_inv_rate).collect();
                let _ = writeln!(
                    summary,
                    "| {shape} | {mu} | {k} | {log_n} | {folds:?} | {rates:?} | {q:?} | {ood:?} | {g:?} | {} | {} |",
                    if any_change { "CHANGED" } else { "same" },
                    validate
                );
            }
        }
    }
    println!("\n## Summary (queries / OOD / grinding vs base at the same mu)\n");
    println!("| shape | mu | k | mu_total | folds | log_inv_rates | queries | OOD | grind | vs base | validate() |");
    println!("|---|---|---|---|---|---|---|---|---|---|---|");
    print!("{summary}");
    let path = format!("{out_dir}/sweep.csv");
    std::fs::write(&path, csv).expect("write csv");
    println!("\nwrote {path}");
}

fn print_case(shape: &str, mu: usize, k: usize, log_n: usize, rep: &[LevelReport], base: &[LevelReport], validate: &str) {
    println!("\n### {shape}  mu={mu} k={k} (n={}) mu_total={log_n}  validate: {validate}", 1usize << k);
    println!(
        "| L | fold | log_inv_rate | log_msg_cols | mu_vars | prev_q | queries | OOD | grind | eta | m | log2 L | pg (192-log2 a) | fold row | query | query+grind | OOD bits | algebraic | batch(doc) | dQ |"
    );
    println!("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|");
    for (i, r) in rep.iter().enumerate() {
        let dq = base.get(i).map(|b| r.queries as i64 - b.queries as i64);
        println!(
            "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {:.6e} | {} | {:.3} | {:.3} | {:.3} | {:.3} | {:.3} | {:.3} | {:.3} | {:.3} | {} |",
            r.level,
            r.fold,
            r.log_inv_rate,
            r.log_msg_cols,
            r.mu_vars,
            r.prev_queries,
            r.queries,
            r.ood_samples,
            r.grinding_bits,
            r.eta,
            r.m_param,
            r.log2_list,
            r.pg_bits,
            r.fold_row_bits,
            r.query_bits,
            r.query_plus_grind_bits,
            r.ood_bits,
            r.algebraic_bits,
            r.batch_row_doc_bits,
            dq.map(|d| format!("{d:+}")).unwrap_or_else(|| "n/a".into()),
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn probe_reproduces_production_and_table() {
        let mut log = String::new();
        assert!(cross_check(&mut log), "{log}");
    }

    #[test]
    fn deterministic() {
        for shape in ["L0cut", "L0cut_rule", "L1cut", "L1cut_nq"] {
            let (_, s) = shape_specs(shape, 25, 2).unwrap();
            let a = probe_levels(&s).unwrap();
            let b = probe_levels(&s).unwrap();
            for (x, y) in a.iter().zip(&b) {
                assert_eq!(x.queries, y.queries);
                assert_eq!(x.eta.to_bits(), y.eta.to_bits());
            }
        }
    }

    #[test]
    fn widened_l0_keeps_l0_code() {
        // k extra interleaving variables leave the L0 code (dimension, rate) unchanged.
        let (_, base) = shape_specs("base", 25, 0).unwrap();
        let (_, wide) = shape_specs("L0cut", 25, 3).unwrap();
        assert_eq!(base[0].log_msg_cols, wide[0].log_msg_cols);
        assert_eq!(base[0].log_inv_rate, wide[0].log_inv_rate);
        assert_eq!(wide[0].log_num_interleaved, 9);
    }
}

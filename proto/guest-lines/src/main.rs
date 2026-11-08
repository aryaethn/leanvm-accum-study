//! usage: guest-lines OUT
//! Writes `# code_len N`, then `F name entry len` per compiled function (the same
//! table DBG_PROF_DUMP writes), then `L pc line` for every pc below code_len.
use std::fmt::Write;

fn main() {
    let out = std::env::args().nth(1).expect("usage: guest-lines OUT");
    let g = rec_aggregation::aggregation::unified_guest();
    let mut s = String::new();
    writeln!(s, "# code_len {} padded_log {}", g.code_len(), g.prog.len().trailing_zeros()).unwrap();
    for (name, entry, len) in &g.fn_ranges {
        writeln!(s, "F {name} {entry} {len}").unwrap();
    }
    for (pc, line) in g.src_lines.iter().enumerate() {
        writeln!(s, "L {pc} {line}").unwrap();
    }
    std::fs::write(&out, s).unwrap();
    eprintln!("wrote {out}: {} fns, {} lines", g.fn_ranges.len(), g.src_lines.len());
}

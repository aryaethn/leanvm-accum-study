#!/usr/bin/env python3
"""T03 exact per-stage cycle attribution of the recursion node from leanVM's own profiler.

usage: attribute.py PROF LINES DISASM [--guest GUEST_SOURCE] [--json out.json]

Inputs (all produced WITHOUT changing guest or VM semantics):
  PROF    DBG_PROF_DUMP output of the node run: '# steps N', 'F name entry len', 'pc count'
  LINES   proto/guest-lines output: 'F name entry len' and 'L pc srcline' (1-based lines of
          crates/rec_aggregation/guests/lean_ethereum.py) from rec_aggregation::unified_guest()
  DISASM  DBG_DISASM output (function table, then one 'pc  OPCODE ...' line per pc)

Method
  1. Every pc gets a bucket from its source line (BUCKETS below). Functions that contain a
     bucketed line are "split" functions (verify_sub, the open_stacked arms, opening_queries and
     the __loop helpers lowered out of them). In a split function, a pc whose line is NOT in
     the table is code of an @inline helper expanded at a call site; it takes the bucket of
     the previous bucketed pc in pc order (the call-site statement). Where the previous and next
     bucketed pcs disagree, the cycles are counted as 'boundary-ambiguous' and reported.
  2. A non-split function inherits its call sites' bucket. Calls are recovered statically from
     the disassembly: 'SET fp[k] = g^E' then 'JUMP ... pc=fp[k]' with E a function entry. The
     call count is the profile count of the JUMP. Inclusive cost (self + callees) is pushed to
     call sites in proportion to call counts; self-edges (loop iterations) are skipped. A
     callee reached from sites in DIFFERENT buckets is split proportionally (assumes equal cost
     per call); such callees are listed with their cycles so the approximation is visible.
  3. Per-opcode counts are carried along (opcode of each pc from the disassembly), so
     KECCAK per bucket is exact under the same rules.
"""
import re, sys, json, collections

# (first_line, last_line, bucket). Stage letters follow the T03 task definitions.
BUCKETS = [
    # ---- verify_sub (lean_ethereum.py:3325-3517) ----
    (3325, 3345, 'a:seed'),
    (3346, 3395, 'a:layout announce+certify'),
    (3396, 3411, 'a:commit root'),
    (3412, 3427, 'a:bus challenges'),
    (3428, 3430, 'b:bus GKR'),
    (3431, 3434, 'c:tables (leaves+table sumcheck+PI)'),
    (3435, 3441, 'd:Keccak GKR'),
    (3442, 3490, 'e3:ring-switch front+claim batch'),
    (3491, 3502, 'e3:placement+config certify'),
    (3503, 3507, 'e3:open dispatch'),
    (3508, 3510, 'e3:terminal weights'),
    (3511, 3517, 'a:export deferred'),
    # ---- check_opening_terminal (3238-3322): weights are e3, the final equality e4 ----
    (3238, 3321, 'e3:terminal weights'),
    (3322, 3322, 'e4:final check'),
    # ---- open_stacked (1434-1764) ----
    (1434, 1479, 'e:setup'),
    (1480, 1482, 'eq:query sampling'),        # win_tabs, read only by decode_query_windows
    (1483, 1496, 'e:setup'),
    (1497, 1503, 'e3:sumcheck rounds'),
    (1504, 1505, 'e4:final message'),
    (1506, 1519, 'e:level roots'),
    (1520, 1538, 'e3:OOD'),
    (1539, 1558, 'eq:query grinding'),
    (1559, 1581, 'eq:query sampling'),
    (1582, 1595, 'e3:level batching'),
    (1596, 1598, 'e2:row eq weights'),
    (1599, 1605, 'e1:Merkle cap'),
    (1606, 1607, 'e2:query rows'),
    (1608, 1642, 'e3:level batching'),
    (1643, 1661, 'e3:sumcheck rounds'),
    (1662, 1662, 'e4:final message'),
    (1663, 1690, 'e3:point rotation'),
    (1691, 1748, 'e2:residual (query weights)'),
    (1749, 1764, 'e3:OOD'),
    # ---- opening_query (1351-1394, @inline) / opening_queries (1397-1419) ----
    (1351, 1360, 'e2:query rows'),
    (1361, 1370, 'e1e2:lane packing'),
    (1371, 1390, 'e2:query rows'),
    (1391, 1393, 'e1:Merkle leaf+path'),
    (1394, 1420, 'e2:query rows'),
    # ---- residual_query (1423-1431, @inline, only in the residual) ----
    (1423, 1431, 'e2:residual (query weights)'),
]

STAGE_OF = lambda b: b.split(':')[0]

import os, difflib
HERE = os.path.dirname(os.path.abspath(__file__))
# BUCKETS and FS_LINES are written against the df7d122 guest (git show df7d122:<guest>).
BASE_GUEST = os.path.join(HERE, '..', '..', 'results', 'T03', 'prof', 'guest_base.py')
SRC, DEF_OF, LINE_MAP = [], {}, {}
# Fiat-Shamir sponge helpers (lean_ethereum.py:555-692 at df7d122): pack_pair .. squeeze.
# Cycles whose line lies here are tagged '|FS' as a cross-cut of every bucket.
FS_LINES = range(555, 693)


def set_guest(path):
    """Use the guest source the profiled program was compiled from. For a variant, its lines are
    mapped back to df7d122 lines by a difflib alignment; an inserted line takes the df7d122 line
    of the nearest unchanged line above it."""
    global SRC
    SRC = open(path).read().split('\n')
    base = open(BASE_GUEST).read().split('\n')
    DEF_OF.clear(); LINE_MAP.clear()
    cur = None
    for k, t in enumerate(SRC, 1):
        m = re.match(r'def (\w+)\(', t)
        if m: cur = m.group(1)
        elif t and not t[0].isspace() and not t.startswith('@') and not t.startswith('#'): cur = None
        if cur: DEF_OF[k] = cur
    sm = difflib.SequenceMatcher(None, base, SRC, autojunk=False)
    for blk in sm.get_matching_blocks():
        for d in range(blk.size): LINE_MAP[blk.b + d + 1] = blk.a + d + 1
    last = 0
    for k in range(1, len(SRC) + 1):
        if k in LINE_MAP: last = LINE_MAP[k]
        else: LINE_MAP[k] = last


def base_line(line):
    return LINE_MAP.get(line, 0)


def bucket_of_line(line):
    line = base_line(line)
    for lo, hi, b in BUCKETS:
        if lo <= line <= hi:
            return b
    return None


def load(prof, lines, disasm):
    counts, steps = {}, None
    for ln in open(prof):
        if ln.startswith('# steps'):
            steps = int(ln.split()[2])
        elif ln[0] not in '#F':
            p, c = ln.split(); counts[int(p)] = int(c)
    fns, src = [], {}
    for ln in open(lines):
        p = ln.split()
        if p[0] == 'F': fns.append((p[1], int(p[2]), int(p[3])))
        elif p[0] == 'L': src[int(p[1])] = int(p[2])
    ops = {}
    rx = re.compile(r'^\s*([\d,]+)\s+(\w+)\s+(.*)$')
    for ln in open(disasm):
        if ln.startswith('#'): continue
        m = rx.match(ln)
        if m: ops[int(m.group(1).replace(',', ''))] = (m.group(2), m.group(3))
    return steps, counts, fns, src, ops


def main():
    a = sys.argv[1:]
    out_json = None
    if '--json' in a:
        i = a.index('--json'); out_json = a[i + 1]; del a[i:i + 2]
    guest = BASE_GUEST
    if '--guest' in a:
        i = a.index('--guest'); guest = a[i + 1]; del a[i:i + 2]
    set_guest(guest)
    steps, counts, fns, src, ops = load(*a)
    assert sum(counts.values()) == steps
    entry_of = {e: n for n, e, l in fns}
    fn_at = {}
    for n, e, l in fns:
        for pc in range(e, e + l): fn_at[pc] = n
    rng = {n: (e, l) for n, e, l in fns}

    # --- per-pc bucket in split functions ---
    # An inlined run (consecutive pcs whose lines are not in the table) is resolved to the
    # caller statement that calls one of the run's helpers: the caller's source lines between
    # the previous and next bucketed pcs are searched for '<helper>('. If those lines sit in a
    # single bucket, the run takes it; otherwise the previous bucket, counted as ambiguous.
    pc_bucket, ambiguous, resolved = {}, collections.Counter(), collections.Counter()
    split = set()
    for n, e, l in fns:
        lines_ = [src.get(pc, 0) for pc in range(e, e + l)]
        bs = [bucket_of_line(x) for x in lines_]
        if not any(bs): continue
        split.add(n)
        i = 0
        prev_i = None
        while i < l:
            if bs[i]:
                pc_bucket[e + i] = bs[i]; prev_i = i; i += 1; continue
            j = i
            while j < l and not bs[j]: j += 1
            next_i = j if j < l else None
            helpers = {DEF_OF.get(x) for x in lines_[i:j]} - {None}
            lp = lines_[prev_i] if prev_i is not None else None
            ln = lines_[next_i] if next_i is not None else None
            lo, hi = (min(x for x in (lp, ln) if x), max(x for x in (lp, ln) if x)) if (lp or ln) else (0, -1)
            if lp is None: lo = max(lo - 40, 1)
            if ln is None: hi = hi + 40
            def calls_in(ks):
                return {bucket_of_line(k) for k in ks
                        if bucket_of_line(k) and any(re.search(r'\b' + h + r'\(', SRC[k - 1]) for h in helpers)}
            cand = calls_in(range(lo, hi + 1))
            if not cand:  # the call site is in an @inline caller def (e.g. opening_query): search its whole def
                defs = {DEF_OF.get(x) for x in (lp, ln) if x}
                cand = calls_in([k for k, d in DEF_OF.items() if d in defs])
            pb = bs[prev_i] if prev_i is not None else None
            nb = bs[next_i] if next_i is not None else None
            cyc = sum(counts.get(e + k, 0) for k in range(i, j))
            if len(cand) == 1:
                b = cand.pop()
                if b != pb: resolved[(n, pb, b)] += cyc
            else:
                b = pb or nb
                if pb and nb and pb != nb: ambiguous[(n, pb, nb, tuple(sorted(helpers)))] += cyc
            for k in range(i, j): pc_bucket[e + k] = b
            i = j

    # --- static call edges ---
    calls = collections.defaultdict(list)    # caller -> [(pc, callee, count)]
    callers = collections.defaultdict(list)  # callee -> [(caller, pc, count)]
    setrx = re.compile(r'fp\[(\d+)\] = g\^(\d+)$')
    jrx = re.compile(r'pc=fp\[(\d+)\]')
    for n, e, l in fns:
        last_set = {}
        for pc in range(e, e + l):
            op, arg = ops.get(pc, ('?', ''))
            if op == 'SET':
                m = setrx.search(arg)
                if m: last_set[int(m.group(1))] = int(m.group(2))
            elif op == 'JUMP':
                m = jrx.search(arg)
                if m and int(m.group(1)) in last_set:
                    tgt = last_set[int(m.group(1))]
                    if tgt in entry_of and entry_of[tgt] != n:
                        c = counts.get(pc, 0)
                        calls[n].append((pc, entry_of[tgt], c))
                        callers[entry_of[tgt]].append((n, pc, c))

    # --- match dispatch edges ---
    # `__jump_tables` fills main-frame cells with arm addresses ('SET fp[o] = g^target'). A
    # dispatch site reads slot o2 + index ('DEREF *(fp[x]*g^o2) = fp[k]', then 'JUMP pc=fp[k]').
    # A site's table is taken to run from its base o2 to the next site's base. An arm that is a
    # function entry gets an edge from every site whose table holds it; the edge count is the
    # arm's entry count, split over its sites by their dispatch counts when there are several.
    jt = {}
    e0, l0 = rng['__jump_tables']
    for pc in range(e0, e0 + l0):
        m = setrx.search(ops[pc][1]); jt[int(re.search(r'fp\[(\d+)\]', ops[pc][1]).group(1))] = int(m.group(2))
    drx = re.compile(r'^\*\(fp\[(\d+)\]·g\^(\d+)\) = fp\[(\d+)\]\s+\[Cell\]')
    sites = []  # (caller, pc, base, count)
    for n, e, l in fns:
        last_deref = {}
        for pc in range(e, e + l):
            op, arg = ops.get(pc, ('?', ''))
            if op == 'DEREF':
                m = drx.match(arg)
                if m: last_deref[int(m.group(3))] = int(m.group(2))
            elif op == 'SET':
                m = setrx.search(arg)
                if m: last_deref.pop(int(m.group(1)), None)
            elif op == 'JUMP':
                m = jrx.search(arg)
                if m and int(m.group(1)) in last_deref and int(m.group(1)) not in last_set_of(n, pc, ops, setrx, e):
                    sites.append((n, pc, last_deref[int(m.group(1))], counts.get(pc, 0)))
    bases = sorted({b for _, _, b, _ in sites})
    jt_end = max(jt) + 1
    arm_sites = collections.defaultdict(list)
    for n, pc, b, c in sites:
        nb = next((x for x in bases if x > b), jt_end)
        for o in range(b, nb):
            t = jt.get(o)
            if t in entry_of and entry_of[t] != n:
                arm_sites[entry_of[t]].append((n, pc, c))
    dyn_multi = []
    for h, ss in arm_sites.items():
        ent = counts.get(rng[h][0], 0)
        if not ent: continue
        live = [s for s in ss if s[2]]
        tot = sum(c for _, _, c in live)
        if len(live) > 1: dyn_multi.append((h, ent, live))
        for n, pc, c in live:
            w = ent * c / tot
            calls[n].append((pc, h, w)); callers[h].append((n, pc, w))

    # --- validation: entry counts vs. call counts ---
    checks = []
    for n, e, l in fns:
        ent = counts.get(e, 0)
        cin = sum(c for _, _, c in callers[n])
        if ent or cin:
            checks.append((n, ent, cin))
    mism = [(n, ent, cin) for n, ent, cin in checks if ent != cin and not n.startswith('__loop')]
    loop_bad = [(n, ent, cin) for n, ent, cin in checks if n.startswith('__loop') and ent < cin]

    # --- self costs ---
    def addc(d, b, op, c):
        d.setdefault(b, collections.Counter())[op] += c
    selfc = {}
    for n, e, l in fns:
        d = {}
        for pc in range(e, e + l):
            c = counts.get(pc, 0)
            if not c: continue
            op = ops.get(pc, ('?',))[0] + ('|FS' if base_line(src.get(pc, 0)) in FS_LINES else '')
            addc(d, pc_bucket[pc] if n in split else 'INHERIT', op, c)
        selfc[n] = d

    # --- inclusive propagation, callees first ---
    order, state = [], {}
    sys.setrecursionlimit(100000)
    def dfs(n):
        state[n] = 1
        for _, h, _ in calls[n]:
            if state.get(h) == 1: raise SystemExit(f'call cycle through {n} -> {h}')
            if h not in state: dfs(h)
        state[n] = 2; order.append(n)
    for n, _, _ in fns:
        if n not in state: dfs(n)
    incl = {}
    multi_bucket = []
    for h in order:
        d = {b: collections.Counter(v) for b, v in selfc[h].items()}
        for pc, g, c in calls[h]:
            tot = sum(cc for _, _, cc in callers[g])
            if not tot or not c: continue
            fr = c / tot
            tb = pc_bucket[pc] if h in split else 'INHERIT'
            for b, v in incl[g].items():
                bb = tb if b == 'INHERIT' else b
                for op, x in v.items():
                    d.setdefault(bb, collections.Counter())[op] += x * fr
        incl[h] = d
    # callees whose INHERIT cost lands in more than one bucket (proportional split used)
    def site_bucket_set(g, seen=None):
        out = collections.Counter()
        for f, pc, c in callers[g]:
            if not c: continue
            if f in split: out[pc_bucket[pc]] += c
            else:
                for b, x in site_bucket_set(f).items(): out[b] += x
        if not callers[g]: out['ROOT:' + g] += 1
        return out
    for n, e, l in fns:
        inh = sum(selfc[n].get('INHERIT', {}).values())
        if inh and n not in split:
            sb = site_bucket_set(n)
            stages = {STAGE_OF(b) if not b.startswith('ROOT') else b for b in sb}
            if len(stages) > 1:
                multi_bucket.append((n, inh, dict(sb)))

    roots = [n for n, _, _ in fns if not callers[n] and sum(sum(v.values()) for v in incl[n].values()) > 0]
    total = collections.defaultdict(collections.Counter)
    for r in roots:
        for b, v in incl[r].items():
            total[b if b != 'INHERIT' else 'outside verify_sub: ' + r] += v
    grand = sum(sum(v.values()) for v in total.values())

    # verify_sub inclusive
    vs = incl['verify_sub']; vs_tot = sum(sum(v.values()) for v in vs.values())
    vs_calls = sum(c for _, _, c in callers['verify_sub'])
    res = dict(steps=steps, grand=grand, roots=roots, verify_sub_calls=vs_calls, verify_sub_incl=vs_tot,
               buckets={b: dict(v) for b, v in total.items()},
               ambiguous=[[f, p, q, list(h), c] for (f, p, q, h), c in ambiguous.items() if c],
               entry_mismatch=mism, loop_entry_below_calls=loop_bad,
               multi_stage_callees=[[n, c, sb] for n, c, sb in sorted(multi_bucket, key=lambda x: -x[1])])
    print(f"steps {steps}; attributed {grand:.1f}; roots {roots}; verify_sub calls {vs_calls}, inclusive {vs_tot:.1f}")
    print(f"entry-count mismatches (non-loop fns): {len(mism)} {mism[:10]}")
    print(f"loop fns entered fewer times than called: {loop_bad[:10]}")
    print(f"dispatch arms reachable from several live sites: {[(h, e, [(n, c) for n, _, c in s]) for h, e, s in dyn_multi][:12]}")
    res_extra = dict(dispatch_multi=[[h, e, [[n, pc, c] for n, pc, c in s]] for h, e, s in dyn_multi])
    print(f"inlined runs moved off the previous bucket by call-site search: {sum(resolved.values())}  {[(k, v) for k, v in resolved.items() if v][:20]}")
    print(f"boundary-ambiguous inlined cycles (left on previous bucket): {sum(ambiguous.values())}  {[(k, v) for k, v in ambiguous.items() if v][:12]}")
    res_extra['ambiguous_total'] = sum(ambiguous.values())
    print("callees reached from more than one stage (cost split by call counts):")
    for n, c, sb in sorted(multi_bucket, key=lambda x: -x[1])[:25]:
        print(f"   {c:9d} self  {n}  sites by bucket {dict(sb)}")
    print(f"\n{'bucket':42s} {'cycles':>11s} {'KECCAK':>8s} {'FS-helper':>10s}")
    for b in sorted(total, key=lambda b: (b.startswith('outside'), b)):
        v = total[b]
        kc = sum(x for k, x in v.items() if k.startswith('KECCAK'))
        fs = sum(x for k, x in v.items() if k.endswith('|FS'))
        print(f"{b:42s} {sum(v.values()):11.1f} {kc:8.1f} {fs:10.1f}")
    res.update(res_extra)
    if out_json:
        json.dump(res, open(out_json, 'w'), indent=1, default=float)


def last_set_of(n, pc, ops, setrx, e):
    """Cells whose latest writer before pc (in function n) is a SET of a g-power."""
    out, seen = set(), set()
    for p in range(pc - 1, e - 1, -1):
        op, arg = ops.get(p, ('?', ''))
        if op in ('SET', 'DEREF'):
            m = re.search(r'fp\[(\d+)\]', arg if op == 'SET' else arg.split('=')[-1])
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                if op == 'SET': out.add(int(m.group(1)))
        if pc - p > 64: break
    return out


if __name__ == '__main__':
    main()

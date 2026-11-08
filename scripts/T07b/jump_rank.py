#!/usr/bin/env python3
"""T07b: rank JUMP rows by guest source line.  usage: jump_rank.py NODE_N2 NODE_N1 LINES DISASM GUEST [TOP] """
import sys, re, collections, gzip
def op(path):
    return gzip.open(path, 'rt') if path.endswith('.gz') else open(path)
def load_prof(p):
    c = {}
    for ln in op(p):
        if ln[0] in '#F': continue
        a, b = ln.split(); c[int(a)] = int(b)
    return c
n2 = load_prof(sys.argv[1]); n1 = load_prof(sys.argv[2])
lines = {}; fns = []
for ln in op(sys.argv[3]):
    if ln.startswith('L '):
        _, pc, l = ln.split(); lines[int(pc)] = int(l)
    elif ln.startswith('F '):
        _, name, e, sz = ln.split(); fns.append((int(e), int(sz), name))
fns.sort()
def fn_of(pc):
    import bisect
    i = bisect.bisect_right([f[0] for f in fns], pc) - 1
    e, sz, name = fns[i]
    return name if pc < e + sz else '?'
ops = {}
for ln in op(sys.argv[4]):
    m = re.match(r'\s*([\d,]+)\s+([A-Z]+)', ln)
    if m: ops[int(m.group(1).replace(',', ''))] = m.group(2)
guest = open(sys.argv[5]).read().splitlines()
top = int(sys.argv[6]) if len(sys.argv) > 6 else 45
bl = collections.Counter(); bf = collections.Counter(); per_line_fn = collections.defaultdict(collections.Counter)
tot = 0
for pc, c2 in n2.items():
    if ops.get(pc) != 'JUMP': continue
    d = c2 - n1.get(pc, 0)
    if d == 0: continue
    tot += d
    l = lines.get(pc, 0); bl[l] += d; f = fn_of(pc); bf[f] += d; per_line_fn[l][f] += d
print(f"child-1 JUMP rows (n2 - n1): {tot}")
print("\n# by source line")
for l, d in bl.most_common(top):
    src = guest[l-1].strip()[:110] if 0 < l <= len(guest) else ''
    fs = ", ".join(f"{n}" for n, _ in per_line_fn[l].most_common(2))
    print(f"{d:7d}  L{l:<5d} {src}   [{fs}]")
print("\n# by function")
for f, d in bf.most_common(30):
    print(f"{d:7d}  {f}")

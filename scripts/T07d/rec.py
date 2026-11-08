import os, re
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'results', 'T07d')
ansi=re.compile(r'\x1b\[[0-9;]*m')
for f in ['base_n5_350','base_n6_350','v6_n6_350','v6_n7_350']:
    t=ansi.sub('',open(os.path.join(R, 'runs', f'{f}.log')).read())
    blocks=re.findall(r'DBG_TABLES kind=node cycles=(\d+) mu=(\d+) n_lanes=(\d+) committed_len=(\d+).*?\n((?:DBG_TABLES kind=node (?:shared|table)=.*\n)+)',t)
    cyc,mu,ln,tc,body=blocks[0]
    print(f, 'blocks',len(blocks),'distinct',len(set(blocks)),'cycles',cyc,'mu',mu,'lanes',ln,'TC',tc)
    print('  ',' '.join(f"{m.group(1)}={m.group(2)}(tau{m.group(3)})" for m in re.finditer(r'table=(\w+) rows=(\d+) tau=(\d+)',body) for m in [re.match(r'(\w+)=(\d+)',f"{m.group(1)}={m.group(2)}") ] ) if False else '')
    print('  ',' '.join(f"{a}={b}(tau{c})" for a,b,c in re.findall(r'table=(\w+) rows=(\d+) tau=(\d+)',body)))
    print('  ',' '.join(f"{a}:n_vars{b}" for a,b in re.findall(r'shared=(\w+) n_vars=(\d+)',body)))
    for k in ['proof size','proving time','verifying','peak memory footprint','maximum resident set size','recursion']:
        m=re.search(r'.*'+k+r'.*',t); print('  ',m.group(0).strip()[:120] if m else None)
    print('   h(log_mem)=',re.search(r'log_mem=(\d+)',t).group(1))

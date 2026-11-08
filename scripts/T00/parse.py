import re,glob,statistics,csv,sys,os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','results','T00'))  # reads and writes results/T00
rows=[]
def order(f): 
    m=re.search(r'(\d+)',re.sub(r'^[a-z]+_','',f)); return (f.split('_')[0],int(re.findall(r'\d+',f)[-3 if f.startswith('recursion') else 0] if False else 0))
for f in sorted(glob.glob('*.log')):
    if f=='build.log': continue
    t=open(f).read(); t=re.sub(r'\x1b\[[0-9;]*m','',t)
    t=re.sub(r'(generating leanXMSS signers[^\n]*?\d+/\d+\s*)+','',t)
    g=lambda p:(re.search(p,t) or [None,None])[1]
    cmd=g(r'# cmd: /usr/bin/time -l \S+leanvm (.*)')
    passes=g(r'passes\s*:\s*([^\n]*)')
    ps=[float(x) for x in re.findall(r'([\d.]+) s',passes)] if passes else []
    if f.startswith('recursion'):
        tt=re.sub(r'(generating leanXMSS signers[^\n\r]*[\r])','',t)
        st=re.search(r'\n +([\d.]+) s *\n',tt)
        if st: ps.append(float(st.group(1)))
    sb=lambda k:float(re.search(r'used = ([\d.]+)M',g(r'# '+k+r': (.*)')).group(1))
    rows.append(dict(workload=f.split('_')[0],params=cmd.split(' ',1)[1] if ' ' in cmd else cmd,
      cycles=g(r'cycles \(VM steps\)\s*:\s*([\d,]+)'),per_opcode_line=g(r'details\s*:\s*([^\n]*)'),
      total_committed_log2_words=g(r'TOTAL_COMMITTED 2\^([\d.]+)'),proof_kib=g(r'proof size\s*:\s*([\d.]+) KiB'),
      prove_s_each_repeat=' '.join(map(str,ps)),prove_s_median=statistics.median(ps) if ps else '',
      printed_mean=g(r'(?:proving(?: time)?)\s*:\s*([^\n]*?)\s{2,}'),
      leanvm_peak_mem_gib=g(r'peak memory ([\d.]+) GiB'),os_max_rss_bytes=g(r'(\d+)\s+maximum resident set size'),
      swap_delta_mib=round(sb('swap_after')-sb('swap_before')),os_peak_footprint_bytes=g(r'(\d+)\s+peak memory footprint'),wall_s=g(r'([\d.]+) real'),verify_ms=g(r'verifying\s*:\s*([\d.]+) ms'),
      flags=('AC' if 'AC Power' in t.split('swap_before')[0] or 'charging' in g(r'# power: (.*)') else 'battery')+('; memory-pressured' if (sb('swap_after')-sb('swap_before'))>256 else ''),file=f))
if not rows: sys.exit('no *.log files in results/T00 (raw T00 logs are not bundled); summary.csv left unchanged')
w=csv.DictWriter(open('summary.csv','w'),fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print({k:r[k] for k in ['file','cycles','total_committed_log2_words','proof_kib','prove_s_each_repeat','prove_s_median','leanvm_peak_mem_gib','os_max_rss_bytes','swap_delta_mib','verify_ms','flags']})

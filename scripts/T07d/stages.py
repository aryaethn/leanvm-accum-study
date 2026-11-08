import re, sys, json, statistics as st
import os
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..')  # bundle-relative (edited from absolute path)
R=B+'/results/T07c/runs/'
ansi=re.compile(r'\x1b\[[0-9;]*m')
unit={'ns':1e-6,'µs':1e-3,'ms':1.0,'s':1000.0}
line_re=re.compile(r'INFO\s+((?:[│ ]  )*)?(┝━|┕━)?\s*(.+?) \[ ([0-9.]+)(ns|µs|ms|s) \| ([0-9.e-]+)% \]')
def parse(fn):
    txt=ansi.sub('',open(R+fn).read())
    lines=txt.split('\n')
    # find tree start: line with 'INFO     Prove ['
    out=[]
    start=None
    for i,l in enumerate(lines):
        if re.search(r'INFO\s+Prove \[',l): start=i;break
    pre={}
    for l in lines[:start]:
        m=re.match(r'.*?INFO\s+(Replay children|Build witness|Batch deferred claims) \[ ([0-9.]+)(ns|µs|ms|s)',l)
        if m: pre[m.group(1)]=float(m.group(2))*unit[m.group(3)]
    nodes=[]
    for l in lines[start:]:
        if 'Recompute deferred' in l: break
        m=re.match(r'\s*INFO(\s+)(.*?)\[ ([0-9.]+)(ns|µs|ms|s) \| ',l)
        if not m: continue
        body=(m.group(1)[5:]+m.group(2))
        # depth: position of branch glyph
        g=re.search(r'[┝┕]━',body)
        if g: depth=(g.start()//3)+1; name=body[g.end():].strip()
        else: depth=0; name=body.strip()
        # extract kv fields after the closing
        rest=l[l.index('|')+1:]
        kv=dict(re.findall(r'(\w+): ("?[\w ]+"?)',rest))
        nodes.append((depth,name,float(m.group(3))*unit[m.group(4)],kv))
    return pre,nodes
def stages(nodes):
    S={}
    tot=nodes[0][2]
    top=[n for n in nodes if n[0]==1]
    def add(k,v): S[k]=S.get(k,0)+v
    # top-level children of Prove
    cur=None
    for idx,(d,name,t,kv) in enumerate(nodes):
        if d==1:
            if name=='Execute program': add('execute',t)
            elif name=='Build witness': add('witness build',t)
            elif name=='Commit': add('commit (encode+Merkle)',t)
            elif name=='Prove bus': add('bus total',t)
            elif name=='Prove constraints': add('table sumcheck (Prove constraints)',t)
            elif name=='Keccak reduction': add('Keccak reduction',t)
            elif name=='PCS open': add('PCS open total',t)
            else: add('??'+name,t)
            cur=name
        elif d==2 and cur=='Prove bus' and name=='Bus GKR': add('bus GKR',t)
    # PCS open children, in order
    pcs=[]
    inpcs=False
    for (d,name,t,kv) in nodes:
        if d==1: inpcs=(name=='PCS open'); continue
        if inpcs and d==2: pcs.append((name,t,kv))
    # assign
    first=True; L=-1; seen_commit=False
    cur_it='front'  # ring switch, basis, first sumcheck
    for name,t,kv in pcs:
        if name=='Commit':
            lvl=int(kv['level']); cur_it=f'WHIR L{lvl-1}'; add(cur_it,t)
        elif name in('Open','Induce','Introduce','Sumcheck'):
            if cur_it=='front' and name=='Sumcheck': add('ring switch + claim batching',t)
            else: add(cur_it,t)
        elif name in('Ring switch','Basis'): add('ring switch + claim batching',t)
        elif name=='Final level': add('final/tail',t)
        else: add('??pcs '+name,t)
    S['bus other (leaves+decompose+tables+untraced)']=S['bus total']-S.get('bus GKR',0)
    kids=sum(t for d,n,t,k in nodes if d==1)
    S['untraced (Prove total - top-level children)']=tot-kids
    S['TOTAL (Prove span)']=tot
    return S
if __name__=='__main__':
    cfg={'base_n5_300':['base_n5_300_p1.log','base_n5_300_p2.log'],'base_n6':['base_n6_p1.log','base_n6_p2.log'],'v6_n6':['v6_n6_p1.log','v6_n6_p2.log']}
    res={}
    for c,fs in cfg.items():
        res[c]={}
        for f in fs:
            pre,nodes=parse(f)
            S=stages(nodes); S.update({'PRE '+k:v for k,v in pre.items()})
            res[c][f]=S
    json.dump(res,open(B+'/results/T07d/stages.json','w'),indent=1)
    for c in res:
        for f in res[c]: print(c,f,{k:round(v,1) for k,v in res[c][f].items()})

import subprocess,re,time,sys,os
S=os.path.dirname(os.path.abspath(__file__)); R=os.path.abspath(os.path.join(S,'..','..','results','T00'))
BUDGET=8*2**30
def swap_used(s): return float(re.search(r'used = ([\d.]+)M',s).group(1))
def run(name,args):
    subprocess.run([S+'/run.sh',name]+args)
    t=open(f'{R}/{name}.log').read()
    sb=swap_used(re.search(r'swap_before: (.*)',t).group(1)); sa=swap_used(re.search(r'swap_after: (.*)',t).group(1))
    rss=int(re.search(r'(\d+)\s+maximum resident set size',t).group(1))
    return rss,sa-sb
def sweep(label,sizes,mk):
    last=None
    for s in sizes:
        if last:
            pred=last[1]*s/last[0]
            if pred>BUDGET:
                print(f'SKIP {label} {s}: predicted {pred/2**30:.2f} GiB > budget',flush=True); open(f'{R}/skipped.txt','a').write(f'{label} {s} predicted_peak_GiB={pred/2**30:.2f}\n'); break
        time.sleep(30)
        rss,d=run(*mk(s))
        print(f'{label} {s}: rss={rss/2**30:.2f} GiB swapdelta={d:.0f} MiB',flush=True)
        last=(s,rss)
        if False:
            print('MEMORY-PRESSURED, stop',flush=True); open(f'{R}/skipped.txt','a').write(f'{label} stopped after {s}: swap grew {d:.0f} MiB (memory-pressured)\n'); break
run('fibonacci_n200000_lir1',['fibonacci','--n','200000','--log-inv-rate','1','--repeat','3','--tracing'])
sweep('aggregate',[50,100,250,500,1000,1500],lambda n:(f'aggregate_xmss{n}_lir2',['aggregate','--xmss',str(n),'--log-inv-rate','2','--repeat','3','--tracing']))
sweep('recursion',[50,100,250,500,900],lambda m:(f'recursion_n2_m{m}_leaflir2_lir1',['recursion','--n','2','--xmss-per-leaf',str(m),'--leaf-log-inv-rate','2','--log-inv-rate','1','--repeat','3','--tracing']))
print('DONE')

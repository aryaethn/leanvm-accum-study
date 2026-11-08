import json, os, statistics as st
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'results', 'T07d')
r=json.load(open(os.path.join(R, 'stages.json')))
order=['execute','witness build','commit (encode+Merkle)','bus GKR','bus other (leaves+decompose+tables+untraced)','table sumcheck (Prove constraints)','Keccak reduction','ring switch + claim batching','WHIR L0','WHIR L1','WHIR L2','WHIR L3','final/tail','untraced (Prove total - top-level children)','TOTAL (Prove span)']
med={c:{k:st.median([v[k] for v in r[c].values()]) for k in order} for c in r}
print('| stage | n5_300 ms | n6 ms | diff ms | ratio n6/n5 | v6_n6 ms |')
for k in order:
    a,b,v=med['base_n5_300'][k],med['base_n6'][k],med['v6_n6'][k]
    print(f'| {k} | {a:.1f} | {b:.1f} | {b-a:+.1f} | {b/a:.2f} | {v:.1f} |')
print('sum of diffs excl TOTAL', sum(med['base_n6'][k]-med['base_n5_300'][k] for k in order[:-1]))
for c in r:
    print(c,{f:(round(x['execute'],0),round(x['commit (encode+Merkle)'],0),round(x['TOTAL (Prove span)'],0)) for f,x in r[c].items()})

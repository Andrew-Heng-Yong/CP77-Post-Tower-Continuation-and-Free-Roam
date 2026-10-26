"""Inspect reachable native writes and journal freshness without game changes."""
from common import *
import copy
plan=read(ROOT/'research/sidejobs_s29/plan_01.json')
targets={r['id']:r for r in read(ROOT/'research/sidejobs_s29/scope_01.json')['targets']}
meta=metadata()
rows=[]
for job in plan['jobs']:
    obj=load(job['native']);root=obj['Data']['RootChunk'];hh=handles(obj)
    if job['subset']:
        nodes=deref(root['graph'],hh)['nodes']
        selected=[deref(n,hh) for n in nodes if deref(n,hh)['id'] in job['subset']]
        seeds=[]
        for n in selected:
            seeds+=references(n,'phaseResource')+references(n,'sceneFile')
        deps,missing=closure(seeds);assert not missing
        objects=selected+[load(d)['Data']['RootChunk'] for d in deps]
    else:
        deps=job['closure'];objects=[load(d)['Data']['RootChunk'] for d in deps]
    writes={}
    for obj in objects:
        for n in walk(obj):
            if n.get('$type')=='questSetVar_NodeType':
                name=value(n['factName']);writes.setdefault(name,[]).append({k:v for k,v in n.items() if k!='$type'})
    journals=[]
    for ident in job['journal_ids']:
        jp=targets[ident]['snapshot_row']['root']
        assert meta[jp]=='gameJournalQuest'
        journals += [dict(path=p,**{'class':c},states=[1]) for p,c in meta.items() if p==jp or p.startswith(jp+'/')]
    row={**job,'reachable':deps,'journals':journals,'native_writes':writes}
    rows.append(row)
    print(job['id'],len(deps),'resources',len(journals),'journal entries')
    prefix=job['id'][:5]
    own=[f for f in writes if f.startswith(prefix) or (job['id']=='sts_ep1_12_pickup' and f.startswith('wst_ep1_02'))]
    print('  ', ' '.join(sorted(own)))
write('contracts_review_01.json',{'jobs':rows})

import json,sys
from pathlib import Path
W=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent
A=W/'diagnostics/sidejob_entry_phone_audit_20261026_01'
sys.path.insert(0,str(W/'tools'))
from test_rite_g2 import SafeResource

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def diff(a,b,path=''):
    if type(a)!=type(b):return [{'path':path,'donor':a,'current':b}]
    if isinstance(a,dict):
        out=[]
        for k in sorted(a.keys()|b.keys()):
            if k not in a or k not in b:out.append({'path':path+'/'+k,'donor':a.get(k),'current':b.get(k)})
            else:out+=diff(a[k],b[k],path+'/'+k)
        return out
    if isinstance(a,list):
        if len(a)!=len(b):return [{'path':path,'donor_length':len(a),'current_length':len(b),'donor':a,'current':b}]
        out=[]
        for i,(x,y) in enumerate(zip(a,b)):out+=diff(x,y,path+'/'+str(i))
        return out
    return [] if a==b else [{'path':path,'donor':a,'current':b}]

rows=[]
for r in read(A/'collision_semantics_01.json'):
    if 'graph_differences' not in r:continue
    row={'depot':r['depot'],'graphs':[]}
    for g in r['graph_differences']:
        row['graphs'].append({'path':g['graph'],'removed_nodes':[x['id'] for x in g['removed']],
            'added_nodes':[x['id'] for x in g['added']], 'changes':[{'id':n['id'],'leaves':diff(n['donor'],n['current'])} for n in g['changed']],
            'removed_edges':g['removed_edges'],'added_edges':g['added_edges']})
    rows.append(row)
for r in read(A/'collision_decoded_01/inventory.json'):
    if not r['depot'].endswith('rogue.scene'):continue
    resources=[SafeResource(read(r[k])) for k in ('donor_json','current_json')]
    docs=[]
    for res in resources:
        root=res.obj['Data']['RootChunk'].copy();root.pop('sceneGraph',None)
        docs.append(res.payload(root))
    rows.append({'depot':r['depot'],'non_graph_changes':diff(*docs)})
(O/'compact_changes_01.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:
    if any(x in r['depot'] for x in ['m10_owner','h10_owner','gang_retaliation','rogue.scene']):
        print(json.dumps(r,indent=2))

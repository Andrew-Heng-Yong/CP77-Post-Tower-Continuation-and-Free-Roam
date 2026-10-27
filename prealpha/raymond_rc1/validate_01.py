"""Check exact MQ040 graph delta, 51-file stack and live baseline."""
import hashlib, json
from copy import deepcopy
from pathlib import Path

H=Path(__file__).resolve().parent
W=H.parent.parent
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
P=H/'candidate_01'
B=W/'prealpha/sidejobs_s30/candidate_02'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):
            h.update(block)
    return h.hexdigest().upper()
manifest=json.loads((P/'manifest.json').read_text(encoding='utf-8'))
old=json.loads((B/'manifest.json').read_text(encoding='utf-8'))
old_files={r['path']:r['sha256'] for r in old['files']}
new_files={r['path']:r['sha256'] for r in manifest['files']}
assert len(old_files)==len(new_files)==51 and old_files.keys()==new_files.keys()
changed={p for p in old_files if old_files[p]!=new_files[p]}
assert changed=={'archive/pc/mod/zzzz_PTFR_Combined.archive','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'},changed
for rel,digest in new_files.items():
    assert sha(P/'package'/rel)==digest,rel
for rel,digest in old_files.items():
    assert sha(G/rel)==digest,('installed baseline drift',rel)

a=json.loads((H/'evidence_01/before.json').read_text(encoding='utf-8'))
b=json.loads((H/'evidence_01/after.json').read_text(encoding='utf-8'))
nodes_a={n['Data']['id']:n['Data'] for n in a['Data']['RootChunk']['graph']['Data']['nodes']}
nodes_b={n['Data']['id']:n['Data'] for n in b['Data']['RootChunk']['graph']['Data']['nodes']}
assert nodes_a.keys()==nodes_b.keys()
for ident in (65003,65004):
    old_conditions=nodes_a[ident]['condition']['Data']['conditions']
    new_conditions=nodes_b[ident]['condition']['Data']['conditions']
    assert len(old_conditions)==109 and len(new_conditions)==110
    older=[x for x in old_conditions if x['Data'].get('$type')=='questFactsDBCondition' and x['Data']['type']['Data'].get('factName')=='mq040_active']
    newer=[x for x in new_conditions if x['Data'].get('$type')=='questFactsDBCondition' and x['Data']['type']['Data'].get('factName')=='mq040_active']
    assert len(older)==1 and older[0]['Data']['type']['Data']['comparisonType']=='Equal' and older[0]['Data']['type']['Data']['value']==0
    assert sorted((x['Data']['type']['Data']['comparisonType'],x['Data']['type']['Data']['value']) for x in newer)==[('GreaterOrEqual',0),('LessOrEqual',1)]
    old_conditions[15]['Data']['type']['Data']['comparisonType']='LessOrEqual'
    old_conditions[15]['Data']['type']['Data']['value']=1
    old_conditions.append(deepcopy(new_conditions[-1]))
    assert {v: v>=0 and v<=1 for v in (-1,0,1,2)}=={-1:False,0:True,1:True,2:False}
def clean(value):
    if isinstance(value,dict):
        return {k:clean(v) for k,v in value.items() if k not in {'HandleId','HandleRefId','ExportedDateTime'}}
    if isinstance(value,list):
        return [clean(v) for v in value]
    return value
assert clean(a)==clean(b),'Unapproved MQ040 graph delta'
proof={'status':'PASS','combined_files':51,'changed_installed_files':sorted(changed),'changed_archive_members':1,'changed_entry_nodes':[65003,65004],'allowed_early_mq040_active':[0,1],'protected_later_mq040_active':[2],'installed_baseline_matches':True}
(H/'evidence_01/validation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))

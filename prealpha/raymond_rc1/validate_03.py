"""Bounded RC2 source, graph, package and installed-baseline validation."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'tools')
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten

H=Path(__file__).resolve().parent
W=H.parent.parent
P=H/'candidate_03'
B=W/'prealpha/consolidation_repair_cr1/candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):
            h.update(block)
    return h.hexdigest().upper()
old={r['path']:r['sha256'] for r in json.loads((B/'manifest.json').read_text(encoding='utf-8'))['files']}
new={r['path']:r['sha256'] for r in json.loads((P/'manifest.json').read_text(encoding='utf-8'))['files']}
assert len(old)==len(new)==51 and old.keys()==new.keys()
changed={p for p in old if old[p]!=new[p]}
assert changed=={'archive/pc/mod/zzzz_PTFR_Combined.archive','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'},changed
for rel,digest in old.items():
    assert sha(G/rel)==digest,('installed CR1 drift',rel)
for rel,digest in new.items():
    assert sha(P/'package'/rel)==digest,('candidate drift',rel)

def graphs(name):
    d=json.loads((H/'evidence_02'/name).read_text(encoding='utf-8'))
    r=SafeResource(d)
    return {g['path']:g for g in flatten(r,d['Data']['RootChunk'])}
before=graphs('native_before.json')
after=graphs('native_after.json')
assert before.keys()==after.keys()
for path in before:
    old_nodes={n['id']:n for n in before[path]['nodes']}
    new_nodes={n['id']:n for n in after[path]['nodes']}
    if path=='root':
        assert set(new_nodes)==set(old_nodes)|{65000}
        assert new_nodes[65000]=={'$type':'questConditionNodeDefinition','condition':{'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'mq040_active','value':1}},'id':65000}
        old_edges=set(map(tuple,before[path]['edges']))
        new_edges=set(map(tuple,after[path]['edges']))
        assert old_edges-new_edges=={(0,'Out',3,'In1')}
        assert new_edges-old_edges=={(0,'Out',65000,'In'),(65000,'False',3,'In1'),(65000,'True',4,'In1')}
    else:
        assert before[path]['edges']==after[path]['edges'],path
        assert old_nodes.keys()==new_nodes.keys(),path
    for ident in old_nodes:
        assert old_nodes[ident]==new_nodes[ident],(path,ident)

a=json.loads((H/'evidence_02/entry_before.json').read_text(encoding='utf-8'))
b=json.loads((H/'evidence_02/entry_after.json').read_text(encoding='utf-8'))
na={n['Data']['id']:n['Data'] for n in a['Data']['RootChunk']['graph']['Data']['nodes']}
nb={n['Data']['id']:n['Data'] for n in b['Data']['RootChunk']['graph']['Data']['nodes']}
assert na.keys()==nb.keys()
def fact(c):
    d=c['Data'];assert d['$type']=='questFactsDBCondition'
    v=d['type']['Data'];return (v['factName'],v['comparisonType'],v['value'])
for ident in (65003,65004):
    old_guard=na[ident]['condition']['Data']['conditions']
    guard=nb[ident]['condition']['Data']['conditions']
    assert len(old_guard)==109 and len(guard)==111
    assert fact(old_guard[15])==('mq040_active','Equal',0)
    assert fact(guard[15])==('mq040_active','LessOrEqual',1)
    assert fact(guard[-2])==('mq040_active','GreaterOrEqual',0)
    outer=guard[-1]['Data'];assert outer['$type']=='questLogicalCondition' and outer['operation']=='OR'
    assert fact(outer['conditions'][0])==('mq040_active','Equal',0)
    inner=outer['conditions'][1]['Data'];assert inner['$type']=='questLogicalCondition' and inner['operation']=='AND'
    assert [fact(x) for x in inner['conditions']]==[('elcoyote_barman_default_on','Equal',0),('PTFRB0STPEPE_OwnerActive','Equal',0)]

def admit(active,barman,owner):
    return 0<=active<=1 and (active==0 or (barman==0 and owner==0))
assert admit(0,1,1) and admit(1,0,0)
assert not admit(1,1,0) and not admit(1,0,1) and not admit(2,0,0)
assert json.loads((H/'compile_03/result.json').read_text())['status']=='PASS'
report={'status':'STATIC_PASS_LIVE_TEST_PENDING','combined_files':51,'changed_install_files':sorted(changed),'changed_members':2,'normal_fresh_route':'unchanged','stranded_setup_route':'skips setup spawns and enters original bar phase','lease_state_required':'barman_default_on=0 and PTFRB0STPEPE_OwnerActive=0','compile':'PASS','game_writes':0,'save_writes':0}
(H/'evidence_02/validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))

"""Offline native graph contracts and execution model, not an engine test."""
import binascii
import hashlib
import json
import re
from pathlib import Path
from test_streetkid_scene_load_s3 import quest_edges

root=Path(__file__).resolve().parents[1]
audit=root/'research/b0_tv_restore'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
m=read(audit/'manifest.json')
r=read(audit/'bootstrap.json')['Data']['RootChunk']
edges,nodes=quest_edges(r)
nodes={n['id']:n for n in nodes}
assert len(nodes)==6 and not r['phasePrefabs']
assert edges=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'True',3,'In'),(2,'False',4,'In'),(3,'Out',4,'In'),(4,'Out',5,'In')}
guard=nodes[1]['condition']['Data']
assert guard['$type']=='questLogicalCondition' and guard['operation']=='AND'
expected=dict(PostTowerFreeRoamActive=1,PTFRP0_DR13=1,q307_active=0,q307_done=1,q307_finished=1,q307_2079=1,q307_main_game_killed=1,q305_johnny_scene_active=0,q115_point_of_no_return=0,PTFRBASE_Suspended=0,PTFRTV_Suspended=0,PTFRTV_Applied=0)
actual={}
for c in guard['conditions']:
    assert c['Data']['$type']=='questFactsDBCondition'
    t=c['Data']['type']['Data']
    assert t['$type']=='questVarComparison_ConditionType' and t['comparisonType']=='Equal'
    actual[t['factName']]=t['value']
assert len(guard['conditions'])==len(expected) and actual==expected==m['guards']
c=nodes[2]['condition']['Data']['type']['Data']
assert c==dict({'$type':'questVarComparison_ConditionType'},comparisonType='Equal',factName='tv_on',value=0)
for i,f in [(3,'tv_on'),(4,'PTFRTV_Applied')]:
    t=nodes[i]['type']['Data']
    assert t['$type']=='questSetVar_NodeType' and (t['factName'],t['value'],t['setExactValue'])==(f,1,1)
assert nodes[5]['$type']=='questOutputNodeDefinition'

# Execute the serialized graph with a small fact-only interpreter. Blocked
# guards have no writes; once marked, new instantiation cannot overwrite a
# subsequent legitimate TV shutdown. Already-on/custom nonzero values stay.
def condition(c, facts):
    if c['$type']=='questLogicalCondition':return all(condition(x['Data'],facts) for x in c['conditions'])
    t=c['type']['Data'];assert t['comparisonType']=='Equal'
    return facts.get(t['factName'],0)==t['value']
def execute(facts):
    f=dict(facts);writes=[];i=0
    for _ in range(10):
        n=nodes[i];typ=n['$type'];socket='Out'
        if typ=='questOutputNodeDefinition':return f,writes
        if typ=='questPauseConditionNodeDefinition' and not condition(n['condition']['Data'],f):return f,writes
        if typ=='questConditionNodeDefinition':socket='True' if condition(n['condition']['Data'],f) else 'False'
        if typ=='questFactsDBManagerNodeDefinition':
            t=n['type']['Data'];f[t['factName']]=t['value'];writes.append((t['factName'],t['value']))
        destinations=[e[2] for e in edges if e[:2]==(i,socket)]
        assert len(destinations)==1;i=destinations[0]
    raise AssertionError('Unexpected loop')
base=expected|{'tv_on':0,'q307_2079':1,'unrelated_quest_fact':23}
result,writes=execute(base)
assert writes==[('tv_on',1),('PTFRTV_Applied',1)]
for k in base:
    if k not in ('tv_on','PTFRTV_Applied'):assert result[k]==base[k]
negative=0
for name,value in expected.items():
    for bad in (-1,0,1,2):
        if bad==value:continue
        f=base|{name:bad};assert execute(f)==(f,[]);negative+=1
for value in (-1,1,2):
    f,w=execute(base|{'tv_on':value});assert f['tv_on']==value and w==[('PTFRTV_Applied',1)]
for value in (0,1):
    f=result|{'tv_on':value};assert execute(f)==(f,[])
depot=m['resource'];crc=binascii.crc_hqx((depot+':1').encode(),65535)
assert crc==m['registration_id']
for p in (root/'archive').rglob('*.xl'):
    for d in re.findall(r'path:\s*([^\s#]+\.questphase)',p.read_text(encoding='utf-8-sig')):
        if d!=depot:assert binascii.crc_hqx((d+':1').encode(),65535)!=crc,(p,d)
archive=root/'build/TVRestore/TowerContinued_TVRestore.archive'
assert hashlib.sha256(archive.read_bytes()).hexdigest().upper()==m['archive_sha256']
xl=Path(str(archive)+'.xl')
assert hashlib.sha256(xl.read_bytes()).hexdigest().upper()==m['xl_sha256']
assert re.findall(r'path:\s*([^\s#]+\.questphase)',xl.read_text())==[depot]
assert 'parent: ep1\\quest\\ep1.quest' in xl.read_text()
print(f'PASS: native one-shot graph, {negative} negative guards, conditional TV write, no story writes/owner restart, saved-state idempotence, registration and archive hashes')

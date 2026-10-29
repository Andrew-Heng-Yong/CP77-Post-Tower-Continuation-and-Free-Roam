"""Check the serialized clinic owner independently of its builder."""
import copy, hashlib, itertools, json, sys
from pathlib import Path
W=Path(__file__).resolve().parents[2]
H=Path(__file__).resolve().parent
C=H/'candidate_02'
sys.path.insert(0,str(W/'diagnostics/skippy_triggers_20261027_01/runtime_review'))
from inspect_graph_01 import Resource, walk
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
r=Resource(C/'owner_readback_01.json');n={i:r.plain(v) for i,v in r.nodes(r.graph).items()};e=r.edges(r.graph)
b=read(C/'build_01.json');g=b['guards'];target=b['target'];checks=[]
def check(name,value):
    checks.append({'name':name,'pass':bool(value)})
    assert value,name
def evaluate(c,f,loaded):
    kind=c['$type']
    if kind=='questLogicalCondition':
        a=[evaluate(x,f,loaded) for x in c['conditions']]
        return all(a) if c['operation']=='AND' else any(a)
    if kind=='questFactsDBCondition':
        t=c['type'];eq=f.get(t['factName'],0)==t['value']
        assert t['comparisonType'] in ('Equal','NotEqual')
        return eq if t['comparisonType']=='Equal' else not eq
    if kind=='questNodeLoadingCondition':
        assert c['objectRef']['$value']==target
        return not loaded if c['inverted'] else loaded
    raise ValueError(kind)
expected={(0,'Out',1,'In'),(1,'True',2,'In'),(2,'Out',3,'In'),(3,'Out',10,'In'),(10,'Out',11,'In'),(11,'False',10,'In'),(11,'True',12,'In'),(12,'Out',13,'In'),(13,'Out',14,'In'),(14,'Out',15,'In'),(15,'Out',16,'In'),(16,'Out',10,'In')}
check('Exact lifecycle edges and node IDs',e==expected and set(n)=={0,1,2,3,10,11,12,13,14,15,16})
check('Duplicate owner rejected',evaluate(n[1]['condition'],{},False) and not evaluate(n[1]['condition'],{'PTFRVD1_Claimed':1},True))
check('Admission wait and immediate recheck agree',n[10]['condition']==n[11]['condition'])
oldguards=read(W/'research/misty_viktor_world/access_r11_manifest.json')['guards']
check('Preserves all existing world gates and adds setup completion',g==dict(oldguards,PTFRPA2_Finished=1))
check('Valid loaded door admitted',evaluate(n[10]['condition'],g,True))
check('Valid unloaded door waits',not evaluate(n[10]['condition'],g,False))
check('Stable loaded world cannot repeat requests',not evaluate(n[15]['condition'],g,True))
check('Streaming loss rearms',evaluate(n[15]['condition'],g,False))
for key in g:
    f=dict(g);f[key]+=1
    check('Reject changed gate '+key,not evaluate(n[10]['condition'],f,True) and evaluate(n[15]['condition'],f,True))
# Enumerate the logical gate combinations using the serialized flat fact predicates.
admit=n[10]['condition']['conditions'][0];release=n[15]['condition']['conditions'][0]
check('Admission AND and release OR',admit['operation']=='AND' and release['operation']=='OR')
forward=[x['type'] for x in admit['conditions']];reverse=[x['type'] for x in release['conditions']]
check('Every gate has exact inverse',len(forward)==len(g)==len(reverse) and all(a['factName']==z['factName'] and a['value']==z['value'] and a['comparisonType']=='Equal' and z['comparisonType']=='NotEqual' for a,z in zip(forward,reverse)))
states=0
for matched in itertools.product((False,True),repeat=len(g)):
    f={key:value if ok else value+1 for (key,value),ok in zip(g.items(),matched)}
    assert evaluate(n[10]['condition'],f,True)==all(matched)
    assert evaluate(n[15]['condition'],f,True)==(not all(matched))
    states+=1
p=n[12]['type']['params']
check('One exact native unlock only',len(p)==1 and p[0]['deviceAction']['$value']=='ForceUnlock' and p[0]['deviceControllerClass']['$value']=='DoorControllerPS' and p[0]['objectRef']['$value']==target and not p[0]['actionProperties'])
writes=[x['type'] for x in n.values() if x.get('type',{}).get('$type')=='questSetVar_NodeType']
check('Only five mod-owned diagnostic fact writes',len(writes)==5 and all(x['factName'].startswith('PTFRVD1_') for x in writes))
check('Counter and readiness lifecycle',n[13]['type']['factName']=='PTFRVD1_Requests' and n[13]['type']['setExactValue']==0 and n[14]['type']['value']==1 and n[16]['type']['value']==0)
providers=read(H/'native_review_03/providers.json')
phase=next(v for v in providers['providers'] if v['depot'].endswith('q307_06_viktor.questphase'))
native=Resource(Path(phase['source']+'.json'));native_nodes=native.nodes(native.graph)
actions=[x for x in walk(native.plain(native_nodes[42])) if 'deviceAction' in x]
check('Current vanilla explicitly locks this clinic door',len(actions)==1 and actions[0]['objectRef']['$value']=='#q115_dvc_ripperdoc_room_door' and actions[0]['deviceAction']['$value']=='ForceLock')
oldphase=Resource(W/'prealpha/credits_cover_lc4/candidate_02/archive_source/towercontinued/misty_viktor_world/access_r11.questphase.json') if (W/'prealpha/credits_cover_lc4/candidate_02/archive_source/towercontinued/misty_viktor_world/access_r11.questphase.json').exists() else Resource(Path(next(v['source'] for v in providers['providers'] if v['depot'].endswith('access_r11.questphase'))+'.json'))
oldactions=[x for x in walk(oldphase.plain(oldphase.graph)) if 'deviceAction' in x]
check('Existing access owner omits clinic target',not any('q115_dvc_ripperdoc_room_door' in x['objectRef']['$value'] for x in oldactions))
unlock_source=(W/'research/finalboards_dismissal/decompiled/cyberpunk/devices/door/doorController.script').read_text()
handler=unlock_source.split('public final func OnQuestForceUnlock(',1)[1].split('private final func ',1)[0]
check('Native unlock clears lock and seal without forcing open','this.SetIsLocked(false);' in handler and 'this.SetIsSealed(false);' in handler and 'SetIsOpened' not in handler)
oldxl=(W/'prealpha/credits_cover_lc4/candidate_02/package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl').read_bytes()
newxl=(C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl').read_bytes()
nl=b'\r\n' if b'\r\n' in oldxl else b'\n'
addition=nl.join([('    - path: '+b['new_resource']).encode(),b'      parent: ep1\\quest\\ep1.quest',b'      input:',b'        node: [1]',b'        socket: Out'])+nl
check('One new registration with exact prior XL retained',newxl.count(addition)==1 and newxl.replace(addition,b'')==oldxl)
check('Every existing archive member unchanged',b['old_member_bytes_unchanged']==1563 and b['archive_members']==1564 and len(b['members'])==1564)
for row in b['package_files']:
    check('Package hash '+row['path'],sha(C/'package'/row['path'])==row['after'])
check('Only archive and XL change',{x['path'] for x in b['package_files'] if x['before']!=x['after']}=={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl'})
# Negative controls exercise target, inverse gate and edge failure detection.
bad=copy.deepcopy(n[10]['condition']);bad['conditions'][1]['objectRef']['$value']='$/unrelated'
try:evaluate(bad,g,True)
except AssertionError:pass
else:raise AssertionError('Wrong-door negative control accepted')
check('Missing guard and added action edge are detectable',len(forward[:-1])!=len(g) and e|{(3,'Out',12,'In')}!=expected)
report={'status':'PASS_INDEPENDENT_SERIALIZED_OWNER_CHECKS','checks':checks,'guard_combinations':states,'negative_controls':3,'game_writes':0,'save_writes':0,'limits':['Observed symptom plus concrete omitted unlock; no current live door-state capture.','EndGameSave-62 has no matching PersistencySystem2 entry under the historical entity ID; not evidence that the door is unlocked.','Runtime opening, streaming and reload require gameplay observation.']}
(C/'verification_01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'checks':len(checks),'guard_combinations':states}))

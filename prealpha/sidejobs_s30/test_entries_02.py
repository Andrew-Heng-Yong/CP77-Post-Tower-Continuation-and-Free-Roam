"""Readback of three native entry wrappers and their side job contracts."""
import json,sys
from pathlib import Path
sys.path.insert(0,'prealpha/sidejobs_s29')
from common import read,walk,value,SafeResource,flatten,handles,deref
ROOT=Path(__file__).resolve().parents[2];H=ROOT/'prealpha/sidejobs_s30';checks=0
def check(ok,msg):
 global checks
 assert ok,msg;checks+=1
contracts=read(H/'prepared_02/contracts.json')['jobs']
manifest=read(H/'serialized_02/entries_manifest.json')
assert len(contracts)==len(manifest['entries'])==3
expected={'mq006_rollercoaster','mws_se5_07','mws_wat_08_trauma_drama'}
check({x['id'] for x in contracts}==expected,'three entry IDs')
for rec in manifest['entries']:
 job=next(x for x in contracts if x['id']==rec['id'])
 obj=read(H/'serialized_02/entry_readback'/(rec['depot']+'.json'))
 g=flatten(SafeResource(obj),obj['Data']['RootChunk'])[0]
 ns={n['id']:n for n in g['nodes']};edges=g['edges']
 check(edges==sorted(rec['edges']),('entry edges',job['id']))
 check(ns[65003]['condition']==ns[65004]['condition'],('atomic recheck',job['id']))
 check([65004,'False',65003,'In'] in edges and [65004,'True',65005,'In'],('durable claim',job['id']))
 check(ns[65007]['type']['factName']==job['tag']+'_Finished',('completion receipt',job['id']))
 node=ns[rec['child']]
 check(value(node['phaseResource']['DepotPath'])==job['private_native'],('private native phase',job['id']))
 guard={v['factName']:v['value'] for v in walk(ns[65003]['condition']) if v.get('$type')=='questVarComparison_ConditionType' and v.get('comparisonType')=='Equal'}
 for fact,num in rec['guard'].items():check(guard.get(fact)==num,('guard',job['id'],fact))
 check(job['tag']+'_Permit' in guard and guard[job['tag']+'_Permit']==1,('permit guard',job['id']))
 check(job['tag']+'_Issued' in guard and guard[job['tag']+'_Issued']==0,('issued guard',job['id']))
 if job['id']=='mq006_rollercoaster':
  check([65005,'Out',65008,'In'] in edges and [65008,'Out',65006,'In'] in edges,'coaster lease before story')
  check([20,'Out1',65009,'In'] in edges and [65009,'Out',65007,'In'] in edges,'coaster lease release after story')
  check(ns[65008]['type']['factName']=='PTFRWORLD_Coaster_QuestOwns' and ns[65008]['type']['value']==1,'coaster acquire')
  check(ns[65009]['type']['factName']=='PTFRWORLD_Coaster_QuestOwns' and ns[65009]['type']['value']==0,'coaster release')
  check({54,55,59,62,70,73,80,81,83,84,86,20}<=set(ns),'native q001/q005/q101 parent chain retained')
 else:check([65006,'Out',rec['child'],job['input']] in edges and [rec['child'],job['output'],65007,'In'] in edges,('original input/output port',job['id']))
 if job['id']=='mws_wat_08_trauma_drama':
  check('shooter_appeared_on_leaderboard' in {x['name'] for x in job['facts']} and job['fact_ranges']['shooter_appeared_on_leaderboard']['min']==1,'earned leaderboard gate')
 if job['id']=='mws_se5_07':check(job['vehicle_zero']==[{'record':'Vehicle.v_sport2_porsche_911turbo_cabrio_player'}],'Porsche ownership guard')
xl=(H/'candidate_02/package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl').read_text(encoding='utf-8')
for job in contracts:check(xl.count('towercontinued\\sidejobs_s30\\entries\\'+job['id']+'.questphase')==1,('XL registration',job['id']))
check('mq057_motorbreath' not in xl,'River entry hold')
lip=read(H/'serialized_02/lipmap_readback.json')['Data']['RootChunk']
check(len(lip['scenePaths'])==len(lip['sceneEntries'])==48,'four extra English lipmap registrations')
proof={'status':'PASS_STATIC_ENTRY_AND_GUARD_NOT_LIVE','checks':checks,'entries':len(contracts)}
(H/'serialized_02/test_entries_02.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))

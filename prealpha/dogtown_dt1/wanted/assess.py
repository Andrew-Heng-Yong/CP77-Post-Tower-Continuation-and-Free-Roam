"""Bind the wanted report to exact stock gate paths and prevention evidence."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'tools')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def main():
 out=ROOT/'research/dogtown_dt1/wanted/assessment_01.json'
 if out.exists():raise FileExistsError(out)
 gate=ROOT/'research/dogtown_dt1/gate/native_01/json/ep1/openworld/combat_zone_gate/combat_zone_gate.questphase.json'
 r=SafeResource(read(gate));graphs={g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
 g=graphs['root/105'];nodes={n['id']:n for n in g['nodes']};edges=g['edges'];checks=0
 for e in [[0,'Out',2,'In'],[0,'Out',3,'In'],[2,'Out',4,'In1'],[3,'Out',4,'In2'],[4,'Out1',10,'In'],[10,'True',5,'In'],[5,'Out',6,'In1'],[6,'Out1',1,'In']]:assert e in edges;checks+=1
 assert nodes[2]['condition']['type']['deviceConditionFunction']['$value']=='IsSystemInCombat';checks+=1
 assert nodes[2]['condition']['type']['objectRef']['$value']=='#combat_zone_gate_dvc_security_system';checks+=1
 condition=nodes[3]['condition'];assert condition['operation']=='OR';checks+=1
 actors=[]
 for c in condition['conditions']:
  t=c['type'];assert t['$type']=='questCharacterCombat_ConditionType' and t['isPlayer']==0 and t['inverted']==0;checks+=3
  actor=t['objectRef'];assert actor['reference']['$value']=='#combat_zone_gate_com';checks+=1
  actors.extend(n['$value'] for n in actor['names'])
 assert nodes[10]['condition']['type']=={'$type':'questVarComparison_ConditionType','comparisonType':'Less','factName':'wanted_level','value':3};checks+=1
 assert nodes[5]['event']['$type']=='SetWantedLevel' and nodes[5]['event']['wantedLevel']=='Heat_3';checks+=2
 for key in ['forceGreyStars','forceIgnoreSecurityAreas','forcePlayerPositionAsLastCrimePoint','resetGreyStars']:assert nodes[5]['event'][key]==0;checks+=1
 tests=read(ROOT/'research/dogtown_dt1/wanted/tests_01.json');assert tests['status']=='PASS_NATIVE_EVIDENCE_AND_LUAJIT_NOT_LIVE';checks+=1
 files=[gate,HERE/'assess.py',ROOT/'research/dogtown_dt1/wanted/tests_01.json',ROOT/'research/dogtown_dt1/wanted/saved_prevention_01.json',ROOT/'research/dogtown_dt1/wanted/native_records_01.json']
 report={
  'status':'SOURCE_BACKED_GATE_WANTED_DEPENDENCY_IDENTIFIED_NOT_LIVE_PASS',
  'separate_wanted_runtime_component':False,
  'repair_owner':'gate component restores original gate controller including root/105; no separate prevention reset or new star-forcing policy',
  'reported_context':'User shot Barghest guards and courier vehicle could not cross Dogtown gate; exact shooting location not yet independently confirmed.',
  'cause_scope':'Killed/missing gate owner removes the explicit stock guard-combat to Heat_3 branch. This explains checkpoint-specific escalation failure; does not prove all Dogtown prevention failure has same cause.',
  'native_branch':{'graph':'root/105','guard_combat_actors':actors,'security_node':2,'guard_node':3,'threshold_node':10,'event_node':5,'payload':nodes[5]['event'],'edges':edges},
  'stock_heat_tables':tests['heat0'],
  'saved_observation':'Both snapshots decode prevention enabled, empty source-lock array and quest multiplier1. No identified persistent blanket lock. Parser constructor defaults are separately recorded; nonpersistent HLS/district/free-area/heat-limiter state is not inferred.',
  'not_modified':['prevention native script','prevention source locks','mq304 leadership facts','crime multipliers/heat tables','quest-specific safe areas','wanted_level facts','save files'],
  'manual_diagnostic':(HERE/'diagnostic.lua').read_text().strip(),
  'diagnostic_use':'If wanted still fails away from gate, reproduce outdoors away from shops/security areas, then run the readonly command; output distinguishes disabled/locked/input suppression, district recognition, free-area and heat. Nil/errors return Unknown.',
  'live_acceptance':['Approach gate in vehicle without combat/wanted; stock scan and doors should work.','On a disposable branch, gate guard combat should follow the original wanted escalation/lockdown. Do not use the combat branch to test peaceful courier passage.','Repeat wanted test on a normal Dogtown street away from the gate; do not claim district-wide pass from gate alone.','Escape/de-escalate normally, save/reload and repeat peaceful crossing.'],
  'checks':checks,'prior_command_and_table_checks':tests['checks'],
  'source_pins':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files},
  'game_writes':0,'save_writes':0,'native_writes':0,
 }
 out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'output':str(out),'checks':checks,'guard_actor_count':len(actors)}))
if __name__=='__main__':main()

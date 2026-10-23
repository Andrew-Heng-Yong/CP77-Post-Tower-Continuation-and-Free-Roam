"""Independent read-only scene-binding review; writes a new workspace report only."""
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SERVICES=ROOT/'prealpha/sidejobs_s25/services'
# Use the scene-aware service reader, not this directory's graph-only reader.
sys.path.insert(0,str(SERVICES))
sp=importlib.util.spec_from_file_location('s25_services_review_tests',SERVICES/'test.py')
t=importlib.util.module_from_spec(sp);sp.loader.exec_module(t)
def main():
 build=ROOT/sys.argv[1];report=ROOT/sys.argv[2];assert not report.exists()
 base=t.verify(build);m=t.read(build/'build.json');contract=t.read(ROOT/m['contract'])
 gun=next(o for o in contract['owners'] if o['key']=='GUN')
 r=t.scene(build/'readback/gun_scene.json');ns=t.sn(r);checks=0
 assert len(r['actors'])==1;actor=r['actors'][0]
 assert actor['actorName']=='wilson' and actor['acquisitionPlan']=='spawnSet'
 assert t.value(actor['spawnSetParams']['reference'])=='#wilson';checks+=3
 assert r['props']==[];checks+=1
 for ep in r['entryPoints']:
  assert ep['nodeId']['id'] in ns
  assert t.value(ep['name'])=='wilson_default_in';checks+=2
 assert r['sceneGraph']['startNodes']==[{'$type':'scnNodeId','id':0}];checks+=1
 assert r['exitPoints']==[] and r['sceneGraph']['endNodes']==[];checks+=1
 for n in ns.values():
  for v in t.walk(n):
   if v.get('$type')=='scnPropId':assert v['id']==4294967295;checks+=1
 for sc in r['interruptionScenarios']:
  assert sc['id']['id']==0 and sc['enabled']==1 and sc['talkOnReturn']==0;checks+=1
 # The only surviving section-condition self-reference resolves to an actual
 # retained notable section, not a removed original-scene node.
 names={t.value(p['name']):p['nodeId']['id'] for p in r['notablePoints']}
 section=ns[512]['questNode']['condition']['type']
 assert t.value(section['sceneFile']['DepotPath'])==gun['scene_depot']
 assert names[t.value(section['sectionName'])]==308 and ns[308]['$type']=='scnSectionNode';checks+=2
 assert t.sedges(ns[678])==[[[224,1]]];checks+=1
 # Reused B0 body remains the sole actor/proximity owner. S23 MQ011 owner file
 # is only pinned and is not replaced by the fresh Gun route.
 assert not any(p.endswith('owner.questphase') for p in m['resources']);checks+=1
 body=t.graphs(build/'readback/wilson_body.json')['root'];bn=t.nmap(body)
 assert t.value(bn[101]['sceneFile']['DepotPath'])==gun['scene_depot']
 assert (12,'CutSource',101,'CutDestination') in t.es(body);checks+=2
 pins={str(p.relative_to(ROOT)).replace('\\','/'):t.sha(p) for p in (Path(__file__),SERVICES/'test.py',SERVICES/'inspect.py',ROOT/m['contract'],build/'build.json',build/'tests.json')}
 result={'status':'PASS_INDEPENDENT_BOUNDED_SCENE_REVIEW_NOT_LIVE','component':str((build/'build.json').relative_to(ROOT)).replace('\\','/'),'component_sha256':t.sha(build/'build.json'),'source_pins':pins,'base_readonly_verifier':base,'additional_scene_binding_checks':checks,'findings':[],'notes':['Paid in Full restores only native debt options with original debit metadata; existing Viktor scene/actors unchanged outside declared options.','Gun uses one existing Wilson actor/proximity owner; native inventory reward branch preserved and Dying Night quantity protects repeated grant.','Reachable Gun sections use no real props; entry/start, interruption path and scoped section self-reference resolve.','Services proof covers static native structure only; actual prompt/payment/inventory behavior and reload need fresh-save playtest.']}
 report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':result['status'],'checks':checks,'component_sha256':result['component_sha256']}))
if __name__=='__main__':main()

"""Resolve Johnny workspots through current world/animation sources, retaining unknowns."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import walk,value
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def main():
 out=ROOT/'research/sidejobs_s28/vehicles/presentation_01.json';assert not out.exists()
 wi=read(ROOT/'research/sidejobs_s28/vehicles/workspots_01/inventory.json');ai=read(ROOT/'research/sidejobs_s28/vehicles/animations_01/inventory.json');world=read(ROOT/'research/sidejobs_s28/vehicles/world_03/inventory.json')
 pins={};checks=0;animation={}
 for index in ['workspots_01/inventory.json','animations_01/inventory.json','world_03/inventory.json']:
  p='research/sidejobs_s28/vehicles/'+index;pins[p]=sha(ROOT/p)
 for row in wi['rows']+ai['rows']:
  for field in ['raw','json']:
   assert sha(ROOT/row[field])==row[field+'_sha256'];checks+=1;pins[row[field]]=row[field+'_sha256']
 for row in ai['rows']:
  data=read(ROOT/row['json'])['Data']['RootChunk'];clips=[]
  for x in walk(data):
   if x.get('$type')=='animAnimSetEntry':
    anim=x['animation']['Data'];events=(x.get('events') or {}).get('Data',{})
    actions=[a for a in walk(events) if a.get('$type','').startswith('work') and ('Action' in a.get('$type',''))]
    clips.append({'name':value(anim['name']),'actions':actions,'event_types':sorted({e['$type'] for e in walk(events) if e.get('$type','').startswith('animAnimEvent')})})
  animation[row['depot']]=clips
 reports=[]
 for row in wi['rows']:
  data=read(ROOT/row['json'])['Data']['RootChunk'];nodes=list(walk(data));names={value(x[k]) for x in nodes for k in ['animName','idleAnim'] if k in x};names.discard('None')
  refs={value(x['DepotPath']) for x in nodes if 'DepotPath' in x and str(value(x['DepotPath'])).endswith('.anims')}
  matched=[];transitions=[]
  for ref in sorted(refs):
   for clip in animation[ref]:
    if clip['name'] in names:matched.append(dict(source=ref,**clip))
    elif '__to__' in clip['name'] and any(n in clip['name'] for n in names):transitions.append(dict(source=ref,**clip))
  allmatched={c['name'] for c in matched};missing=sorted(names-allmatched)
  reports.append({'depot':row['depot'],'initial_actions':[x['initialActions'] for x in nodes if 'initialActions' in x],'global_props':[x['globalProps'] for x in nodes if 'globalProps' in x],'entry_animation_names':sorted(names),'matched_clips':matched,'related_automatic_transitions':transitions,'missing_named_clips':missing,'explicit_item_actions':[{'clip':c['name'],'action':a} for c in matched for a in c['actions']],'transition_actions':[{'clip':c['name'],'action':a} for c in transitions for a in c['actions']]})
 worldrefs=[]
 wanted={'{mq050_ws_johnny}','{mq029_ws_johhny_josie_garage}','{mq029_ws_johnny_find_josie}'}
 for row in world['rows']:
  if not row['parsed'] or '_quest_' not in row['json']:continue
  data=read(ROOT/row['json'])
  for n in walk(data['Data']['RootChunk']):
   if n.get('$type')=='worldAISpotNode' and value(n.get('debugName')) in wanted:
    ref=value(n['spot']['Data']['resource']['DepotPath']);assert ref in {r['depot'] for r in reports};checks+=1
    for f in ['raw','json']:pins[row[f]]=row[f+'_sha256']
    worldrefs.append({'name':value(n['debugName']),'workspot':ref,'sector':row['depot'],'raw':row['raw'],'json':row['json']})
 assert {r['name'] for r in worldrefs}==wanted;checks+=1
 owner='research/sidejobs_s28/encounters/johnny_owner_01.json'
 if (ROOT/owner).exists():pins[owner]=sha(ROOT/owner)
 pins[str(Path(__file__).relative_to(ROOT)).replace('\\','/')]=sha(__file__)
 result={'status':'SOURCE_PRESENTATION_RISKS_IDENTIFIED_NOT_CLEARED','checks':checks,'world_references':worldrefs,'workspots':reports,'source_pins':pins,'world_scan_errors':len(world['errors']),'limitations':['World scan errors are retained; all three requested vehicle Johnny NodeRefs resolved exactly.','Empty scene props/initialActions does not prove no independent props: animation item actions are separately inspected.','Automatic transition matching is a conservative name-endpoint screen, not engine execution proof.','Candidate boots remain empty; cigarette/glasses events require scoped remediation before vehicle dispatch.']}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'path':str(out),'checks':checks,'sha256':sha(out),'workspots':[{k:r[k] for k in ['depot','missing_named_clips','explicit_item_actions','transition_actions']} for r in reports]}))
if __name__=='__main__':main()

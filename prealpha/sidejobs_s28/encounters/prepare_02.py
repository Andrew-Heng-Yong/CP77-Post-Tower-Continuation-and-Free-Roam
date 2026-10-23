"""Bounded S28 encounter native beginnings; no predecessor generator main calls."""
import json,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk,value,handles,deref
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten,references
from prepare_gig_family_b7 import ancestors,descendants
from prepare_native_gigs_u9 import facts
HERE=ROOT/'research/sidejobs_s28/encounters'
INDEX='research/omitted_jobs_audit/native_screen_03.json'
PARENT='research/sidejobs_s2/sacrum_audit/native_01/json/base/quest/minor_quests/minorquests.questphase.json'
JOURNAL='research/gig_restoration/journal_sources/json/base/journal/cooked_journal.journal.json'
SPECS=[('mq003_orbitals','Space Oddity',7,r'base\quest\minor_quests\mq003\mq003_orbitals.questphase'),('mq022_ezekiel','Ezekiel Saw the Wheel',6,r'base\quest\minor_quests\mq022\mq022.questphase')]
ITEMS={'mq003_orbitals':[('Items.mq003_shard',74384870070),('Items.mq003_painting',89925329454)]}
def raw(j):return j.replace('/json/','/raw/').removesuffix('.json')
def main():
 assert not (HERE/'contracts_02.json').exists()
 idx=read(ROOT/INDEX);pins={};owners=[];jobs=[]
 def pin(p,paired=False):
  pins[p]=sha(ROOT/p)
  if paired:pins[raw(p)]=sha(ROOT/raw(p))
 for p in [INDEX,str(Path(__file__).relative_to(ROOT)).replace('\\','/'), 'tools/catalog_gig_rollout_r2.py','tools/test_rite_g2.py','tools/test_gig_pilot_r1.py','tools/audit_activity_batches_b1.py','tools/prepare_gig_family_b7.py','tools/prepare_native_gigs_u9.py']:pin(p)
 pin(PARENT,True);pin(JOURNAL,True)
 proof=read(HERE/'source_assessment_01.json');pin('research/sidejobs_s28/encounters/source_assessment_01.json')
 for p in proof['source_pins']:pin(p)
 current_mq003='research/sidejobs_s28/encounters/official_check_01/basegame_4_gamedata/json/base/quest/minor_quests/mq003/mq003_orbitals.questphase.json'
 idx['resources'][SPECS[0][3]]={**idx['resources'][SPECS[0][3]],'source':current_mq003}
 jd=read(ROOT/JOURNAL);hh=handles(jd);catalog={}
 def visit(w,path):
  n=deref(w,hh);p=path+([n['id']] if n.get('id') else []);catalog['/'.join(p)]=n.get('$type')
  for c in n.get('entries',[]):visit(c,p)
 visit(jd['Data']['RootChunk']['entry'],[])
 pr=SafeResource(read(ROOT/PARENT));pg=flatten(pr,pr.obj['Data']['RootChunk'])[0];pns={n['id']:n for n in pg['nodes']}
 for ident,title,child,main in SPECS:
  keep=ancestors([e for e in pg['edges'] if e[3]=='In1' or e[3]=='In' or e[2]!=child],{child}) & descendants(pg['edges'],0)
  assert {0,child,54,55,80}<=keep
  keep.discard(0);parent_edges=[e for e in pg['edges'] if e[0] in keep|{0} and e[2] in keep]
  pending=[main];seen=set();resources=[];ownfacts=set();external=set();inventory=[]
  while pending:
   dep=pending.pop(0)
   if dep in seen:continue
   seen.add(dep);m=idx['resources'][dep];pin(m['source'],True);obj=read(ROOT/m['source']);rr=SafeResource(obj);root=obj['Data']['RootChunk']
   pending+=references(root,'phaseResource')+references(root,'sceneFile');ownfacts|={f for f in facts(root) if f.startswith(ident[:5])};external|={f for f in facts(root) if not f.startswith(ident[:5])}
   graphs=flatten(rr,root) if dep.endswith('.questphase') else []
   resources.append({'depot':dep,'source':m['source'],'raw':raw(m['source']),'graphs':graphs,'root_metadata':{k:v for k,v in root.items() if k!='graph'} if graphs else {}})
  for record,hashvalue in ITEMS.get(ident,[]):
   assert zlib.crc32(record.encode()) | len(record)<<32 == hashvalue
   matches=[dict(record=record,hash=str(hashvalue),raw=r['raw'],embedded_index=None,graph=g['path'],node=n['id'],source_condition=n['condition']) for r in resources for g in r['graphs'] for n in g['nodes'] if isinstance(n.get('condition',{}).get('type',{}),dict) and n.get('condition',{}).get('type',{}).get('$type')=='questInventory_ConditionType' and n['condition']['type']['itemID']['hash']==hashvalue]
   assert matches and matches[0]['source_condition']['type']['isPlayer']==1
   inventory.append(matches[0])
  journals=[{'path':p,'class':c,'states':[1]} for p,c in catalog.items() if (p=='quests/minor_quest/'+ident or p.startswith('quests/minor_quest/'+ident+'/')) and c in ['gameJournalQuest','gameJournalQuestPhase','gameJournalQuestObjective']]
  assert journals and journals[0]['class']=='gameJournalQuest'
  external_path='quests/main_quest/act_01/q101_resurrection';assert catalog[external_path]=='gameJournalQuest';journals.append({'path':external_path,'class':'gameJournalQuest','states':[3]})
  fs={f:0 for f in sorted(ownfacts)};fs.update({'ep1_standalone':0,'cp77_ep1_testing':0})
  ranges={f:{'min':1,'max':2147483647} for f in ['q001_done','q005_done','q101_done','q101_enable_side_content']}
  owner={'id':ident,'title':title,'tag':'PTFRS28_'+ident,'journals':journals,'facts_equal':fs,'fact_ranges':ranges,'inventory_zero':[{'record':i['record'],'hash':i['hash']} for i in inventory],'inventory_native':inventory,'vehicle_zero':[],'service_facts_equal':{},'dependency_roots':[external_path],'resume':'DEFER_UNSUPPORTED_PROGRESS_PRESERVE','phone_dependencies':[]}
  owners.append(owner);jobs.append({'id':ident,'title':title,'parent_source':PARENT,'parent_raw':raw(PARENT),'parent_ids':sorted(keep),'parent_nodes':[pns[i] for i in sorted(keep)],'parent_edges':parent_edges,'parent_child':child,'native_depot':main,'resources':resources,'external_facts':sorted(external),'normal_input':'In1','finished_output':'Out1'})
 result={'schema':1,'status':'SOURCE_BOUND_S28_FRESH_ENCOUNTER_CONTRACT','owners':owners,'source_pins':pins,'source_assessment':'research/sidejobs_s28/encounters/source_assessment_01.json','policy':'No reset or restart. Completed or unsupported earned progress defers. Excluded early story completed before Tower is proven by native causal ordering, with q101 full-completion journal/fact plus normal-campaign guards.'}
 (HERE/'contracts_02.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');(HERE/'build_plan_02.json').write_text(json.dumps({'jobs':jobs,'source_pins':pins},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'owners':len(owners),'resources':sum(len(j['resources']) for j in jobs),'journals':[len(o['journals']) for o in owners],'sha256':sha(HERE/'contracts_02.json')}))
if __name__=='__main__':main()

"""Build bounded fresh-family contract and original-resource dependency closure."""
import argparse,json,hashlib
from pathlib import Path
from inspect import ROOT,read,walk,value,graphs,sha
HERE=Path(__file__).parent;NATIVE=ROOT/'research/sidejobs_s25/families/native_01'
def refs(obj):
 return sorted({value(v) for x in walk(obj) for k,v in x.items() if k=='DepotPath' and isinstance(value(v),str) and value(v).endswith(('.questphase','.scene'))})
def catalog(path):
 d=read(path);h={x['HandleId']:x['Data'] for x in walk(d) if 'HandleId' in x and 'Data' in x};out={}
 def visit(w,p):
  n=w.get('Data',h.get(w.get('HandleRefId'),w));k=n.get('id','');p=p+([k] if k else [])
  if n.get('$type','').startswith('gameJournal'):out['/'.join(p)]=n['$type']
  for child in n.get('entries',[]):visit(child,p)
 visit(d['Data']['RootChunk']['entry'],[]);return out
def main():
 a=argparse.ArgumentParser();a.add_argument('--revision',default='01');a.add_argument('--discover',action='store_true');args=a.parse_args()
 rootq='quests/side_quest/';rootm='quests/minor_quest/'
 defs=[
  {'id':'mq025_psycho_brawl','key':'MQ025_FRESH','title':'Beat on the Brat (fresh family)','ids':['mq025_psycho_brawl','mq025_02_kabuki','mq025_03_arroyo','mq025_05_glen','mq025_06_pacifica','mq025_07_fight_club'],'prefix':'mq025_','source':'base\\quest\\minor_quests\\mq025\\mq025_psycho_brawl.questphase','entry':'In1','remove_nodes':[17,46,68,69,70],'contact':'contacts/trainer_fred','old_tags':['PTFRS22_MQ025'],'extra_sources':[],'extra_facts':['q001_fistfight_tutorial_seen','q001_fistfight_tut_won','q001_fistfight_trainer_sits','ozob_weakspot_nose_destroyed','wwd_05_done'],'ranges':{},'services':['PTFRB0STFRED_Ready','PTFRB0STFRED_Enabled']},
  {'id':'sq025_delamain','key':'SQ025_FRESH','title':'Human Nature / Tune Up / Epistrophy (fresh family)','ids':['sq025_delamain','sq025_0_pickup','sq025_compensation','sq025c01_angry','sq025c02_sad','sq025c03_mean','sq025c04_manic','sq025c05_scared','sq025c06_mean','sq025c07_suicidal'],'prefix':'sq025_','source':'base\\quest\\side_quests\\sq025\\sq025.questphase','entry':'In1','selected_nodes':[76,77,78,79,85,105,110,114,115,122,123,124,126,127,128,129,130,131,137,139,142,143,145,147,150,155,157,160,163,164,166,169,170,86],'contact':None,'old_tags':['PTFRS22_SQ025'],'extra_sources':['base\\quest\\side_quests\\sq025\\phases\\sq025_return_archer.questphase','base\\quest\\holocalls\\delamain\\delamain_holocall.questphase'],'extra_facts':[],'ranges':{'sq025_active':{'min':0,'max':1}},'services':[]},
  {'id':'sq024_races','key':'SQ024_FRESH','title':'The Beast in Me (fresh story races)','ids':[],'prefix':'sq024_','source':'base\\quest\\side_quests\\sq024\\sq024.questphase','entry':'sq024_in','remove_nodes':[2,13,14,16,18,20,27,31,32,65,114,115,116],'contact':'contacts/marianne','old_tags':[],'extra_sources':['base\\quest\\holocalls\\claire\\claire_holocall.questphase','base\\quest\\holocalls\\claire\\claire_cleanup.questphase'],'extra_facts':[],'ranges':{'sq024_active':{'min':0,'max':1},'sq024_intro_dialogues_done':{'min':0,'max':1}},'services':['PTFRB0CLA_Ready','PTFRB0CLA_Enabled']},
 ]
 # Exact whitelist identities, not titles inferred from file names.
 cap=read(ROOT/'research/sidejobs_s23/live_20261016_01/capture.json')
 jobs=cap['second']['jobs'];raceids=[j['id'] for j in jobs if j['id'].startswith('sq024')]
 defs[2]['ids']=raceids
 # Connected root/53/55 requires an absent official helper. Do not substitute
 # or cut original story-race gameplay merely to complete this component.
 defs=defs[:2]
 defs[0]['extra_sources']=['base\\open_world\\vendors\\watson\\little_china\\wat_lch_melee_01\\wat_lch_melee_01.scene']
 defs[0]['ranges']={'q001_left_v_apartment':{'min':1,'max':2147483647}}
 basejournal=ROOT/'research/sidejobs_s24/ep1/native_02/json/base/journal/cooked_journal.journal.json';cat=catalog(basejournal)
 index={}
 for folder in sorted((ROOT/'research/sidejobs_s25/families').glob('native_*')):
  for p in (folder/'json').rglob('*.json'):index[p.relative_to(folder/'json').as_posix()[:-5].replace('/','\\')]=p
 missing=set();owners=[];pins={};native={}
 def pin(p):pins[p.relative_to(ROOT).as_posix()]=sha(p)
 for d in defs:
  p=index[d['source']];gs=graphs(p);g=gs['root'];ids=d.get('selected_nodes') or [n['id'] for n in g['nodes'] if n['id'] not in d.get('remove_nodes',[])]
  nodes=[n for n in g['nodes'] if n['id'] in ids]
  # flatten() deliberately strips phaseGraph from node payloads. Include every
  # selected embedded graph explicitly, or late completion facts and messages
  # would disappear from the freshness/closure audit.
  selected_graphs=[v for gp,v in gs.items() if gp!='root' and int(gp.split('/')[1]) in ids]
  selected_objects=[nodes]+[v['nodes'] for v in selected_graphs]
  queue=refs(selected_objects)+d['extra_sources'];closure={};objects=selected_objects.copy()
  while queue:
   depot=queue.pop(0)
   if depot in closure:continue
   if depot not in index:missing.add(depot);continue
   f=index[depot];obj=read(f);closure[depot]=f;objects.append(obj);queue+=refs(obj)
  facts={};phonepaths={}
  for obj in objects:
   for x in walk(obj):
    for k in ('factName','factName1','factName2'):
     f=value(x.get(k))
     if isinstance(f,str) and (f.startswith(d['prefix']) or f.startswith('#'+d['prefix']) or (d['key']=='MQ025_FRESH' and (f.startswith('q001_fistfight_') or f.startswith('q001_02a_')))):facts[f]=0
    if x.get('$type')=='gameJournalPath':
     jp=x.get('realPath','');cls=value(x.get('className'))
     if '/contacts/' in '/'+jp and cls and (d['prefix'].rstrip('_') in jp or (d['key']=='SQ025_FRESH' and jp.startswith('contacts/delamain/'))):phonepaths[jp]=cls
  for f in d['extra_facts']:facts[f]=0
  for t in d['old_tags']:facts[t+'_Issued']=0;facts[t+'_Fault']=0
  if d['key']=='SQ025_FRESH':facts['PTFRS22_SQ025_SupportIssued']=0
  for f in d['services']:facts[f]=1
  if d['key']=='MQ025_FRESH':facts.update({'PTFRB0STFRED_Excluded':0,'PTFRB0ST_Suspended':0,'PTFRBASE_Suspended':0})
  if d['key']=='SQ024_FRESH':facts.update({'PTFRB0CLA_Excluded':0,'PTFRB0CLA_Suspended':0,'PTFRBASE_Suspended':0,'PTFRR1_Issued':0})
  for f in ('holo_setup_active','holo_setup_started','holo_interrupt_call','holo_active_call_interrupted','holo_reset','holo_force_reset','holo_reset_soft','holo_interrupt_call_manual','holo_interrupt_braindance'):facts[f]=0
  if d['key']!='MQ025_FRESH':
   for obj in objects:
    for x in walk(obj):
     for k,v in x.items():
      f=value(v)
      if isinstance(f,str) and f.startswith(('holo_','audio_')) and f.endswith(('_start_activate','_end_activate','_active','_started')):facts[f]=0
  facts['ep1_standalone']=0
  for f in d['ranges']:facts.pop(f,None)
  journals=[]
  for jid in d['ids']:
   roots=[p for p,c in cat.items() if c=='gameJournalQuest' and p.endswith('/'+jid)]
   assert len(roots)==1,(jid,roots)
   for jp,cls in cat.items():
    if jp==roots[0] or jp.startswith(roots[0]+'/'):journals.append({'path':jp,'class':cls,'states':[1]})
  # Guard only actual cooked entries; stale native references are evidence, not
  # a reason to invent paths or wait forever on unavailable journal lookups.
  excluded=[]
  for jp,cls in phonepaths.items():
   if cat.get(jp)==cls:journals.append({'path':jp,'class':cls,'states':[1]})
   else:excluded.append({'path':jp,'class':cls})
  tag='PTFRS25_'+d['key'];depot='towercontinued\\sidejobs_s25\\families\\'+d['key'].lower()+'.questphase'
  pin(p);pin(Path(str(p).replace('/json/','/raw/').replace('\\json\\','\\raw\\')[:-5]))
  for dep,f in closure.items():
   raw=Path(str(f).replace('/json/','/raw/').replace('\\json\\','\\raw\\')[:-5]);pin(f);pin(raw)
   native[dep]={'json':f.relative_to(ROOT).as_posix(),'json_sha256':sha(f),'raw':raw.relative_to(ROOT).as_posix(),'raw_sha256':sha(raw)}
  if d['contact']:assert cat.get(d['contact'])=='gameJournalContact',d['contact']
  owners.append({'id':d['id'],'ids':d['ids'],'key':d['key'],'title':d['title'],'tag':tag,'depot':depot,'entry':d['entry'],'native_source':p.relative_to(ROOT).as_posix(),'selected_nodes':ids,'facts_equal':facts,'fact_ranges':d['ranges'],'journals':journals,'contact':d['contact'],'native_dependencies':sorted(closure),'metadata_invalid_native_refs_excluded':excluded})
 if missing:
  dest=ROOT/'research/sidejobs_s25/families'/('missing_'+args.revision+'.json');assert not dest.exists();dest.write_text(json.dumps(sorted(missing),indent=2)+'\n');print(json.dumps({'missing':len(missing),'path':str(dest)}));return
 if args.discover:print('Closure complete');return
 for p in (Path(__file__),HERE/'inspect.py',basejournal,Path(str(basejournal).replace('/json/','/raw/').replace('\\json\\','\\raw\\')[:-5]),ROOT/'research/sidejobs_s23/live_20261016_01/capture.json',ROOT/'research/sidejobs_s25/families/claire_deferred_01.json'):pin(p)
 for p in ('prealpha/ncpd_scanner_n1/native_inspect.py','tools/audit_activity_batches_b1.py','tools/catalog_gig_rollout_r2.py','research/sidejobs_s25/families/native_03/raw/base/quest/minor_quests/minorquests.questphase','research/sidejobs_s25/families/native_03/json/base/quest/minor_quests/minorquests.questphase.json'):pin(ROOT/p)
 common=read(ROOT/'prealpha/sidejobs_s24/ep1/contract02.json')['common_equal']
 result={'schema':'S25_FRESH_FAMILIES_CONTRACT_1','status':'PREPARED_NOT_LIVE','common_equal':common,'owners':owners,'source_pins':pins,'native_resources':native,'scope':'Only native Inactive and unstarted full family, existing/completed children and owners protected. New ownership does not reset native progress. Original quest delays/prerequisites retained. Excluded Delamain resurgence/core removed at parent edge only. EP1 standalone fresh entry deferred.'}
 dest=HERE/('contract'+args.revision+'.json');assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'owners':[(o['key'],len(o['ids']),len(o['facts_equal']),len(o['journals']),len(o['native_dependencies'])) for o in owners]}))
if __name__=='__main__':main()

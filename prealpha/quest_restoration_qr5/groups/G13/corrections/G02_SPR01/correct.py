"""Direction-aware correction; frozen G02 remains untouched; only this fresh folder writes."""
from pathlib import Path
import argparse,collections,copy,json,re,sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[1]));import source_inputs as I
from common import walk,value
from model import Resource,compare_graph
def path(g,a,b):
 todo=collections.deque([[str(a)]]);seen={str(a)}
 while todo:
  p=todo.popleft()
  if p[-1]==str(b):return p
  for x,so,y,si in g['edges']:
   if x==p[-1] and so!='CutSource' and si!='CutDestination' and not(g['nodes'][x]['type']=='scnCutControlNode' and so.startswith('1:')) and y not in seen:seen.add(y);todo.append(p+[y])
 return None
def run(O):
 assert not O.exists();checks=[];pins=[];models={};rows=[]
 def ck(name,ok,e=None):checks.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,(name,e)
 def load(d):
  if d not in models:m,p=I.load(d);models[d]=m;pins.append(p);ck('actual source '+d,not m['errors'],p['sha256'])
  return models[d]
 qs=['sts_hey_gle_04','sts_hey_rey_09','sts_hey_rey_06','sts_hey_rey_08','sts_hey_spr_01','sts_hey_spr_06','sts_hey_spr_03','sts_pac_cvi_02','sts_pac_wwd_05']+I.Q
 for d in I.MI:
  if not d.startswith('base\\') or not any('\\'+q+'\\' in d for q in qs):continue
  m=load(d)
  for gp,g in m['graphs'].items():
   for i,n in g['nodes'].items():
    for w in n['writes']:
     f=w['factName'];r=re.fullmatch(r'(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate',f)
     if w.get('value')==1 and r:rows.append(dict(quest=next(q for q in qs if '\\'+q+'\\' in d),resource=d,graph=gp,node=i,request=f,direction='outgoing' if r[3] else'incoming',medium=r[1],contact=r[3] or r[2],incoming=[e for e in g['edges'] if e[2]==i],outgoing=[e for e in g['edges'] if e[0]==i]))
 ck('all12 processed quest directions actually scanned',set(r['quest'] for r in rows)==set(qs),qs)
 outgoing=[r for r in rows if r['direction']=='outgoing'];ck('outgoing exception isolated to SPR01 after exhaustive producer scan',len(outgoing)==8 and {r['quest'] for r in outgoing}=={'sts_hey_spr_01'},outgoing)
 ck('no audio producer hidden by original holo filter in these12',not any(r['medium']=='audio' for r in rows),dict(scope='Exact selected native resources only; G05 Karl separately uses audio and is outside this no-audio claim'))
 d=r'base\open_world\street_stories\heywood\wellsprings\sts_hey_spr_01\scenes\sts_hey_spr_01_padre_fixer_conversation.scene';m=load(d);g=m['graphs']['scene'];a=next(a for a in m['metadata']['actors'] if a['actorName']=='padre');ck('actual Padre actor is outgoing holo spawnSet',a['acquisitionPlan']=='spawnSet' and value(a['spawnSetParams']['entryName'])=='padre_holo' and value(a['spawnSetParams']['reference'])=='#padre_holo',a)
 hc=r'base\quest\holocalls\padre\padre_holocall.questphase';hs=hc.replace('.questphase','.scene');cl=hc.replace('_holocall','_cleanup');cg=load(hc)['graphs']['root'];sg=load(hs)['graphs']['scene'];lg=load(cl)['graphs']['root']
 for req,reader,clear,ack in [('holo_v_calls_padre_start_activate',4,12,43),('holo_v_calls_padre_end_activate',5,13,44)]:
  base=req.removesuffix('_activate');ck('actual outgoing listener '+req,any(r.get('factName')==req and r.get('comparisonType')=='Greater' and r.get('value')==0 for r in cg['nodes'][str(reader)]['reads']) and [str(clear),'Out','0',base] in cg['edges'],dict(controller=hc,reader=reader,clear=clear));ck('actual outgoing real ACK '+req,any(w.get('factName')==base+'_done' and w.get('value')==1 for w in sg['nodes'][str(ack)]['writes']) and bool(path(sg,sg['entries'][base],ack)),dict(scene=hs,entry=sg['entries'][base],writer=ack))
 for producer,wait,clear,fact in [(556,587,550,'holo_v_calls_padre_start'),(557,551,552,'holo_v_calls_padre_end'),(577,574,575,'holo_v_calls_padre_end')]:ck('exact outgoing request/wait/clear '+str(producer),any(w.get('factName')==fact+'_activate' and w.get('value')==1 for w in g['nodes'][str(producer)]['writes']) and bool(path(g,producer,wait)) and bool(path(g,wait,clear)) and any(w.get('factName')==fact+'_done' and w.get('value')==0 for w in g['nodes'][str(clear)]['writes']),dict(scene=d,producer=producer,wait=wait,clear=clear,path=path(g,producer,clear)))
 entry=g['entries']['spr_01_padre_start'];ck('retry606 has native prearmed waiter context',bool(path(g,entry,606)) and bool(path(g,entry,587)) and path(g,606,587) is None,dict(entry=entry,to_retry=path(g,entry,606),to_wait=path(g,entry,587),limit='Native retry not a new direct wait path; actual engine parallel scheduling remains conditional'))
 ck('outgoing cleanup real reset/end',any(w.get('factName')=='holo_v_calls_padre_reset_counter' and w.get('value')==1 for w in lg['nodes']['7']['writes']) and ['7','Out','2','holo_v_calls_padre_end'] in lg['edges'],dict(resource=cl,node=7,end_scene_node=2))
 # Actual ACK resource mutation: independent source receipt detector must reject0.
 raw=copy.deepcopy(I.read(next(p['json'] for p in pins if p['depot']==hs)));changed=0
 for x in walk(raw):
  if x.get('$type')=='questSetVar_NodeType' and x.get('factName')=='holo_v_calls_padre_start_done' and x.get('value')==1:x['value']=0;changed+=1
 bm=Resource(raw).normalize();det=changed>0 and not any(w.get('factName')=='holo_v_calls_padre_start_done' and w.get('value')==1 for w in bm['graphs']['scene']['nodes']['43']['writes']) and bool(compare_graph(models[hs],bm));ck('raw outgoing ACK1to0 detected',det,dict(resource=hs,node=43,changed=changed))
 oldpath=I.H.parent/'G02/quests/sts_hey_spr_01/contracts.json';old=I.read(oldpath);new=copy.deepcopy(old)
 def replace(x):
  if isinstance(x,str):return x.replace('contact Padre physically','complete the outgoing Padre holographic call').replace('Padre in-person conversation','Padre outgoing holographic conversation').replace('physical Padre conversation','outgoing Padre holographic conversation').replace('physical outcome conversation','outgoing holographic outcome conversation').replace('Physical Padre conversation is a distinct context, not assumed covered by phone studio alone.','The outcome is an outgoing holographic call; native outgoing controller4/5, real ACK43/44 and cleanup7 are separately verified in this addendum.')
  if isinstance(x,list):return [replace(v) for v in x]
  if isinstance(x,dict):return {k:replace(v) for k,v in x.items()}
  return x
 new=replace(new);c=new['contracts']['communications'];c['status']='CONDITIONAL';c['proven']=['Both prebrief incoming and outcome outgoing holo paths are native. Outcome scene padre_fixer_conversation uses Padre spawnSet padre_holo/#padre_holo; its name is not evidence of a physical visit.','Actual outgoing producers556/557/577/606 plus OW root/2/156 RET64/INT65 and/157 RET105/INT106 issue holo_v_calls_padre_* requests. Controller4/5 and clears12/13 bind actual scene43/44 ACKs. Primary556→587→550;557→551→552;577→574→575 preserve real request/wait/clear paths. Native outgoing cleanup7 resets the proper counter and enters its real end scene.'];c['remaining']=['CONDITIONAL: retry606 shares a prearmed entry→587 waiter and has no direct retry→587 path. Actual phone/scene parallel scheduling, interruption/cleanup/reload and saved shared studio/controller ownership remain live-dependent.','No gameplay defect or runtime repair is implied. The previous communications PASS is superseded, not re-earned by these static controls.']
 for cc in new['contracts'].values():cc['evidence'].append(dict(path=str(O/'source_pins.json'),scope='Fresh explicit SPR01 outgoing correction; prior incoming-only counts/statements superseded'))
 new['status']='DEEP_CONTRACTS_WITH_EXPLICIT_OUTGOING_PROTOCOL_CORRECTION';new['supersedes']=dict(path=str(oldpath),sha256=I.sha(oldpath),reason='Incorrect physical/incoming-only communications interpretation; expanded direction-aware producer scan')
 I.write(O/'source_pins.json',pins);I.write(O/'direction_inventory.json',dict(quests=qs,producers=rows,directions={q:sorted({(r['medium'],r['direction'],r['contact']) for r in rows if r['quest']==q}) for q in qs},limit='All original indexed native own-body/scene resources for12 quests; dynamic runtime providers and arbitrary scripts not enumerated.'));I.write(O/'contracts.corrected.json',new);I.write(O/'tests.json',dict(count=len(checks),checks=checks,mutations=[dict(fault='actual outgoing ACK1to0',detected=det)]));I.write(O/'correction.json',dict(status='SUPERSEDE_G02_SPR01_COMMUNICATIONS_AND_PHYSICAL_PROSE',original=str(oldpath),original_sha256=I.sha(oldpath),corrected=str(O/'contracts.corrected.json'),corrected_sha256=I.sha(O/'contracts.corrected.json'),prior_communications_status='PASS',new_communications_status='CONDITIONAL',new_G02_status_counts={'APPROVED_DEVIATION':3,'PASS':3,'CONDITIONAL':21,'OPAQUE':3},tests=str(O/'tests.json'),tests_sha256=I.sha(O/'tests.json'),checks=len(checks),mutations=1,source_pins=str(O/'source_pins.json'),source_pins_sha256=I.sha(O/'source_pins.json'),direction_inventory=str(O/'direction_inventory.json'),direction_inventory_sha256=I.sha(O/'direction_inventory.json'),code_sha256=I.sha(__file__),stock_fact_precision='Disconnected native SPR06 LOOP waiter14 reads sts_hey_spr_06_finished>0; separate earlier body outcome is spr_06_finished. The no-counter-patch conclusion remains unchanged.',runtime_changes=[]));print(json.dumps(dict(checks=len(checks),mutations=1,correction=str(O/'correction.json'),sha256=I.sha(O/'correction.json'))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);run(Path(p.parse_args().output).resolve())

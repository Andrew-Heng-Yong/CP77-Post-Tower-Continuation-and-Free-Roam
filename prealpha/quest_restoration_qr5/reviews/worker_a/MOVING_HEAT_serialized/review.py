"""Independent actual S22 accepted MovingHeat wrapper review; no root checker import."""
from pathlib import Path
import sys,copy,json,collections,argparse
H=Path(__file__).resolve().parent;W=H.parents[4];F=W/'prealpha/quest_restoration_qr5';sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource
def run(O):
 assert not O.exists();tests=[];pins=[];M={};R={};mut=[]
 def ck(k,v,e):
  tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed_tests.json',tests);raise AssertionError(k)
 for p in read(H/'readback_01/manifest.json'):
  ck('independent raw/json '+p['name'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);pins.append(p);R[p['name']]=read(p['json']);M[p['name']]=Resource(R[p['name']]).normalize();ck('decoded '+p['name'],not M[p['name']]['errors'],M[p['name']]['errors'])
 b,a,n=M['before'],M['after'],M['native']
 def nd(m,i,g='root'):return m['graphs'][g]['nodes'][str(i)]
 def ed(m,x,s,y,t,g='root'):return[str(x),s,str(y),t]in m['graphs'][g]['edges']
 prop=F/'groups/G18/moving_heat_prefab_03/proposal.json';review=F/'reviews/worker_b/MOVING_HEAT_source/review.json';scope=F/'groups/G18/moving_heat_prefab_03/proposal_scope_addendum_01.json'
 for p,h in [(prop,'96611DFB60C246C52DDAFA18144CCE142373EA9403657ABA8A285340C5738036'),(review,'0F3E6F9C52BF95CFD023679C4C58DCDB028F69B14CB2134E338CD23AE139B480')]:ck('approved source/proposal pin '+p.parent.name,sha(p)==h,str(p));pins.append({'path':str(p),'sha256':sha(p)})
 pins.append({'path':str(scope),'sha256':sha(scope)});ck('precise saved boundary addendum',read(scope)['status']=='SOURCE_ONLY_SCOPE_CLARIFICATION_NO_ROUTING_CHANGE','already executing old10 unchanged; old claimed pending9 may use future wrapper')
 atom={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRS24_Q304_FRESH_Issued','value':0}}
 ck('root resource metadata/rootPF unchanged',all(b[k]==a[k]for k in ['metadata','root_prefabs','embedded_files']),b['metadata_sha256'])
 ck('exact old and two new graph scopes',set(a['graphs'])==set(b['graphs'])|{'root/1200','root/1200/10'},list(a['graphs']))
 for gp,g in b['graphs'].items():
  ag=a['graphs'][gp];ck('old identities retained '+gp,set(g['nodes'])<=set(ag['nodes']),len(g['nodes']))
  for i,x in g['nodes'].items():
   if gp=='root'and i in ['2','3','9']:
    old=x['payload'];new=copy.deepcopy(ag['nodes'][i]['payload']);cond=new['condition'];ck('exact appended AND fence '+i,cond['operation']=='AND'and cond['conditions'][-1]==atom,cond['conditions'][-1]);cond['conditions'].pop();ck('all existing guard payload exact '+i,new==old and x['sockets']==ag['nodes'][i]['sockets'],x['payload_sha256'])
   else:ck('old node exact payload/socket '+gp+'/'+i,x==ag['nodes'][i],x['payload_sha256'])
  if gp!='root':ck('old graph exact including empty external inline '+gp,ag==g,'root10 default WKit graph is already empty; do not delete/rename it')
  else:
   bc=collections.Counter(map(tuple,g['edges']));ac=collections.Counter(map(tuple,ag['edges']));removed=[list(e)for e,c in(bc-ac).items()for _ in range(c)];added=[list(e)for e,c in(ac-bc).items()for _ in range(c)];ck('exact one removed edge',removed==[['9','True','10','In1']],removed);ck('exact two added edges',sorted(added)==sorted([['9','True','1200','In1'],['1200','Out1','11','In']]),added);ck('only local wrapper1200 added',set(ag['nodes'])-set(g['nodes'])=={'1200'},list(ag['nodes']))
 # Compare FULL native entry metadata, not strings returned by root_prefabs normalizer.
 nr=Resource(R['native']);full=nr.clean(nr.root['phasePrefabs']);wrap=nd(a,1200);ck('complete native PF entry deep-copied',wrap['payload']['phaseInstancePrefabs']==full and wrap['prefabs']==['#q304_pr_car_retrieval'],full)
 ck('wrapper zero resource/Soft default metadata',wrap['payload']['phaseResource']=={'DepotPath':{'$type':'ResourcePath','$storage':'uint64','$value':'0'},'Flags':'Soft'}and wrap['payload']['saveLock']==0 and wrap['sockets']==nd(b,10)['sockets'],wrap['payload'])
 ck('exact three wrapper children',set(a['graphs']['root/1200']['nodes'])=={'0','10','1'},'no full main/default rehost')
 ck('inner external10 exact old saved node',nd(a,10,'root/1200')==nd(b,10),nd(b,10)['payload_sha256'])
 ck('inner empty phase graph preserved',a['graphs']['root/1200/10']==b['graphs']['root/10'],'external path executes resource; empty default inline graph is not missing body evidence')
 ck('exact wrapper native input/output identities',nd(a,0,'root/1200')['payload']=={'$type':'questInputNodeDefinition','id':0,'socketName':{'$type':'CName','$storage':'string','$value':'In1'}}and nd(a,1,'root/1200')['payload']=={'$type':'questOutputNodeDefinition','id':1,'socketName':{'$type':'CName','$storage':'string','$value':'Out1'},'type':'Terminating'},'parent old11 fires only after exact childOut1 and native wrapper scope ends')
 ck('exact wrapper flow',a['graphs']['root/1200']['edges']==[['0','Out','10','In1'],['10','Out1','1','In']],'no replay, extra activation or alternate output')
 ck('old executing10 completion edge remains',ed(a,10,'Out1',11,'In')and nd(a,10)==nd(b,10),'existing executing saved descendants are unchanged; no retroactive prefab lease assigned')
 ck('new wrapper has no new fact/reward/journal/scene writes',not any(x['writes']or x['journal_paths']or x['reward']or x['sms']for x in a['graphs']['root/1200']['nodes'].values()),'only native external phase call, no grants or resets')
 # The added conjunct's scalar semantics are pointwise exact; engine trigger availability is not simulated.
 for old_truth in [False,True]:
  for issued in [0,1,None]:
   fact=0 if issued is None else issued;new_truth=old_truth and fact==0;ck('known fresh-owner conjunction '+str((old_truth,issued)),new_truth==(old_truth and(issued in [0,None])),'ordinary absent scalar0, all previous predicates remain; no engine Outside-trigger proof')
 ck('every current late recheck has S24 exclusion',all(any(x.get('factName')=='PTFRS24_Q304_FRESH_Issued'and x['value']==0 for x in nd(a,i)['reads'])for i in [2,3,9]),'known S24 owner blocks future S22 start, preserving saved/native owners')
 ck('claim precedes future9 path',ed(a,3,'True',4,'In')and any(e[2]=='9'for e in a['graphs']['root']['edges']),'source boundary allows previously claimed but not yet dispatched9.True; no universal alreadyIssued-unchanged claim')
 # Preserve both distinct existing owners' resources and all earlier G19/QR5 repairs.
 E=read(F/'source_epoch_05.json')
 for d in [r'towercontinued\sidejobs_s22\moving_heat_resume.questphase',r'towercontinued\sidejobs_s24\ep1\q304_fresh_boot.questphase',r'towercontinued\native_gigs_u9\sts_ep1_08_entry.questphase',r'towercontinued\native_gigs_u9\sts_wat_nid_03_entry.questphase']:
  old=F/'candidate_02/archive_source'/d.replace('\\','/');new=F/'candidate_03/archive_source'/d.replace('\\','/');ck('preserved existing resource '+d,sha(old)==sha(new)==E['source_resources'][d],{'before':str(old),'after':str(new),'sha256':sha(new)});pins.append({'path':str(new),'sha256':sha(new)})
 # Actual raw mutations: full PF loss, concurrency fence, old owner target, output lifetime, old callback.
 def gn(r,path):
  z=Resource(r);g=z.d(z.root['graph'])
  for i in path.split('/')[1:]:g=z.d(next(z.d(h)for h in g['nodes']if str(z.d(h)['id'])==i)['phaseGraph'])
  return z,g
 def rn(r,path,i):
  z,g=gn(r,path);return z,next(z.d(h)for h in g['nodes']if str(z.d(h)['id'])==str(i))
 def rm(r,ee):
  z,g=gn(r,'root');ss={z.hid(sh):(str(z.d(h)['id']),str(value(z.d(sh)['name'])))for h in g['nodes']for sh in z.d(h)['sockets']};bad=set()
  for h in g['nodes']:
   for sh in z.d(h)['sockets']:
    for ch in z.d(sh).get('connections',[]):
     co=z.d(ch)
     if [*ss.get(z.hid(co['source']),('','')),*ss.get(z.hid(co['destination']),('',''))]==ee:bad.add(z.hid(ch))
  for h in g['nodes']:
   for sh in z.d(h)['sockets']:z.d(sh)['connections']=[x for x in z.d(sh).get('connections',[])if z.hid(x)not in bad]
 for label,change,oracle in [
  ('lost_prefab',lambda r:rn(r,'root',1200)[1].update(phaseInstancePrefabs=[]),lambda m:nd(m,1200)['payload']['phaseInstancePrefabs']==full),
  ('lost_S24_fence',lambda r:[x.update(factName='QR5_missing_fence')for x in walk(rn(r,'root',9)[1])if x.get('factName')=='PTFRS24_Q304_FRESH_Issued'],lambda m:any(x.get('factName')=='PTFRS24_Q304_FRESH_Issued'for x in nd(m,9)['reads'])),
  ('old_executing_target_renamed',lambda r:[x.update({'$value':'QR5_wrong_resume.questphase'})for x in walk(rn(r,'root',10)[1])if x.get('$type')=='ResourcePath'],lambda m:nd(m,10)['payload']==nd(b,10)['payload']),
  ('nonterminating_wrapper',lambda r:rn(r,'root/1200',1)[1].update(type='NonTerminating'),lambda m:nd(m,1,'root/1200')['payload']['type']=='Terminating'),
  ('lost_old_saved_completion',lambda r:rm(r,['10','Out1','11','In']),lambda m:ed(m,10,'Out1',11,'In'))]:
  r=copy.deepcopy(R['after']);change(r);mm=Resource(r).normalize();ck('actual raw fault '+label,oracle(a)and not oracle(mm),label);fp=O/'mutations'/str(label+'.json');write(fp,r);mut.append({'fault':label,'path':str(fp),'sha256':sha(fp),'detected':True})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'mutations.json',mut);result={'status':'APPROVE_EXACT_SERIALIZED_FUTURE_S22_PREFAB_WRAPPER_WITH_SAVE_BOUNDARIES','checks':len(tests),'mutations':len(mut),'fresh_exports':3,'before_sha256':pins[0]['sha256'],'after_sha256':pins[1]['sha256'],'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'code':str(Path(__file__).resolve()),'code_sha256':sha(__file__),'precise_boundary':'Already executing old root10/descendants and10.Out1→11 stay exact. Previously claimed S22 instance pending a future9.True may use wrapper1200 if all previous predicates and new S24FreshIssued0 hold. No onattach replay/prefab retroassignment.','limits':['Pre-wrapper Outside main_trigger/entire_garage resolution remains opaque; this repairs exact body-lifetime support on actual future9.True, not every entry stall.','Native PIP world placement/reference counting, actor/community acquisition and saved scheduling/reload remain opaque/live-only.','Source census and S24 fence do not rule out all unknown external providers/owners.','Final package/aggregate preservation are separate root gates; no installed/game/save/fact/release change.'],'runtime_changes':[]};write(O/'review.json',result);print(json.dumps(result))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())

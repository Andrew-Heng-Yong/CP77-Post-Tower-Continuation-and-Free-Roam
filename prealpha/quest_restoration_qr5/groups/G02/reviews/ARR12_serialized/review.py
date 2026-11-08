"""Independent WKit9.1 readback oracle; no root checker imports or resource writes."""
from pathlib import Path
import argparse,collections,copy,json,sys
W=Path(__file__).resolve().parents[6];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,compare_graph,reachable
def ev(c,f):
 t=c['$type']
 if t=='questLogicalCondition':return all(ev(x,f) for x in c['conditions']) if c['operation']=='AND' else any(ev(x,f) for x in c['conditions'])
 if t=='questFactsDBCondition':return ev(c['type'],f)
 if t=='questVarComparison_ConditionType':
  a,b=f.get(c['factName'],0),c['value'];return {'Equal':a==b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b,'NotEqual':a!=b}[c['comparisonType']]
 raise ValueError(t)
def closure(g,seeds,f,scene=False):
 """Bounded monotone token model: AND needs each socket, scalar guards branch.
 Scene cut outputs excluded. Engine predicates treated MAY; no scheduling proof.
 """
 active=set(map(str,seeds));done=set();ins=collections.defaultdict(set);change=True
 while change:
  change=False
  for i in list(active-done):
   node=g['nodes'][i];t=node['type'];isand=t in ['scnAndNode','questLogicalAndNodeDefinition']
   if isand:
    required=int(node['payload'].get('numInSockets',node['payload'].get('inputSocketCount',0)))
    if len(ins[i])<required:continue
   done.add(i);change=True;pred=node['payload'].get('condition')
   if t=='scnQuestNode':pred=node['payload'].get('questNode',{}).get('condition')
   allowed=None
   if pred:
    try:truth=ev(pred,f);allowed={'0:0' if truth else '0:1'} if scene else {'True' if truth else 'False'}
    except ValueError:pass
   if not scene and t=='questPauseConditionNodeDefinition' and pred:
    try:allowed={'Out'} if ev(pred,f) else set()
    except ValueError:pass
   for a,so,b,si in g['edges']:
    if a!=i or so=='CutSource' or si=='CutDestination' or (scene and so.startswith('1:')):continue
    if allowed is not None and so not in allowed:continue
    if not scene and i=='17' and so=='success':continue # callee's independently proved failed1 output contract
    ins[b].add(si)
    if b not in active:active.add(b)
 return dict(active=sorted(active),executed=sorted(done),received={k:sorted(v) for k,v in ins.items()})
def run(O):
 assert not O.exists();tests=[];mutations=[];exports=read(H/'readback_02/manifest.json');models={};raws={}
 def ck(name,ok,e=None):tests.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,(name,e)
 for p in exports:
  ck('fresh raw/export '+p['name'],sha(p['raw'])==p['raw_sha256'] and sha(p['json'])==p['json_sha256'],p);raws[p['name']]=read(p['json']);models[p['name']]=Resource(raws[p['name']]).normalize();ck('readback parse '+p['name'],not models[p['name']]['errors'],models[p['name']]['errors'])
 a,b,native=models['before'],models['after'],models['native'];gp='root/10';mgp=gp+'/1202';bg=b['graphs'][gp];ng=native['graphs']['root/3'];monitor=b['graphs'][mgp]
 expected_added={gp+'/1202',gp+'/1202/32',gp+'/1202/36'};ck('only three cloned graphs',set(b['graphs'])-set(a['graphs'])==expected_added and set(a['graphs'])<=set(b['graphs']),list(b['graphs']))
 ck('resource root metadata unchanged',a['metadata']==b['metadata'] and a['root_prefabs']==b['root_prefabs'],b['metadata'])
 oldedge=['65003','Out','8','In'];newedges=[['65003','Out','1200','In'],['1200','True','1201','In'],['1201','Out','1202','In1'],['1201','Out','8','In']]
 for p,gr in a['graphs'].items():
  now=b['graphs'][p];ck('old IDs exact '+p,set(now['nodes'])==set(gr['nodes'])|({'1200','1201','1202'} if p==gp else set()),list(now['nodes']))
  for i,node in gr['nodes'].items():ck('old payload/socket exact '+p+':'+i,node==now['nodes'][i],dict(graph=p,node=i))
  edges=collections.Counter(map(tuple,gr['edges']));expected=edges-collections.Counter([tuple(oldedge)])+collections.Counter(map(tuple,newedges)) if p==gp else edges
  ck('exact allowed edge delta '+p,collections.Counter(map(tuple,now['edges']))==expected,now['edges'])
 ck('native phase3 clone metadata only ID',dict(native['graphs']['root']['nodes']['3']['payload'],id=1202)==bg['nodes']['1202']['payload'],bg['nodes']['1202']['payload'])
 for p in ['root/3','root/3/32','root/3/36']:
  orig=native['graphs'][p];cur=b['graphs'][mgp+p[len('root/3'):]]
  ck('exact cloned nodes '+p,orig['nodes']==cur['nodes'],dict(nodes=len(orig['nodes'])))
  ee=collections.Counter(map(tuple,orig['edges']))
  if p=='root/3':ee-=collections.Counter([('0','Out','15','In')]);ee+=collections.Counter([('0','Out','13','In')])
  ck('exact cloned recursive edges '+p,ee==collections.Counter(map(tuple,cur['edges'])),cur['edges'])
 required={'PTFRU9_sts_std_arr_12_ParentEntered':1,'PTFRU9_sts_std_arr_12_Started':0,'PTFRU9_sts_std_arr_12_MainFinished':0,'PTFRU9_sts_std_arr_12_OwnerFinished':0,'PTFRU9_sts_std_arr_12_Fault':0,'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0,'arr_12_start':0,'arr_12_finished':0,'PTFRU9_sts_std_arr_12_MonitorEntered':0,'arr_12_fail_loop_end':0,'dlc_sts_std_arr_12_failed':0,'dlc_sts_std_arr_12_convoy_destroyed':0,'dlc_sts_std_arr_12_failed_spawn_additional_car':0}
 guard=bg['nodes']['1200']['payload']['condition'];items=list(walk(guard));facts={x['factName']:x['value'] for x in items if x.get('$type')=='questVarComparison_ConditionType'};ck('exact approved fresh guard14 predicates',guard['operation']=='AND' and facts==required and all(x.get('comparisonType')=='Equal' for x in items if x.get('$type')=='questVarComparison_ConditionType'),guard)
 ck('positive fresh fixture missing zero valid',ev(guard,required) and ev(guard,{k:v for k,v in required.items() if v==1}) and not ev(guard,{}),dict(missing_scalar_semantics=0))
 for f,v in required.items():ck('each incompatible guard value rejected '+f,not ev(guard,required|{f:0 if v else 1}),dict(fact=f,required=v))
 ck('native arm0 and1 supported without native write',all(ev(guard,required|{'arr_12_fail_loop_start':v}) for v in [0,1]) and '14' not in reachable(monitor['nodes'],monitor['edges'],['0']) and not any(w['factName']=='arr_12_fail_loop_start' for i in reachable(monitor['nodes'],monitor['edges'],['0']) for w in monitor['nodes'][i]['writes']),dict(disconnected_native_nodes=[14,15]))
 ck('new private claim only writer',bg['nodes']['1201']['writes']==[{'$type':'questSetVar_NodeType','factName':'PTFRU9_sts_std_arr_12_MonitorEntered','setExactValue':1,'value':1}],bg['nodes']['1201'])
 ck('future event only guard incoming', [e for e in bg['edges'] if e[2]=='1200']==[['65003','Out','1200','In']],bg['edges'])
 ck('already-entered no-event not polled',all(e[0]=='65003' for e in bg['edges'] if e[2]=='1200') and all(e[0]=='1201' for e in bg['edges'] if e[2]=='1202'),dict(limit='No new65003 pulse means no new enrollment; no retroactive attach scan'))
 ck('private parent and ancestor no terminal output',not any(x['type']=='questOutputNodeDefinition' for p in ['root',gp] for x in b['graphs'][p]['nodes'].values()),dict(main12=bg['nodes']['12']['payload'],monitor1202=bg['nodes']['1202']['payload']))
 ck('monitor exact Terminating child only',monitor['nodes']['1']['payload']['type']=='Terminating',monitor['nodes']['1']['payload'])
 ck('monitor no root or nested extra prefab claims',not native['root_prefabs'] and not native['graphs']['root']['nodes']['3']['prefabs'] and all(not x['prefabs'] for p in ['root/3','root/3/32','root/3/36'] for x in native['graphs'][p]['nodes'].values()),dict(limit='Original main prefabs retained; actual streamed targets remain OPAQUE'))
 ck('exact real failure flags before debrief',monitor['nodes']['8']['writes']==[{'$type':'questSetVar_NodeType','factName':'dlc_sts_std_arr_12_failed','setExactValue':1,'value':1}] and all(e in monitor['edges'] for e in [['5','Out','8','In'],['8','Out','7','Failed'],['16','Out','22','In'],['22','Out','24','In']]),dict(flag8=monitor['nodes']['8'],end22=monitor['nodes']['22']))
 ck('no reachable failed0 reset',not any(w.get('factName')=='dlc_sts_std_arr_12_failed' and w.get('value')==0 for p in expected_added for x in b['graphs'][p]['nodes'].values() for w in x['writes']),None)
 for suffix,facts_expected,outs in [('/32',{8:('#arr_12_hacking_completed',1,'GreaterOrEqual'),14:('dlc_sts_std_arr_12_convoy_destroyed',0,'Greater')},[(8,9),(14,9)]),('/36',{8:('arr_12_additional_fail_loop_after_chase_start',0,'Equal'),12:('arr_12_additional_fail_loop_after_chase_end',0,'Greater'),14:('dlc_sts_std_arr_12_convoy_destroyed',0,'Greater')},[(8,9),(12,13),(14,13)])]:
  gg=b['graphs'][mgp+suffix]
  for i,(fact,v,cmp) in facts_expected.items():ck('actual nested cancellation '+suffix+str(i),any(x.get('factName')==fact and x.get('value')==v and x.get('comparisonType')==cmp for x in gg['nodes'][str(i)]['reads']),dict(graph=mgp+suffix,node=i,fact=fact))
  for i,j in outs:ck('actual nested terminating cancellation edge '+suffix+str(i),[str(i),'Out',str(j),'In'] in gg['edges'] and gg['nodes'][str(j)]['payload']['type']=='Terminating',dict(graph=mgp+suffix,edge=[i,'Out',j,'In']))
 scene=models['native_sts_std_arr_12_holocall_debriefs']['graphs']['scene'];sc=closure(scene,[268,88],{'dlc_sts_std_arr_12_failed':1},True);ck('actual failed scene excludes success AND251',all(i in sc['executed'] for i in ['268','22','20','259','249']) and not any(i in sc['executed'] for i in ['252','251','16']),sc)
 ck('scene failure/success output names',any(value(x.get('name'))=='fail' and str(x.get('nodeId',{}).get('id'))=='249' for x in models['native_sts_std_arr_12_holocall_debriefs']['metadata'].get('exitPoints',[])),models['native_sts_std_arr_12_holocall_debriefs']['metadata'].get('exitPoints'))
 mc=closure(monitor,[8],{'dlc_sts_std_arr_12_failed':1});ck('failed branch closure excludes monitor reward20', '20' not in mc['executed'] and '25' in mc['executed'] and '23' in mc['executed'],mc)
 ow=models['native_sts_std_arr_12_ow'];og=ow['graphs']['root/5'];ck('normal owner uses same failure scene and failed0 SMS reward gate',og['nodes']['14']['refs']==monitor['nodes']['17']['refs'] and any(x.get('factName')=='dlc_sts_std_arr_12_failed' and x.get('comparisonType')=='Equal' and x.get('value')==0 for x in og['nodes']['45']['reads']) and ['45','False','43','Active'] in og['edges'] and all(e[1]=='success' or e[0] in ['47','48'] for e in og['edges'] if e[2]=='18'),dict(normal_reward=og['nodes']['18'],gate45=og['nodes']['45']))
 for name,gp2,i in [('native_sts_std_arr_12_ow','root/3/2',56),('native_sts_std_arr_12_ow','root/4',375),('native_sts_std_arr_12_gpl','root',8),('native_sts_std_arr_12_gpl','root/1',571)]:ck('actual cleanup consumer '+name+gp2+str(i),any(x.get('factName')=='arr_12_fail_loop_end' and x.get('comparisonType')=='Greater' and x.get('value')==0 for x in models[name]['graphs'][gp2]['nodes'][str(i)]['reads']),models[name]['graphs'][gp2]['nodes'][str(i)])
 # Deliberately corrupt raw after resource, re-normalize, compare independent clone oracle.
 def mutant(label,gpath,i,action):
  bad=copy.deepcopy(raws['after']);res=Resource(bad);gr=res.d(res.root['graph'])
  for p in gpath.split('/')[1:]:gr=res.d(next(res.d(h) for h in gr['nodes'] if str(res.d(h)['id'])==p)['phaseGraph'])
  nn=next(res.d(h) for h in gr['nodes'] if str(res.d(h)['id'])==str(i));action(nn,res);bm=Resource(bad).normalize();det=bool(compare_graph(b,bm));mutations.append(dict(fault=label,resource='after',graph=gpath,node=i,detected=det));ck('raw mutation '+label,det,mutations[-1])
 mutant('future start listener changed',mgp,13,lambda nn,res:next(x for x in walk(res.d(nn['condition'])) if x.get('$type')=='questVarComparison_ConditionType').update(value=9))
 mutant('old arm receipt becomes active',mgp,0,lambda nn,res:nn.update(socketName={'$type':'CName','$storage':'string','$value':'WrongInput'}))
 mutant('nested hacking cancellation threshold changed',mgp+'/32',8,lambda nn,res:next(x for x in walk(res.d(nn['condition'])) if x.get('$type')=='questVarComparison_ConditionType').update(value=99))
 mutant('native failure end flag removed',mgp,22,lambda nn,res:res.d(nn['type']).update(value=0))
 mutant('native reward exclusion reversed',mgp,25,lambda nn,res:next(x for x in walk(res.d(nn['condition'])) if x.get('$type')=='questVarComparison_ConditionType').update(value=1))
 mutant('nested chase cancellation fact changed',mgp+'/36',8,lambda nn,res:next(x for x in walk(res.d(nn['condition'])) if x.get('$type')=='questVarComparison_ConditionType').update(factName='QR5_missing_chase_cancel'))
 bad=copy.deepcopy(raws['after']);res=Resource(bad);gr=res.d(res.root['graph'])
 for pp in ['10','1202']:gr=res.d(next(res.d(h) for h in gr['nodes'] if str(res.d(h)['id'])==pp)['phaseGraph'])
 socks={res.hid(sh):(str(res.d(h)['id']),str(value(res.d(sh)['name']))) for h in gr['nodes'] for sh in res.d(h).get('sockets',[])};remove=set()
 for h in gr['nodes']:
  for sh in res.d(h).get('sockets',[]):
   for ch in res.d(sh).get('connections',[]):
    co=res.d(ch)
    if socks.get(res.hid(co.get('source')))==('13','Out') and socks.get(res.hid(co.get('destination')))==('4','In'):remove.add(res.hid(ch))
 for h in gr['nodes']:
  for sh in res.d(h).get('sockets',[]):
   so=res.d(sh);so['connections']=[c for c in so.get('connections',[]) if res.hid(c) not in remove]
 bm=Resource(bad).normalize();det=bool(remove) and ['13','Out','4','In'] not in bm['graphs'][mgp]['edges'] and bool(compare_graph(b,bm));mutations.append(dict(fault='actual start-to-spawn monitor connection removed',resource='after',graph=mgp,edge=[13,'Out',4,'In'],detected=det));ck('raw mutation removes real monitor listener connection',det,mutations[-1])
 write(O/'tests.json',dict(status='PASS_INDEPENDENT_SERIALIZED_REVIEW',count=len(tests),checks=tests,mutations=mutations));write(O/'review.json',dict(status='APPROVE_EXACT_BOUNDED_SERIALIZED_FUTURE_EVENT_REPAIR',resource='towercontinued\\native_gigs_u9\\sts_std_arr_12_entry.questphase',after_sha256=next(x['raw_sha256'] for x in exports if x['name']=='after'),before_sha256=next(x['raw_sha256'] for x in exports if x['name']=='before'),checks=len(tests),mutations=len(mutations),actual_raw_exports=len(exports),exports=str(H/'readback_02/manifest.json'),exports_sha256=sha(H/'readback_02/manifest.json'),code_sha256=sha(__file__),tests=str(O/'tests.json'),tests_sha256=sha(O/'tests.json'),actual_diff=compare_graph(a,b),scene_failure_closure=sc,monitor_failure_closure=mc,guard=required,limitations=['Static fresh future event only; no current ParentEntered/done/progressed save enrollment or native-arm reset.','FactsDB absent scalar0 supported; positive ParentEntered/SupportIssued and upstream certified admission provide provenance.','Monotone token model binds actual scene AND inputs and scalar guard; engine callbacks, interrupts, field scheduling/reload and streamed world placement are LIVE_ONLY/OPAQUE.','No new prefab owner/provider/XL registration; exact main root prefabs remain unchanged; no package or deployment approval implied.','Native success/reward paths retained exactly; reward exclusion is the fresh failed1 closure, not arbitrary external fact-modifier behavior.'],runtime_writes=[]));print(json.dumps(dict(checks=len(tests),mutations=len(mutations),status='APPROVED_SERIALIZED_SCOPE')))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(Path(a.output).resolve())

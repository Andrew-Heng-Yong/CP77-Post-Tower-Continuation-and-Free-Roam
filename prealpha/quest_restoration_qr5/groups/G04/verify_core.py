"""Pinned Muamar protocol checks. Does not import or execute builders."""
import sys,copy,collections,argparse
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
def path(g,a,b):
 q=collections.deque([[str(a)]]);seen={str(a)}
 while q:
  p=q.popleft()
  if p[-1]==str(b):return p
  for x,s,y,t in g['edges']:
   cut=g['nodes'].get(x,{}).get('type')=='scnCutControlNode'and s.startswith('1:')
   if x==p[-1]and s!='CutSource'and t!='CutDestination'and not cut and y not in seen:seen.add(y);q.append(p+[y])
 return None
def run(O):
 assert not O.exists();M={};pins=[];tests=[]
 def ck(name,ok,evidence):
  tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':evidence});assert ok,name
 for d in I.COMMON:
  m,p=I.load(d);M[d]=m;pins.append(p);ck('pinned '+d,not m['errors'],p)
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def e(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
 def wr(d,i,f,v,gp='root',exact=1):return any(x.get('factName')==f and x.get('value')==v and x.get('setExactValue')==exact for x in n(d,i,gp)['writes'])
 corep=H.parents[1]/'quest_restoration_qr4/groups/G09/shared_core.json'
 # Correct absolute predecessor path rather than relying on directory naming.
 corep=I.W/'prealpha/quest_restoration_qr4/groups/G09/shared_core.json';core=read(corep)
 ck('existing_U9_core_evidence',sha(core['tests'])==core['tests_sha256']and sha(core['source_pins'])==core['source_pins_sha256'],{'path':str(corep),'sha256':sha(corep),'checks':core['checks'],'scope':'U9 support, receipts and studio only; Muamar protocol checked here'})
 for row in core['sources']:
  if row.get('depot','').startswith('towercontinued\\'):ck('shared_binary_unchanged '+row['depot'],sha(I.C/'archive_source'/row['depot'].replace('\\','/'))==row['resource_sha256'],row['resource_sha256'])
 init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cl='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase';studio='towercontinued\\phone_studios_ph3\\studio_support.questphase'
 ck('owned_Muamar_controller',n(init,75)['refs']==[I.HC]and e(init,25,'Out1',75,'In1'),{'node':75,'owner':init,'edge':[25,'Out1',75,'In1']})
 ck('owned_Muamar_cleanup',n(cl,332)['refs']==[I.CL]and e(cl,464,'True',332,'In38')and e(cl,332,'Out38',466,'In'),{'owner':cl,'route':'464.True→332.In38→466.In'})
 ck('owned_two_shared_studios',set(n(studio,3)['prefabs'])=={'$/03_night_city/c_pacifica/#holocalls_studio_ep1','$/03_night_city/ne2/#holocalls_studio'},n(studio,3)['prefabs'])
 routes=[(32,'Out',33,'In'),(33,'Out',34,'In'),(34,'Out',35,'In1'),(36,'Out',28,'In'),(28,'False',10,'In'),(10,'Out',0,'holo_muamar_calls_v_start'),(3,'Out',11,'In'),(11,'Out',0,'holo_muamar_calls_v_end')]
 for edge in routes:ck('native_request_edge '+str(edge),e(I.HC,*edge),edge)
 ck('native_queue_counter',wr(I.HC,33,'holo_muamar_calls_v_start_activate_count',1,exact=0)and wr(I.HC,34,'holo_muamar_calls_v_start_activate',0)and wr(I.HC,10,'holo_muamar_calls_v_start_activate_count',-1,exact=0),'request→increment→clear; queued consumer decrements one, no fabricated acknowledgement')
 ck('incoming_listener_predicates',any(x.get('factName')=='holo_muamar_calls_v_start_activate'and x.get('comparisonType')=='Greater'for x in n(I.HC,32)['reads'])and {x.get('factName')for x in n(I.HC,36)['reads']}=={'holo_muamar_calls_v_start_activate_count','holo_setup_active','holo_setup_started'},n(I.HC,36)['payload'])
 ackroutes=[]
 for inp,ni in [('holo_muamar_calls_v_start',41),('holo_muamar_calls_v_end',42),('holo_v_calls_muamar_start',43),('holo_v_calls_muamar_end',44),('audio_muamar_calls_v_start',757),('audio_muamar_calls_v_end',759),('audio_v_calls_muamar_start',761),('audio_v_calls_muamar_end',763)]:
  fact=inp.replace('audio_','holo_')+'_done';p=path(g(I.HS,'scene'),g(I.HS,'scene')['entries'][inp],ni)
  ck('real_scene_ack '+inp,wr(I.HS,ni,fact,1,'scene')and bool(p),{'input':inp,'path':p,'node':ni,'fact':fact});ackroutes.append({'input':inp,'node':ni,'fact':fact,'path':p})
 for ni,one,two in [(4,'holo_muamar_calls_v_start_count','holo_muamar_calls_v_end_count'),(5,'holo_v_calls_muamar_start_count','holo_v_calls_muamar_end_count')]:
  c=n(I.CL,ni)['payload']['condition']['conditions'][0]['type'];ck('native_unbalanced_cleanup '+str(ni),c=={'$type':'questVarVsVarComparison_ConditionType','comparisonType':'Greater','factName1':one,'factName2':two},c)
 ck('native_reset_counts_and_end',wr(I.CL,6,'holo_muamar_calls_v_reset_counter',1,exact=0)and wr(I.CL,7,'holo_v_calls_muamar_reset_counter',1,exact=0)and e(I.CL,6,'Out',0,'holo_muamar_calls_v_end')and e(I.CL,7,'Out',1,'holo_v_calls_muamar_end'),'only reset request counters; scene executes end')
 ck('interrupt_real_flags',wr(I.HS,535,'holo_muamar_calls_v_interrupted',1,'scene')and wr(I.HS,527,'holo_v_calls_muamar_interrupted',1,'scene')and wr(I.HS,586,'holo_muamar_calls_v_interrupted',0,'scene'),'native scene interrupted and cleanup flags, not synthetic success')
 # Mutate actual deserialized quest/scene copies and re-normalize; production untouched.
 mutations=[]
 raw=read(next(p['json']for p in pins if p['depot']==I.HS));r=Resource(copy.deepcopy(raw));changed=0
 for x in walk(r.obj):
  if isinstance(x,dict)and x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='holo_muamar_calls_v_start_done'and x.get('value')==1:x['value']=0;changed+=1
 mutated=r.normalize()['graphs']['scene'];caught=not any(w.get('factName')=='holo_muamar_calls_v_start_done'and w.get('value')==1 for w in mutated['nodes']['41']['writes']);ck('mutation_real_ack_removed',changed>0 and caught,{'changed_raw_writers':changed});write(O/'mutations/ack_removed.scene.json',r.obj);mutations.append({'fault':'real scene start ACK removed','caught':caught,'path':str(O/'mutations/ack_removed.scene.json')})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'mutation_tests.json',mutations)
 out={'status':'VERIFIED_SHARED_SOURCE_PROTOCOL_WITH_EXPLICIT_LIMITS','source_epoch':'QR5 epoch00 = QR4 candidate_01 epoch03','tests':str(O/'tests.json'),'tests_sha256':sha(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'source_pins_sha256':sha(O/'source_pins.json'),'checks':len(tests),'sources':pins,'acknowledgements':ackroutes,'owned_controller':{'initializer':init,'node':75,'cleanup':cl,'cleanup_node':332,'studio':studio,'studio_node':3},'proven':['Native Muamar queued incoming producer consumer and real start/end acknowledgements, outgoing/audio acknowledgement routes, interrupted/reset-counter cleanup retained.','Current U9 owns Muamar listener and cleanup, while shared PH3 studio owns both original prefabs; native holocall root has no separate root prefab.'],'remaining':['Native resource source equality does not certify saved controller retirement or live scene binding.','Per-gig callers, tier/map/accounting, source omissions and scene outcomes must be checked separately.','Exact prefab presence does not decode the world sector or prove live placement; TDB definitions resolved separately by root.']}
 write(H/'shared_core.json',out);print({'checks':len(tests),'shared_core':str(H/'shared_core.json'),'sha256':sha(H/'shared_core.json')})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);run(Path(p.parse_args().out))

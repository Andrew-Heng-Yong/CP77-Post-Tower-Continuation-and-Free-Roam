"""Independent source/proposal review. Reads binaries' fresh WK9.1 exports, never writes resources."""
from pathlib import Path
import sys,json,copy,argparse,gzip
H=Path(__file__).resolve().parent;W=H.parents[4]
sys.path.insert(0,str(W/'prealpha/quest_restoration_qr5/groups/G14'));import source_inputs as I
from common import read,write,sha,walk,value
from model import Resource,reachable

def run(O):
 assert not O.exists();tests=[];pins=[];mut=[]
 def ck(name,ok,e):
  tests.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e))
  assert ok,name
 manifest=read(H/'readback_01/manifest.json');M=[];R=[]
 for p in manifest:
  ck('fresh binary+JSON pin '+p['name'],sha(p['binary'])==p['sha256'] and sha(p['json'])==p['json_sha256'],p)
  r=read(p['json']);m=Resource(r).normalize();ck('decoded '+p['name'],not m['errors'],m['errors']);M.append(m);R.append(r);pins.append(p)
 cur,main,bug,ow=M
 def n(m,k,gp='root'):return m['graphs'][gp]['nodes'][str(k)]
 def ed(m,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in m['graphs'][gp]['edges']
 def writes(m,f):return [(gp,k,x)for gp,g in m['graphs'].items()for k,v in g['nodes'].items()for x in v['writes']if x.get('factName')==f]
 def fact(m,k,f,v,gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(m,k,gp)['writes'])
 def rr(m,k,f,gp='root'):return any(x.get('factName')==f for x in n(m,k,gp)['reads'])
 # Actual fallback producer/waiter and the still-existing normal alternative.
 for e in [(176,'Out',303,'In'),(303,'Out',272,'In1'),(272,'Out1',304,'In'),(304,'Out',305,'In'),(273,'Out1',288,'In')]:
  ck('native fallback/normal edge '+str(e),ed(ow,*e,'root/4'),e)
 ck('request is increment, not synthetic ack',fact(ow,303,'sts_wat_nid_03_bugfixing',1,'root/4') and n(ow,303,'root/4')['writes'][0]['setExactValue']==0,n(ow,303,'root/4'))
 ck('real end waiter',rr(ow,304,'sts_wat_nid_03_bugfixing_end','root/4'),n(ow,304,'root/4'))
 ck('end writer native helper18 only locally',writes(bug,'sts_wat_nid_03_bugfixing_end')==[('root/3','18',n(bug,18,'root/3')['writes'][0])],writes(bug,'sts_wat_nid_03_bugfixing_end'))
 ck('end acknowledgement increments',n(bug,18,'root/3')['writes'][0]['setExactValue']==0 and n(bug,18,'root/3')['writes'][0]['value']==1,n(bug,18,'root/3'))
 # Two independent waits join by native XOR, then helper outcomes acknowledge.
 ck('17 XOR and24 AND actual raw',n(bug,17,'root/3')['type']=='questLogicalXorNodeDefinition' and n(bug,24,'root/3')['type']=='questLogicalAndNodeDefinition','not inferred from socket names')
 for e in [(0,'Out',8,'In'),(8,'False',9,'In'),(9,'Out',12,'In'),(9,'Out',13,'In'),(12,'Out',17,'In2'),(13,'Out',17,'In1'),(17,'Out1',10,'In1'),(10,'Out1',18,'In'),(10,'Out3',18,'In'),(10,'hwang_walk',19,'In'),(19,'Out',20,'In'),(20,'Out',21,'In'),(21,'Out',24,'In1'),(18,'Out',24,'In2'),(24,'Out1',1,'In')]:
  ck('native bounded monitor '+str(e),ed(bug,*e,'root/3'),e)
 ck('CYB receipt is armed before both future waits',fact(bug,9,'CYB-626818',1,'root/3') and rr(bug,8,'CYB-626818','root/3'),'9 before12/13; CYB1 is compatible with never-started job')
 ck('12 exact escort Active',n(bug,12,'root/3')['reads'][0]['state']=='Active' and n(bug,12,'root/3')['journal_paths']==['quests/street_stories/watson/northside_industrial_district/sts_wat_nid_03/sts_wat_nid_03/escort_haruo_to_nomad'],n(bug,12,'root/3'))
 ck('13 actual native request',rr(bug,13,'sts_wat_nid_03_bugfixing','root/3'),n(bug,13,'root/3'))
 # Shared lease is not absent merely because the bugfix resource root is empty.
 pf='#sts_wat_nid_03_streetstory'
 ck('exact original shared PIP',bug['root_prefabs']==[] and n(bug,3)['prefabs']==[pf] and main['root_prefabs']==[pf],{'bugfix_node3':n(bug,3),'main_root':main['root_prefabs']})
 ck('current main actually runs native prefab-owning body',n(cur,8)['refs']==[manifest[1]['depot']] and ed(cur,65004,'Out',8,'In1'),'native main root owns same PIP; proposed helper preserves original simultaneous relationship')
 ck('parent has no terminating output',not any(x['type']=='questOutputNodeDefinition'for x in cur['graphs']['root']['nodes'].values()),'helper terminator remains internal, not parent/main killer')
 ck('native monitor owns terminating cleanup scope',n(bug,1,'root/3')['payload']['type']=='Terminating','no new external root output')
 # Exact native actions, relative bindings, brakes, time, balanced courier cleanup.
 gp='root/3/10'
 for k,typ in [(3,'questStopVehicle_NodeType'),(4,'questToggleForceBrake_NodeType'),(7,'questAssignCharacter_NodeType'),(20,'questToggleForceBrake_NodeType')]:
  ck('native vehicle action '+str(k),n(bug,k,gp)['payload']['type']['$type']==typ,n(bug,k,gp)['payload'])
 ck('original brake release and seat unassignment',n(bug,4,gp)['payload']['type']['val']==1 and n(bug,20,gp)['payload']['type']['val']==0 and n(bug,7,gp)['payload']['type']['assign']==0,'#mounted_vehicle player vehicle; seat_front_right Haruo')
 ck('real100ms delay preserved',n(bug,13,gp)['payload']['condition']['type']['$type']=='questRealtimeDelay_ConditionType' and n(bug,13,gp)['payload']['condition']['type']['miliseconds']==100,n(bug,13,gp)['payload'])
 ck('Haruo AI role reset is native bounded action',value(n(bug,9,gp)['payload']['function'])=='AIClearRoleCommandParams' and '#nid_03_com_haruo'in n(bug,9,gp)['node_refs'],n(bug,9,gp)['payload'])
 ck('native movement/despawn bindings',set(n(bug,19,'root/3')['node_refs'])=={'#nid_03_com_haruo','#nid_03_mp_haruo_run'} and '#nid_03_com_haruo'in n(bug,21,'root/3')['node_refs'],{'move':n(bug,19,'root/3'),'cleanup':n(bug,21,'root/3')})
 ck('courier decrement guarded by exact native stopped receipt',rr(bug,77,'sts_wat_nid_03_stopped_courier_loop',gp) and ed(bug,77,'True',75,'In',gp) and ed(bug,77,'False',17,'Sts_wrongfully_finished',gp) and fact(bug,75,'sa_ep1_courier_force_despawn_and_block',-1,gp),'no blind counter decrement; original scene input Sts_wrongfully_finished')
 ck('hwang_walk nonterminating, completed stop remains distinct',n(bug,69,gp)['payload']['type']=='NonTerminating' and n(bug,15,gp)['payload']['type']=='Terminating' and not any(e[0]=='10'and e[1]=='Out2'for e in bug['graphs']['root/3']['edges']),'preserve native output2 no added acknowledgement')
 ck('helper no reward grant nodes',not any(v['reward']for v in bug['graphs'][gp]['nodes'].values()),'native journals/debriefs retained; no setup/reward replay')
 # Retired ancestor source is independently parsed, not inferred solely from q307 fact.
 ap=W/'prealpha/quest_restoration_qr2/ancestor_review.json';a=read(ap);ck('ancestor evidence pin',sha(ap)=='C5B943CE147AD37C9426C8E24203345D4D2C155FCB8935855D3E009451DCF7D5',str(ap));pins.append({'path':str(ap),'sha256':sha(ap)})
 anc=[]
 for p in a['inputs'][:2]:
  ck('ancestor JSON pin '+p['depot'],sha(p['source_json'])==p['json_sha256'],p);anc.append(Resource(read(p['source_json'])).normalize());pins.append(p)
 for e in [(106,'Out',109,'In'),(109,'Out',107,'In')]:ck('actual genuine Tower termination '+str(e),ed(anc[0],*e),e)
 ck('ancestor107 Terminating',n(anc[0],107)['payload']['type']=='Terminating',n(anc[0],107))
 ck('bugfix resides under killed main82',manifest[2]['depot'] not in n(anc[0],4,'root/82')['refs'] and a['inputs'][1]['depot']in n(anc[0],4,'root/82')['refs'],n(anc[0],4,'root/82'))
 # Bounded independent all-model scan; exact cache pins and epoch applicability are explicit.
 scans=[];hits=[];priv=[]
 for d,p in I.MI.items():
  z=Path(p['normalized_model']);b=z.read_bytes();import hashlib
  scans.append([d,hashlib.sha256(b).hexdigest().upper()]);m=json.loads(gzip.decompress(b))
  for gp,g in m['graphs'].items():
   for k,nd in g['nodes'].items():
    for x in nd.get('writes',[]):
     if x.get('factName')=='sts_wat_nid_03_bugfixing_end':hits.append({'depot':d,'graph':gp,'node':k,'write':x})
  if d in I.E['source_resources'] and 'sts_wat_nid_03_bugfixing_end'in json.dumps(m):priv.append(d)
 ck('pinned cache unique native end writer',len(hits)==1 and hits[0]['depot']==manifest[2]['depot'] and hits[0]['node']=='18',hits)
 ck('no current indexed private substitute',not priv,priv)
 pk=[]
 for p in I.E['package_files']:
  if Path(p['path']).suffix.lower()not in ['.reds','.lua','.yaml','.xl']:continue
  f=I.C/'package'/p['path'];ck('current package source pin '+p['path'],sha(f)==p['sha256'],p);s=f.read_text(encoding='utf-8-sig');lines=[{'line':i+1,'text':v,'catalogue_return':('return ['in v or 'MetadataJSON'in v)}for i,v in enumerate(s.splitlines())if 'sts_wat_nid_03_bugfixing_end'in v];pk.append({'path':str(f),'sha256':sha(f),'mentions':lines})
 ck('current package exact end mentions are catalogue returns',all(x['catalogue_return']for p in pk for x in p['mentions']),pk)
 # Existing companion prestate may race but cannot write Started/native progress.
 pre=n(cur,64000)['refs'][0];pm,pp=I.load(pre);pins.append(pp)
 ck('prestate remains independent and has no fact writes',ed(cur,65003,'Out',64000,'In1') and not any(v['writes']for g in pm['graphs'].values()for v in g['nodes'].values()),pre)
 # Revised actual proposal, explicitly reject frozen01's AND and missing refusal.
 prop=I.F/'groups/G12/cheetah_proposal_02/proposal.json';p=read(prop);ck('corrected proposal02 hash',sha(prop)=='32086A3AB3812DE1FF6C4E5BE95DBD6872A79B6741A99827CDB2B582A09DB3A3',str(prop));pins.append({'path':str(prop),'sha256':sha(prop)})
 ee=p['attachment']['new_edges'];ck('ordered guarded fork with native refusal continuation',ee==[[65003,'Out',1200,'In'],[1200,'True',1201,'In'],[1200,'False',2,'In1'],[1201,'Out',1202,'In1'],[1201,'Out',2,'In1']],ee)
 ck('source native2 attachment exists',ed(cur,65003,'Out',2,'In1') and ed(cur,69,'Out',65004,'In'),'guard happens before native2 path writes Started65004; old64000 untouched')
 ck('new IDs available',not {'1200','1201','1202'}&set(cur['graphs']['root']['nodes']),list(cur['graphs']['root']['nodes']))
 # Predicate oracle uses normal absent scalar=0; private positive provenance is required.
 pos=['ParentEntered'];zero=['Started','MainFinished','OwnerFinished','Fault','MonitorEntered'];native=['nid_03_start','nid_03_finished','sts_wat_nid_03_bugfixing','sts_wat_nid_03_bugfixing_end','sts_wat_nid_03_completed']
 def permit(f):return f.get('ParentEntered',0)==1 and f.get('SupportIssued',0)==1 and all(f.get(k,0)==0 for k in zero+native) and f.get('SupportFault',0)==0
 good={'ParentEntered':1,'SupportIssued':1}
 ck('missing scalar zeros allowed with positive provenance',permit(good) and not permit({}),'candidate must also retain65002 genuineTower event; journal missing remains separate')
 for k in zero+native+['SupportFault']:
  f=good|{k:1};ck('refuse without changing original main '+k,not permit(f),'1200.False→2.In1')
 for cyb in [0,1]:ck('no CYB reset or historical gate '+str(cyb),permit(good|{'CYB-626818':cyb}),'old CYB arm8/9 retained but unreachable from cloned entry')
 # Actual raw-copy mutations, each caught by a distinct source predicate.
 def rawnode(r,gp,k):
  z=Resource(r);g=z.d(z.root['graph'])
  for ni in gp.split('/')[1:]:g=z.d(next(z.d(h)for h in g['nodes']if str(z.d(h)['id'])==ni)['phaseGraph'])
  return next(z.d(h)for h in g['nodes']if str(z.d(h)['id'])==str(k))
 def uh(x):return x.get('Data',x)
 gp='root/3/10'
 specs=[('strip_PIP','root',3,lambda x:x.update(phaseInstancePrefabs=[]),lambda m:n(m,3)['prefabs']==[pf]),('XOR_to_AND','root/3',17,lambda x:x.update({'$type':'questLogicalAndNodeDefinition'}),lambda m:n(m,17,'root/3')['type']=='questLogicalXorNodeDefinition'),('missing_end_writer','root/3',18,lambda x:uh(x['type']).update(factName='QR5_broken_ack'),lambda m:fact(m,18,'sts_wat_nid_03_bugfixing_end',1,'root/3')),('brake_never_released',gp,20,lambda x:uh(x['type']).update(val=1),lambda m:n(m,20,gp)['payload']['type']['val']==0),('unguarded_courier_decrement',gp,77,lambda x:uh(uh(x['condition'])['type']).update(factName='QR5_other_receipt'),lambda m:rr(m,77,'sts_wat_nid_03_stopped_courier_loop',gp)),('real_delay_to_game_delay',gp,13,lambda x:uh(uh(x['condition'])['type']).update({'$type':'questGameTimeDelay_ConditionType'}),lambda m:n(m,13,gp)['payload']['condition']['type']['$type']=='questRealtimeDelay_ConditionType')]
 for label,gp2,k,change,oracle in specs:
  r=copy.deepcopy(R[2]);change(rawnode(r,gp2,k));mm=Resource(r).normalize();ck('raw fault detected '+label,oracle(bug) and not oracle(mm),{'graph':gp2,'node':k});fp=O/'mutations'/str(label+'.json');write(fp,r);mut.append({'fault':label,'path':str(fp),'sha256':sha(fp),'detected':True})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'model_scan.json',{'models':scans,'unique_end_writer':hits,'private_substitutes':priv,'limit':'Pinned5136 historical normalized inputs plus epoch00 private and current package source. Not a new installation/provider/external-mod scan.'});write(O/'package_scan.json',pk);write(O/'mutations.json',mut)
 result={'status':'APPROVE_BOUNDED_FUTURE_ONLY_PROPOSAL02_SOURCE_SCOPE','checks':len(tests),'failures':sum(t['status']=='FAIL'for t in tests),'mutations':len(mut),'tests':str(O/'tests.json'),'proposal':str(prop),'proposal_sha256':sha(prop),'confirmed_defect':'Reachable native request303/end-wait304 lacks retired original consumer18 in current restored owner; normal273 route remains possible.','corrections':'Frozen01 AND17 prose rejected; native17 XOR preserved; refusal continuation2 required and present in02.','safety_scope':'Only a future65003 event after retained genuineTower65002; guard before native2; private receipt once. Clone exact node3 PIP+recursive10 and only bypass old8/9 CYB entry. No old started/progressed state adoption, no counter/fact reset, no new arbitrary AI/device commands, no new reward/setup.','required_serialized_gates':['Actual guard exact predicates and receipt writes, positive Tower event and refusal route','Exact old payloads/IDs/edges unchanged except allowlisted fork','Recursive copied source3/10 and PIP exact except cloned input prefix','All final resource/package preservation/readback/regression gates'], 'limits':['World placement/relative NodeRef availability and simultaneous native PIP engine lease behavior remain OPAQUE/LIVE_ONLY; source scope matches native main+helper relationship.','Original helper output2 no end edge remains unchanged; not proof every fallback can complete.','Fresh enrollment only; old already-started fallback states not recovered.','No gameplay success claim; installed/provider state unchanged and not newly scanned.'],'runtime_changes':[],'source_epoch':str(I.F/'source_epoch_00.json'),'source_epoch_sha256':sha(I.F/'source_epoch_00.json')}
 write(O/'review.json',result);print(json.dumps(result))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())

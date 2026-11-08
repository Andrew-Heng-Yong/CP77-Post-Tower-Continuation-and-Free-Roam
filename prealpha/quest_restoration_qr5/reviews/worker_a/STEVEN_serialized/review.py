"""Independent actual serialized Steven delta/guard/actor audit. No root checker imports."""
from pathlib import Path
import sys,copy,collections,argparse,json
H=Path(__file__).resolve().parent;W=H.parents[4];F=W/'prealpha/quest_restoration_qr5'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable

def run(O):
 assert not O.exists();tests=[];M={};R={};pins=read(H/'readback_01/manifest.json')
 def ck(k,v,e):
  tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':sorted(e)if isinstance(e,set)else e})
  if not v:write(O/'failed_tests.json',tests);raise AssertionError(k)
 for p in pins:
  ck('fresh exact raw/json '+p['name'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p)
  R[p['name']]=read(p['json']);M[p['name']]=Resource(R[p['name']]).normalize();ck('decode '+p['name'],not M[p['name']]['errors'],M[p['name']]['errors'])
 ppath=F/'groups/G15/actor_proposal_02/proposal.json';p=read(ppath);ck('approved proposal exact pin',sha(ppath)=='FDA1923D9471E24E45748FAE009CB665F958BAB265BE9695D26ADD6B28266381',str(ppath));pins.append({'path':str(ppath),'sha256':sha(ppath)})
 rpath=F/'groups/G11/reviews/STEVEN/proposal02_verification_01/review.json';ck('independent source approval pin',sha(rpath)=='23CE232D1D3DE41174249A2AE1522A407369957BE5DB32793BC6370B190A6F48',str(rpath));pins.append({'path':str(rpath),'sha256':sha(rpath)})
 before,after,template,actor,cleanup,body=M['before'],M['after'],M['native_7'],M['native_3'],M['native_1'],M['native_phase'];gp='root/50';hp=gp+'/1302'
 def n(m,k,g='root'):return m['graphs'][g]['nodes'][str(k)]
 def edge(m,a,s,b,t,g='root'):return [str(a),s,str(b),t]in m['graphs'][g]['edges']
 # Exact serialized preservation, including all old graph descendants and metadata.
 ck('exact graph set delta',set(after['graphs'])-set(before['graphs'])=={hp} and not set(before['graphs'])-set(after['graphs']),list(after['graphs']))
 ck('whole resource metadata/embedded/root PF unchanged',all(before[k]==after[k]for k in ['metadata','root_prefabs','embedded_files']),before['metadata_sha256'])
 for path,g in before['graphs'].items():
  old=g['nodes'];new=after['graphs'][path]['nodes'];ck('old identities retained '+path,set(old)<=set(new),len(old))
  for i,nd in old.items():ck('old node exact payload/sockets '+path+'/'+i,nd==new[i],nd['payload_sha256'])
  if path!=gp:ck('old graph edges exact '+path,g['edges']==after['graphs'][path]['edges'],len(g['edges']))
  else:
   a=collections.Counter(map(tuple,g['edges']));b=collections.Counter(map(tuple,after['graphs'][path]['edges']));removed=[list(e)for e,c in (a-b).items()for _ in range(c)];added=[list(e)for e,c in(b-a).items()for _ in range(c)]
   ck('exact removed two edges',sorted(removed)==sorted([[str(a),s,str(b),t]for a,s,b,t in p['parent_removed_edges']]),removed)
   ck('exact added seven ordered edges',sorted(added)==sorted([[str(a),s,str(b),t]for a,s,b,t in p['parent_added_edges']]),added)
   ck('exact new local nodes',set(new)-set(old)=={'1300','1301','1302'},set(new)-set(old))
 ck('parent nonterminating scope retained',not any(x['type']=='questOutputNodeDefinition'for x in after['graphs'][gp]['nodes'].values()),'original native23 body Terminating only, helper sibling survives')
 # Match guard predicates to approved table, then independently evaluate actual tree.
 guard=n(after,1300,gp);late=n(after,1303,hp)
 ck('immediate initial guard vs waiting late guard',guard['type']=='questConditionNodeDefinition'and late['type']=='questPauseConditionNodeDefinition','no sibling Started0 scheduling race')
 actualfacts={x['factName']:x['value']for x in guard['reads']if x['$type']=='questVarComparison_ConditionType'}
 ck('exact initial fact table',actualfacts==p['initial_guard_facts'],actualfacts)
 ck('initial all comparisons Equal',all(x['comparisonType']=='Equal'for x in guard['reads']if 'factName'in x),'no weakened post-Tower/native/default/S23/new receipt predicates')
 actualj=[x for x in guard['reads']if x['$type']=='questJournalEntryState_ConditionType'];ck('exact seven all-Inactive journal histories',actualj==p['initial_guard_journals']and len(actualj)==7,actualj)
 actual_late=[dict(fact=x['factName'],comparison=x['comparisonType'],value=x['value'])for x in late['reads']if 'factName'in x]
 ck('exact late fact table',actual_late==p['helper_graph_change']['late_guard_facts'],actual_late)
 lj=[x for x in late['reads']if x['$type']=='questJournalEntryState_ConditionType'];ck('late rootjournal Inactive orActive only',len(lj)==2 and {x['state']for x in lj}=={'Inactive','Active'}and all(x['path']['realPath']==p['helper_graph_change']['late_guard_journal']['path']for x in lj),lj)
 ck('private once-only receipt exact',n(after,1301,gp)['writes']==[{'$type':'questSetVar_NodeType','factName':p['claim_fact'],'setExactValue':1,'value':1}],n(after,1301,gp))
 # Exact helper metadata and3 native node payloads; no501 message subtree.
 expected=copy.deepcopy(n(template,100)['payload']);expected['id']=1302
 ck('phase metadata exact template exceptid',n(after,1302,gp)['payload']==expected,expected)
 ck('only four helper identities',set(after['graphs'][hp]['nodes'])=={'0','17','19','1303'},list(after['graphs'][hp]['nodes']))
 for i in ['0','17','19']:ck('native helper source payload/sockets '+i,n(after,i,hp)==n(template,i,'root/100'),n(after,i,hp)['payload_sha256'])
 ck('all actor dispatches go through late fence',after['graphs'][hp]['edges']==sorted([['0','Out','19','In'],['19','Out','1303','In'],['1303','Out','17','In1'],['17','Out1','19','In']]),after['graphs'][hp]['edges'])
 ck('no501 subtree anywhere under new helper',not any(path.startswith(hp+'/')for path in after['graphs'])and'501'not in after['graphs'][hp]['nodes'],'no native SMS/timer/journal/reward clone')
 ck('only new private writer; no grant/SMS/default_on1',not any(v['writes']or v['sms']or v['reward']for v in after['graphs'][hp]['nodes'].values()),'external original actor remains exact; helper only dispatches it')
 ck('actor actual external target',n(after,17,hp)['refs']==[p['native_actor']],n(after,17,hp)['refs'])
 # Actual native body mandatory finished suffix and preserved cleanup producer.
 ck('current body23 binding exact',n(after,23,gp)['refs']==[next(x['depot']for x in pins if x.get('name')=='native_phase')],n(after,23,gp))
 ck('real native finished312 before terminal suffix',n(body,312)['writes'][0]['factName']=='sts_ep1_08_finished' and n(body,312)['writes'][0]['value']==1 and edge(body,312,'Out',314,'In'),n(body,312))
 ck('existing own MainFinished write after real native out',edge(after,23,'Out1',65005,'In',gp)and n(after,65005,gp)['writes'][0]['factName']=='PTFRU9_sts_ep1_08_MainFinished','late requires both native+own receipts')
 ck('existing cleanup owner remains exact',n(after,64000,gp)==n(before,64000,gp)and n(after,64000,gp)['refs']==[next(x['depot']for x in pins if x.get('name')=='native_1')],n(after,64000,gp))
 ck('native invitation remains sole original cleanup message',n(cleanup,8,'root/3')['sms'] and 'biomonitor_destroyed_meeting_invitation'in str(n(cleanup,8,'root/3')['payload']),'native cloned cleanup not edited')
 for k in [4,5]:ck('native66gamehour timer '+str(k),n(cleanup,k,'root/3')['payload']['condition']['type']['$type']=='questGameTimeDelay_ConditionType'and n(cleanup,k,'root/3')['payload']['condition']['type']['hours']==66,n(cleanup,k,'root/3')['payload'])
 ck('original default_on1 genuine writer unchanged',n(cleanup,2,'root/3')['writes'][0]=={'$type':'questSetVar_NodeType','factName':'steven_santos_default_on','setExactValue':1,'value':1},n(cleanup,2,'root/3'))
 # Original actor/scene/context and cleanup scopes; do not confuse empty PIP with no world requirements.
 ck('native actor Ana selector preserved',n(actor,2)['reads'][0]['factName']=='sts_ep1_08_biomonitor_ana'and edge(actor,2,'False',5,'In')and edge(actor,2,'True',3,'In'),'late Ana0 chooses native night_city; no new stadium actor')
 ck('native night_city community target', '#steven_default_night_city_com'in n(actor,5)['node_refs']and value(n(actor,5)['payload']['actions'][0]['type']['communityEntryPhaseName'])=='night_city',n(actor,5)['payload'])
 ck('native actor shutdown default/escape OR',n(actor,30)['payload']['condition']['operation']=='OR'and edge(actor,30,'Out',32,'In')and edge(actor,32,'False',31,'In')and edge(actor,31,'Out',1,'In'),'retains original deactivation/output')
 ck('original conversation default0 cleanup',n(actor,14,'root/28')['writes'][0]['factName']=='steven_santos_default_on'and n(actor,14,'root/28')['writes'][0]['value']==0 and edge(actor,7,'Out',14,'In','root/28'),'preserve earned conversation ending')
 ck('contact/prevention/vehicle cleanup remains authored',edge(actor,14,'Out',23,'In','root/28')and edge(actor,23,'Out',27,'In','root/28')and n(actor,23,'root/28')['payload']['type']['params'][0]['addContact']==0 and n(actor,27,'root/28')['payload']['event']['enable']==0 and n(actor,30,'root/28')['payload']['type']['activate']==0,'native exact external actor bytes, no arbitrary stand-in AI/device action')
 # Fixtures derive semantics from actual condition tree, not from proposal table.
 def ev(x,f,j):
  t=x['$type']
  if t=='questLogicalCondition':
   a=[ev(c,f,j)for c in x['conditions']];return all(a)if x['operation']=='AND'else any(a)
  if t in ['questFactsDBCondition','questJournalCondition']:return ev(x['type'],f,j)
  if t=='questVarComparison_ConditionType':
   a=f.get(x['factName'],0);b=x['value'];return {'Equal':a==b,'Greater':a>b,'GreaterOrEqual':a>=b}[x['comparisonType']]
  if t=='questJournalEntryState_ConditionType':return j.get(x['path']['realPath'],'UNKNOWN')==x['state']
  raise ValueError(t)
 ini={k:v for k,v in actualfacts.items()if v};jj={x['path']['realPath']:'Inactive'for x in actualj};lc={x['factName']:max(1,x['value'])if x['comparisonType']in ['Greater','GreaterOrEqual']else x['value']for x in late['reads']if 'factName'in x};rootj={lj[0]['path']['realPath']:'Inactive'}
 ck('actual initial fresh with absent scalar0 accepted',ev(guard['payload']['condition'],ini,jj),'missing expected0 scalar is0, missing journal is UNKNOWN')
 ck('absent positive provenance refuses',not ev(guard['payload']['condition'],{},jj),'existing65002 genuineTower event additionally unchanged')
 for k,v in actualfacts.items():
  f=ini|{k:0 if v else 1};ck('initial altered fact refuses helper '+k,not ev(guard['payload']['condition'],f,jj),'both original children run onFalse')
 for jp in jj:
  for state in ['UNKNOWN','Active','Succeeded','Failed']:
   ck('initial journal protects '+jp+':'+state,not ev(guard['payload']['condition'],ini,jj|{jp:state}),'missing/progressed history defers helper only')
 for os in [0,1]:ck('late ownerFinished irrelevant '+str(os),ev(late['payload']['condition'],lc|{'PTFRU9_sts_ep1_08_OwnerFinished':os},rootj),'no lateStarted0 requirement')
 for ana in [1,2]:ck('late changed Ana always refuses '+str(ana),not ev(late['payload']['condition'],lc|{'sts_ep1_08_biomonitor_ana':ana},rootj),'checked every19→1303→17 dispatch')
 for jpstate in ['Inactive','Active','Succeeded','Failed','UNKNOWN']:ck('late journal '+jpstate,ev(late['payload']['condition'],lc,{lj[0]['path']['realPath']:jpstate})==(jpstate in ['Inactive','Active']),'terminal/unknown refuses')
 # Raw actual-resource mutation controls, resolve handles before editing.
 def gn(r,path):
  z=Resource(r);g=z.d(z.root['graph'])
  for i in path.split('/')[1:]:g=z.d(next(z.d(h)for h in g['nodes']if str(z.d(h)['id'])==i)['phaseGraph'])
  return z,g
 def rn(r,path,i):
  z,g=gn(r,path);return z,next(z.d(h)for h in g['nodes']if str(z.d(h)['id'])==str(i))
 def remove_edge(r,path,e):
  z,g=gn(r,path);socks={z.hid(sh):(str(z.d(h)['id']),str(value(z.d(sh)['name'])))for h in g['nodes']for sh in z.d(h)['sockets']};bad=set()
  for h in g['nodes']:
   for sh in z.d(h)['sockets']:
    for ch in z.d(sh).get('connections',[]):
     c=z.d(ch)
     if [*socks.get(z.hid(c['source']),('','')),*socks.get(z.hid(c['destination']),('',''))]==e:bad.add(z.hid(ch))
  for h in g['nodes']:
   for sh in z.d(h)['sockets']:z.d(sh)['connections']=[c for c in z.d(sh).get('connections',[])if z.hid(c)not in bad]
  return len(bad)
 muts=[]
 for label,modify,oracle in [
  ('drop_refusal_main',lambda r:remove_edge(r,gp,['1300','False','10','In1']),lambda m:edge(m,1300,'False',10,'In1',gp)),
  ('drop_refusal_companion',lambda r:remove_edge(r,gp,['1300','False','64001','In1']),lambda m:edge(m,1300,'False',64001,'In1',gp)),
  ('missing_late_Ana',lambda r:[x.update(factName='QR5_missing_Ana')for x in walk(rn(r,hp,1303)[1])if x.get('factName')=='sts_ep1_08_biomonitor_ana'],lambda m:any(x.get('factName')=='sts_ep1_08_biomonitor_ana'and x['value']==0 for x in n(m,1303,hp)['reads'])),
  ('weaken_initial_Started',lambda r:[x.update(value=1)for x in walk(rn(r,gp,1300)[1])if x.get('factName')=='PTFRU9_sts_ep1_08_Started'],lambda m:any(x.get('factName')=='PTFRU9_sts_ep1_08_Started'and x['value']==0 for x in n(m,1300,gp)['reads'])),
  ('break_actor_target',lambda r:[x.update({'$value':'QR5_missing_actor.questphase'})for x in walk(rn(r,hp,17)[1])if x.get('$type')=='ResourcePath'],lambda m:n(m,17,hp)['refs']==[p['native_actor']])]:
  r=copy.deepcopy(R['after']);modify(r);mm=Resource(r).normalize();ck('raw deliberate fault '+label,oracle(after)and not oracle(mm),label);fp=O/'mutations'/str(label+'.json');write(fp,r);muts.append({'fault':label,'path':str(fp),'sha256':sha(fp),'detected':True})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'mutations.json',muts);write(O/'actor_scene_bindings.json',{'actor':actor,'scenes':{k:M[k]for k in ['native_4','native_5']},'limits':'Exact original bindings only; target world/community/scene/notifier/vehicle-area placement OPAQUE, live scheduling/save state unproved.'})
 result={'status':'APPROVE_EXACT_SERIALIZED_FUTURE_ACTOR_ONLY_DELTA','checks':len(tests),'mutations':len(muts),'failures':0,'tests':str(O/'tests.json'),'before_sha256':pins[0]['sha256'],'after_sha256':pins[1]['sha256'],'source_pins':str(O/'source_pins.json'),'code':str(Path(__file__).resolve()),'code_sha256':sha(__file__),'scope':'Actual candidate01→candidate02 spy entry; exact two removed/seven ordered edges, three nodes/four-node helper, native actor/context unchanged, no501/messages/timer/reward/default1 writer.','limits':['Already-entered/started owners not adopted; unknown journals defer helper while original main continues.','Native world/scene/community/vehicle target resolution OPAQUE; engine timing/streaming/reload LIVE_ONLY.','Separate gameplay JSON/cache discrepancy mentioned by prior source reviewer not used as positive parity proof here; native mandatory finished suffix separately fresh-exported.','Package validation remains root gate; no installed modification or live success claim.'],'runtime_changes':[]};write(O/'review.json',result);print(json.dumps(result))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())

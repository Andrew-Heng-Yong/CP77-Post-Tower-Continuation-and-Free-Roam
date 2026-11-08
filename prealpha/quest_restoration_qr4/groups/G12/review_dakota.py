"""Independent worker-B raw-source review; no G09/G10 verifier imports."""
from pathlib import Path
import sys,json,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from verify import path,externalize
from common import read,write,sha
def run(group):
 O=H/'reviews'/f'{group}.json';assert not O.exists();prior=read(H.parent/group/'results.json');quests=prior['quest_ids'];M={};pins=[];checks=[];cases=[]
 def load(d):
  if d not in M:m,p=I.load(d);M[d]=m;pins.append(p)
  return M[d]
 def g(d,gp='root'):return load(d)['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def ck(name,ok,ev):checks.append({'name':name,'pass':bool(ok),'evidence':ev});assert ok,name
 ctl='base\\quest\\holocalls\\dakota\\dakota_holocall.questphase';hs='base\\quest\\holocalls\\dakota\\dakota_holocall.scene';cl='base\\quest\\holocalls\\dakota\\dakota_cleanup.questphase';init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cleanup='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase'
 inode=[i for i,x in g(init)['nodes'].items()if ctl in x['refs']];cnode=[i for i,x in g(cleanup)['nodes'].items()if cl in x['refs']]
 ck('actual_U9_Dakota_listener_connected',len(inode)==1 and any(x[2]==inode[0]for x in g(init)['edges']),inode)
 ck('actual_U9_Dakota_cleanup_connected',len(cnode)==1 and any(x[2]==cnode[0]for x in g(cleanup)['edges'])and any(x[0]==cnode[0]for x in g(cleanup)['edges']),cnode)
 sceneid=next(i for i,x in g(ctl)['nodes'].items()if hs in x['refs'])
 for typ in ['start','end']:
  pref='holo_dakota_calls_v_'+typ;req=pref+'_activate';done=pref+'_done'
  readers=[i for i,x in g(ctl)['nodes'].items()if any(z.get('factName')==req for z in x['reads'])];clears=[i for i,x in g(ctl)['nodes'].items()if any(z.get('factName')==req and z.get('value')==0 for z in x['writes'])]
  ck('native_request_consume_clear '+typ,any(path(g(ctl),a,b)for a in readers for b in clears),{'readers':readers,'clears':clears})
  if typ=='start':
   counter=req+'_count';inc=[i for i,x in g(ctl)['nodes'].items()if any(z.get('factName')==counter and z.get('value')==1 for z in x['writes'])];dec=[i for i,x in g(ctl)['nodes'].items()if any(z.get('factName')==counter and z.get('value')==-1 for z in x['writes'])];wait=[i for i,x in g(ctl)['nodes'].items()if any(z.get('factName')==counter and z.get('comparisonType')=='Greater'for z in x['reads'])]
   ck('native_queued_request_count_writer_reader',bool(inc)and bool(dec)and any(path(g(ctl),a,b)for a in wait for b in dec)and any([b,'Out',sceneid,pref]in g(ctl)['edges']for b in dec),{'inc':inc,'wait':wait,'decrement':dec})
  else:ck('native_real_end_to_scene',any([b,'Out',sceneid,pref]in g(ctl)['edges']for b in clears),{'scene':sceneid,'input':pref})
  ack=[i for i,x in g(hs,'scene')['nodes'].items()if any(z.get('factName')==done and z.get('value')==1 for z in x['writes'])and path(g(hs,'scene'),g(hs,'scene')['entries'][pref],i)]
  ck('real_native_ack '+typ,bool(ack),ack)
 for q in quests:
  rs=[r for r in I.U['recipes']if r.get('id')==q and r.get('kind')in ['entry','credit','map']];entry=next(r for r in rs if r['kind']=='entry');cur=entry['depot'];native=entry['native'];body=next(i for i,x in g(cur)['nodes'].items()if native in x['refs'])
  ck('actual_native_gig_body '+q,n(cur,body)['refs']==[native]and ['65004','Out',body,entry['main_input']]in g(cur)['edges'],{'target':native,'body_node':body})
  for r in rs:
   d=r['depot'];don='recipe:'+r['raw'];gp=r['graph']
   ck('original_selected_payloads '+d,all(n(d,ni)['payload']==externalize(n(don,ni,gp)['payload'])for ni in r['ids']if ni!=0),{'original':don,'graph':gp,'selected_ids':r['ids']})
   ck('recipe_exact_edges '+d,g(d)['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),r['edges'])
   if r['kind']=='credit':
    incr=[(i,x)for i,x in g(d)['nodes'].items()if any(z.get('factName')=='bls_sts_counter'for z in x['writes'])]
    ck('once_native_credit_increment '+q,len(incr)==1 and all(z['value']==1 and z['setExactValue']==0 for z in incr[0][1]['writes']if z.get('factName')=='bls_sts_counter')and any(z.get('factName')=='PTFRU9_'+q+'_CreditEntered'and z.get('value')==1 for z in n(d,65001)['writes']),{'increment_nodes':[i for i,x in incr],'claim':65001})
  # All native local resources and scenes are loaded by namespace, no title assumptions.
  local=[d for d,r in I.IDX.items()if r.get('graphs')and q+'\\'in d and d.startswith('base\\open_world')]
  for d in local:load(d)
  outcomes=[];calls=[]
  short=q.replace('sts_bls_','')
  for d in local:
   for gp,gr in M[d]['graphs'].items():
    for ni,node in gr['nodes'].items():
     for w in node['writes']:
      if w['factName'].startswith(short)and ('finished'in w['factName']or'failed'in w['factName']):outcomes.append({'depot':d,'graph':gp,'node':ni,'write':w,'incoming':[e for e in gr['edges']if e[2]==ni]})
     if d.endswith('.scene')and'holocall'in d:
      for w in node['writes']:
       if w['factName']not in ['holo_dakota_calls_v_start_activate','holo_dakota_calls_v_end_activate']or w['value']!=1:continue
       done=w['factName'][:-9]+'_done';seeds=gr['entries'].values();reachable=any(path(gr,a,ni)for a in seeds)
       waits=[i for i,x in gr['nodes'].items()if any(z.get('factName')==done for z in x['reads'])and any(path(gr,a,i)for a in seeds)];clear=[i for i,x in gr['nodes'].items()if any(z.get('factName')==done and z.get('value')==0 for z in x['writes'])and any(path(gr,wa,i)for wa in waits)]
       ck('actual_native_caller_protocol '+q+gp+ni,reachable and bool(waits)and bool(clear),{'scene':d,'producer':ni,'request':w['factName'],'waits':waits,'clears':clear,'limit':'retry ACK may be prearmed by native parallel fork; not a direct request→wait assertion'})
       calls.append({'scene':d,'producer':ni,'request':w['factName'],'waits':waits,'clears':clear})
  ck('native_terminal_outcome_writers '+q,bool(outcomes)and all(x['incoming']for x in outcomes),outcomes)
  cp=H.parent/group/'quests'/q/'contracts.json';claim=read(cp);ck('peer_retains_limits '+q,not claim.get('fully_static_verified',False)and any(x['status']in ['OPAQUE','CONDITIONAL','UNKNOWN']for x in claim['contracts'].values()),{'contracts':str(cp),'sha256':sha(cp)})
  cases.append({'quest_id':q,'main':native,'native_root_prefabs':load(native)['root_prefabs'],'terminal_outcomes':outcomes,'caller_protocols':calls,'claim_pin':{'path':str(cp),'sha256':sha(cp)}})
 write(O,{'reviewer':'worker_B','method':'Independent current raw/native donor pins and Resource normalization; original selected payload/edge checks, actual owned Dakota listener/reset/real acknowledgements, native local terminal writers and scene protocols. No G09/G10 verifier imported or run.','status':'NO_NEW_SOURCE_DEFECT_FOUND_WITH_LIMITS','group':group,'checks':checks,'total_checks':len(checks),'source_pins':pins,'quest_cases':cases,'remaining':['Does not independently certify every source target definition, opaque streamed prefab/world/camera/workspot, save-persistent actor/credit owner or engine phone/reward behavior.','Native mappins may already be active; omitted admission targets require writer/lifecycle/history evidence and remain conditional in primary findings.','Native request/reset/ACK topology and MAY paths are static properties; no claim of gameplay success.'],'runtime_changes':[]})
 return {'checks':len(checks),'quests':len(quests),'sources':len(pins),'output':str(O)}
if __name__=='__main__':print(json.dumps({'G09':run('G09'),'G10':run('G10')}))

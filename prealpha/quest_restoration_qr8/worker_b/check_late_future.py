"""Actual-source QR8 prospective receipt/late completion regression.

Only private output writes; imports no builder, packer or root checker.
"""
from lib import *
import argparse,copy,csv,itertools

CASES=[('12',200,210,2,35,10,110),('08',201,211,37,45,38,115),('03',202,212,47,55,48,117),('01',203,213,57,65,58,119)]
def evaluate(c,f,j='Active'):
 if c['$type']=='questLogicalCondition':
  q=[evaluate(z,f,j)for z in c['conditions']]
  return all(q)if c['operation']=='AND'else any(q)if c['operation']=='OR'else (_ for _ in()).throw(ValueError('Unsupported operation'))
 if c['$type']=='questFactsDBCondition':
  t=c['type'];a=f.get(t['factName'],0);b=t['value'];return {'Equal':a==b,'GreaterOrEqual':a>=b,'Greater':a>b,'Less':a<b,'LessOrEqual':a<=b,'NotEqual':a!=b}[t['comparisonType']]
 if c['$type']=='questJournalCondition':return (j==c['type']['state'])!=bool(c['type'].get('inverted',0))
 raise ValueError('Non-fixtureable condition '+str(c))
def expected_after(before):
 after=copy.deepcopy(before)
 for code,gid,wait,*_ in CASES:
  c=after['graphs']['root/202']['nodes'][str(gid)]['payload']['condition'];old=c['conditions'][0]
  c['conditions'][0]={'$type':'questLogicalCondition','conditions':[old,{'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRQR7_RonaldNews_Armed_sts_ep1_'+code,'value':1}}],'operation':'OR'}
 return after
def comparison_errors(before,after):
 e=[];want=expected_after(before)
 # Payload hashes and aggregate resource hashes are derived fields, not semantic changes.
 def semantic(x):
  if isinstance(x,dict):return {k:semantic(v)for k,v in x.items()if k not in('payload_sha256','metadata_sha256','conditions','reads')}
  if isinstance(x,list):return [semantic(v)for v in x]
  return x
 # Do not strip actual condition payload fields: conditions/reads are dropped only on normalized nodes below.
 def prune(x):
  x=copy.deepcopy(x);x.pop('metadata_sha256',None)
  for g in x['graphs'].values():
   for n in g['nodes'].values():
    for k in('payload_sha256','reads','conditions'):n.pop(k,None)
  return x
 if prune(want)!=prune(after):e.append('not-exact-four-condition-delta')
 return e
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--proposal',default='proposal_late_future_03');a=ap.parse_args();out=H/a.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir();checks=[];mutants=[];fixtures=[]
 def ck(name,ok,**ev):checks.append({'name':name,'pass':bool(ok),**ev})
 pins=read(H/'readback_01/manifest.json')+read(H/'readback_03/manifest.json')+read(H/'readback_04/manifest.json')+read(H/'readback_05/manifest.json');m={}
 for p in pins:
  ck('source-pin:'+p['depot'],p['status']=='EXPORTED'and sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256']);m[p['depot']]=Resource(read(p['json'])).normalize()
 plan=read(H/a.proposal/'NOT_FOR_INTEGRATION.json');ck('proposed-serialized-readback-hashes',sha(plan['raw'])==plan['raw_sha256']and sha(plan['json'])==plan['json_sha256'])
 before=m[NEWS];doc=read(plan['json']);after=Resource(doc).normalize();g=before['graphs']['root/202'];ag=after['graphs']['root/202'];native=m[RN]['graphs']['root/11']
 ck('exact-four-gates-only-entire-normalized-resource',not comparison_errors(before,after),errors=comparison_errors(before,after))
 ck('root-once-claim-and-all-guard-identities-unchanged',before['graphs']['root']==after['graphs']['root'])
 ck('all-edges-sockets-saved-nodeIDs-and-private-prefabs-unchanged',all(gp in after['graphs']and bg['edges']==after['graphs'][gp]['edges']and set(bg['nodes'])==set(after['graphs'][gp]['nodes'])and all(n['sockets']==after['graphs'][gp]['nodes'][i]['sockets']and n['prefabs']==after['graphs'][gp]['nodes'][i]['prefabs']for i,n in bg['nodes'].items())for gp,bg in before['graphs'].items()))
 native_ids=set(map(str,read(W/'prealpha/quest_restoration_qr7/worker_b/future_protocol_spec_01.json')['kept_native_ids']))
 ck('all73-native-protocol-payloads-still-identical-to-QR7',len(native_ids)==73 and all(g['nodes'][i]==ag['nodes'][i]for i in native_ids))
 # The exact existing authored loading pause precedes each gate. Actual U9/native owners do not read it.
 ck('authored-loaded-hold-before-all-case-first-evaluations',g['nodes']['220']['payload']['condition']['$type']=='questLogicalCondition'and len(g['nodes']['220']['payload']['condition']['conditions'])==2 and all(c['$type']=='questNodeLoadingCondition'for c in g['nodes']['220']['payload']['condition']['conditions'])and ['0','Out','220','In']in g['edges'])
 rootguard=after['graphs']['root']['nodes']['200']['payload']['condition'];rootfacts={q['factName']:q['value']+(1 if q['comparisonType']=='Greater'else 0)for q in after['graphs']['root']['nodes']['200']['reads']if q.get('$type')=='questVarComparison_ConditionType'}
 ck('valid-existing-contact-root-fixture-is-admitted',evaluate(rootguard,rootfacts))
 ck('existing-issued-owner-cannot-reenter-root',not evaluate(rootguard,{**rootfacts,'PTFRQR7_RonaldNews_Issued':1}))
 for j in('Inactive','Failed','Succeeded'):
  ck('no-contact-history-adoption:'+j,not evaluate(rootguard,rootfacts,j))
 ck('native-enabled0-not-synthetic-enrollment',not evaluate(rootguard,{**rootfacts,'q302_ronald_messages_enabled':0}))
 producers=read(W/'prealpha/quest_restoration_qr7/worker_b/producer_readback_01/manifest.json')['producers'];ordering=[]
 for code,gid,wait,done,sent,pause,clock in CASES:
  q='sts_ep1_'+code;arm='PTFRQR7_RonaldNews_Armed_'+q;parent='PTFRU9_'+q+'_ParentEntered';depot='towercontinued\\native_gigs_u9\\'+q+'_entry.questphase';entry=m[depot];eg=entry['graphs']['root/50']
  ck(q+':only-arm-producer-dominates-ParentEntered',eg['nodes']['65007']['writes']==[{'$type':'questSetVar_NodeType','factName':arm,'setExactValue':1,'value':1}]and [e for e in eg['edges']if e[2]=='65007']==[['65002','Out','65007','In']]and [e for e in eg['edges']if e[2]=='65003']==[['65007','Out','65003','In']])
  guard=eg['nodes']['65002']['reads'];ck(q+':source-fresh-parent-native-start-finished-guards',all(any(x.get('factName')==f and x.get('comparisonType')=='Equal'and x.get('value')==0 for x in guard)for f in(parent,q+'_start',q+'_finished'))and any(x.get('factName')=='q307_ep1_killed'and x.get('value')==1 for x in guard))
  ck(q+':native-wait-follows-unchanged-future-arm-wait',[str(gid),'True',str(wait),'In']in g['edges']and ag['nodes'][str(wait)]==g['nodes'][str(wait)]and [e for e in g['edges']if e[2]==str(gid)]==[['220','Out',str(gid),'In']])
  p=next(p for p in producers if p['quest_id']==q);dm=m[p['depot']];dg=dm['graphs'][p['graph']];dn=dg['nodes'][p['node']]
  ck(q+':actual-source-done-writer-not-private-callback',dn['writes']==[{'$type':'questSetVar_NodeType','factName':q+'_done','setExactValue':1,'value':1}]and any(e[2]==p['node']for e in dg['edges']))
  parent_depot='ep1\\openworld\\street_stories\\'+q+'\\phases\\'+q+'_phase.questphase';pm=m[parent_depot]
  ck(q+':current-U9-actually-starts-native-parent',any(parent_depot in n['refs']for n in eg['nodes'].values()))
  ck(q+':native-parent-binds-real-completion-resource',parent_depot==p['depot']or any(p['depot']in n['refs']for graph in pm['graphs'].values()for n in graph['nodes'].values()),parent_depot=parent_depot,writer_depot=p['depot'])
  ck(q+':native-done-writer-is-graph-entry-reachable',p['node']in dg['reachable'])
  all_reads=[r.get('factName','')for model in(entry,dm,pm)for graph in model['graphs'].values()for n in graph['nodes'].values()for r in n['reads']]
  ck(q+':producer-independent-of-news-loading-and-receipts',not any('PTFRQR7_RonaldNews' in f or f.startswith('q302_msg_ronald')for f in all_reads))
  sf='q302_msg_ronald_'+q;writers=[(gp,i,w)for gp,graph in m[RN]['graphs'].items()for i,n in graph['nodes'].items()for w in n['writes']if w['factName']==sf]
  ck(q+':native-sent-one-only-no-reset-in-original-controller',writers==[('root/11',str(sent),{'$type':'questSetVar_NodeType','factName':sf,'setExactValue':1,'value':1})],writers=writers)
  ck(q+':sent-before-pause-before-exact2-game-day-timer',[str(sent),'Out',str(pause),'In']in native['edges']and [str(pause),'Out',str(clock),'In']in native['edges']and native['nodes'][str(clock)]['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':2,'hours':0,'minutes':0,'seconds':0}and native['nodes'][str(done)]['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':q+'_done','value':1}])
  old=g['nodes'][str(gid)]['payload']['condition'];new=ag['nodes'][str(gid)]['payload']['condition']
  for d,s,a1,p1 in itertools.product((0,1),(0,1),(0,1),(0,1)):
   f={q+'_done':d,sf:s,arm:a1,parent:p1};b=evaluate(old,f);v=evaluate(new,f);expected=(s==0 and (p1==0 or a1==1)and(d==0 or a1==1));ck(q+':history-fixture:'+str((d,s,a1,p1)),v==expected and (b==v or (d==1 and s==0 and a1==1)))
   fixtures.append({'quest_id':q,'done':d,'sent':s,'Armed':a1,'ParentEntered':p1,'before_gate':b,'after_gate':v,'native_done_wait':evaluate(native['nodes'][str(done)]['payload']['condition'],f),'meaning':'prospective-earned-completion-now-retained'if not b and v else'unchanged'})
  f={q+'_done':1,sf:0,arm:1,parent:1};ck(q+':FAIL-BEFORE-PASS-AFTER-exact-native-delay-route',not evaluate(old,f)and evaluate(new,f)and evaluate(native['nodes'][str(done)]['payload']['condition'],f))
  ordering.append({'quest_id':q,'source_hold':'helper root/202 input0→NodeLoading220 (both exact private triggers); no callback received yet','future_native_route':['entry root/50 65002 fresh prerequisites','65007 real private Armed1','65003 ParentEntered1','unchanged native job phases',{'depot':p['depot'],'graph':p['graph'],'done_writer':p['node'],'value':1}],'no_cross_dependency':True,'then':'Normal streaming callback satisfies220; first unchanged case gate evaluates done1/sent0/Armed1. Defective gate skips; proposal enters unchanged future-arm wait and native done listener, sent1 then native two-day timer.','proof_limit':'Static partial order of authored independent owners; actual streaming latency/save scheduling is LIVE_ONLY, not measured or forced.'})
 # Mutate actual resource condition documents and reject changed source guard/timing/protocol.
 def graph(rr):return rr.d(next(rr.d(n)for n in rr.d(rr.root['graph'])['nodes']if rr.d(n)['id']==202)['phaseGraph'])
 def node(rr,i):return next(rr.d(n)for n in graph(rr)['nodes']if rr.d(n)['id']==i)
 def armtype(rr):return rr.d(rr.d(rr.d(rr.d(node(rr,200)['condition'])['conditions'][0])['conditions'][1])['type'])
 for name,edit in [('drop-sent-history-guard',lambda rr:rr.d(node(rr,200)['condition'])['conditions'].pop(1)),('remove-earned-arm-gate',lambda rr:armtype(rr).__setitem__('value',0)),('clock-one-day',lambda rr:rr.d(rr.d(node(rr,110)['condition'])['type']).__setitem__('days',1))]:
  d=copy.deepcopy(doc);rr=Resource(d)
  try:edit(rr);err=comparison_errors(before,rr.normalize())
  except (KeyError,TypeError) as ex:
   # Keep malformed mutation coding errors visible; do not count them as detection.
   err=[];mutants.append({'fault':name,'detected':False,'mutation_error':repr(ex)});continue
  save(out/(name+'.json'),d);mutants.append({'fault':name,'detected':bool(err),'errors':err})
 for x in mutants:ck('actual-resource-negative-control:'+x['fault'],x['detected'])
 result={'status':'PASS_PRIVATE_PROPOSAL_PENDING_INDEPENDENT_REVIEW'if all(x['pass']for x in checks)else'FAIL','checks':checks,'check_count':len(checks),'fixtures':fixtures,'partial_orders':ordering,'mutations':mutants,'proposal_manifest':{'path':str(H/a.proposal/'NOT_FOR_INTEGRATION.json'),'sha256':sha(H/a.proposal/'NOT_FOR_INTEGRATION.json')},'source_pins':pins,'not_repaired':['Missing first enrollment menu routes/contact/bootstrap/native bar support.','Old Armed0 jobs, sent1 clocks, unknown native ownership, already-skipped/processed helper branches, existing HUD/notification history.','Actor/trigger streaming, engine save transition and real SMS receipt remain LIVE_ONLY.'],'runtime_writes':0,'new_namespaces':0,'production_integrated':False}
 save(out/'evidence.json',result);save(out/'checks.json',checks);save(out/'hash_observations.json',list(OBS.values()))
 with(out/'history_fixtures.csv').open('w',encoding='utf-8',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(fixtures[0]));w.writeheader();w.writerows(fixtures)
 print(result['status'],len(checks),'checks',len(fixtures),'cases',len(mutants),'mutants')
 if result['status']=='FAIL':raise SystemExit(1)
if __name__=='__main__':main()

"""Bounded actual CVI admission/callback history controls, no old-controller replay."""
from lib import *
from check_late_future import evaluate
import argparse,copy

NATIVE=['new_sts_pac_cvi_02_holocall_prebrief','new_sts_pac_cvi_02_holocall_debrief_failed','new_sts_pac_cvi_02_holocall_debrief_perfect','new_q110_prebrief_rejected_or_end','new_q110_debrief_failed_end','new_q110_debrief_perfect_end','new_q110_rejected_failed_out','new_q110_rejected_perfect_out']
PRIVATE=['PTFRQR7_CVI02_CustomControllerIssued','PTFRQR7_CVI02_PrebriefInFlight','PTFRQR7_CVI02_FailedInFlight','PTFRQR7_CVI02_PerfectInFlight']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=H/a.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir();checks=[];fixtures=[]
 def ck(name,v,**e):checks.append({'name':name,'pass':bool(v),**e})
 pin=next(p for p in read(H/'readback_03/manifest.json')if 'cvi_02_entry' in p['depot']);doc=read(pin['json']);model=Resource(doc).normalize();g=model['graphs']['root'];h=model['graphs']['root/65010'];guard=g['nodes']['65002']['payload']['condition'];facts={r['factName']:r['value']for r in g['nodes']['65002']['reads']};facts['ep1_installed']=1
 ck('canonical-CVI-source-fresh-readback-pin',sha(pin['raw'])==pin['raw_sha256']=='67EE759D9D431DAED4ADBB2BD443715AFF69833DB02F1136FF828E0FE3DEBCB9'and sha(pin['json'])==pin['json_sha256'])
 ck('valid-future-EP1-idle-fixture-admitted',evaluate(guard,facts))
 for name in NATIVE+PRIVATE+['PTFRU9_sts_pac_cvi_02_ParentEntered','cvi_02_start','cvi_02_finished','PTFRB7_pac_cvi_02_Started','PTFRB7_pac_cvi_02_RewardClaim','PTFRB7_pac_cvi_02_CounterClaim']:
  f={**facts,name:1};v=evaluate(guard,f);ck('old-or-owned-history-rejected:'+name,not v);fixtures.append({'field':name,'value':1,'new_controller_admitted':v,'policy':'No retrospective native request/outcome adoption; preserve original saved owner and history.'})
 ck('fresh-parent-admission-before-controller-install',['65002','Out','65003','In']in g['edges']and ['65003','Out','65007','In']in g['edges']and ['65007','True','65008','In']in g['edges']and ['65008','Out','65009','In']in g['edges'])
 ck('marker-loaded-before-original-owner-and-new-listener',['65009','Out','2','In1']in g['edges']and ['65009','Out','65010','In1']in g['edges']and g['nodes']['65009']['payload']['condition']['$type']=='questNodeLoadingCondition')
 ck('three-inflight-writes-only-from-real-request-listeners',all([str(l),'Out',str(w),'In']in h['edges']and [str(w),'Out','13',socket]in h['edges']for l,w,socket in[(16,22,'debrief_failed_in'),(17,21,'prebrief_in'),(18,23,'debrief_perfect_in')]))
 callbacks=[('prebrief_out',24),('prebrief_rejected_out',24),('debrief_failed_end_out',25),('debrief_rejected_failed_out',25),('debrief_perfect_end_out',26),('debrief_rejected_perfect_out',26)]
 ck('inflight-cleared-only-by-same-scene-real-terminal-callbacks',all([e for e in h['edges']if e[2]==str(w)]==sorted([['13',s,str(w),'In']for s,v in callbacks if v==w])for w in[24,25,26]))
 ck('interrupt-does-not-fabricate-terminal-inflight-ACK',['13','Holocall INT','8','In']in h['edges']and not any(e[0]=='8'and e[2]in('24','25','26')for e in h['edges']))
 ck('owner-cleanup-waits-all-real-inflight-receipts',g['nodes']['65011']['payload']['condition']['operation']=='AND'and [(x['factName'],x['value'])for x in g['nodes']['65011']['reads']]==[(f,0)for f in PRIVATE[1:]]and ['65011','Out','65012','In']in g['edges']and ['65012','CutSource','65010','CutDestination']in g['edges'])
 ck('only-new-helper-cut-original-owner-never-cut-by-new-control',[e for e in g['edges']if e[0]=='65012'and e[1]=='CutSource']==[['65012','CutSource','65010','CutDestination']])
 acknotes={i: {'reads':n['reads'],'writes':n['writes'],'outgoing':[e for e in h['edges']if e[0]==i]}for i,n in h['nodes'].items()if n['writes']}
 # Actual resource history mutant: remove the outcome guard and demonstrate a formerly held save starts.
 mutants=[]
 for target in[NATIVE[0],NATIVE[3]]:
  d=copy.deepcopy(doc);rr=Resource(d);root=rr.d(rr.root['graph']);node=next(rr.d(n)for n in root['nodes']if rr.d(n)['id']==65002)
  def remove(x):
   if isinstance(x,dict):
    resolved=rr.d(x)
    if resolved.get('$type')=='questLogicalCondition':
     cs=resolved['conditions'];resolved['conditions']=[z for z in cs if not any(q.get('factName')==target for q in walk(rr.clean(z)))or rr.d(z).get('$type')=='questLogicalCondition']
     for z in resolved['conditions']:remove(z)
  remove(node['condition']);mg=rr.normalize()['graphs']['root']['nodes']['65002']['payload']['condition'];v=evaluate(mg,{**facts,target:1});mutants.append({'fault':'remove-history-guard:'+target,'detected':v,'counterexample':'Old native request/outcome would now be admitted'});save(out/('missing_'+target+'.json'),d)
 for t in mutants:ck('actual-resource-mutant:'+t['fault'],t['detected'])
 result={'status':'PASS_FRESH_SCOPE_AND_HISTORY_DEFERRALS'if all(c['pass']for c in checks)else'FAIL','checks':checks,'check_count':len(checks),'history_fixtures':fixtures,'actual_resource_mutants':mutants,'source_pin':pin,'real_acknowledgements':acknotes,'scope':'Current EP1 future-idle controller remains conditionally supported; no change or promotion for historical entered/requested/acknowledged jobs.','live_only':['Engine listener registration ordering after65009 fanout','Actual scene acquisition/actor/render','Interrupt and reload restoration of active graph and phone queue','Native callback effect and real phone delivery'],'old_history_requirements':['Exact saved native owner/node/socket identity and active phone queue entry; absent from static source exports.','Exact native request/outcome path and actual remaining acknowledgement/cleanup owner.','No shared phone end-call or synthetic zero reset proves these states safe.'],'runtime_writes':0}
 save(out/'evidence.json',result);save(out/'hash_observations.json',list(OBS.values()));print(result['status'],len(checks),'assertions',len(mutants),'actual resource mutants')
 if result['status']=='FAIL':raise SystemExit(1)
if __name__=='__main__':main()

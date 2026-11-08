"""Independent source review of five G11 Dino gigs; no G11 code/models imported."""
from pathlib import Path
import sys,json,copy,argparse,re
W=Path(__file__).resolve().parents[5];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable
G11=H.parents[1]/'G11';MF=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');PLAN=read(W/'research/gig_restoration/native_gigs_u9/build_plan.json');EPOCH=read(H.parents[2]/'source_epoch_00.json');PKG=W/'prealpha/quest_restoration_qr3/candidate_01/package'
IDS=['sts_cct_cpz_01','sts_cct_dtn_05','sts_cct_dtn_03','sts_cct_dtn_04','sts_cct_dtn_02'];HC=r'base\quest\holocalls\dino\dino_holocall.questphase';HS=HC.replace('.questphase','.scene');SH=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
def run(O):
 assert not O.exists();tests=[];pins=[];M={};findings={}
 def check(name,ok,e):tests.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,name
 declared=read(G11/'verification_05/source_pins.json')
 for p in declared:
  d=p['depot'];check('actual binary pin '+d,sha(p['binary'])==p['resource_sha256'],p['binary']);check('raw JSON pin '+d,sha(p['json'])==p['json_sha256'],p['json']);M[d]=Resource(read(p['json'])).normalize();check('raw decoding '+d,not M[d]['errors'],M[d]['errors']);pins.append(p)
 check('exact U9 approved plan',sha(W/'research/gig_restoration/native_gigs_u9/build_plan.json')==MF['plan_sha256'],MF['plan_sha256'])
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def edge(d,e,gp='root'):return list(map(str,e)) in g(d,gp)['edges']
 def wr(d,i,f,v,gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,gp)['writes'])
 def rd(d,i,f,v=None,gp='root'):return any(x.get('factName')==f and (v is None or x.get('value')==v) for x in n(d,i,gp)['reads'])
 scriptrel='r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';script=PKG/scriptrel;pin=next(x for x in EPOCH['package_files'] if x['path']==scriptrel);check('current effective producer script',sha(script)==pin['sha256'],str(script));txt=script.read_text(encoding='utf8');cat=txt.split('public abstract class NativeGigDataU9 {',1)[1].split('public class NativeGigsU9',1)[0];ids=json.loads(re.search(r'func IDs\(\).*?return (\[.*?\]);',cat).group(1));producer=txt.split('public class NativeGigsU9 extends ScriptableSystem {',1)[1].split('public class NativeGigsTickU9',1)[0]
 for term in ['if this.State(paths[k],classes[k])!=1 { return false; }','if this.Fact(a[k])!=0 { return false; }','this.OldUnused(k) && this.EntrySafe(k)','this.Root(k)==1 && !this.Terminal(k)','return this.Request(id,"DISPOSABLE_SAVE",true);']:
  check('effective Request/EntrySafe/Poll '+term,term in producer,term)
 def data(method,i):
  block=re.search(r'func '+method+r'\(i: Int32\).*?(?=public static func|\Z)',cat,re.S).group(0);m=re.search(r'if i\s*==\s*'+str(i)+r'\s*\{\s*return (\[.*?\]);',block);return json.loads(m.group(1)) if m else []
 for q in IDS:
  er=next(r for r in MF['recipes'] if r.get('id')==q and r['kind']=='entry');d=er['depot'];donor='vanilla_recipe:'+er['raw'];ng=g(donor,er['graph']);body=next(i for i in er['ids'] if er['native'] in n(d,i)['refs']);comparisons=[]
  for i in er['ids']:
   if i==0:continue
   native=copy.deepcopy(ng['nodes'][str(i)]['payload'])
   if i==body and native.get('phaseResource',{}).get('Flags')=='Embedded':native['phaseResource']['Flags']='Soft'
   check('original retained parent payload '+q+':'+str(i),n(d,i)['payload']==native,dict(resource=d,node=i,native_binary=er['raw'],main_reference_flag='same depot Embedded→Soft' if i==body else None));comparisons.append(i)
  edits=next(x for x in PLAN['jobs'] if x['id']==q)['parent']['edits']
  for gp,gr in M[d]['graphs'].items():
   if gp=='root':continue
   base=copy.deepcopy(g(donor,gp))
   for e in edits:
    if e['graph']!=gp:continue
    base['edges'].remove(list(map(str,e['remove'])))
    if e.get('add'):base['edges'].append(list(map(str,e['add'])))
   base['edges'].sort();seen=reachable(base['nodes'],base['edges'],base['entries'].values());base['reachable']=sorted(seen);base['unreachable']=sorted(set(base['nodes'])-seen)
   check('copied exact inline graph plus pinned edits '+q+gp,base==gr,dict(resource=d,graph=gp,edits=edits))
  check('main actual native input binding '+q,edge(d,[65004,'Out',body,er['main_input']]) and er['main_input'] in g(er['native'])['entries'],dict(body=body,input=er['main_input'],native=er['native']))
  check('fact-only graph gate boundary '+q,not n(d,65002)['journal_paths'] and rd(d,65002,'PTFRU9_'+q+'_Permit',1),dict(resource=d,node=65002))
  cr=next(r for r in MF['recipes'] if r.get('id')==q and r['kind']=='credit');cd=cr['depot'];dg=g('vanilla_recipe:'+cr['raw'],cr['graph'])
  for i in cr['ids']:
   if i==0:continue
   check('original actual credit payload '+q+':'+str(i),n(cd,i)['payload']==dg['nodes'][str(i)]['payload'],dict(resource=cd,node=i,native_graph=cr['graph']))
  check('once-only district credit remains additive '+q,n(cd,10)['writes']==[{'$type':'questSetVar_NodeType','factName':'cct_sts_counter','setExactValue':0,'value':1}] and edge(cd,[10,'Out',65002,'In']) and all(rd(cd,65000,f,0) for f in ['PTFRU9_'+q+'_CreditEntered','PTFRU9_'+q+'_CreditDone']),dict(resource=cd,nodes=[65000,65001,10,65002]))
  ci=ids.index(q);paths=data('Paths',ci);facts=data('Facts',ci);actual=[];reward=[];writes=[]
  for nd,m in M.items():
   if not nd.startswith('base\\') or '\\'+q+'\\' not in nd:continue
   for gp,gr in m['graphs'].items():
    for i,nn in gr['nodes'].items():
     for p in nn['journal_paths']:
      if p.startswith('quests/') and q in p:actual.append(dict(resource=nd,graph=gp,node=i,path=p,classes=[value(x['className']) for x in walk(nn['payload']) if x.get('$type')=='gameJournalPath' and x.get('realPath')==p],incoming=[e for e in gr['edges'] if e[2]==i]))
     if nn['reward']:reward.append(dict(resource=nd,graph=gp,node=i,payload=nn['payload']))
     if nn['writes']:writes.append(dict(resource=nd,graph=gp,node=i,writes=nn['writes'],incoming=[e for e in gr['edges'] if e[2]==i]))
  gaps=[x for x in actual if x['path'] not in paths];findings[q]=dict(entry=d,native=er['native'],body=body,retained_nodes=comparisons,native_root=g(er['native']),root_prefabs=M[er['native']]['root_prefabs'],credit=cd,exact_credit_nodes=cr['ids'],catalogue_index=ci,catalogued_paths=paths,catalogued_facts=facts,uncatalogued_journal_references=gaps,rewards=reward,native_writers=writes,remaining=['Exact journal definitions/classes/history implications of noncatalogued references require target evidence; do not manufacture guards from MapPins or Inactive-only historical paths.','Original saved district/body/credit owners, native/retaliation/weapon-deposit consequences and live engine transitions remain explicit obligations.'])
 # Independent concrete regression classes reported by C, checked in original sources.
 cole=next(r for r in MF['recipes'] if r.get('id')=='sts_cct_dtn_05' and r['kind']=='entry')['depot'];pigs=next(r for r in MF['recipes'] if r.get('id')=='sts_cct_dtn_04' and r['kind']=='entry')['depot'];check('Cole only sibling-deactivation entry disconnected',not edge(cole,[0,'Out',6,'In'],'root/4') and '6' in g(cole,'root/4')['nodes'] and '7' in g(cole,'root/4')['nodes'] and edge(pigs,[0,'Out',6,'In'],'root/4'),dict(cole=cole,pigs=pigs,scope='Cole bypasses foreign GuineaPigs deactivation; actual GuineaPigs owner retains it'))
 cpzscene=next(d for d in M if '\\sts_cct_cpz_01\\' in d and d.endswith('_holocall_prebrief.scene'));check('SerialSuicide actual native end wait uses request not ack',edge(cpzscene,[65,'0:0',60,'0:1'],'scene') and rd(cpzscene,60,'holo_dino_calls_v_end_activate',0,'scene') and not rd(cpzscene,60,'holo_dino_calls_v_end_done',None,'scene'),dict(scene=cpzscene,writer=65,wait=60,payload=n(cpzscene,60,'scene')['payload'],classification='CONDITIONAL native protocol semantic discrepancy, not mod-introduced difference'))
 ck=findings['sts_cct_dtn_02']['credit'];check('InconvenientKiller native failure OR finish district credit',edge(ck,[4,'Out',6,'In1']) and edge(ck,[5,'Out',6,'In2']) and edge(ck,[6,'Out1',10,'In']) and rd(ck,4,'dtn_02_finished',0) and rd(ck,5,'dtn_02_failed',0),dict(resource=ck,nodes=[4,5,6,10],note='Native district credit includes failure; this does not award a duplicate quest payout'))
 check('Dino native queued listener preserved',all(edge(HC,e) for e in [(32,'Out',33,'In'),(33,'Out',35,'In'),(35,'Out',36,'In1'),(37,'Out',28,'In'),(28,'False',34,'In'),(34,'Out',0,'holo_dino_calls_v_start')]),dict(resource=HC,nodes=[32,33,35,36,37,28,34,0]))
 for suf,i in [('start',41),('end',42)]:check('Dino real acknowledgement '+suf,wr(HS,i,'holo_dino_calls_v_'+suf+'_done',1,'scene'),dict(scene=HS,node=i))
 check('Dino shared cleanup is actually called',edge(SH,[441,'True',307,'In15']) and edge(SH,[307,'Out15',462,'In']),dict(resource=SH,nodes=[441,307,462]))
 transport=[x for x in findings['sts_cct_dtn_04']['uncatalogued_journal_references'] if x['path'].endswith('/call_fixer_for_transportation')];check('GuineaPigs transport reference inactive-only in inspected closure',bool(transport) and all(e[3]=='Inactive' for row in transport for e in row['incoming']),transport)
 report=dict(status='APPROVE_G11_SCOPED_FINDINGS_NATIVE_PROTOCOL_AND_TARGET_GAPS_RETAINED',reviewer='qr4_worker_a',independent=True,checks=len(tests),tests=tests,source_pins=pins,effective_script=dict(path=str(script),sha256=sha(script)),not_imported=['G11/verify.py','G11/lib.py','G11 models or quest_evidence output'],quest_ids=IDS,quests=findings,ten_contract_review={q:{k:'Independent raw-source/native recipe/credit/current-producer review agrees with bounded conclusion; named unresolved inputs retained' for k in ['entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies']} for q in IDS},qualifications=['Serial Suicide original prebrief end wait actually checks request_activate, not the real end_done acknowledgement. Exact native parity is preserved; report it CONDITIONAL and do not silently convert this into a new mod repair.','Cole own entry preserves removal only of foreign GuineaPigs community deactivation; actual GuineaPigs retains its native branch. No broad rule to strip shared community/device dependencies.','MapPin references and obsolete Inactive-only transportation objective are exact native references outside current admission catalogue; complete definitions/history implication remain CONDITIONAL.','Native full body/credit scopes, target records, world/prefab placement, saved owners and actual delivery/reward/retaliation execution remain unverified; no full-static or gameplay certification.'],runtime_changes=[])
 write(O/'G11.json',report);return dict(status=report['status'],checks=len(tests),sources=len(pins))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(json.dumps(run(Path(a.output).resolve())))

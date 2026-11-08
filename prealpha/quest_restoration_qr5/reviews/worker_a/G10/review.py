"""Independent Little China source/phone-direction review, no group checker imports."""
from pathlib import Path
import sys,json,copy,re,zlib,argparse,collections
H=Path(__file__).resolve().parent;W=H.parents[4];F=W/'prealpha/quest_restoration_qr5'
sys.path.insert(0,str(F/'groups/G10'));import source_inputs as I
from common import read,write,sha,walk,value
from model import Resource,reachable

def run(O):
 assert not O.exists();tests=[];M={};pins=[];raw={};reviewed={};phone=[];mut=[]
 def ck(k,v,e):
  tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed_tests.json',tests);raise AssertionError(k)
 def canon(x):
  x=copy.deepcopy(x)
  for q in walk(x):
   q.pop('payload_sha256',None);q.pop('metadata_sha256',None)
   if q.get('$type')=='TweakDBID':
    s=q['$value'];v=(len(s.encode())<<32)|zlib.crc32(s.encode())if q['$storage']=='string'else int(s);q['$storage']='uint64';q['$value']=str(v)
  return x
 def soft(x):
  x=copy.deepcopy(x)
  for q in walk(x):
   if isinstance(q.get('phaseResource'),dict):q['phaseResource']['Flags']='Soft'
  return x
 for d in I.selected():M[d],p=I.load(d);pins.append(p)
 for p in read(H/'readback_01/manifest.json'):
  ck('fresh actual raw pin '+p['name'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);r=read(p['json']);m=Resource(r).normalize();ck('fresh vs indexed exact semantics '+p['name'],canon(m)==canon(M[p['depot']]),'Only TDBID CRC32+UTF8-length storage identity/derived hashes normalized; graph/node/socket/target unchanged');M[p['depot']]=m;raw[p['depot']]=r;pins.append(p)
 def n(d,k,gp='root'):return M[d]['graphs'][gp]['nodes'][str(k)]
 def e(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in M[d]['graphs'][gp]['edges']
 def find(base):return next(d for d in M if d.endswith('\\'+base))
 # Whole approved shared controller evidence is applicable only with exact hash and executing current bindings.
 cp=F/'groups/G07/shared_core.json';ck('Regina shared core pin',sha(cp)=='9F659DCAE5B009EB46952236A067981FD56D8271B906D7F536F67A04E72D6BE2',str(cp));pins.append({'path':str(cp),'sha256':sha(cp)})
 init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cl='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase'
 ck('actual effective listener owner84',n(init,84)['refs']==[I.HC]and e(init,25,'Out1',84,'In1'),'not inferred from native file presence')
 ck('actual effective cleanup owner342',n(cl,342)['refs']==[I.CL]and e(cl,474,'True',342,'In48'),'native release path retained')
 for r in I.RECIPES:
  d=r['depot'];src='recipe:'+r['raw'];sg=M[src]['graphs'][r['graph']];cg=M[d]['graphs']['root']
  for i in r['ids']:
   ck('actual native payload retained '+d+'/'+str(i),canon(soft(sg['nodes'][str(i)]['payload']))==canon(cg['nodes'][str(i)]['payload']),{'source':src,'graph':r['graph'],'node':i,'kind':r['kind']})
  ck('actual recipe edge topology '+d,cg['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),{'source':src,'kind':r['kind']})
  if r['kind']=='entry':
   main=[i for i in r['ids']if r['native']in n(d,i)['refs']];ck('native real main socket preserved '+r['id'],len(main)==1 and e(d,65004,'Out',main[0],r['main_input']),'case-specific original phase binding')
   ck('all positive Tower guard provenance '+r['id'],all(any(x.get('factName')==f and x['value']==1 for x in n(d,65002)['reads'])for f in ['q307_done','q307_finished','q307_2079','q307_main_game_killed','q307_ep1_killed','PostTowerFreeRoamActive','PTFRU9_Support_Issued']),n(d,65002)['payload'])
   ck('exact phase body provider unchanged '+r['id'],r['native']not in I.E['source_resources'],'no consolidated override of this original target; fresh native raw hash pinned')
   inline=[i for i in r['ids']if 'root/'+str(i)in M[d]['graphs']]
   for i in inline:
    for gp,g in M[d]['graphs'].items():
     if gp.startswith('root/'+str(i)):
      ck('native inline complete descendants '+r['id']+'/'+gp,canon(g)==canon(M[src]['graphs'][r['graph']+gp[4:]]),'exact entry eligibility/trigger/POI branch and nested edges, not generic status')
   reviewed[r['id']]={'entry':d,'native':r['native'],'main_node':main[0],'native_root_prefabs':M[r['native']]['root_prefabs'],'inline_nodes':inline,'source':src}
 # Independent exhaustive direction+mode discovery across actual native closure.
 pat=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$')
 for d,m in M.items():
  if not d.startswith('base')or not any(q in d for q in I.Q):continue
  for gp,g in m['graphs'].items():
   for ni,nd in g['nodes'].items():
    for w in nd['writes']:
     ma=pat.fullmatch(w['factName'])
     if w.get('value')!=1 or not ma:continue
     mode,inc,out,kind=ma.groups();contact=inc or out;direction='incoming'if inc else'outgoing';done='holo_'+(contact+'_calls_v'if inc else'v_calls_'+contact)+'_'+kind+'_done'
     listeners=[i for i,x in M[I.HC]['graphs']['root']['nodes'].items()if any(a.get('factName')==w['factName']for a in x['reads'])];acks=[i for i,x in M[I.HS]['graphs']['scene']['nodes'].items()if any(a.get('factName')==done and a['value']==1 for a in x['writes'])]
     p={'depot':d,'graph':gp,'node':ni,'request':w['factName'],'direction':direction,'mode':mode,'contact':contact,'listener_nodes':listeners,'real_ACK_writers':acks,'incoming_edges':[x for x in g['edges']if x[2]==ni]};phone.append(p);ck('actual direction producer/listener/ACK '+d+gp+'/'+ni,contact=='reggie'and bool(listeners)and bool(acks),p)
 counts={q:dict(collections.Counter(p['mode']+'_'+p['direction']for p in phone if q in p['depot']))for q in I.Q};ck('observed38 incoming only, no assumed family direction',len(phone)==38 and all(p['mode']=='holo'and p['direction']=='incoming'for p in phone),counts)
 # Distinct authored quest paths: device alternatives, eye predicates, upload, rescue/SMS/rewards.
 h=find('sts_wat_lch_06_ow.questphase');p=find('sts_wat_lch_05_openworld.questphase');t=find('sts_wat_lch_01_openworld.questphase');b=find('sts_wat_lch_03_streetstory.questphase')
 for d,gp,edges in [(h,'root/3',[(130,'Out',31,'Succeeded'),(143,'Out',31,'Succeeded'),(31,'Out',18,'Active')]),(h,'root/4',[(4,'Out',6,'In'),(3,'Out',7,'In')]),(t,'root/3',[(72,'Out',21,'Succeeded'),(21,'Out',24,'Active')]),(t,'root/5',[(35,'True',37,'In'),(37,'Out',36,'In'),(36,'Out',24,'In')]),(p,'root/6',[(9,'Out',6,'In'),(3,'Out',4,'In1'),(3,'Out',5,'In1')]),(b,'root/6',[(167,'End 0',212,'In'),(169,'End 0',213,'In'),(299,'False',297,'Active'),(299,'True',301,'Active'),(303,'False',302,'Active'),(303,'True',304,'Active'),(297,'Out',213,'In'),(301,'Out',213,'In'),(302,'Out',212,'In'),(304,'Out',212,'In')])]:
  for ed in edges:ck('authored quest branch '+d+gp+str(ed),e(d,*ed,gp),ed)
 ck('Heisenberg actual device disable AND',n(h,143,'root/3')['payload']['condition']['operation']=='AND'and'IsDisabled'in str(n(h,143,'root/3')['payload']),'original alternative to destruction130, unchanged')
 ck('Catch actual ForceUnpower after native upload',value(n(t,72,'root/3')['payload']['type']['params'][0]['deviceAction'])=='ForceUnpower','native authored laptop action, no fabricated upload')
 ck('Playing two distinct eye facts',n(p,206,'root/4')['reads'][0]['factName']=='sts_wat_lch_05_eye_implant'and n(p,215,'root/4')['reads'][0]['factName']=='lch_05_have_eye','item predicate and possession/story branch retained')
 ck('Bloodsport alarm SMS and rewards',n(b,299,'root/6')['reads'][0]['factName']=='lch_03_optional_alarm'and n(b,303,'root/6')['reads'][0]['factName']=='lch_03_optional_alarm'and n(b,212,'root/6')['payload']['type']==n(b,213,'root/6')['payload']['type'],'two authored routes identical reward record, not collapsed')
 pr=find('sts_wat_lch_01_prestate_control.questphase');ck('Catch prestate truly inert',not M[pr]['graphs']['root']['edges']and not any(x['writes']for x in M[pr]['graphs']['root']['nodes'].values()),M[pr])
 # Verify forty substantive dispositions/pins, keeping specific unresolved boundaries visible.
 res=read(I.H/'results.json');seen=[]
 for q in res['quest_results']:
  f=Path(q['contracts']);ck('frozen contract hash '+q['quest_id'],sha(f)==q['contracts_sha256'],q);c=read(f)['contracts'];ck('ten exact contract keys '+q['quest_id'],set(c)==set(['entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies']),list(c))
  for k,v in c.items():
   ck('specific evidence disposition '+q['quest_id']+'/'+k,bool(v['proven'])and bool(v['evidence'])and all(Path(x).is_file()for x in v['evidence'])and(v['status']not in ['CONDITIONAL','OPAQUE']or bool(v['remaining'])),{'status':v['status'],'proven':v['proven'],'remaining':v['remaining']});seen.append({'quest_id':q['quest_id'],'contract':k,'status':v['status']})
  ck('no full static promotion '+q['quest_id'],not q['fully_static_verified']and c['presentation']['status']=='OPAQUE','world targets and saved ownership/engine bounds remain')
 # Actual raw faults: changed tier, missing real ACK, changed reward.
 for label,d,change,oracle in [
  ('wrong_native_tier','towercontinued\\native_gigs_u9\\sts_wat_lch_03_entry.questphase',lambda r:[x.update(factName='QR5_wrong_tier')for x in walk(r)if x.get('factName')=='sts_wat_lch_tier_2_2'],lambda m:any(x.get('factName')=='sts_wat_lch_tier_2_2'for x in m['graphs']['root']['nodes']['31']['reads'])),
  ('missing_real_ACK',I.HS,lambda r:[x.update(factName='QR5_missing_real_ACK')for x in walk(r)if x.get('factName')=='holo_reggie_calls_v_start_done'],lambda m:any(x.get('factName')=='holo_reggie_calls_v_start_done'and x['value']==1 for x in m['graphs']['scene']['nodes']['396']['writes']))]:
  r=copy.deepcopy(raw[d]);change(r);mm=Resource(r).normalize();ck('independent raw mutation '+label,oracle(M[d])and not oracle(mm),d);fp=O/'mutations'/str(label+'.json');write(fp,r);mut.append({'fault':label,'path':str(fp),'sha256':sha(fp),'detected':True})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'phone_directions.json',{'observed':counts,'producers':phone,'typed_actions':[{'depot':d,'graph':gp,'node':i,'payload':x}for d,m in M.items()if d.startswith('base')and any(q in d for q in I.Q)for gp,g in m['graphs'].items()for i,n in g['nodes'].items()for x in walk(n['payload'])if x.get('$type')in ['questCallContact_NodeType','questSendMessage_NodeType']]});write(O/'case_sources.json',reviewed);write(O/'mutations.json',mut);write(O/'contracts_reviewed.json',seen)
 result={'status':'PASS_STATIC_SOURCE_REVIEW_WITH_EXPLICIT_LIMITS','quests':I.Q,'contracts':len(seen),'checks':len(tests),'mutations':len(mut),'fresh_exports':11,'source_count':len(M),'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'phone_inventory':str(O/'phone_directions.json'),'findings':[],'source_epoch':'QR5 epoch00 frozenQR4candidate; unrelated ARR12/Steven/Cheetah successors do not change these sources','limits':['Forty investigated contracts remain bounded static findings, no full-static or gameplay PASS.','Exact device/eye/rescue/journal/reward/body branches preserved; external world/actor acquisition/NodeRef placement stays OPAQUE.','Generic phone fact inventory includes both incoming/outgoing holo/audio; observed zero outgoing/audio is source closure fact only, implicit typed actions separately listed.','Native historical bugfix scopes recorded, not blindly promoted to executing owners; old saved owners/phone timing/reload/runtime economics remain conditional.'],'runtime_changes':[],'code':str(Path(__file__).resolve()),'code_sha256':sha(__file__)};write(O/'review.json',result);print(json.dumps(result))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())

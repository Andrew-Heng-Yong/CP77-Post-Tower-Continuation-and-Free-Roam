"""Independent raw handle/socket reviews of B and F; no verifier imports."""
from pathlib import Path
import json,copy,hashlib,sys
W=Path(__file__).resolve().parents[4];O=Path(__file__).resolve().parent/'reviews';O.mkdir(exist_ok=True)
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def val(x):return x.get('$value',x) if isinstance(x,dict) else x
class Raw:
 def __init__(self,p):
  self.p=Path(p);self.o=rd(p);self.hs={str(x['HandleId']):x['Data'] for x in walk(self.o) if 'HandleId'in x and 'Data'in x};self.gs={}
  self.visit(self.o['Data']['RootChunk'].get('graph'),'root')
 def d(self,x):
  if not isinstance(x,dict):return x
  if 'HandleId'in x:return x.get('Data')
  if 'HandleRefId'in x:return self.hs.get(str(x['HandleRefId']))
  return x
 def hid(self,x):return str(x.get('HandleId',x.get('HandleRefId')))
 def clean(self,x,seen=frozenset()):
  if isinstance(x,dict):
   if 'HandleId'in x or 'HandleRefId'in x:
    key=self.hid(x)
    return {'cycle':True} if key in seen else self.clean(self.d(x),seen|{key})
   return {k:self.clean(v,seen) for k,v in x.items() if k not in ['sockets','connections','phaseGraph','graph','sceneGraph','debugSymbols']}
  if isinstance(x,list):return [self.clean(v,seen) for v in x]
  return x
 def visit(self,h,gp):
  gr=self.d(h)
  if not isinstance(gr,dict) or 'nodes'not in gr:return
  ns={str(self.d(h)['id']):self.d(h) for h in gr['nodes']};ss={};es=set()
  for i,n in ns.items():
   for h in n.get('sockets',[]):
    s=self.d(h);ss[self.hid(h)]=(i,str(val(s.get('name',''))))
  for i,n in ns.items():
   for h in n.get('sockets',[]):
    for c in self.d(h).get('connections',[]):
     c=self.d(c);a=ss.get(self.hid(c['source']));b=ss.get(self.hid(c['destination']))
     if a and b:es.add((*a,*b))
  self.gs[gp]={'nodes':{i:self.clean(n) for i,n in ns.items()},'edges':es}
  for i,n in ns.items():self.visit(n.get('phaseGraph'),gp+'/'+i)
 def node(self,i,gp='root'):return self.gs[gp]['nodes'][str(i)]
 def edge(self,a,s,b,t,gp='root'):return (str(a),s,str(b),t) in self.gs[gp]['edges']
 def ref(self,i,gp='root'):
  return [str(val(x['DepotPath'])) for x in walk(self.node(i,gp)) if 'DepotPath'in x and str(val(x['DepotPath'])) not in ['0','None']]
def save(name,obj):
 p=O/name;assert not p.exists();p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
def review_b():
 base=W/'prealpha/quest_restoration_qr3';B=base/'agents/agent_b';pins=rd(B/'verification_01/source_pins.json');ms={};checks=[]
 def ck(n,b,e):checks.append({'name':n,'status':'PASS' if b else 'FAIL','evidence':e});assert b,n
 for p in pins:
  ck('binary pin '+p['depot'],sh(p['binary'])==p['sha256'],p['binary']);ck('JSON pin '+p['depot'],sh(p['source_json'])==p.get('json_sha256',p.get('source_json_sha256')),p['source_json']);ms[p['depot']]=Raw(p['source_json'])
 parent=r'base\open_world\minor_activities\badlands\inland_avenue_se1\ma_bls_ina_se1_minor_activities.questphase'
 for num,pn in [('46',141),('47',145)]:
  P=r'towercontinued\sidejobs_s23\ep1\mq0'+num+'_boot.questphase';a=ms[P]
  ck('native district body binding mq0'+num,a.node(pn,'root/100')==ms[parent].node(pn),{'native_parent':parent,'node':pn})
  ck('actual private owner activation mq0'+num,all(a.edge(*e) for e in [(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'True',4,'In'),(4,'Out',89,'In'),(89,'Out',90,'In'),(90,'True',92,'In'),(92,'Out',100,'In1')]),P)
  ck('native seven tick delay mq0'+num,all(a.edge(*e,'root/100') for e in [(0,'Out',173,'In'),(173,'Out',pn,'In1')]) and any(x.get('$type')=='questTickDelay_ConditionType' and x.get('tickCount')==7 for x in walk(a.node(173,'root/100'))),P)
  ck('native already-owned-car NOR mq0'+num,any(x.get('$type')=='questLogicalCondition' and x.get('operation')=='NOR' and any(y.get('$type')=='questVehicleAvailable_ConditionType' for y in walk(x)) for x in walk(a.node(3))),P)
  for guard in [2,3,90]:ck('explicit inactive journal root mq0'+num+str(guard),any(x.get('$type')=='questJournalEntryState_ConditionType' and x.get('path',{}).get('realPath')=='quests/minor_quest/mq0'+num+('_cave_vehicle' if num=='46' else '_ad_vehicle') and x.get('state')=='Inactive' for x in walk(a.node(guard))),P)
 fresh=rd(base/'native_owner_gap_resolution.json');ck('fresh owner chain status',fresh['status'].startswith('PASS_CURRENT_NATIVE_ANCESTOR'),str(base/'native_owner_gap_resolution.json'))
 fm={}
 for d,r in fresh['fresh_inputs'].items():
  ck('fresh native ancestor raw '+d,sh(r['raw'])==r['sha256'],r['raw']);fm[d]=Raw(r['json'])
 for step in fresh['chain']:
  d=step['parent'];m=fm.get(d)
  if m:ck('current ancestor contains '+step['child'],step['child'] in m.ref(step['node'],step['graph']),step)
 ck('stale historical parent evidence explicitly superseded',len(fresh['historical_source_corrections'])==2 and all(x['historical_hash_mismatch'] for x in fresh['historical_source_corrections']),fresh['historical_source_corrections'])
 for q in ['mq046_cave_vehicle','mq047_ad_vehicle']:
  f=rd(B/'quests'/q/'contracts.json');ck('full contract no blanket certification '+q,len(f['contracts'])==10 and not f['fully_static_verified'],q)
  ck('target data and saved-state bounds retained '+q,f['contracts']['completion_rewards_cleanup']['status']=='CONDITIONAL' and f['contracts']['ownership']['status']=='CONDITIONAL',q)
 save('vehicles.json',{'status':'PASS_INDEPENDENT_RAW_REVIEW_WITH_ANCESTRY_TEXT_UPDATE','reviewer':'agent_e','quest_ids':['mq046_cave_vehicle','mq047_ad_vehicle'],'checks':checks,'input_pins':pins,'fresh_owner_resolution_sha256':sh(base/'native_owner_gap_resolution.json'),'issues':[{'id':'REVIEW-B-ANCESTRY','finding':'Initial B contracts still say top native ancestry is unavailable. Fresh coordinator exports now prove that structural chain, while two historical global parents are stale.','resolution':'Use current native_owner_gap_resolution.json as authority for authored containment; retain saved executing-owner/runtime cancellation limitations. No gameplay repair implied.'}],'runtime_defects_confirmed':0,'runtime_changes':[],'boundary':'Independent raw socket/handle parser, not import/execution of B verify.py; no rendered vehicle/entitlement/gameplay claim.'})
 print('vehicles',len(checks))
def review_f():
 F=W/'prealpha/quest_restoration_qr3/agents/agent_f';pins=rd(F/'verification_02/source_pins.json');ms={};checks=[]
 def ck(n,b,e):checks.append({'name':n,'status':'PASS' if b else 'FAIL','evidence':e});assert b,n
 for p in pins:
  ck('binary pin '+p['depot'],sh(p['binary'])==p['sha256'],p['binary']);ck('JSON pin '+p['depot'],sh(p['source_json'])==p.get('json_sha256',p.get('source_json_sha256')),p['source_json']);ms[p['depot']]=Raw(p['source_json'])
 N=r'base\quest\minor_quests\mq025\mq025_psycho_brawl.questphase';P=r'towercontinued\sidejobs_s22\mq025_progress.questphase';FRESH=r'towercontinued\sidejobs_s25\families\mq025_fresh.questphase';PAC=r'base\quest\minor_quests\mq025\phases\mq025_06_pacifica.questphase'
 raw=ms[N];prog=ms[P];fresh=ms[FRESH]
 for i in [3,5,7,9]:ck('native required fight into AND '+str(i),any(e[0]==str(i) and e[2]=='10' for e in raw.gs['root']['edges']),i)
 ck('native finale AND output',raw.edge(10,'Out1',11,'In1'),N)
 ck('native Pacifica optional cleanup joined',any(e[0]=='8' and e[1]=='Cleanup' and e[2]=='25' for e in raw.gs['root']['edges']) and any(e[0]=='11' and e[2]=='25' for e in raw.gs['root']['edges']),N)
 keep=set(raw.gs['root']['nodes'])-{'17','46','68','69','70'}
 ck('fresh dispatcher retained raw native nodes',all(fresh.node(i,'root/100')==raw.node(i) for i in keep),{'nodes':len(keep)})
 ck('fresh dispatcher retained native sockets and edges',all(e in fresh.gs['root/100']['edges'] for e in raw.gs['root']['edges'] if e[0] in keep and e[2] in keep),N)
 ck('fresh actual entry reaches dispatcher',fresh.edge(93,'Out',100,'In1'),FRESH)
 ck('progress actual postclaim entry reaches native hub',prog.edge(1009,'True',55,'In1'),P)
 for d,m,gids in [(P,prog,[1001,1002]),(FRESH,fresh,[2,3])]:
  for i in gids:
   cond=m.node(i)['condition'];entries=[x for x in walk(cond) if x.get('$type')=='questJournalEntryState_ConditionType' and x.get('path',{}).get('realPath')=='quests/minor_quest/mq025_psycho_brawl']
   ck('primary boxing root strictly Inactive '+d+str(i),entries and all(x['state']=='Inactive' for x in entries),entries)
  cross='PTFRS25_MQ025_FRESH_Issued' if d==P else 'PTFRS22_MQ025_Issued'
  ck('cross owner receipt excluded '+d,any(x.get('factName')==cross and x.get('value')==0 for x in walk(m.node(gids[-1])['condition'])),cross)
 pac=ms[PAC]
 ck('Pacifica earned Ozob completion retained',any(x.get('factName')=='mq035_done' and x.get('comparisonType')=='Greater' and x.get('value')==0 for x in walk(raw.node(24))),N)
 ck('Pacifica actual timer and token path',raw.edge(24,'Out',33,'In') and raw.edge(33,'False',31,'In') and raw.edge(31,'Out',32,'In') and raw.edge(32,'Out',8,'In1'),{'native':N,'test_flag_branch':raw.node(33)})
 for a,s,b,t in [(46,'True',56,'Active'),(46,'False',55,'Active'),(43,'True',57,'Active'),(43,'False',58,'Active')]:ck('Pacifica native SMS branch '+str(a)+s,pac.edge(a,s,b,t),PAC)
 for q in ['mq025_06_pacifica','mq025_psycho_brawl']:
  f=rd(F/'quests'/q/'contracts.json');ck('boxing unresolved historical seam retained '+q,f['contracts']['eligibility']['status']=='CONDITIONAL' and f['contracts']['journal']['status']=='CONDITIONAL',q)
  ck('boxing reward target boundary retained '+q,f['contracts']['completion_rewards_cleanup']['status']=='CONDITIONAL',q)
 save('boxing.json',{'status':'PASS_INDEPENDENT_RAW_BOXING_REVIEW','reviewer':'agent_e','quest_ids':['mq025_06_pacifica','mq025_psycho_brawl'],'checks':checks,'input_pins':pins,'issues':[],'runtime_defects_confirmed':0,'runtime_changes':[],'remaining':'Allowed Failed child-objective provenance, saved executing-owner adoption, TweakDB wager/reward definitions and world/voice presentation remain correctly conditional/opaque. Agreement is not used to promote any full quest to PASS.','method':'Independent raw phase handles/socket traversal; no import/execution of F verify.py'})
 print('boxing',len(checks))
if __name__=='__main__':
 if len(sys.argv)==1:review_b();review_f()
 elif sys.argv[1]=='b':review_b()
 elif sys.argv[1]=='f':review_f()
 else:raise ValueError('Use b or f')

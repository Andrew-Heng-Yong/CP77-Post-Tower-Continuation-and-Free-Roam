"""Independent A-group review, using own fresh raw re-exports and own assertions.

Does not import the investigation worker, its verifier, or B's verifier.
"""
from pathlib import Path
import sys,json,hashlib,copy,re,zlib,argparse,collections
W=Path(__file__).resolve().parents[4];sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
S28ALIASES={r'towercontinued\sidejobs_s28\vehicles\mq029_tourist.questphase':r'base\quest\minor_quests\mq029\mq029_tourist.questphase',r'towercontinued\sidejobs_s28\vehicles\mq029_garage.questphase':r'base\quest\minor_quests\mq029\phases\mq029_garage.questphase',r'towercontinued\sidejobs_s28\vehicles\mq029_josie_corpse.questphase':r'base\quest\minor_quests\mq029\phases\mq029_josie_corpse.questphase',r'towercontinued\sidejobs_s28\vehicles\mq029_01a_garage.scene':r'base\quest\minor_quests\mq029\scenes\mq029_01a_garage.scene',r'towercontinued\sidejobs_s28\vehicles\mq029_01b_josie_body.scene':r'base\quest\minor_quests\mq029\scenes\mq029_01b_josie_body.scene'}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def val(x):return x.get('$value',x)if isinstance(x,dict)else x
def canon(x):
 if isinstance(x,dict):
  if x.get('$type')=='TweakDBID':
   s=str(val(x));return {'$type':'TweakDBID','hash':s if s.isdigit()else str((len(s.encode())<<32)|zlib.crc32(s.encode()))}
  return{k:canon(v)for k,v in x.items()if k!='payload_sha256'}
 if isinstance(x,list):return[canon(v)for v in x]
 if isinstance(x,str)and x.startswith('towercontinued')and '\\native\\'in x:return x.split('\\native\\',1)[1]
 return S28ALIASES.get(x,x)if isinstance(x,str)else x
def run(group,verification='verification_01'):
 H=W/'prealpha/quest_restoration_qr6/groups/B01/reviews'/group;O=H/verification;assert not O.exists();O.mkdir();(O/'mutations').mkdir();R=read(H/'raw_exports_01/manifest.json');raw={};M={};T=[];issues=[];evidence={};E=read(W/'prealpha/quest_restoration_qr5/source_epoch_08.json')
 def ck(k,b,e):
  T.append({'name':k,'pass':bool(b),'evidence':e})
  if not b:save(O/'failed_tests.json',T);raise AssertionError(k)
 for r in R:
  ck('independent raw/JSON byte pins '+r['depot'],r['status']=='EXPORTED'and sha(r['raw'])==r['raw_sha256']and sha(r['json'])==r['json_sha256'],r)
  if r['status']!='EXPORTED':continue
  raw[r['depot']]=read(r['json']);M[r['depot']]=Resource(raw[r['depot']]).normalize();ck('independent handles/edges '+r['depot'],not M[r['depot']]['errors'],M[r['depot']]['errors'])
  if r['depot'].startswith('towercontinued'):ck('effective canonical payload '+r['depot'],r['raw_sha256']==E['source_resources'][r['depot']],E['source_resources'][r['depot']])
 inp=read(H/'reviewed_input.json');res=read(inp['results']);ck('reviewed frozen group manifest',sha(inp['results'])==inp['results_sha256'],inp)
 for p in inp['contract_pins']:ck('frozen contract '+p['path'],sha(p['path'])==p['sha256'],p['sha256'])
 for r in res['quest_results']:
  c=read(r['contracts']);ck('all ten dispositions source specific '+r['quest_id'],len(c['contracts'])==10 and all(v.get('proven')and v.get('evidence')and v['status']in ['PASS','CONDITIONAL','APPROVED_DEVIATION','OPAQUE','UNKNOWN','FAIL','LIVE_ONLY']for v in c['contracts'].values()),list(c['contracts']))
  ck('no fullstatic/gameplay claim '+r['quest_id'],c['fully_static_verified']is False and not c.get('runtime_changes'),r['contracts'])
  for stage,v in c['contracts'].items():ck('all contract links resolve '+r['quest_id']+':'+stage,all(Path(p).is_file()for p in v['evidence']),v['evidence'])
 # Independently compare the effects/topology of every available native/private pair.
 pairs=[]
 for d,m in M.items():
  if not d.startswith('towercontinued'):continue
  donor=d.split('\\native\\',1)[1]if '\\native\\'in d else S28ALIASES.get(d)
  if donor not in M:continue
  a=M[donor];b=m;pair={'native':donor,'restored':d,'graphs':[]}
  for gp,g in b['graphs'].items():
   if gp not in a['graphs']:pair['graphs'].append({'graph':gp,'new_private_graph':True});continue
   ag=a['graphs'][gp];original=set(ag['nodes']);current=set(g['nodes']);common=original&current
   stout_slice=d.endswith('q003_stout.questphase')and gp=='root'
   if stout_slice:
    selected={'146'};todo=['146']
    while todo:
     x=todo.pop()
     for aa,ss,bb,tt in ag['edges']:
      if aa==x and bb not in selected:selected.add(bb);todo.append(bb)
    ck('Stout exact native-derived58-node farewell slice',len(selected)==58 and current==selected|{'65000'},sorted(selected))
   else:ck('original node IDs retained '+d+':'+gp,not(original-current),sorted(original-current))
   ck('native side-effect and journal predicates retained '+d+':'+gp,all(canon(ag['nodes'][i]['writes'])==canon(g['nodes'][i]['writes'])and ag['nodes'][i]['journal_paths']==g['nodes'][i]['journal_paths']for i in common),sorted(common))
   ed=set(map(tuple,g['edges']))^set(map(tuple,ag['edges']));new=current-original
   allowed={
    ('mq040_biosculpt.questphase','root'):({('0','Out','3','In1'),('0','Out','65000','In'),('65000','False','3','In1'),('65000','True','4','In1')},{'65000'}),
    ('mq040_biosculpt.questphase','root/3'):({('11','Out','2','In'),('11','Out','64000','In'),('64000','Out','2','In')},{'64000'}),
    ('mq016_bartmoss.questphase','root'):({('6','Out','3','In1'),('6','Out','64000','In'),('64000','Out','64001','In'),('64001','Out','3','In1')},{'64000','64001'})}
   special=next((v for(k,gp0),v in allowed.items()if d.endswith(k)and gp==gp0),None)
   if stout_slice:
    expect=[e for e in ag['edges']if e[0]in selected and e[2]in selected]+[['65000','Out','146','In']]
    ck('Stout native-derived edge slice plus exact new input',set(map(tuple,g['edges']))==set(map(tuple,expect)),expect)
   else:ck('exact original graph topology or named inherited handoff '+d+':'+gp,(ed,new)==special if special else not ed and not new,{'edge_difference':sorted(ed),'added_ids':sorted(new)})
   if d.endswith('.scene'):
    ck('native scene entries exact '+d,ag['entries']==g['entries'],ag['entries'])
    # Dialogue events/timing survive, except independently authorized SC1 Johnny14 removal.
    changed=[]
    for i in common:
     ae=[x for x in walk(ag['nodes'][i]['payload'])if x.get('$type')=='scnDialogLineEvent'];be=[x for x in walk(g['nodes'][i]['payload'])if x.get('$type')=='scnDialogLineEvent']
     if ae!=be:changed.append({'node':i,'native':ae,'restored':be})
    ck('dialogue events identical except exact SC1 finale',not changed or group=='A02'and'mq006'in d,{'changed_nodes':[v['node']for v in changed]})
    pair['dialogue_changes']=changed
   else:
    # Native root prefab plus every nested instance prefab are separate contracts.
    ck('root/nested prefab obligations '+d+':'+gp,a['root_prefabs']==b['root_prefabs']and all(ag['nodes'][i]['prefabs']==g['nodes'][i]['prefabs']for i in common),{'root':a['root_prefabs']})
    ck('native eligibility leaf semantics '+d+':'+gp,all(canon(ag['nodes'][i]['reads'])==canon(g['nodes'][i]['reads'])for i in common),gp)
   pair['graphs'].append({'graph':gp,'native_ids':sorted(original),'current_ids':sorted(current),'edge_difference':sorted(ed)})
  pairs.append(pair)
 if group=='A02':
  removed=[];added=[];altered=[]
  for pair in pairs:
   if 'mq006'not in pair['restored']or not pair['restored'].endswith('.scene'):continue
   a=M[pair['native']];b=M[pair['restored']];lines={str(x['itemId']['id']):x for x in walk(a.get('metadata',{}))if x.get('$type')=='scnscreenplayDialogLine'}
   for gp,g in a['graphs'].items():
    for i,n in g['nodes'].items():
     ae={str(x['id']['id']):x for x in walk(n['payload'])if x.get('$type')=='scnDialogLineEvent'};be={str(x['id']['id']):x for x in walk(b['graphs'][gp]['nodes'][i]['payload'])if x.get('$type')=='scnDialogLineEvent'}
     for e in set(ae)-set(be):
      ev=ae[e];line=lines[str(ev['screenplayLineId']['id'])];removed.append({'source':pair['native'],'node':i,'event':e,'speaker':line['speaker']['id']})
     added.extend(set(be)-set(ae));altered.extend(e for e in set(ae)&set(be)if ae[e]!=be[e])
  ck('SC1 exactly14Johnny actor5 lines removed; all others unchanged',len(removed)==14 and all(x['speaker']==5 for x in removed)and not added and not altered,removed)
 def nd(d,i,g='root'):return M[d]['graphs'][g]['nodes'][str(i)]
 def edge(d,a,s,b,t,g='root'):return[str(a),s,str(b),t]in M[d]['graphs'][g]['edges']
 controls=[]
 def fixed(k,d,i,fn,g='root'):
  ck(k,fn(nd(d,i,g)),{'depot':d,'graph':g,'node':i,'payload':nd(d,i,g)['payload']});controls.append((k,d,str(i),g,fn))
 if group=='A01':
  for ident,fact in [('mq040_biosculpt','mq040_active'),('mq028_stalker','mq028_started'),('mq018_writer','mq018_started')]:
   d='towercontinued\\sidejobs_s29\\entries\\'+ident+'.questphase'
   for i in [65003,65004]:fixed('fresh guard refuses existing '+fact+':'+str(i),d,i,lambda n,f=fact:any(x.get('factName')==f and x['comparisonType']=='Equal'and x['value']==0 for x in n['reads']))
  d=r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq040\mq040_biosculpt.questphase'
  fixed('Raymond retained historical active1 branch separate from admission',d,65000,lambda n:any(x.get('factName')=='mq040_active'and x['value']==1 for x in n['reads']))
  fixed('Raymond actual service handoff waits source lease0',d,64000,lambda n:any(x.get('factName')=='PTFRB0STPEPE_OwnerActive'and x['value']==0 for x in n['reads']),'root/3')
  d=r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq028\mq028.questphase'
  for e in [(0,'Out',5,'In'),(5,'Out',9,'main_in'),(9,'main_out',6,'In')]:ck('BlueMoon started-before-active lifecycle '+str(e),edge(d,*e),e)
  p=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
  for e in [(1253,'True',1206,'In'),(1206,'True',1207,'In10'),(1254,'True',1208,'In'),(1208,'True',1209,'In44'),(1252,'True',1204,'In'),(1204,'True',1205,'In3'),(1251,'True',1202,'In'),(1202,'True',1203,'In39')]:ck('actual specialized effective cleanup '+str(e),edge(p,*e),e)
  for contact,i in [('cynthia',49),('pepe',81),('blue_moon',36),('nancy',76)]:
   d='towercontinued\\sidejobs_s29\\phone\\'+contact+'.questphase';ck('specialized listener after durable issue '+contact,edge(d,1003,'True',1004,'In')and edge(d,1004,'Out',i,'In1'),d)
 elif group=='A02':
  d=r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq016\mq016_bartmoss.questphase'
  fixed('Nix late service release waits0',d,64001,lambda n:any(x.get('factName')=='PTFRB0S4NIX_OwnerActive'and x['value']==0 for x in n['reads']))
  for e in [(6,'Out',64000,'In'),(64000,'Out',64001,'In'),(64001,'Out',3,'In1')]:ck('actual Nix late handoff '+str(e),edge(d,*e),e)
  d=r'towercontinued\sidejobs_s30\entries\mq006_rollercoaster.questphase'
  for i in [65003,65004]:fixed('CC1 deliberate postDoubleLife story exclusion0:'+str(i),d,i,lambda n:any(x.get('factName')=='q105_done'and x['comparisonType']=='Equal'and x['value']==0 for x in n['reads']))
  ck('JC1 story lease brackets actual body output',edge(d,65005,'Out',65008,'In')and edge(d,65008,'Out',65006,'In')and edge(d,20,'Out1',65009,'In')and edge(d,65009,'Out',65007,'In'),M[d]['graphs']['root']['edges'])
  d=r'towercontinued\sidejobs_s28\vehicles\mq029_tourist_entry.questphase'
  if d not in M:d=next(d for d in M if d.startswith('towercontinued')and'mq029_tourist'in d and ('entry'in d or'entries'in d))
  fixed('Highwayman untouched fresh claim receipt',d,5,lambda n:n['writes'][0]['factName'].endswith('_Issued')and n['writes'][0]['value']==1)
 elif group=='A03':
  d=r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq017\mq017_streetkid.questphase'
  fixed('StreetKid typed native lifepath',d,9,lambda n:any(x.get('$type')=='LifePath_ScriptConditionType'and canon(x['lifePathId'])['hash']==str((len('LifePaths.StreetKid'.encode())<<32)|zlib.crc32('LifePaths.StreetKid'.encode()))for x in walk(n['payload'])))
  d=r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq036\mq036_overload.questphase'
  fixed('SweetDreams earned actual market prerequisite',d,11,lambda n:n['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'sq012_market_done','value':0}])
  d=next(d for d in M if d.startswith('towercontinued')and d.endswith('q003_stout.questphase'))
  fixed('Stout real consent entry AND',d,146,lambda n:n['payload']['condition']['operation']=='AND')
  ck('Stout selected body has no fake native output',not any(n['type']=='questOutputNodeDefinition'for g in M[d]['graphs'].values()for n in g['nodes'].values()),d)
  scene=next(p for p in nd(d,111)['refs']if p.endswith('.scene'))
  g=M[scene]['graphs']['scene'];seen={'2197'};todo=['2197']
  while todo:
   x=todo.pop()
   for aa,ss,bb,tt in g['edges']:
    if aa==x and bb not in seen:seen.add(bb);todo.append(bb)
  ck('actual Stout farewell excludes Meredith3300','3300'not in seen and len(seen)>1,{'scene':scene,'entry':'2197','reachable':sorted(seen)})
 # Three independent raw mutation sentinels per group, on actual current document leaves.
 mutations=[]
 for k,d,i,g,fn in controls:
  if len(mutations)==3:break
  mu=copy.deepcopy(raw[d]);node=next(x for x in walk(mu)if x.get('$type')==nd(d,i,g)['type']and str(x.get('id'))==i);old=copy.deepcopy(node)
  # Mutate a real selected scalar prerequisite (or typed lifepath), not the checker.
  if 'lifepath'in k:
   for x in walk(node):
    if x.get('$type')=='TweakDBID':x['$value']='0'
  elif 'consent entry AND'in k:
   for x in walk(node):
    if x.get('$type')=='questLogicalCondition':x['operation']='OR';break
  else:
   names={x.get('factName')for x in nd(d,i,g)['reads']if'factName'in x}
   # Change every compared scalar in this node; caller invariant must reject.
   for x in walk(node):
    if x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')in names:x['value']=int(x['value'])+1
  if node==old:continue
  mm=Resource(mu).normalize();detected=not fn(mm['graphs'][g]['nodes'][i]);ck('independent raw mutation rejects '+k,detected,{'depot':d,'graph':g,'node':i});p=O/'mutations'/str(str(len(mutations))+'.json');save(p,mu);mutations.append({'name':k,'source':next(r['json']for r in R if r['depot']==d),'path':str(p),'sha256':sha(p),'detected':detected,'scope':'Raw readback-document mutation, no binary/engine execution'})
 ck('three actual source mutation controls',len(mutations)==3,mutations)
 save(O/'fresh_source_pins.json',R);save(O/'pair_comparisons.json',pairs);save(O/'tests.json',{'count':len(T),'checks':T,'mutations':mutations});report={'group':group,'status':'INDEPENDENT_SOURCE_REVIEW_PASS_WITH_RETAINED_CONDITIONAL_OPAQUE_LIMITS','reviewer':'QR6 worker B, separate from worker A','reviewed_group_results':inp['results'],'reviewed_group_sha256':inp['results_sha256'],'quest_ids':res['quest_ids'],'contract_count':len(res['quest_ids'])*10,'checks':len(T),'failures':0,'issues':issues,'fresh_readbacks':len(R),'raw_document_mutations':len(mutations),'source_pins':str((O/'fresh_source_pins.json').resolve()),'source_pins_sha256':sha(O/'fresh_source_pins.json'),'tests':str((O/'tests.json').resolve()),'tests_sha256':sha(O/'tests.json'),'pair_comparisons':str((O/'pair_comparisons.json').resolve()),'scope':['Own fresh WolvenKit exports from pinned native and current binaries; independent expected predicates/edges and per-contract evidence link review.','Source effect/topology/read/prefab comparison and named inherited adapter review; actor/world placements and actual engine scheduling remain opaque/live.','No author checker imported; no runtime/resource/deployment/save/fact writes.','Assertions are verification events, not unique gameplay coverage.']};save(O/'review.json',report);print(json.dumps({'group':group,'checks':len(T),'fresh':len(R),'mutations':len(mutations),'review_sha256':sha(O/'review.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('group');p.add_argument('--verification',default='verification_01');a=p.parse_args();run(a.group,a.verification)

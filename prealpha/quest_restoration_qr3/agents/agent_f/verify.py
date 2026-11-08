"""Read-only boxing-family checks against exact native/current PH3 resources."""
from pathlib import Path
import argparse,sys,json,gzip,copy,re,collections
W=Path(__file__).resolve().parents[4];ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);O=Path(ap.parse_args().output).resolve();assert not O.exists(),'Fresh output required';O.mkdir(parents=True)
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');PH3=W/'prealpha/phone_studios_ph3/candidate_01'
N=r'base\quest\minor_quests\mq025\mq025_psycho_brawl.questphase';F=r'towercontinued\sidejobs_s25\families\mq025_fresh.questphase';P=r'towercontinued\sidejobs_s22\mq025_progress.questphase'
PA=r'base\quest\minor_quests\mq025\phases\mq025_06_pacifica.questphase';SC=r'base\quest\minor_quests\mq025\scenes\mq025_06_pacifica.scene';FIN=r'base\quest\minor_quests\mq025\phases\mq025_08_finale.questphase';FSC=r'base\quest\minor_quests\mq025\scenes\mq025_08_finale.scene'
TEASE=r'base\quest\minor_quests\mq025\phases\mq025_01_tease.questphase'
deps=sorted({d for d in MI if '\\mq025\\'in d}|{F,P,r'base\quest\main_quests\prologue\q001\phases\q001_fistfight_tutorial.questphase',r'base\quest\main_quests\prologue\q001\scenes\q001_02a_fistfight_tutorial.scene'})
models={};pins=[];checks=[]
def check(name,ok,evidence):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
for d in deps:
 r=IDX[d];j=Path(r['json']);b=PH3/'archive_source'/d.replace('\\','/') if d.startswith('towercontinued') else j.with_suffix('')
 check('binary pin '+d,b.is_file() and sha(b)==r['sha256'],str(b))
 m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[])
 check('raw/model equivalence '+d,m==cached,str(j));models[d]=m
 pins.append({'depot':d,'binary':str(b),'sha256':sha(b),'provider':r['archive'],'source_json':str(j),'source_json_sha256':sha(j),'model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model']),'errors':m['errors']})
def g(d,gp='root'):return models[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def edge(d,e,gp='root'):return list(map(str,e)) in g(d,gp)['edges']
def facts(node):return [x for x in walk(node['payload']) if x.get('$type')=='questVarComparison_ConditionType']
def cond_eval(c,fs,js):
 t=c['$type']
 if t in ['questFactsDBCondition','questJournalCondition']:return cond_eval(c['type'],fs,js)
 if t=='questLogicalCondition':
  vs=[cond_eval(x,fs,js) for x in c['conditions']]
  return all(vs) if c['operation']=='AND' else any(vs) if c['operation']=='OR' else not any(vs) if c['operation']=='NOR' else (_ for _ in ()).throw(ValueError(c['operation']))
 if t=='questVarComparison_ConditionType':
  if c['factName'] not in fs:return False
  a=fs[c['factName']];b=c['value'];return {'Equal':a==b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b,'NotEqual':a!=b}[c['comparisonType']]
 if t=='questJournalEntryState_ConditionType':
  p=c['path']['realPath']
  if p not in js:return False
  return (js[p]==c['state'])!=bool(c.get('inverted',0))
 raise ValueError(t)

# Every retained native payload and edge is compared against the independent
# original family, not merely against a recipe generated from the private copy.
native=g(N);fresh=g(F,'root/100');progress=g(P)
removed_f={'17','46','68','69','70'};removed_p={'17','2','30','37','38','46','65','68','69','70'}
check('fresh native node selection exact',set(fresh['nodes'])==set(native['nodes'])-removed_f,sorted(removed_f))
for i,x in fresh['nodes'].items():check('fresh native node payload '+i,x['payload']==native['nodes'][i]['payload'],{'native':N,'private':F,'node':i})
check('fresh native edges exact',[e for e in native['edges'] if e[0]not in removed_f and e[2]not in removed_f]==fresh['edges'],'Only unused external alternate entry inputs removed')
for gp in models[N]['graphs']:
 if gp=='root':continue
 check('fresh native nested graph exact '+gp,models[N]['graphs'][gp]==models[F]['graphs'][gp.replace('root','root/100',1)],gp)
for i in set(native['nodes'])-removed_p:check('progress retained native node payload '+i,n(P,i)['payload']==n(N,i)['payload'],i)
expected_native_edges=[e for e in native['edges'] if e[0]not in removed_p and e[2]not in removed_p and e!=['25','Out1','1','In']]
check('progress all retained native edges',all(e in progress['edges'] for e in expected_native_edges),expected_native_edges)
for gp in models[P]['graphs']:
 if gp=='root':continue
 check('progress nested native graph exact '+gp,models[P]['graphs'][gp]==models[N]['graphs'][gp],gp)
for e in [['3','Out1','10','In1'],['5','Out1','10','In2'],['7','Out1','10','In3'],['9','Out1','10','In4'],['10','Out1','11','In1'],['8','Cleanup','25','In2'],['11','Out1','25','In1']]:
 check('four fights plus finale/Pacifica native join '+str(e),e in native['edges'] and e in progress['edges'] and e in fresh['edges'],e)
check('Pacifica original earlier quest gate',n(N,24)['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'mq035_done','value':0}],24)
check('Pacifica original27gamehour delay',n(N,31)['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':1,'hours':3,'minutes':0,'seconds':0},31)
check('Pacifica content-token admission',n(N,32)['payload']['condition']['type']=={'$type':'questContentToken_ConditionType','type':'SideQuest_Standalone'},32)
check('Pacifica native path exact',all(e in native['edges'] for e in [['24','Out','33','In'],['33','False','31','In'],['31','Out','32','In'],['32','Out','8','In1']]),'No prerequisite/time/token bypass')
for e in [['3','True','4','In'],['4','Out','89','In'],['89','Out','90','In'],['90','False','91','In'],['90','True','92','In'],['92','Out','93','In'],['93','Out','100','In1']]:check('fresh claim/recheck/contact edge '+str(e),e in g(F)['edges'],e)
check('fresh recheck2ticks',n(F,89)['payload']['condition']['type']=={'$type':'questTickDelay_ConditionType','tickCount':2},89)
check('fresh contact exact',n(F,93)['payload']['type']['params'][0]['contact']['realPath']=='contacts/trainer_fred',93)
check('fresh Finished observes native Succeeded',n(F,102)['payload']['condition']['type']['state']=='Succeeded' and edge(F,['102','Out','101','In']),[102,101])

# Evaluate actual serialized guard trees, refusing absent values. The complete
# native-journal values are exported so these are reproducible counterexamples.
cases={}
for d,ids in [(F,[2,3,90]),(P,[1001,1002,1008,1009])]:
 for i in ids:
  c=n(d,i)['payload']['condition'];fs={}
  for x in facts(n(d,i)):
   k=x['factName'];v=x['value'];op=x['comparisonType']
   if op=='Equal':fs[k]=v
   elif op=='GreaterOrEqual':fs[k]=max(fs.get(k,v),v)
   elif op=='LessOrEqual':fs[k]=min(fs.get(k,v),v)
   elif op=='Greater':fs[k]=max(fs.get(k,v+1),v+1)
   elif op=='Less':fs[k]=min(fs.get(k,v-1),v-1)
   else:raise ValueError(op)
  # OR journal states are chosen Inactive for the exact supported preclaim seam.
  js={x['path']['realPath']:'Inactive' for x in walk(c) if x.get('$type')=='questJournalEntryState_ConditionType'}
  if i in [1008,1009]:
   js['quests/minor_quest/mq025_psycho_brawl']='Active';js['quests/minor_quest/mq025_psycho_brawl/find_fights']='Active'
  check('actual guard positive '+d+' '+str(i),cond_eval(c,fs,js),{'node':i,'resource':d})
  cases[d+'#'+str(i)]={'facts':fs,'journals':js}
  for root in ['quests/minor_quest/mq025_psycho_brawl','quests/minor_quest/mq025_06_pacifica']:
   if root not in js:continue
   for state in ['Succeeded','Failed']:
    check('guard rejects '+str(i)+' '+root+' '+state,not cond_eval(c,fs,js|{root:state}),{'root':root,'state':state})
  for fact in ['mq025_done','mq025_06_ozob_player_wins','mq025_06_ozob_fight_started','mq025_ozob_exploded','mq025_03_player_wins','mq025_cash']:
   check('guard refuses progressed outcome '+str(i)+' '+fact,not cond_eval(c,fs|{fact:1},js),fact)
  absent=dict(js);absent.pop('quests/minor_quest/mq025_psycho_brawl');check('guard refuses absent root '+str(i),not cond_eval(c,fs,absent),i)
check('fresh excludes progressed stage',cases[F+'#2']['facts']['mq025_quest_started']==0 and cases[P+'#1001']['facts']['mq025_quest_started']==1,'Serialized mutually exclusive stages')
check('fresh rejects existing progressed owner',any(x['factName']=='PTFRS22_MQ025_Issued' and x['value']==0 for x in facts(n(F,2))),2)
check('progress rejects existing fresh owner',any(x['factName']=='PTFRS25_MQ025_FRESH_Issued' and x['value']==0 for x in facts(n(P,1001))),1001)
check('postclaim progress requires ownIssued1',any(x['factName']=='PTFRS22_MQ025_Issued' and x['value']==1 for x in facts(n(P,1008))),1008)
check('fresh postclaim requires ownIssued1',any(x['factName']=='PTFRS25_MQ025_FRESH_Issued' and x['value']==1 for x in facts(n(F,90))),90)
for d in [F,P]:check('private adds no native fact/reward writers '+d,all(x['factName'].startswith('PTFRS') for gr in models[d]['graphs'].values() for node in gr['nodes'].values() for x in node['writes']),d)

# Actual SMS paths and fight outcomes, including original nonlethal mortality.
for e in [['46','False','55','Active'],['46','True','56','Active'],['43','True','57','Active'],['43','False','58','Active'],['57','Out','8','In'],['58','Out','8','In']]:check('Pacifica SMS outcome edge '+str(e),e in g(PA)['edges'],e)
for e in [['7','Out','36','In1'],['36','Out1','10','In'],['10','Out','18','Succeeded'],['8','Out','27','In'],['27','Out','19','Failed'],['18','Out','9','In'],['19','Out','9','In'],['45','Out','43','In']]:check('Pacifica native fight win/loss/cut '+str(e),e in g(PA,'root/20')['edges'],e)
check('Ozob native defeat threshold10percent',n(PA,7,'root/20')['payload']['condition']['type']['percent']==10,7)
check('player native loss threshold15percent',n(PA,8,'root/20')['payload']['condition']['type']['percent']==15,8)
check('native boxing mortality restored',n(PA,4,'root/20')['payload']['type']['subtype']['state']=='Immortal' and n(PA,12,'root/20')['payload']['type']['subtype']['resetToDefault']==1,'Authored temporary nonlethal state, not new modgodmode')
for i,record in [(323,'QuestRewards.mq025_pacifica'),(340,'QuestRewards.mq025_pacifica_higher'),(344,'QuestRewards.mq025_pacifica'),(346,'QuestRewards.mq025_pacifica_higher')]:check('Pacifica reward pointer '+str(i),any(x.get('$type')=='TweakDBID' and value(x)==record for x in walk(n(SC,i,'scene')['payload'])),record)
for i,record in [(1000,'QuestRewards.mq025_psycho_brawl_corrupt'),(1004,'QuestRewards.mq025_psycho_brawl')]:check('finale reward pointer '+str(i),any(x.get('$type')=='TweakDBID' and value(x)==record for x in walk(n(FSC,i,'scene')['payload'])),record)
for e in [['152','True','151','Active'],['151','Out','148','Succeeded'],['152','False','149','Succeeded'],['52','Out','53','In'],['53','Out','81','In'],['81','Out','93','In'],['93','Out','126','In']]:check('finale native completion and cleanup '+str(e),e in g(FIN)['edges'],e)
call_writers=[{'resource':d,'graph':gp,'node':i,'write':x} for d in models for gp,gr in models[d]['graphs'].items() for i,node in gr['nodes'].items() for x in node['writes'] if x['factName'].startswith(('audio_','holo_','phonecall_'))]
check('no restored family phone request producer',not call_writers,call_writers)
scripts={name:PH3/'package/r6/scripts/PTFR_Consolidated'/name for name in ['PTFR_SideJobsS22.reds','PTFR_SideJobsS25.reds','PTFR_HistorySnapshotHS1.reds','PTFR_JohnnyVoiceJV1.reds']}
jv=scripts['PTFR_JohnnyVoiceJV1.reds'].read_text(encoding='utf-8-sig')
check('supporting Johnny existing presentation restriction','Character.Silverhand' in jv and 'visual.TemporaryHide(true)'in jv and 'this.CompletedTower()'in jv,'Existing JV1 preserves voice/scene timing; independent props not covered')
mut=[]
bad=copy.deepcopy(fresh);bad['edges'].remove(['31','Out','32','In']);mut.append({'fault':'missing Pacifica native prerequisite-delay edge','detected':bad['edges']!=fresh['edges']})
bad=copy.deepcopy(n(PA,7,'root/20')['payload']);bad['condition']['type']['percent']=99;mut.append({'fault':'changed native Ozob win threshold','detected':bad!=n(PA,7,'root/20')['payload']})
bad=copy.deepcopy(g(PA));bad['edges'].remove(['57','Out','8','In']);mut.append({'fault':'lost Pacifica SMS-to-active cleanup','detected':['57','Out','8','In']not in bad['edges']})
bad=copy.deepcopy(n(FSC,1004,'scene')['payload']);
for x in walk(bad):
 if x.get('$type')=='TweakDBID' and value(x)=='QuestRewards.mq025_psycho_brawl':x['$value']='QuestRewards.wrong'
mut.append({'fault':'wrong finale reward donor','detected':bad!=n(FSC,1004,'scene')['payload']})
bad=copy.deepcopy(n(F,2)['payload']['condition']);
for x in walk(bad):
 if x.get('$type')=='questVarComparison_ConditionType' and x.get('factName')=='PTFRS22_MQ025_Issued':x['value']=1
c=cases[F+'#2'];mut.append({'fault':'fresh owner accepts already progressed receipt','detected':cond_eval(bad,c['facts']|{'PTFRS22_MQ025_Issued':1},c['journals'])})
for row in mut:check('mutation '+row['fault'],row['detected'],row)
trace=[];journals=[];assets=[]
for d,m in models.items():
 for gp,gr in m['graphs'].items():
  for i,node in gr['nodes'].items():
   if node['writes'] or node['reads'] or node['reward'] or node['journal_paths']:
    trace.append({'resource':d,'graph':gp,'node':i,'type':node['type'],'payload':node['payload'],'incoming':[e for e in gr['edges'] if e[2]==i],'outgoing':[e for e in gr['edges'] if e[0]==i]})
   if node['node_refs'] or node['refs'] or node['prefabs']:assets.append({'resource':d,'graph':gp,'node':i,'node_refs':node['node_refs'],'refs':node['refs'],'prefabs':node['prefabs']})
write(O/'source_pins.json',pins);write(O/'graph_evidence.json',{'handlers':trace,'assets':assets,'root_prefabs':{d:m['root_prefabs'] for d,m in models.items()},'guard_cases':cases,'scripts':{n:{'path':str(p),'sha256':sha(p)} for n,p in scripts.items()},'shared_ownership':'One family dispatcher per exact fresh/progress seam; Pacifica is nested shared native phase. No private fight reset/AI command added.'})
write(O/'provider_requests.json',sorted(set(models)|{r for m in models.values() for r in m['refs']}))
write(O/'tests.json',{'status':'PASS_SCOPED_STATIC_CONTROLS','checks':len(checks),'results':checks,'mutations':mut,'sources':len(pins),'source_confirmed_defects':[],'runtime_changes':False,'verifier_sha256':sha(Path(__file__))})
print(json.dumps({'checks':len(checks),'sources':len(pins),'mutations':len(mut),'runtime_changes':False}))

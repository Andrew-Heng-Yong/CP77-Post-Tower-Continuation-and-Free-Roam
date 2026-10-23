"""Independent packed-readback graph/policy/Lua checks, not engine playtests."""
import binascii,copy,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'research/phase2b_p0/tooling/python')]
from native_inspect import SafeResource,flatten
from catalog_gig_rollout_r2 import read,sha,walk,value
from lupa.luajit21 import LuaRuntime

def gs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def ns(g):return {n['id']:n for n in g['nodes']}
def es(g):return {tuple(e) for e in g['edges']}
def evaluate(c,f,j):
 if c['$type']=='questLogicalCondition':
  v=[evaluate(x,f,j) for x in c['conditions']];return all(v) if c['operation']=='AND' else any(v)
 t=c['type']
 if c['$type']=='questJournalCondition':return j.get(t['path']['realPath'],'UNKNOWN')==t['state']
 a=f.get(t['factName'],0);b=t['value'];return {'Equal':a==b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b}[t['comparisonType']]
def outer(g,tag):
 n=ns(g['root']);assert set(n)==set(range(6))
 assert es(g['root'])=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(4,'Out',5,value(ns(g['root/5'])[min(ns(g['root/5']))]['socketName']))}
 assert n[2]['condition']==n[3]['condition']
 for i,s in [(1,'_Ready'),(4,'_Issued')]:assert n[i]['type']=={'$type':'questSetVar_NodeType','factName':tag+s,'setExactValue':1,'value':1}
 return n[2]['condition']
def verify(build):
 m=read(build/'build.json');cat={x['key']:x for x in read(ROOT/'research/cyberpsycho_p1/catalog_v1.json')['rows']}
 assert len(m['files'])==4 and len(m['resources'])==len(m['boots'])==20 and len(m['activities'])==17
 assert not m['official_overrides'] and m['packed_readback'] and m['native_scenes_unchanged'] and m['runtime_scripts_added']==0
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 for p,h in m['resources'].items():assert sha(build/'source'/p)==h,p
 for f in m['files']:assert sha(build/Path(f['relative']).name)==f['sha256']
 exact=neg=0;allgs={}
 for row in m['activities']:
  key=row['key'];s=cat[key];p=gs(ROOT/s['parent']);n=ns(p['root']);g=gs(build/f'readback/{key}.json');allgs[key]=g
  child=ns(g['root/5']);ids=set(s['selected_nodes']);tag='PTFRP1_'+key
  for i in ids:assert child[i]==n[i],(key,i);exact+=1
  for name,sub in p.items():
   if name!='root' and int(name.split('/')[1]) in ids:
    assert ns(g['root/5'+name[4:]])==ns(sub) and es(g['root/5'+name[4:]])==es(sub);exact+=len(sub['nodes'])
  ad=tuple(s['admission_edges'][0]);want={e for e in es(p['root']) if e[0] in ids and e[2] in ids}-{ad}
  want|={(ad[0],ad[1],1000,'In'),(1000,'False',1002,'In'),(1000,'True',1001,'Active'),(1001,'Out',1003,'In'),(1003,'Out',ad[2],ad[3])}
  if s['extra_parent_gate']:
   old={e for e in want if e[0]==s['input']};want-=old;want.add((s['input'],'Out',1010,'In'));want|={(1010,'Out',e[2],e[3]) for e in old}
   bg=gs(ROOT/'research/ncpd_scanner_n1/parents_02/json/base/open_world/minor_activities/badlands/badlands_minor_activities.questphase.json');b=copy.deepcopy(ns(bg['root'])[9]);b['id']=1010;assert child[1010]==b
  assert es(g['root/5'])==want,(key,'native-edge preservation')
  guard=m['common']|{tag+'_Issued':0}|{f:0 for f in s['start_facts']+s['finish_facts'] if f!='ow_psychos_done'}
  assert row['guard_equal']==guard and 'ow_psychos_done' not in guard
  c=outer(g,tag);j={row['quest']:'Inactive'}
  assert evaluate(c,guard|{'ow_psychos_done':16},j)
  for count in [-1,17,18,99]:assert not evaluate(c,guard|{'ow_psychos_done':count},j);neg+=1
  for k,v in guard.items():assert not evaluate(c,guard|{k:1-v},j),(key,k);neg+=1
  for state in ['UNKNOWN','Active','Succeeded','Failed']:assert not evaluate(c,guard,{row['quest']:state});neg+=1
  assert evaluate(child[1000]['condition'],guard|{tag+'_Issued':1},j)
  assert not evaluate(child[1000]['condition'],guard|{tag+'_Issued':1,s['start_facts'][0]:1},j)
  assert not any(e[0]==1002 for e in want)
  added=[child[i] for i in set(child)-ids]
  assert [x['type']['factName'] for x in added if x['$type']=='questFactsDBManagerNodeDefinition']==[tag+'_Refused',tag+'_Entered']
  assert child[1001]['type']['path']['realPath']==row['poi'] and child[1001]['type']['path']['fileEntryIndex']==1
 report=gs(build/'readback/report.json');original=gs(ROOT/(m['report_source'].replace('/raw/','/json/')+'.json'));n=ns(report['root/5']);old=ns(original['root'])
 for i,p in old.items():assert n[i]==p;exact+=1
 want={e for e in es(original['root']) if e[0]!=0 and not(e[0]==112 and 27<=e[2]<=59) and e[0]!=113}
 want|={(0,'Out',1000,'In'),(1000,'True',63,'In'),(0,'Out',111,'In'),(113,'Out',1040,'In'),(1040,'True',84,'In1'),(1040,'False',9,'In')}
 for i in range(1,18):
  a=1010+i;want|={(112,'Out1',a,'In'),(a,'True',25+2*i,'In')}
  for current in range(18):assert evaluate(n[a]['condition'],{'ow_psychos_done':current},{})==(current<i)
 assert es(report['root/5'])==want
 assert n[24]['condition']['type']['hours']==12
 rc=outer(report,'PTFRP1_Report');mq='quests/minor_quest/mq043_cyberpsychos'
 normal=m['common']|{'PTFRP1_Report_Issued':0,'mq043_done':0,'ow_psychos_reward_collected':0}
 for count in range(18):assert evaluate(rc,normal|{'ow_psychos_done':count},{mq:'Active'})
 for f in ['mq043_done','ow_psychos_reward_collected','PTFRP1_Report_Issued']:assert not evaluate(rc,normal|{f:1},{mq:'Active'})
 assert not evaluate(rc,normal,{mq:'Succeeded'})
 bug=gs(ROOT/(m['reward_source'].replace('/raw/','/json/')+'.json'));reward=gs(build/'readback/reward.json')
 outer(reward,'PTFRP1_Reward')
 for prefix in ['root/7','root/8']:
  for name,sub in bug.items():
   if name==prefix or name.startswith(prefix+'/'):assert ns(reward['root/5'+name[4:]])==ns(sub) and es(reward['root/5'+name[4:]])==es(sub);exact+=len(sub['nodes'])
 assert set(ns(reward['root/5']))=={0,7,8} and es(reward['root/5'])=={(0,'Out',7,'In1'),(0,'Out',8,'In1')}
 test=gs(build/'readback/test_only.json');tc=outer(test,'PTFRP1_Test');tn=ns(test['root/5']);te=es(test['root/5'])
 assert evaluate(tc,m['test_guard'],{mq:'Succeeded','quests/minor_quest/ma_wat_kab_08':'Succeeded'})
 for k,v in m['test_guard'].items():assert not evaluate(tc,m['test_guard']|{k:1-v},{mq:'Succeeded','quests/minor_quest/ma_wat_kab_08':'Succeeded'});neg+=1
 assert len(te)==len(tn)-1 and all(len([e for e in te if e[0]==i])<=1 for i in tn),'Test must be linear and one-use'
 seen={0};cur=0
 while any(e[0]==cur for e in te):cur=next(e[2] for e in te if e[0]==cur);assert cur not in seen;seen.add(cur)
 assert seen==set(tn)
 writes={x['type']['factName']:x['type']['value'] for x in tn.values() if x['$type']=='questFactsDBManagerNodeDefinition'}
 assert writes=={'ma_kab_08_start':0,'ma_kab_08_finished':0,'ma_wat_kab_08_psycho_combat_started':0,'mq043_done':0,'ow_psychos_reward_collected':0,'ow_psychos_killed':0,'ow_psychos_done':16,'PTFRP1_TestResetDone':1,'PTFRP1_TestPreparing':0,'PTFRP1_TestCrateReady':1}
 items=[n for n in tn.values() if n['$type']=='questItemManagerNodeDefinition']
 assert len(items)==2
 for n in items:
  b=copy.deepcopy(ns(bug['root/13'])[8 if n['type']['$type']=='questAddRemoveItem_NodeType' else 6]);b['id']=n['id'];assert n==b
 for n in tn.values():
  if n['$type']=='questSpawnManagerNodeDefinition':
   # WolvenKit's Respawn enum is an alias of Reactivate (both native value 3).
   for a in n['actions']:assert a['type']['action'] in ['Reactivate','ResetKillCount'] and value(a['type']['spawnerReference']) in ['#ma_wat_kab_08_com_psycho','#ma_wat_kab_08_com_civ']
 # New helper has no auto callbacks; test guards fail before any mutation.
 source=(build/'init.lua').read_text();assert 'registerForEvent' not in source and 'onUpdate' not in source and 'print(' not in source
 def runtime():
  l=LuaRuntime(unpack_returned_tuples=True);l.execute('''
   facts={};writes={};visits=0;missing=false;badstate=false;counter=17;noPlayer=false
   gameJournalEntryState={Succeeded=3};q={GetFactStr=function(self,n)return facts[n] or 0 end,SetFactStr=function(self,n,v)facts[n]=v;writes[#writes+1]=n end}
   j={GetEntryByString=function(self,p,c)if missing then return nil end;return p end,GetEntryState=function()return badstate and 2 or 3 end,GetObjectiveCurrentCounter=function()return counter end,SetEntryVisited=function()visits=visits+1 end}
   Game={GetQuestsSystem=function()return q end,GetJournalManager=function()return j end,GetPlayer=function()return not noPlayer and {} or nil end}
   io={open=function()return {read=function()return '{}' end,close=function()end} end}
   json={decode=function()return {key='ma_wat_kab_08',paths={{path='local/onscreen',class='gameJournalOnscreen'}}} end}
  ''')
  f=l.globals().facts
  require=dict(re.findall(r'(\w+)=(\d+)',source.split('local required = {')[1].split('}')[0]))
  for k,v in require.items():f[k]=int(v)
  return l,l.execute(source),require
 l,module,requirements=runtime();assert len(l.globals().writes)==0
 assert module.Test('wrong').startswith('Refused') and len(l.globals().writes)==0
 for k,v in requirements.items():
  l,module,_=runtime();l.globals().facts[k]=1-int(v);assert module.Test('DISPOSABLE_SAVE').startswith('Refused') and len(l.globals().writes)==0;k;neg+=1
 for expression in ['missing=true','badstate=true','counter=16','noPlayer=true']:
  l,module,_=runtime();l.execute(expression);assert module.Test('DISPOSABLE_SAVE').startswith('Refused') and len(l.globals().writes)==0;neg+=1
 l,module,_=runtime();assert module.Test('DISPOSABLE_SAVE').startswith('Queued TEST ONLY');assert list(l.globals().writes.values())==['PTFRP1_TestPreparing','PTFRP1_TestRequest']
 assert l.globals().visits==1 and module.Test('DISPOSABLE_SAVE').startswith('Refused');module.Status();assert len(l.globals().writes)==2
 ids=[binascii.crc_hqx((d+':1').encode(),0xffff) for d in m['boots']];ep=read(ROOT/'research/q307_extracted/json/ep1/quest/ep1.quest.json')
 occupied={x['id'] for x in m['installed_injections']}|{x['Data']['id'] for x in ep['Data']['RootChunk']['graph']['Data']['nodes']}
 assert len(set(ids))==20 and not set(ids)&occupied
 assert not any(d.startswith(('base\\','ep1\\')) for d in m['resources'])
 casts={str(p.relative_to(ROOT)):[a['actorName'] for a in read(p)['Data']['RootChunk']['actors']] for p in (ROOT/'research/cyberpsycho_p1/scenes_01/json').rglob('*.json')}
 assert len(casts)==26
 return {'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),'native_payloads_unchanged':exact,'negative_admissions':neg,'counter_milestone_cases':306,'scene_casts':casts,'luajit_guard_tests':True,'limits':'Native Respawn/reward refill and journal API delivery need live testing; no claim of pristine history or all-17 gameplay coverage.'}
if __name__=='__main__':
 build=Path(sys.argv[1]);dest=build/'tests.json';assert not dest.exists()
 r=verify(build);dest.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='scene_casts'},indent=2))

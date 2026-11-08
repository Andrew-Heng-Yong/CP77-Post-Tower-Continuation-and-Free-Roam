"""Three EP1 follow-ups: exact native owners, SMS/vendor callbacks and cleanup."""
from pathlib import Path
import sys,copy,json,argparse,re,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'C01'))
import inputs as I
from verify_u10 import ev,path
from model import Resource,compare_graph
EXTRA=[r'ep1\openworld\world_stories\ep1_world_stories.questphase',r'ep1\openworld\ep1_open_world.questphase',r'ep1\quest\ep1_persistent_content.questphase',r'ep1\quest\main_quests\q305\phases\q305_11_after_quest.questphase',r'towercontinued\b0_story_eight\yoko.questphase',r'ep1\openworld\street_stories\sts_ep1_07\phases\sts_ep1_07_cleanup.questphase',r'ep1\openworld\street_stories\sts_ep1_12\phases\sts_ep1_12_cleanup.questphase',r'ep1\quest\ep1.quest']
def run(O):
 assert not O.exists();M={};pins=[];T=[];mut=[];cases={};issues=[]
 def ck(name,ok,e=None,q=None):T.append({'name':name,'status':'PASS' if ok else 'FAIL','quest_id':q,'evidence':e});assert ok,(name,str(e)[:1000])
 for d in I.selected('C03',EXTRA):m,p=I.load(d);M[d]=m;pins.append(p);ck('source pin graph integrity '+d,not m['errors'],p)
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def loc(d,gp,i):
  nd=n(d,i,gp);i=str(i);return {'depot':d,'graph':gp,'node':i,'payload':nd['payload'],'reads':nd['reads'],'writes':nd['writes'],'refs':nd['refs'],'journal_paths':nd['journal_paths'],'node_refs':nd['node_refs'],'prefabs':nd['prefabs'],'incoming':[e for e in g(d,gp)['edges'] if e[2]==i],'outgoing':[e for e in g(d,gp)['edges'] if e[0]==i]}
 co=I.W/'research/sidejobs_s29/contracts_review_01.json';contracts=I.read(co)
 for p in [co,I.W/'prealpha/sidejobs_s29/plan_01.py']:
  pins.append({'kind':'adapter_selection_evidence','path':str(p),'sha256':I.sha(p)})
 for q in I.ASSIGN['C03']:
  desc=next(x for x in contracts['jobs'] if x['id']==q);cur='towercontinued\\sidejobs_s29\\native\\'+desc['native'];nat=desc['native'];entry='towercontinued\\sidejobs_s29\\entries\\'+q+'.questphase';case={'native':nat,'current':cur,'entry':entry,'original_root_prefabs':M[nat]['root_prefabs'],'current_root_prefabs':M[cur]['root_prefabs']}
  if q!='q305_postcontent':ck('entire native root/graphs/payloads/edges retained '+q,not compare_graph(M[nat],M[cur]),compare_graph(M[nat],M[cur]),q)
  else:
   for ni in [4,5,6,9]:ck('selected native postcontent payload '+str(ni),n(nat,ni)['payload']==n(cur,ni)['payload'] and n(nat,ni)['sockets']==n(cur,ni)['sockets'],loc(nat,'root',ni),q)
   ck('entire breadcrumb nested graph retained',g(nat,'root/4')==g(cur,'root/4'),'Exact root/4 graph including original unused/test nodes; no whisper subtree',q)
   ck('only selected native root and added input retained',set(g(cur)['nodes'])=={'4','5','6','9','65000'} and g(cur)['edges']==sorted([['65000','Out','5','In'],['5','Out','9','In'],['9','True','6','In'],['6','True','4','Testing_in'],['6','False','4','In1']]) and g(cur)['entries']=={'In1':'65000'},g(cur)['edges'],q)
   ck('removed equipment whisper owner excluded', 'root/2' not in M[cur]['graphs'] and not any('haunted_weapons_reactions.scene' in r for gg in M[cur]['graphs'].values() for nn in gg['nodes'].values() for r in nn['refs']),list(M[cur]['graphs']),q)
   case['intentional_body_difference']='Only selected native breadcrumb root4/5/6/9 plus new input65000; excludes independent equipment whisper subtree/root2; exact original retained root4 including native commentary reset sequence.'
  guard=n(entry,65003)['payload']['condition'];f={x['factName']:x['value'] for x in I.walk(guard) if x.get('$type')=='questVarComparison_ConditionType'};j={x['path']['realPath']:x['state'] for x in I.walk(guard) if x.get('$type')=='questJournalEntryState_ConditionType'}
  ck('actual graph admission positive '+q,ev(guard,f,j,{}),{'facts':f,'journals':j},q)
  for fact,value in f.items():ck('contradicted admission atom rejected '+q+fact,not ev(guard,f|{fact:value+1},j,{}),{'fact':fact,'bad':value+1},q)
  for jp,state in j.items():ck('progressed journal rejected '+q+jp,not ev(guard,f,j|{jp:'Succeeded' if state!='Succeeded' else 'Active'},{}),{'path':jp,'actual':state},q)
  ck('actual late recheck before claim '+q,n(entry,65004)['payload']['condition']==guard and ['65004','True','65005','In'] in g(entry)['edges'] and ['65004','False','65003','In'] in g(entry)['edges'],loc(entry,'root',65004),q)
  if desc.get('parent'):
   parent=desc['parent'];pd=parent['depot'];gate=next(i for i in parent['ids'] if i!=parent['child']);expected=copy.deepcopy(n(pd,parent['child'])['payload']);expected['phaseResource']['DepotPath']['$value']=cur
   ck('original parent activation gate '+q,n(entry,gate)['payload']==n(pd,gate)['payload'] and n(entry,parent['child'])['payload']==expected,{'parent':loc(pd,'root',gate),'child':loc(pd,'root',parent['child'])},q)
   ck('original parent root support obligations '+q,M[pd]['root_prefabs']==[] and n(pd,parent['child'])['prefabs']==[],{'root':M[pd]['root_prefabs'],'child':n(pd,parent['child'])['prefabs']},q)
   case['original_parent']={'resource':pd,'activation':loc(pd,'root',gate),'child':loc(pd,'root',parent['child'])}
  rows=[loc(cur,gp,ni)|{'type':nn['type'],'reward':nn['reward'],'sms':nn['sms']} for gp,gg in M[cur]['graphs'].items() for ni,nn in gg['nodes'].items()];case.update(guard=guard,guard_fixture={'facts':f,'journals':j},handlers=rows,all_native_differences=compare_graph(M[nat],M[cur]));I.write(O/'quests'/q/'evidence.json',case);cases[q]=case
 # Native-specific callback/cleanup and producer controls.
 q='q305_postcontent';d=cases[q]['current'];native=cases[q]['native'];gp='root/4';yy=r'towercontinued\b0_story_eight\yoko.scene';yn=r'base\open_world\vendors\watson\kabuki\wat_kab_netrunner_01\wat_kab_netrunner_01.scene'
 for edge in [['65000','Out','5','In'],['5','Out','9','In'],['9','True','6','In']]:ck('earned native breadcrumb gate '+str(edge),edge in g(d)['edges'],edge,q)
 ck('recipe alternatives are OR',n(d,9)['payload']['condition']['operation']=='OR' and {x['factName'] for x in n(d,9)['reads']}=={'haunted_weapon_recipe_acquired','haunted_deck_recipe_acquired'},loc(d,'root',9),q)
 for edge in [['15','Out','17','In'],['16','Out','17','In'],['17','Out','33','Succeeded'],['38','Out','75','In'],['75','Out','74','Active'],['77','CutSource','60','CutDestination']]:ck('native SMS receipt/craft cleanup '+str(edge),edge in g(d,gp)['edges'],edge,q)
 ck('real vendor callback writer preserved',n(yy,620,'scene')['writes']==n(yn,620,'scene')['writes'] and n(yy,620,'scene')['writes'][0]['factName']=='q305_haunted_component_ready' and n(d,8,gp)['reads'][0]['factName']=='q305_haunted_component_ready',{'writer':loc(yy,'scene',620),'consumer':loc(d,gp,8)},q)
 ck('real talk receipt handshake',n(d,17,gp)['writes'][0]['factName']=='Q305_haunted_component_talk_ready' and n(yy,797,'scene')['writes']==n(yn,797,'scene')['writes'] and n(yy,797,'scene')['writes'][0]['value']==0,{'producer':loc(d,gp,17),'vendorclear':loc(yy,'scene',797)},q)
 ck('native craft requirement exact two inventory alternatives',n(d,19,gp)['payload']==n(native,19,gp)['payload'] and n(d,19,gp)['payload']['condition']['operation']=='OR',loc(d,gp,19),q)
 ck('native15minute after-craft message delay',n(d,75,gp)['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':0,'hours':0,'minutes':15,'seconds':0},loc(d,gp,75),q)
 ck('native persistent owner envelope no omitted PIP',M[r'ep1\quest\ep1_persistent_content.questphase']['root_prefabs']==[] and n(r'ep1\quest\ep1_persistent_content.questphase',13,'root/30')['prefabs']==[],loc(r'ep1\quest\ep1_persistent_content.questphase','root/30',13),q)
 # Yoko service is an actual conditional current owner with earned native default gate, not presence proof.
 y=r'towercontinued\b0_story_eight\yoko.questphase';ck('current Yoko exact owner and scene request',n(y,2)['reads'] and any(r.get('factName')=='wat_kab_netrunner_01_default_on' and r.get('comparisonType')=='Greater' for r in n(y,2)['reads']) and n(y,2,'root/5/11')['refs']==[yy] and ['200','Out','2','wat_kab_netrunner_01_start'] in g(y,'root/5/11')['edges'],{'outer':loc(y,'root',2),'request':loc(y,'root/5/11',200)},q)
 q='wst_ep1_09';d=cases[q]['current'];ck('earned Roads cleanup activation writer',n(EXTRA[5],14)['writes'][0]=={'$type':'questSetVar_NodeType','factName':'wst_ep1_09_active','setExactValue':1,'value':1},loc(EXTRA[5],'root',14),q)
 for edge in [['103','Out','105','Active'],['104','Out','105','Active'],['62','Out','102','In'],['102','Out','65','In'],['65','Success','55','In'],['55','Out','54','In'],['95','Out','144','In'],['144','Out','145','In']]:ck('native Nele completion/response/cleanup '+str(edge),edge in g(d)['edges'],edge,q)
 ck('Nele post-success three game hours',n(d,55)['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':0,'hours':3,'minutes':0,'seconds':0},loc(d,'root',55),q)
 ck('native cleanup receipt precedes terminating output',n(d,144)['writes'][0]['factName']=='wst_ep1_09_cleanup_done' and n(d,145)['payload']['type']=='Terminating',{'receipt':loc(d,'root',144),'output':loc(d,'root',145)},q)
 ck('retains original no outward parent completion socket',not any(e[0]=='9' for e in g(cases[q]['entry'])['edges']),g(cases[q]['entry'])['edges'],q)
 q='sts_ep1_12_pickup';d=cases[q]['current'];ck('earned TreatingSymptoms cleanup activation writer',n(EXTRA[6],14,'root/36')['writes'][0]=={'$type':'questSetVar_NodeType','factName':'wst_ep1_02_active','setExactValue':1,'value':1},loc(EXTRA[6],'root/36',14),q)
 for edge in [['26','Out','27','In'],['27','Out','28','Active'],['10','Out','11','Succeeded'],['11','Out','32','In'],['32','False','31','Inactive'],['31','Out','8','In'],['32','True','8','In'],['8','Out','24','In'],['24','Out','40','In']]:ck('native Alan response/reward/cleanup '+str(edge),edge in g(d)['edges'],edge,q)
 ck('native physical loot interaction required',n(d,10)['payload']['condition']['type']['$type']=='questInteraction_ConditionType' and '#sts_ep1_12_corpo_loot' in str(n(d,10)['payload']),loc(d,'root',10),q)
 ck('Alan native reward record exact', 'QuestRewards.sts_ep1_12_reward_alan' in str(n(d,8)['payload']),loc(d,'root',8),q)
 ck('Alan native body root carries location lease',M[d]['root_prefabs']==['#loc_sts_ep1_12_questdesign'],M[d]['root_prefabs'],q)
 scripts=[]
 for name in ['PTFR_SideJobsS29.reds','PTFR_B0StoryEight.reds','PTFR_HistorySnapshotHS1.reds']:
  p=I.C/'package/r6/scripts/PTFR_Consolidated'/name;expected=next(x['sha256'] for x in I.E['package_files'] if x['path'].endswith('/'+name));ck('effective script source '+name,I.sha(p)==expected,str(p));scripts.append({'path':str(p),'sha256':expected})
 code=Path(scripts[0]['path']).read_text(encoding='utf8')
 for needle in ['if !snapshot.FreshS29(ids[k]) { return false; }','if this.Own(i, "Issued") == 0 { this.Permit(i, false); }','this.Permit(i, this.Same(this.previous[i], current) && this.Ready(i));']:
  ck('actual current history and no-restart source '+needle,needle in code,scripts[0])
 for label,q,field in [('eligibility','q305_postcontent','q307_done'),('alan_reward','sts_ep1_12_pickup','QuestRewards.sts_ep1_12_reward_alan'),('nele_cleanup','wst_ep1_09','wst_ep1_09_cleanup_done')]:
  d=cases[q]['entry'] if label=='eligibility' else cases[q]['current'];pin=next(p for p in pins if p.get('depot')==d);raw=copy.deepcopy(I.read(pin['json']));changed=0
  for x in I.walk(raw):
   if label=='alan_reward' and x.get('$type')=='TweakDBID' and x.get('$value')==field:x['$value']='QuestRewards.QR6_missing';changed+=1
   elif x.get('factName')==field:x['value']=999;changed+=1
  mm=Resource(raw).normalize();caught=bool(compare_graph(M[d],mm));ck('actual raw source mutation detected '+label,caught and changed>0,{'resource':d,'field':field,'changes':changed},q);p=O/'mutations'/(label+'.json');I.write(p,raw);mut.append({'fault':label,'source':d,'mutant':str(p),'sha256':I.sha(p),'caught':caught})
 I.write(O/'crossowner_paths.json',I.read(H/'crossowners_01/crossowners.json'));I.write(O/'source_pins.json',pins+scripts);I.write(O/'tests.json',T);I.write(O/'mutations.json',mut);I.write(O/'summary.json',{'group':'C03','checks':len(T),'resources':len(M),'mutations':len(mut),'quest_ids':I.ASSIGN['C03'],'issues':issues,'status':'PASS_BOUNDED_STATIC_COMPARISONS_WITH_EXPLICIT_LIVE_OPAQUE_LIMITS','epoch':'QR5:08'});print({'checks':len(T),'resources':len(M),'mutations':len(mut)})
if __name__=='__main__':run(Path(sys.argv[1]))

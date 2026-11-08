"""Narrow post-return writer/consumer/retirement investigation, not a repair."""
from pathlib import Path
import sys,json,gzip,copy
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
O=H/'regina_followup_01';assert not O.exists()
tokens=['mq007_done','mq007_skippy_re_acquiring_done','mq007_giving_back_skippy','mq007_pr_gun_return'];found=[];pins=[];loaded={}
for depot,row in I.MI.items():
 raw=gzip.decompress(Path(row['normalized_model']).read_bytes())
 if not any(x.encode()in raw for x in tokens):continue
 m,p=I.load(depot);loaded[depot]=m;pins.append(p)
 hits=[]
 for gp,g in m['graphs'].items():
  for ni,n in g['nodes'].items():
   if any(x in str(n['payload'])for x in tokens):hits.append({'graph':gp,'node':ni,'type':n['type'],'reads':n['reads'],'writes':n['writes'],'paths':n['journal_paths'],'prefabs':n['prefabs'],'payload':n['payload'],'in':[e for e in g['edges']if e[2]==ni],'out':[e for e in g['edges']if e[0]==ni]})
 meta=[x for x in walk(m['metadata'])if x.get('$type')in['questQuestPrefabEntry','NodeRef']and any(t in str(x)for t in tokens)]
 found.append({'depot':depot,'private':depot.startswith('towercontinued\\'),'hits':hits,'metadata_hits':meta,'root_prefabs':m['root_prefabs'],'embedded_files':m['embedded_files']})
# Use freshly exported QR2 native parents with exact pinned payload/JSON hashes.
anc=read(I.W/'prealpha/quest_restoration_qr2/ancestor_review.json');parents={}
for d in ['base\\quest\\cyberpunk2077.questphase','base\\quest\\bugfixing.questphase','base\\quest\\bugfixing\\quest_bugfixing.questphase']:
 row=next(x for x in anc['inputs']if x['depot']==d);p=Path(row['source_json']);assert sha(p)==row['json_sha256'];parents[d]=Resource(read(p)).normalize();pins.append(row)
game=parents['base\\quest\\cyberpunk2077.questphase'];bug=parents['base\\quest\\bugfixing.questphase'];qb=parents['base\\quest\\bugfixing\\quest_bugfixing.questphase'];bf='base\\quest\\bugfixing\\minor_quests\\mq007\\mq007_quest_bugfixes.questphase'
checks=[]
def ck(name,ok,ev):checks.append({'name':name,'pass':bool(ok),'evidence':ev});assert ok,name
ck('genuine_Tower_to_terminating_root',all(x in game['graphs']['root']['edges']for x in [['106','Out','109','In'],['109','Out','107','In']])and game['graphs']['root']['nodes']['107']['payload']['type']=='Terminating'and any(x.get('state')=='Succeeded'and x.get('path',{}).get('realPath')=='ep1/quests/main_quest/q307_before_tomorrow'for x in game['graphs']['root']['nodes']['106']['reads']),'actual native106→109→107, all root descendants including root82')
ck('terminated_root_contains_bugfixing','base\\quest\\bugfixing.questphase'in game['graphs']['root/82']['nodes']['4']['refs'],'root/82 node4')
ck('bugfixing_contains_quest_bugfixing','base\\quest\\bugfixing\\quest_bugfixing.questphase'in bug['graphs']['root']['nodes']['9']['refs']and ['16','Out','9','In1']in bug['graphs']['root']['edges'],'bugfixing root16→9')
ck('quest_bugfixing_contains_mq007',bf in qb['graphs']['root/3']['nodes']['27']['refs']and ['20','Out1','27','In1']in qb['graphs']['root/3']['edges'],'quest_bugfixing root/3 node27, no instanceprefabs')
b=loaded[bf]
ck('actual_return_writer_matches_bugfix_request',any(x.get('factName')=='mq007_done'and x.get('value')==1 for x in loaded[I.R7]['graphs']['root/5']['nodes']['66']['writes'])and any(x.get('factName')=='mq007_done'and x.get('comparisonType')=='GreaterOrEqual'and x.get('value')==1 for x in b['graphs']['root/14']['nodes']['2']['reads']),'current native copied return/66 emits mq007_done1; original post-return14/2 waits >=1')
ck('five_day_delay_precedes_office_context',b['graphs']['root/14']['nodes']['4']['payload']['condition']['type']['days']==5 and ['2','Out','4','In']in b['graphs']['root/14']['edges']and ['4','Out','3','In1']in b['graphs']['root/14']['edges'],'root14 done→five game days→3 nested office+content wait')
ck('then_real_variant_and_three_messages',all(x in b['graphs']['root/14/3']['edges']for x in [['3','Out','4','In'],['4','Out','5','Active'],['5','Out','6','Active'],['6','Out','7','Active']]),'nested3 outside #mq007_tr_regina_jones_office_re_acquiring AND MinorQuestAndSts;4 shows #mq007_pr_gun_return.var_container;5/6/7 messages')
private_consumers=[{'depot':r['depot'],'graph':h['graph'],'node':h['node'],'reads':h['reads'],'writes':h['writes'],'paths':h['paths']}for r in found if r['private']for h in r['hits']if any(p.startswith('contacts/regina_jones/mq007_giving_back_skippy')for p in h['paths'])]
ck('no_current_private_message_rehost',not private_consumers,private_consumers)
# All native resource references are indexed; no current private or embedded target copy.
refowners=[{'depot':d,'private':d.startswith('towercontinued\\')}for d,r in I.IDX.items()if bf in r.get('refs',[])]
ck('only_native_indexed_reference_to_bugfix_owner',refowners==[{'depot':'base\\quest\\bugfixing\\quest_bugfixing.questphase','private':False}],refowners)
script_hits=[]
for p in (I.C/'package/r6/scripts').rglob('*.reds'):
 s=p.read_text(encoding='utf8')
 lines=[{'line':i+1,'text':x}for i,x in enumerate(s.splitlines())if any(t in x for t in ['mq007_giving_back_skippy','mq007_skippy_re_acquiring_done','mq007_pr_gun_return'])]
 if lines:script_hits.append({'path':str(p),'sha256':sha(p),'lines':lines})
write(O/'evidence.json',{'status':'NARROWED_SOURCE_CONFIRMED_MISSING_POST_RETURN_CONSUMER_REVIEW_REQUIRED','checks':checks,'source_pins':pins,'global_model_discovery_count':len(I.MI),'matching_resources':found,'native_ancestry':parents,'script_hits':script_hits,'private_message_consumers':private_consumers,'reference_owners':refowners,'producer':'current fresh native or copied resume root/5/66 mq007_done=1','consumer':'native bugfix MQ007 root/14/2; five-day timer→outside office+MinorQuestAndSts→show gun-return container→three SMS→reacquiring_done1','retirement':'Native authored genuine Tower106→109→Terminating107 encloses root82/4→bugfixing9→quest_bugfixing root3/27→MQ007 bugfix14. This is structural retirement evidence, not a current save observation.','safe_slice_blockers':['Native #mq007_pr_gun_return placement/lease is not established by this phase; its original world/prefab definition and authoring owner must be reviewed before any isolated clone.','No static proof of MinorQuestAndSts token acquisition in a new private post-Tower context.','A saved partially-run native14/timer and mq007_re_acquiring_done/variant state need conservative adaptation, never whole-bugfix replay.'],'runtime_changes':[]})
print(json.dumps({'checks':len(checks),'matching_resources':len(found),'private_message_consumers':len(private_consumers),'script_hit_files':len(script_hits),'output':str(O/'evidence.json')}))

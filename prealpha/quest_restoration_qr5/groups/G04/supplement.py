"""Additional source-specific bindings and eligibility checks; fresh output only."""
from pathlib import Path
import sys,argparse,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from verify_core import path
from verify import ev
def run(O):
 assert not O.exists();M={};pins=[];tests=[]
 def ck(name,ok,e):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,name
 for d in I.selected():m,p=I.load(d);M[d]=m;pins.append(p)
 def find(t):return next(d for d in M if d.endswith('\\'+t))
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,k,gp='root'):return g(d,gp)['nodes'][str(k)]
 def e(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
 for q,spec in [('sts_std_arr_10',(58,74,76,64,72,73)),('sts_std_arr_11',(57,74,75,63,70,71))]:
  d=find(q+'_entry.questphase');t1,t2,x1,tr,poi,x2=spec;ck('tier_alternative_XOR '+q,n(d,x1)['type']=='questLogicalXorNodeDefinition'and e(d,t1,'Out',x1,'In2'if q.endswith('_10')else'In1')and e(d,t2,'Out',x1,'In1'if q.endswith('_10')else'In2'),{'tier_nodes':[n(d,t1)['payload'],n(d,t2)['payload']]});ck('trigger_or_existing_POI_XOR '+q,n(d,x2)['type']=='questLogicalXorNodeDefinition'and e(d,tr,'Out',x2,'In1')and e(d,poi,'Out',x2,'In2'),{'trigger':n(d,tr)['payload'],'POI':n(d,poi)['payload']})
 a10=find('sts_std_arr_10_open_world.questphase');ck('native_auto_data_SMS_then_receipt',e(a10,124,'Out',185,'In','root/4')and e(a10,185,'Out',200,'In','root/4')and e(a10,200,'Out',199,'Active','root/4')and e(a10,199,'Out',171,'In','root/4')and n(a10,185,'root/4')['payload']['condition']['type']['seconds']==3,{'route':'computer-use124→3real seconds185→deletion200→actual SMS199→sentreceipt171; no fabricated user visited ACK','native_choice_unlock':n(a10,134,'root/4')['payload']})
 a11=find('sts_std_arr_11_openworld.questphase');ck('native_five_second_outcome_race',n(a11,73,'root/2')['payload']['condition']['type']['seconds']==5 and e(a11,74,'CutSource',73,'CutDestination','root/2'),{'Lucius_native_condition':n(a11,69,'root/2')['payload'],'engine_limit':'Retain exact native count0 killed/defeated semantics; do not reinterpret as arbitrary Boolean.'});ck('native_drop_reward_ACK',n(a11,71,'root/2')['payload']['condition']['type']['deviceConditionFunction']['$value']=='IsRewardCollected','native DropPointControllerPS owner ack, not a fabricated fact')
 combat=find('sts_std_arr_12_combat.questphase')
 for producer,wait,clear,kind in [(1152,1150,1151,'start'),(1156,1154,1155,'end')]:ck('Pedro_combat_actual_producer_listener_clear '+kind,e(combat,producer,'Out',wait,'In','root/3')and e(combat,wait,'Out',clear,'In','root/3')and n(combat,wait,'root/3')['reads'][0]['factName']=='holo_pedro_aimar_calls_v_'+kind+'_done',{'producer':n(combat,producer,'root/3')['writes'],'listener':wait,'clear':n(combat,clear,'root/3')['writes']})
 ph=I.EXTRA[3];c=n(ph,3)['payload']['condition'];branch=c['conditions'][-1];ck('Pedro_actual_OR_fresh_branch',ev(branch,{'PTFRU9_sts_std_arr_12_Permit':1,'PTFRU9_sts_std_arr_12_Started':0,'PTFRU9_sts_std_arr_12_Fault':0}),branch);ck('Pedro_actual_OR_existing_private_owned_branch',ev(branch,{'PTFRU9_sts_std_arr_12_Permit':0,'PTFRU9_sts_std_arr_12_ParentEntered':1,'PTFRU9_sts_std_arr_12_Started':1,'PTFRU9_sts_std_arr_12_MainFinished':0,'PTFRU9_sts_std_arr_12_OwnerFinished':0,'PTFRU9_sts_std_arr_12_Fault':0}),branch)
 assets={};tdb={}
 for q in I.Q:
  rows=[]
  for d,m in M.items():
   if not d.startswith('base\\open_world')or q not in d:continue
   md=m['metadata'];actors=[]
   for a in md.get('actors',[]):actors.append({'name':a.get('actorName'),'acquisition':a.get('acquisitionPlan'),'community':a.get('communityParams'),'context':a.get('findActorInContextParams'),'world':a.get('findActorInWorldParams')})
   rows.append({'depot':d,'binary_sha256':next(p['sha256']for p in pins if p['depot']==d),'metadata_sha256':m['metadata_sha256'],'root_prefabs':m['root_prefabs'],'recursive_prefabs':[{'graph':gp,'node':ni,'prefabs':n['prefabs']}for gp,gr in m['graphs'].items()for ni,n in gr['nodes'].items()if n['prefabs']],'actors':actors,'workspots':md.get('workspots',[]),'workspotInstances':md.get('workspotInstances',[]),'props':md.get('props',[]),'referencePoints':md.get('referencePoints',[]),'localMarkers':md.get('localMarkers',[]),'resource_refs':[{'depot':dep,'inventory':I.IDX.get(dep,{'status':'NOT_IN_PINNED_RESOURCE_INVENTORY'}),'definition_decoded_here':dep in M}for dep in m['refs']]})
  assets[q]=rows;p=I.W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02'/str(q+'.json');data=read(p);pins.append({'path':str(p),'sha256':sha(p),'role':'Root stock TDB bounded capture; runtime overrides and children not implied'});targets=[r for r in data['targets']if any(a in r.get('requested_aliases',[])for a in ['QuestRewards.'+q+'_completion'])];ck('stock_reward_record_exists '+q,bool(targets)and all(r['exists_in_stock']for r in targets),targets);tdb[q]={'path':str(p),'sha256':sha(p),'completion_targets':targets,'limits':data['limits'],'capture':data['capture']}
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'asset_bindings.json',assets);write(O/'stock_applicability.json',tdb);print({'checks':len(tests),'out':str(O)})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);run(Path(p.parse_args().out))

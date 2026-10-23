"""Generate explicit bounded S23 contracts from audited native ancestry and capture.

Only emits JSON to stdout. Source and generated contracts are installed with apply_patch.
"""
import json
from audit import ROOT, capture, graphs, sha

PARENT='research/sidejobs_s2/sacrum_audit/native_01/raw/base/quest/minor_quests/minorquests.questphase'
CFG={
 'mq024_sandra':('MQ024',[9,128],'SANDRA',['mq024_active','mq024_combat_sandra','mq024_done','mq024_hook_taken','mq024_sandra_opened_door','mq024_test_with_sts'],{'mq024_hacked_data_carrier':{'min':0,'max':1}},'Original main and data-carrier branches share one owner; native Kabuki tier, q105 and kab_05_activated prerequisites are retained.'),
 'mq007_smartgun':('MQ007',[21],None,['mq007_done','mq007_debug','mq007_opt_A','mq007_skippy_50_enemies_defeated','mq007_skippy_50_enemies_killed_and_stoneColdKiller','mq007_skippy_50_enemies_maimed','mq007_skippy_enemies_lethal','mq007_skippy_enemies_non_lethal','mq007_skippy_enemies_total','mq007_skippy_owner_known','mq007_skippy_re_acquiring_done','mq007_skippy_goes_emo','mq007_skippy_stash'],{},'Fresh pickup only. Native inventory-zero guard also required. Captured 95-kill gun is NOT restarted: the 50-enemy flag predates the mode-change scene and is not its completion acknowledgement.'),
 'mq035_ozob':('MQ035',[32],'OZOB',['mq035_car_ride','mq035_done','mq035_drive_chat','mq035_ow_despawn'],{},'Native street-cred/q110 unlock, message/call, car ride, ambush, cleanup and reward retained.'),
 'mq012_stud':('MQ012',[16],'MRSTUD',['mq012_arrived_in_car','mq012_can_stop_at_ripperdoc','mq012_debug','mq012_disable_blockade','mq012_disabled_truck_blockade','mq012_done','mq012_kids_past_danger','mq012_stud_dead','mq012_stud_stop_pose'],{'mq012_active':{'min':0,'max':1}},'Original setup sets active=1 before the encounter; 0 or 1 is admitted without resetting it. All objectives remain unstarted.'),
 'mq002_veterans':('MQ002',[12],None,['mq002_deal_broken_combat','mq002_deal_proceeded','mq002_done','mq002_escaped','mq002_escaped_combat','mq002_sniper_noticed'],{'mq002_active':{'min':0,'max':1}},'Original beginning input0->fact9 active=1->trigger8. Preserve camp outcomes and stock suspension, actor setup, scene and reward branches.'),
 'mq021_guide':('MQ021',[8],None,['mq021_active','mq021_bob_ending_approached','mq021_done','mq021_happy_ending'],{},'Original sq004/sq027 prerequisites, camp state, briefing, hospital, choice and reward branches retained.'),
 'mq041_corpo':('MQ041',[106],'FRANK',['mq041_corpo_started','mq041_debug','mq041_done'],{},'Original Corpo lifepath and q110/EP1 gates remain authoritative; non-Corpo does not receive War Pigs.'),
 'mq044_jakes_vehicle':('MQ044',[149],None,['mq044_done','mq044_started','mq_044_started_in_main'],{},'Original gle_06_finished prerequisite, three-game-day delay and succeed outcome gate retained; no granted vehicle or forced unlock.')
}

def contract():
 parent_json=ROOT/(PARENT.replace('/raw/','/json/')+'.json')
 root=next(g for g in graphs(parent_json) if g['path']=='root')
 edges=root['edges'];nodes={n['id']:n for n in root['nodes']}
 # Only ancestry reachable from the ordinary stock Input0, not EP1/debug inputs.
 reach={0}
 while True:
  new=reach|{e[2] for e in edges if e[0] in reach}
  if new==reach:break
  reach=new
 out=[]
 for jid,(key,targets,phone,zero,ranges,note) in CFG.items():
  c=capture()[jid];anc=set(targets)
  while True:
   new=anc|{e[0] for e in edges if e[2] in anc and e[0] in reach}
   if new==anc:break
   anc=new
  selected=sorted(anc&reach)
  assert 0 in selected and all(i in selected for i in targets)
  journals=[{'path':j['path'],'class':j['class'],'states':[1,4] if j['path']==c['root'] else [1]} for j in c['journals']]
  tag='PTFRS23_'+key
  out.append({'id':jid,'key':key,'title':c['title'],'tag':tag,'root':c['root'],
   'depot':'towercontinued\\sidejobs_s23\\base_a\\'+jid+'.questphase',
   'native_source':PARENT,'selected_nodes':selected,'target_nodes':targets,
   'native_edges':[e for e in edges if e[0] in selected and e[2] in selected],
   'native_target_depots':[nodes[i]['phaseResource']['DepotPath']['$value'] for i in targets],
   'facts_equal':{n:0 for n in zero},'fact_ranges':ranges,'journals':journals,
   'reactivate_paths':[],'conditional_reactivate_paths':[c['root']],
   'phone_dependency':None if not phone else 'PTFRS23_PHONE_'+phone+'_Issued',
   'native_only_guards':['Skippy inventory count = 0'] if key=='MQ007' else [],
   'route':note,'capture_progress_match':all(c['facts'].get(n)==0 for n in zero),
   'limits':['Bounded entry only: all catalogued child journals must be Inactive; no active/completed child is reset.',
     'Failed root is reactivated explicitly only after Issued, with no recursive propagation. Inactive root remains undiscovered until stock gameplay activates it.',
     'Native unlock waits can delay availability. Issued does not prove a visible marker or interaction.',
     'No reconstruction of old timer remaining duration; original waits restart only for this bounded entry.'],
   'live_pending':['actual gameplay/call/interaction','reward once','Johnny voice/body policy','save/reload']})
 return {'schema':1,'component':'base_a','capture_sha256':sha(ROOT/'research/sidejobs_s23/live_20261016_01/capture.json'),'owners':out}

if __name__=='__main__':print(json.dumps(contract(),indent=2))

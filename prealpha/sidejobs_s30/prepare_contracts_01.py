"""Three bounded admission contracts for native S30 stories."""
import importlib.util,json,sys
from pathlib import Path
sys.path.insert(0,'prealpha/sidejobs_s29')
import common
ROOT=Path(__file__).resolve().parents[2]
metadata=common.metadata()
source=json.loads((ROOT/'prealpha/sidejobs_s30/prepared_01/manifest.json').read_text(encoding='utf-8'))
assert source['status']=='PREPARED_NOT_INSTALLED'
rows=[]
specs=[
 dict(id='mq006_rollercoaster',title='Love Rollercoaster',input='In1',output='Out1',facts_equal={'mq006':0,'mq006_done':0,'mq006_roller_coaster_fixed':0,'mq006_enable_repeatable_rollercoaster':0,'mq006_ride_no_quest':0,'PTFRWORLD_Coaster_QuestOwns':0,'PTFRWORLD_Coaster_Registered':0},fact_ranges={},vehicle_zero=[]),
 dict(id='mws_se5_07',title='Shape of a Pony',input='In1',output='Out2',facts_equal={'mws_se5_07_started':0,'mws_se5_07_done':0,'mws_se5_07_objective_cut1':0,'porsche_911_930_turbo_cabriolet_owned':0},fact_ranges={},vehicle_zero=[{'record':'Vehicle.v_sport2_porsche_911turbo_cabrio_player'}]),
 dict(id='mws_wat_08_trauma_drama',title='Career Opportunities',input='Input',output='Output',facts_equal={'mws_wat_08_started':0,'mws_wat_08_done':0,'mws_wat_08_collected_reward':0,'mws_wat_08_activate_trauma_drama_section':0},fact_ranges={'shooter_appeared_on_leaderboard':{'min':1,'max':2147483647}},vehicle_zero=[]),
]
for spec in specs:
 ident=spec['id'];root=f'quests/minor_quest/{ident}'
 paths=[p for p in metadata if p==root or p.startswith(root+'/')]
 assert root in paths,(ident,'missing journal root')
 journals=[{'path':p,'class':metadata[p],'states':[1]} for p in sorted(paths,key=lambda p:(p!=root,p))]
 for p in journals:assert p['class'].startswith('gameJournal'),p
 dep=source['quests'][ident]
 row={**spec,'journal_ids':[ident],'tag':'PTFRS30_'+ident,'native':dep,'private_native':source['mapping'][dep],
      'journals':journals,'facts':[{'name':n,'min':v,'max':v} for n,v in spec['facts_equal'].items()]+[{'name':n,**v} for n,v in spec['fact_ranges'].items()],
      'inventory_zero':[]}
 rows.append(row)
out=ROOT/'prealpha/sidejobs_s30/prepared_01/contracts.json'
out.write_text(json.dumps({'status':'CONTRACTS_NOT_INSTALLED','jobs':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('contracts',len(rows),'journal entries',sum(len(x['journals']) for x in rows))

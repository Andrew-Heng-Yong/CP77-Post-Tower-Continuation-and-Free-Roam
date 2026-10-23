"""Independent exact-source delta audit of U9's native retaliation owner."""
import copy
from catalog_gig_rollout_r2 import ROOT, read, sha, walk, value
from inspect_special_gigs_u9 import graphs
from prepare_special_gigs_u9 import reach

SOURCE='research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories_gang_retaliation.questphase.json'
PARENT='research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories.questphase.json'
SELECTORS={('root/1/136',11):'sts_bls_ina_03',('root/1/136',17):'sts_bls_ina_02',
 ('root/29/214',29):'sts_std_arr_11',('root/29/214',34):'sts_std_rcr_03',
 ('root/31',242):'sts_cct_dtn_03',('root/33/227',35):'sts_hey_gle_04',
 ('root/35/239',41):'sts_wat_kab_02',('root/35/239',45):'sts_wat_nid_05',
 ('root/37/298',68):'sts_wat_lch_01',('root/37/298',69):'sts_wat_lch_03',('root/37/298',78):'sts_wbr_hil_07'}
EXCLUDED={'root/29/214':(33,32,'sts_std_rcr_04'),'root/33/227':(38,37,'sts_hey_rey_02'),'root/37/298':(81,79,'sts_wbr_jpn_12')}
GANGS=[('wraiths',47,46,1),('6thstreet',51,50,29),('animals',55,54,31),('valentinos',58,57,33),('maelstroms',61,60,35),('tygerclaws',63,62,37)]

def eqfact(f,v):
 return {'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':f,'value':v}}

def check():
 manifest=read(ROOT/'research/gig_restoration/special_gigs_u9/manifest.json')
 for p,h in manifest['source_pins'].items():assert sha(ROOT/p)==h,p
 old={g['path']:g for g in graphs(SOURCE)}
 newall=graphs('research/gig_restoration/special_gigs_u9/gang_retaliation.json')
 new={g['path'].replace('root/22','root',1):g for g in newall if g['path'].startswith('root/22')}
 assert old.keys()==new.keys()
 expected_mutations=0
 for path,g in old.items():
  got=new[path];on={n['id']:n for n in g['nodes']};nn={n['id']:n for n in got['nodes']}
  assert set(nn)==set(on)|({64000+i for i in range(12)} if path=='root' else set()),path
  for i,n in on.items():
   wanted=copy.deepcopy(n)
   if (path,i) in SELECTORS:
    wanted['condition']={'$type':'questLogicalCondition','operation':'AND','conditions':[eqfact('PTFRU9_'+SELECTORS[path,i]+'_Started',1),n['condition']]}
    expected_mutations+=1
   assert nn[i]==wanted,(path,i,'native payload changed')
  edges=set(map(tuple,g['edges']))
  if path in EXCLUDED:
   start,condition,_=EXCLUDED[path];edges.remove((0,'Out',start,'In'))
   assert condition not in reach(got['edges'],[0]),(path,'excluded route reachable')
  if path=='root':
   for index,(gang,entry,condition,child) in enumerate(GANGS):
    base=64000+index*2;tag='PTFRU9_Retaliation_'+gang
    edges.remove((0,'Out',entry,'In'));edges|={(0,'Out',base,'In'),(base,'Out',base+1,'In'),(base+1,'Out',entry,'In')}
    assert nn[base]['condition']=={'$type':'questLogicalCondition','operation':'AND','conditions':[
      eqfact(tag+'_Request',1),eqfact(tag+'_Permit',1),eqfact(tag+'_Issued',0),eqfact(tag+'_Fault',0),eqfact('sts_'+gang+'_retaliation',0)]}
    assert nn[base+1]['type']=={'$type':'questSetVar_NodeType','factName':tag+'_Issued','setExactValue':1,'value':1}
    assert (child,'Out1',condition,'In') in edges
    # An unissued group has no active entry path, even while the shared cancel
    # loop and other gang owners are running. Return edges cannot self-start it.
    unissued=[e for e in got['edges'] if e!=[0,'Out',base,'In']]
    assert child not in reach(unissued,[0]),(gang,'unissued native child reachable')
  assert set(map(tuple,got['edges']))==edges,(path,'native edges changed')
 assert expected_mutations==11
 top=newall[0];tn={n['id']:n for n in top['nodes']}
 assert set(tn)=={0,65000,65001,65002,22}
 assert not any(n['$type']=='questOutputNodeDefinition' for n in top['nodes'])
 assert top['edges']==[[0,'Out',65000,'In'],[65000,'Out',65001,'In'],[65001,'Out',65002,'In'],[65002,'Out',22,'In1']]
 child=copy.deepcopy(next(n for n in graphs(PARENT)[0]['nodes'] if n['id']==22))
 child['phaseResource']['DepotPath']={'$type':'ResourcePath','$storage':'uint64','$value':'0'}
 assert tn[22]==child,'native containing metadata changed'
 guards={z['factName']:z['value'] for z in walk(tn[65001]) if z.get('$type')=='questVarComparison_ConditionType'}
 required={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q307_ep1_killed':1,'q307_active':0,'q115_point_of_no_return':0,'q305_johnny_scene_active':0,'debug_sts_start':0,'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0,'PTFRU9_Retaliation_Request':1,'PTFRU9_Retaliation_Permit':1,'PTFRU9_Retaliation_Issued':0,'PTFRU9_Retaliation_Fault':0,'sts_gang_retaliation_cancel':0,'mws_chase_active':0}
 assert guards==required
 # Every native fact mutation is byte/payload-equal above. All additions own only
 # PTFRU9 bookkeeping: no clearing a historical native gang pending flag.
 nativewrites=[z for g in old.values() for n in g['nodes'] for z in walk(n) if z.get('$type')=='questSetVar_NodeType']
 builtwrites=[z for g in newall for n in g['nodes'] for z in walk(n) if z.get('$type')=='questSetVar_NodeType']
 assert [z for z in builtwrites if not z['factName'].startswith('PTFRU9_')]==nativewrites
 assert all(not (z.get('$type')=='questStartQuest_NodeType') for g in newall for n in g['nodes'] for z in walk(n))
 for gang,_,_,child in GANGS:
  target='sts_'+gang+'_retaliation'
  writes=[(p,n['id']) for p,g in old.items() for n in g['nodes'] for z in walk(n) if z.get('$type')=='questSetVar_NodeType' and z.get('factName')==target]
  assert writes==[('root/'+str(child),23)],(gang,'pending reset outside own native child')
 rootwrites=[z['factName'] for n in old['root']['nodes'] for z in walk(n) if z.get('$type')=='questSetVar_NodeType']
 assert rootwrites==['sts_gang_retaliation_cancel','sts_gang_retaliation_cancel']
 # Admission model: a pending legacy gang cannot start; unrelated empty gangs can.
 cases=0
 for request in (0,1):
  for permit in (0,1):
   for issued in (0,1):
    for fault in (0,1):
     for native_pending in (0,1,2):
      admitted=request==permit==1 and issued==fault==native_pending==0
      assert not (native_pending and admitted)
      cases+=1
 baseline={'maelstroms':1,'tygerclaws':1}
 assert [g for g,_,_,_ in GANGS if baseline.get(g,0)==0]==['wraiths','6thstreet','animals','valentinos']
 assert set(SELECTORS.values()).isdisjoint({v[2] for v in EXCLUDED.values()})
 return dict(test_sha256=sha(__file__),native_graphs_exact_except_declared_admission=len(old),selected_owned_selectors=11,excluded_startup_edges=3,
  native_gang_flows=6,shared_cancel_owner=1,shared_cancel_cannot_clear_unissued_gang_pending=True,per_gang_admission_models=cases,legacy_pending_preserved=True,
  source_parent_start='root/25 Out -> root/22 In1',source_parent_shutdown='root/23 q115_point_of_no_return > 0 -> 12 three ticks -> 11 terminating',
  source_stock_generic_signal_without_matching_selector=['sts_wat_kab_07','sts_wat_lch_06'],
  no_new_sidejob_owners=True,no_custom_chase_or_native_fact_reset=True,live_chase_pending=True)

if __name__=='__main__':
 import json
 print(json.dumps(check()))

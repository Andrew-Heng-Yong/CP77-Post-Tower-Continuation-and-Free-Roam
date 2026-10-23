"""Freeze the confirmed Yagami Market location and narrow vendor-02 owner."""
import json,math
from plan_b0_ordinary_vendor_batch import ROOT,OUT,BASE,read,walk,resource,graph_at,nm

DEST=ROOT/'research/b0_cpz_food02'

def main():
    s=next(s for s in read(OUT/'owner_audit.json') if s['id']=='cct_cpz_food_02')
    assert not s['reasons'] and s['scene_fact_writes']==['cct_cpz_food_02_met']
    assert s['panel_records']==['Vendors.cct_cpz_food_02'] and s['spawn']['phase']=='cpz_food_02'
    markers=[r for r in read(DEST/'nearby_service_nodes.json') if r['name']=='cct_sm_cpz_food_02']
    assert len(markers)==2 and len({r['reference'] for r in markers})==1
    marker=markers[0];assert marker['reference'].endswith('/#cct_sm_cpz_food_02_duplicate')
    sector=DEST/'world_trace/basegame_3_nightcity_exterior_-25_-5_-1_0.streamingsector.json'
    r=read(sector)['Data']['RootChunk']
    departure=next(d for d in r['nodeData']['Data'] if d['QuestPrefabRefHash']['$value'].endswith('/#cct_cpz_foodstore_02_mp_duplicate'))
    greeting=next(d for d in r['nodeData']['Data'] if d['QuestPrefabRefHash']['$value'].endswith('/#cpz_food_02_hello'))
    assert r['nodes'][greeting['NodeIndex']]['Data']['$type']=='worldTriggerAreaNode'
    position={axis:departure['Position'][axis.upper()] for axis in ('x','y','z')}
    scene_position={axis:marker[axis] for axis in ('x','y','z')}
    world=read(DEST/'world_trace/basegame_3_nightcity_exterior_-13_-3_-1_1.streamingsector.json')['Data']['RootChunk']
    bartender=next(d for d in world['nodeData']['Data'] if d['QuestPrefabRefHash']['$value'].endswith('/#cct_cpz_food__02_bartender_01'))
    assert world['nodes'][bartender['NodeIndex']]['Data']['$type']=='worldAISpotNode'
    counter={'x':-1541.2741699219,'y':-304.61795043945,'z':-4.4756546020508}
    assert math.dist(list(counter.values()),[bartender['Position'][k] for k in ('X','Y','Z')])<3
    assert any('signage_sp_food_yagami' in d['QuestPrefabRefHash']['$value'] for d in world['nodeData']['Data'])
    s.update(key='yagami',label='Yagami Market, Corpo Plaza food vendor 02',prefix='PTFRB0CPZF2_',
             setup_node=None,setup_payload=None,position=position,scene_position=scene_position,
             exit_radius=50,rearm_radius=45,resolved_scene_marker=marker['reference'],
             marker_correction='Copied scene node only: original short marker -> exact compiled _duplicate marker',
             counter_position=counter,counter_position_observed=True,teleport_verified=False,
             anchor_policy='Exact original departure mappin position; no guessed scene fallback',disposition='static_reviewed_not_live_tested')
    root=resource(s['source']);outer=nm(graph_at(root,'root/node'+str(s['outer'])))
    assert nm(root['graph']['Data'])[s['outer']]['phaseInstancePrefabs']==outer[s['phase']]['phaseInstancePrefabs']==[]
    existing=read(OUT/'cohort.json')
    previous=existing['sites']+existing['existing_owners']+read(ROOT/'research/b0_vendor_variants/cohort.json')['sites']+read(ROOT/'research/b0_ordinary_bars/cohort.json')['sites']
    assert (s['spawn']['reference'],s['spawn']['entry']) not in {(v['spawn']['reference'],v['spawn']['entry']) for v in previous}
    (DEST/'cohort.json').write_text(json.dumps({'schema':1,'sites':[s],'status':'STATIC_REVIEWED_NOT_LIVE_TESTED'},indent=2)+'\n')
    (DEST/'location_evidence.json').write_text(json.dumps({'scene_markers':markers,'mappin_node':departure,'greeting_node':greeting,'bartender_node':bartender,'user_counter':counter,'storefront':'Yagami Market'},indent=2)+'\n')
    print('CONFIRMED Yagami food02; exact mappin',position,'scene marker',marker['reference'])

if __name__=='__main__':main()

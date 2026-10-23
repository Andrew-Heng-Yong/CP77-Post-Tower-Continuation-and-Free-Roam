"""Independent bounded-owner review. No build, game, save, or fact writes."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'prealpha/dogtown_dt1/gate'))
from research import graphs


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    component=ROOT/sys.argv[1]
    output=ROOT/sys.argv[2]
    if output.exists() or not output.resolve().is_relative_to(ROOT/'research/dogtown_dt1/interactions'):
        raise ValueError('Unsafe/occupied review output')
    c=read(component);checks=0
    for source,digest in c['source_pins'].items():
        assert sha(ROOT/source)==digest,source
        checks+=1
    for helper in ('prealpha/ncpd_scanner_n1/native_inspect.py','tools/audit_activity_batches_b1.py',
                   'tools/catalog_gig_rollout_r2.py','tools/test_gig_pilot_r1.py'):
        assert helper in c['source_pins'],helper
        checks+=1
    tests=read(component.parent/'tests.json')
    assert tests['component_sha256']==sha(component) and tests['admission_cases']==55
    checks+=1
    parent=graphs(ROOT/'research/courier_c1/roots_01/json/ep1/openworld/ep1_open_world.questphase.json')
    native=graphs(ROOT/'research/dogtown_dt1/gate/native_01/json/ep1/openworld/combat_zone_gate/combat_zone_gate.questphase.json')
    boot=graphs(component.parent/'readback/gate_boot.json')
    assert set(boot)=={'root'}
    b={x['id']:x for x in boot['root']['nodes']}
    p={x['id']:x for x in parent['root']['nodes']}
    original=copy.deepcopy(p[13]);original['id']=5
    assert b[5]==original
    checks+=2
    assert len(b)==6 and b[5]['saveLock']==0
    assert b[5]['phaseResource']['DepotPath']['$value']==r'ep1\openworld\combat_zone_gate\combat_zone_gate.questphase'
    assert not c['official_overrides'] and len(c['resources'])==1 and len(c['boots'])==1
    checks+=3
    for name,digest in c['resources'].items():
        assert sha(component.parent/'source'/name)==digest
        checks+=1
    all_nodes=[n for g in native.values() for n in g['nodes']]
    assert len(all_nodes)==699 and len(native)==16
    assert not [n for n in b.values() if n['$type'] in ('questSpawnManagerNodeDefinition','questEventManagerNodeDefinition')]
    assert [(n['type']['factName'],n['type']['value']) for n in b.values()
            if n['$type']=='questFactsDBManagerNodeDefinition']==[('PTFRDT1_GateReady',1),('PTFRDT1_GateIssued',1)]
    checks+=3
    assert b[2]['condition']==b[3]['condition'] and b[2]['condition']['operation']=='AND'
    terms=b[2]['condition']['conditions']
    facts={t['type']['factName']:(t['type']['comparisonType'],t['type']['value'])
           for t in terms if t['$type']=='questFactsDBCondition'}
    for name,value in c['guard_equal'].items():
        assert facts.pop(name)==('Equal',value)
        checks+=1
    assert facts=={'ep1_side_content':('Greater',0),'q302_started':('Greater',0)}
    checks+=2
    nr={n['id']:n for n in native['root']['nodes']}
    intro={n['id']:n for n in native['root/7']['nodes']}
    assert [t for t in terms if t['$type']=='questTriggerCondition']==[intro[6]['condition']]
    assert intro[6]['condition']['type']=='IsOutside'
    assert intro[6]['condition']['triggerAreaRef']['$value']=='#combat_zone_gate_tr_respawn'
    combat=[t for t in terms if t['$type']=='questCharacterCondition']
    assert combat==[t for t in nr[177]['condition']['conditions'] if t['$type']=='questCharacterCondition']
    assert combat[0]['type']['isPlayer']==1 and combat[0]['type']['inverted']==1
    checks+=5
    edges=set(map(tuple,boot['root']['edges']))
    assert (3,'False',2,'In') in edges and (3,'True',4,'In') in edges and (4,'Out',5,'In1') in edges
    assert intro[26]['condition']['type']['factName']=='q302_started'
    assert intro[1]['type']=='Terminating'
    assert (26,'Out',27,'In2') in set(map(tuple,native['root/7']['edges']))
    assert (7,'Out1',181,'In') in set(map(tuple,native['root']['edges']))
    assert nr[181]['actions'][0]['type']['action']=='Deactivate'
    checks+=6
    report={'status':'PASS_INDEPENDENT_BOUNDED_GATE_REVIEW_NOT_LIVE','checks':checks,
            'component_sha256':sha(component),'reviewer_sha256':sha(Path(__file__)),
            'direct_native_reference':True,'native_graph_nodes':699,'no_official_override':True,
            'native_writes_added':0,'new_owned_fact_writes':['PTFRDT1_GateReady','PTFRDT1_GateIssued'],
            'caveats':['Native startup briefly Reactivates its own guard community before earned q302_started terminates intro. Admission is checked outside the respawn trigger; retained native #combat_zone_content_tr unfreezing can defer execution, so dispatch does not prove execution timing or player position at native startup.',
                       'Original lane, scanning, wrong-direction, combat, guard respawn and autosave behavior is retained; actual execution is live pending. This is not a forced gate-open bypass.',
                       'Issued acknowledges native dispatch only, not live crossing. All four lanes, security/wanted interaction and save/reload require playtest.']}
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'checks':checks,'component_sha256':sha(component)}))


if __name__=='__main__':main()

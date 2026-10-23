"""S28 admission, entitlement and saved-owner protocol checks, not gameplay."""
import copy
import importlib.util
import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
import generate
MODEL=ROOT/'prealpha/sidejobs_s22/runtime_v2/test.py'
spec=importlib.util.spec_from_file_location('s28_protocol_reference',MODEL)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)


def observe(row,states=None,facts=None,inventory=None,vehicles=None,available=True,settled=True):
    states=states if states is not None else [j['states'][0] for j in row['journals']]
    facts=facts if facts is not None else [f['min'] for f in row['facts']]
    inventory=inventory if inventory is not None else [0]*len(row['inventory_zero'])
    vehicles=vehicles if vehicles is not None else [False]*len(row['vehicle_zero'])
    valid=available and settled and len(states)==len(row['journals']) and len(facts)==len(row['facts'])
    valid=valid and all(type(s) is int and s in j['states'] for s,j in zip(states,row['journals']))
    valid=valid and all(type(v) is int and f['min']<=v<=f['max'] for v,f in zip(facts,row['facts']))
    valid=valid and len(inventory)==len(row['inventory_zero']) and all(type(v) is int and v==0 for v in inventory)
    valid=valid and len(vehicles)==len(row['vehicle_zero']) and all(v is False for v in vehicles)
    return dict(states=list(states),facts=list(facts),inventory=list(inventory),vehicles=list(vehicles),valid=valid)


def verify(folder):
    output=folder/'tests.json';assert not output.exists()
    manifest=generate.read(folder/'manifest.json')
    for p,h in manifest['source_pins'].items():assert generate.sha(ROOT/p)==h,p
    paths=list(dict.fromkeys(ROOT/r['source'] for r in manifest['rows']))
    rows=generate.normalize(paths);assert rows==manifest['rows'] and len(rows)==4
    source=(folder/'SideJobsS28.reds').read_text()
    assert generate.sha(folder/'SideJobsS28.reds')==manifest['files']['SideJobsS28.reds']
    assert source==generate.template().replace('// GENERATED_DATA',generate.data_source(rows))
    method=lambda name:prior.method(source,name)
    assert source.count('.SetFactStr(')==1
    for token in ['!IsDefined(qs) || this.Own(i, "Issued") != 0','SideJobDataS28.Tag(i) + "_Permit"']:
        assert token in method('Permit')
    for forbidden in ['ChangeEntryState','GiveReward','GiveItem','SetFact(','ModLog(','StartQuest','EnablePlayerVehicle','phone.Start','HistoryReady']:
        assert forbidden not in source,forbidden
    for token in ['actual < minimum[k] || actual > maximum[k]','EnumInt(jm.GetEntryState(entry)) : -1',
                  '!IsDefined(players) || !IsDefined(transaction)','!IsDefined(player) || player.IsReplacer()',
                  'transaction.GetItemQuantity(player, ItemID.CreateQuery(TDBID.Create(items[k])))','if actual != 0',
                  '!IsDefined(vehicleSystem)','vehicleSystem.IsVehiclePlayerUnlocked(TDBID.Create(vehicles[k]))',
                  'ArrayPush(sample.vehicles, unlocked)','if unlocked']:
        assert token in method('Read'),token
    assert method('Read').count('jm.HasAnyDelayedStateChanges()')==2
    for field in ['states','facts','inventory','vehicles']:
        assert f'ArraySize(a.{field}) != ArraySize(b.{field})' in method('Same')
        assert f'a.{field}[i] != b.{field}[i]' in method('Same')
    assert 'this.Permit(i, this.Same(this.previous[i], current) && this.Ready(i))' in method('Poll')
    assert 'epoch != this.epoch' in method('Poll')
    assert 'this.Own(i, "Issued") == 0' in method('Restored')
    assert '!player.IsDead() && !player.IsReplacer() && BodyPolicy.Safe(player)' in method('Safe')
    assert 'profile.PTFRPAComplete() && !profile.PTFRPAFaulted()' in method('Common')
    fresh={k:int(v) for k,v in re.findall(r'this.Own\(i, "([^"]+)"\) == (\d+)',method('FreshOwner'))}
    assert fresh==dict(Ready=1,Revision=1,Issued=0,Entered=0,Finished=0,Fault=0)
    cases=arrays=0
    for key,wanted in fresh.items():
        for actual in [-1,0,1,2,3]:
            sample=fresh|{key:actual}
            assert all(sample[k]==v for k,v in fresh.items())==(actual==wanted);cases+=1
    original_read=generate.read
    for path in paths:
        original=original_read(path)
        def rejects(mutator):
            changed=copy.deepcopy(original);mutator(changed['owners'][0])
            with patch.object(generate,'read',side_effect=lambda p:changed if p==path else original_read(p)):
                try:generate.normalize(paths)
                except (AssertionError,ValueError,KeyError,TypeError):return
            raise AssertionError('Unsafe contract accepted')
        for mutation in [lambda r:r.update(id='q307_tower'),lambda r:r.update(tag='PTFRS27_OTHER'),
                         lambda r:r['journals'][0].update(states=[2]),lambda r:r['journals'][0].update(states=[3]),
                         lambda r:r['journals'][0].update(states=[4]),lambda r:r['journals'][0].update(states=[True]),
                         lambda r:r['facts_equal'].update({r['tag']+'_Permit':1}),
                         lambda r:r.setdefault('fact_ranges',{}).update({'test':{'min':2,'max':1}}),
                         lambda r:r.pop('inventory_zero'),lambda r:r.pop('vehicle_zero')]:
            rejects(mutation);cases+=1
    for i,row in enumerate(rows):
        for name,values in generate.arrays(row).items():
            body=method(name+str(i));assert json.loads(body[body.index('return ')+7:body.rindex(';')])==values;arrays+=1
        baseline=observe(row);assert baseline['valid'];cases+=1
        for n,journal in enumerate(row['journals']):
            for value in [None,False,True,-1,0,1,2,3,4,5,999]:
                values=baseline['states'].copy();values[n]=value
                assert observe(row,states=values)['valid']==(type(value) is int and value in journal['states']);cases+=1
        for n,fact in enumerate(row['facts']):
            for value in [None,False,True,-2147483647,-1,0,1,2,999,fact['min']-1,fact['max']+1]:
                values=baseline['facts'].copy();values[n]=value
                assert observe(row,facts=values)['valid']==(type(value) is int and fact['min']<=value<=fact['max']);cases+=1
        for field in ['inventory','vehicles']:
            for n in range(len(baseline[field])):
                for value in [None,False,True,-1,0,1,2]:
                    values=baseline[field].copy();values[n]=value
                    valid=(type(value) is int and value==0) if field=='inventory' else value is False
                    observed=observe(row,**{field:values});assert observed['valid']==valid;cases+=1
                    if not valid:
                        p=prior.Protocol();p.tick(baseline);p.tick(baseline);p.tick(observed);assert p.permit==0;cases+=1
            assert not observe(row,**{field:baseline[field]+[0]})['valid'];cases+=1
        for available,settled in [(False,True),(True,False),(False,False)]:
            assert not observe(row,available=available,settled=settled)['valid'];cases+=1
        p=prior.Protocol();p.tick(baseline);assert p.permit==0;p.tick(baseline);assert p.permit==1;cases+=2
        invalid=observe(row,states=[3]+baseline['states'][1:]);p.tick(invalid);assert p.permit==0;cases+=1
        for guard in ['common','safe','final_safe']:
            p=prior.Protocol();p.tick(baseline);p.tick(baseline);p.tick(baseline,**{guard:False});assert p.permit==0;cases+=1
        p=prior.Protocol();p.tick(baseline);p.tick(baseline);p.issued=1;writes=copy.deepcopy(p.writes)
        p.tick(invalid);p.restore();assert writes==p.writes and p.issued==1;cases+=1
        p=prior.Protocol();p.restore();p.tick(baseline,epoch=p.epoch-1);assert p.warmup==3 and p.permit==0
        for tick in range(1,5):p.tick(baseline);assert p.permit==int(tick==4);cases+=1
    pins=manifest['source_pins']|{p.relative_to(ROOT).as_posix():generate.sha(p) for p in [MODEL,Path(__file__)]}
    result=dict(status='PASS_OFFLINE_NOT_LIVE',manifest_sha256=generate.sha(folder/'manifest.json'),test_sha256=generate.sha(__file__),
                policy_cases=cases,arrays=arrays,source_pins=pins,runtime_direct_writes=['own Permit'],
                resume_limit='Unsupported unfinished progress defers without reset. No item grant or vehicle unlock.')
    output.write_text(json.dumps(result,indent=2)+'\n');return {k:v for k,v in result.items() if k!='source_pins'}


if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1]))))

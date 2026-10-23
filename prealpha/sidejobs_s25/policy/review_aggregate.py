"""Final independent S25 source-witness binding and mixed deployment receipt review."""
import json,sys
from pathlib import Path
from prepare import ROOT,read,sha


def main(fixture):
    build=ROOT/'prealpha/sidejobs_s25/build/s25_04';m=read(build/'build.json')
    manifest_sha=sha(build/'build.json')
    assert manifest_sha=='5884AEB720E9AF6272A277F3750497B3C46021C165C2C3D10B1B56711F3AF6E6'
    for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
    all_json=[]
    for component in m['components']:
        for path in (ROOT/component['root']).rglob('*.json'):
            name=path.relative_to(ROOT).as_posix()
            assert m['source_pins'][name]==sha(path),name;all_json.append(name)
    rows=m['native_source_readbacks'];assert len(rows)==25
    rawmap={r['raw']:r for r in rows};assert len(rawmap)==25
    for r in rows:
        assert r['payload_equal'] is True
        assert m['source_pins'][r['raw']]==r['raw_sha256']==sha(ROOT/r['raw'])
        assert m['source_pins'][r['witness']]==r['witness_sha256']==sha(ROOT/r['witness'])
        assert r['fresh_sha256']==sha(build/r['fresh'])
        assert read(ROOT/r['witness'])['Data']==read(build/r['fresh'])['Data']
    plan=read(ROOT/'prealpha/sidejobs_s25/policy/plan02.json')
    assert len(plan['resources'])==17
    for r in plan['resources']:
        raw=rawmap[r['source']]
        assert raw['raw_sha256']==r['source_sha256']
        assert raw['witness'].startswith('prealpha/sidejobs_s25/policy/build/policy_01/original_readback/')
        assert raw['witness'].endswith(r['depot'].replace('\\','_')+'.json')
    services=read(ROOT/'prealpha/sidejobs_s25/services/build/services_06/build.json')
    for raw,witness in services['native_readbacks'].items():
        assert rawmap[raw]['witness']=='prealpha/sidejobs_s25/services/build/services_06/'+witness
    before=read(ROOT/'prealpha/sidejobs_s25/build/s25_03/build.json')
    assert m['resources']==before['resources'] and m['files'][1:]==before['files'][1:]
    assert {k:v for k,v in m['files'][0].items() if k!='sha256'}=={k:v for k,v in before['files'][0].items() if k!='sha256'}
    for item in m['files']:assert sha(build/item['source'])==item['sha256']
    assert [x['action'] for x in m['files']]==['add','add','add','replace','replace']
    assert len(m['mod_overrides'])==20 and not m['official_overrides']
    for name in ('tests.json','compile_result.json','resource_check.json'):
        proof=read(build/name);assert proof['build_sha256']==manifest_sha
    test=read(build/'tests.json');assert test['status']=='PASS_NOT_LIVE'
    audit=read(build/'resource_check.json');assert audit['status']=='PASS_RESOURCE_AUDIT'
    assert audit['official_comparisons']==54 and len(audit['winning_donors'])==20
    assert not audit['official_overrides']
    comp=read(build/'compile_result.json');assert comp['status']=='PASS_NOT_LIVE' and comp['full_scc'] and comp['equipmentex']
    for f in m['files'][3:]:assert comp['replacement_scripts'][f['relative']]==f['sha256']
    receipt=ROOT/fixture;f=read(receipt)
    assert f['status']=='PASS_WORKSPACE_FIXTURES_NOT_LIVE' and f['build_sha256']==manifest_sha
    assert f['cases']==107 and f['checks']==130
    assert f['installer_sha256']==sha(ROOT/'prealpha/sidejobs_s25/deploy.ps1')
    assert f['tester_sha256']==sha(ROOT/'prealpha/sidejobs_s25/test_deploy.py')
    assert f['game_writes']==f['save_writes']==0
    for case in ('after_first_replacement_recoverable','after_second_replacement_recoverable','junction_game_refused','junction_protected_refused','relative_log','escaping_log'):
        assert case in f['case_names']
    result={'status':'PASS_FINAL_INDEPENDENT_BOUNDED_REVIEW_NOT_LIVE','build_sha256':manifest_sha,
            'reviewer_sha256':sha(Path(__file__)),'component_json_witnesses_pinned':len(all_json),'source_pins_checked':len(m['source_pins']),
            'raw_source_payload_comparisons':25,'policy_original_readbacks_bound':17,'service_native_readbacks_bound':8,
            'original_readback_binding_gap_closed':True,'gameplay_resources_scripts_xl_unchanged_from_03':True,
            'packed_archive_bytes_unchanged_from_03':m['files'][0]['sha256']==before['files'][0]['sha256'],
            'deployment_fixture':fixture,'deployment_fixture_sha256':sha(receipt),'deployment_cases':107,'deployment_checks':130,
            'installed':False,'live_game_writes':0,'live_save_writes':0,'findings':[],
            'limits':'Source/policy/compiler/resource/deployment safety checks only. Live quest starts, dialogue, rewards, current-owner saved continuation, reload and alternate histories remain playtests. Main agent alone handles any installation.'}
    out=ROOT/'research/sidejobs_s25/policy/final_review_02.json';assert not out.exists()
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))


if __name__=='__main__':main(sys.argv[1])

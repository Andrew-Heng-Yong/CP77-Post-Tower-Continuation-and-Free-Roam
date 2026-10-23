"""Bind the reviewed additive DT1 deployer to exact final build and fixture proof."""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    build=ROOT/sys.argv[1];fixture=ROOT/sys.argv[2];out=ROOT/sys.argv[3]
    if out.exists() or not out.resolve().is_relative_to(ROOT/'research/dogtown_dt1/interactions'):
        raise ValueError('Unsafe or occupied review output')
    m=read(build/'build.json');r=read(build/'resource_check.json');t=read(build/'tests.json')
    f=read(fixture);checks=0
    deploy=ROOT/'prealpha/dogtown_dt1/deploy.ps1'
    fixtures=ROOT/'prealpha/dogtown_dt1/test_deploy.py'
    helper=ROOT/'prealpha/graphics_gd2/tools/deploy.ps1'
    assert sha(helper)=='1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307'
    checks+=1
    assert m['status']=='BUILT_DT1_LIVE_PENDING'
    assert m['official_overrides']==[] and m['runtime_scripts_added']==0
    assert m['game_writes']==m['save_writes']==0
    assert len(m['resources'])==len(m['boots'])==1
    assert m['boots']==[r'towercontinued\dogtown_dt1\gate_boot.questphase']
    checks+=5
    assert [x['relative'] for x in m['files']]==['archive/pc/mod/TowerContinued_Dogtown_DT1.archive','archive/pc/mod/TowerContinued_Dogtown_DT1.archive.xl']
    checks+=1
    for file in m['files']:
        assert sha(build/Path(file['relative']).name)==file['sha256']
        checks+=1
    for name,digest in m['source_pins'].items():
        assert sha(ROOT/name)==digest,name
        checks+=1
    assert t['status']==r['status']=='PASS_NOT_LIVE'
    assert t['build_sha256']==r['build_sha256']==sha(build/'build.json')
    assert r['checker_sha256']==sha(ROOT/'prealpha/dogtown_dt1/resource_check.ps1')
    assert t['tester_sha256']==sha(ROOT/'prealpha/dogtown_dt1/test.py')
    assert r['overrides']==r['official_overrides']==[] and r['modlist_absent']
    assert r['official_comparisons']>=4 and r['packed_readbacks']==1
    assert sorted(r['native_root_ids'])==[0,1,2,12,27]
    assert r['injection_ids']==m['injection_ids']
    checks+=8
    assert f['status']=='PASS_WORKSPACE_FIXTURES_NOT_LIVE'
    assert f['build_sha256']==sha(build/'build.json')
    assert f['installer_sha256']==sha(deploy) and f['tester_sha256']==sha(fixtures)
    assert f['cases']>=35 and f['checks']>=45
    cases={x['case'] for x in f['results']}
    assert {'normal','partial','busy','path_escape','wrong_target','native_override','extra_script',
            'game_writes','save_writes','existing_target','rollback_drift','receipt_tamper',
            'receipt_scope','root_escape','installer_identity','junction'}<=cases
    assert all((x['exit']==0)==x['expected_success'] for x in f['results'])
    checks+=6
    source=deploy.read_text(encoding='utf-8-sig')
    # Static control-flow anchors supplement, not replace, reviewed full source
    # and executed negative fixtures. Scope remains exactly two additions.
    for anchor in ("if(@($files).Count -ne 2", "Closed;CopyExact", "if(Test-Path -LiteralPath $target){throw 'DT1 already present",
                   "'DT1_ADD_ONLY'", "installer_sha256 -cne (Hash $PSCommandPath)",
                   "[IO.File]::Move($target,$removed,$false)", "$count=Same $protected",
                   "'PASS_WORKSPACE_FIXTURES_NOT_LIVE'"):
        assert anchor in source,anchor
        checks+=1
    assert 'Remove-Item' not in source and 'Stop-Process' not in source
    checks+=1
    report={'status':'PASS_INDEPENDENT_FINAL_DEPLOY_REVIEW_NOT_LIVE','checks':checks,
            'build_sha256':sha(build/'build.json'),'installer_sha256':sha(deploy),
            'fixture_tester_sha256':sha(fixtures),'fixture_proof':str(fixture.relative_to(ROOT)),
            'fixture_sha256':sha(fixture),'resource_proof_sha256':sha(build/'resource_check.json'),
            'reviewer_sha256':sha(Path(__file__)),'additions':2,'replacements':0,
            'scope':'Exact new archive and XL only; closed-process checks, full protected snapshots, bound paths/reparse rejection, no overwrite, matching proof/source hashes, recoverable hash-guarded rollback.',
            'gate_component_sha256':m['components'][0]['sha256'],'game_writes_by_review':0,
            'limits':'Static/native/package and fixture passes do not prove in-game crossing, police escalation, unfreezing timing or save/reload.'}
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'checks':checks,'build_sha256':report['build_sha256']}))


if __name__=='__main__':main()

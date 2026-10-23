"""Independent final-capture/proof review; never invokes installers or native APIs."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def main(revision):
    base=ROOT/f'prealpha/sidejobs_s26/restart/build/{revision}'
    manifest=read(base/'build.json');data=read(base/'data.json');tests=read(base/'tests.json')
    checks=[]
    def check(ok,label):
        assert ok,label
        checks.append(label)
    check(manifest['status']=='BUILT_READ_ONLY_CAPTURE_NOT_RESTORATION','diagnostic scope only')
    check(set(manifest['files'])=={'init.lua','data.json'},'exact two additive output files')
    for name,digest in manifest['files'].items():check(sha(base/name)==digest,f'output hash {name}')
    for path,digest in manifest['source_pins'].items():
        target=(ROOT/path).resolve()
        check(target.is_relative_to(ROOT.resolve()) and target.is_file() and sha(target)==digest,'source pin '+path)
    check('prealpha/sidejobs_s26/restart/analyze.py' in manifest['source_pins'],'analyzer dependency pinned')
    check(tests['build_sha256']==sha(base/'build.json'),'test receipt matches exact build')
    check(sha(ROOT/'prealpha/sidejobs_s26/restart/test.py')==tests['tester_sha256'],'capture tester identity')
    check(tests['status']=='PASS_LUAJIT_NOT_LIVE' and tests['cases']>=37,'37 actual LuaJIT cases recorded')
    check(all(manifest[k]==0 and tests[k]==0 for k in ('native_writes','save_writes','automatic_callbacks')),'no native/save writes or automatic callbacks')
    check(manifest['manual_observers']==['Vendor.OnVendorMenuOpen','RipperDocGameController.PrepareVendorItems','RipperDocGameController.OnSlotClick'],'exact explicit observer roster')
    check(manifest['manual_observer_count']==3 and manifest['observers_registered_at_load']==0 and manifest['capture_stops_manual_observation'] is True,'manual-only observer lifecycle metadata')
    probe_path=ROOT/'prealpha/sidejobs_s26/cassius/probe.lua'
    capture_path=ROOT/'prealpha/sidejobs_s26/restart/init.lua'
    source=(base/'init.lua').read_text(encoding='utf-8-sig')
    check(source==probe_path.read_text(encoding='utf-8-sig')+'\n'+capture_path.read_text(encoding='utf-8-sig'),'output exact source concatenation')
    check('return tostring(id.hash)' in source and 'player entity hash missing' in source and 'tostring(player:GetEntityID())' not in source,'stable native entity hash instead of temporary userdata identity')
    test_source=(ROOT/'prealpha/sidejobs_s26/restart/test.py').read_text(encoding='utf-8-sig')
    check('fresh wrapper, same entity hash must stay stable' in test_source and "{'changingHash':True},{'noHash':True}" in test_source,'player identity same/changing/missing regressions retained')
    check('diagnostics/PTFR_FreshGigsB5/init.lua' in manifest['source_pins'],'existing native EntityID.hash usage witness pinned')
    check(re.search(r'function M\.Capture\(\)\s+cassius\.Stop\(\)',source) is not None,'capture stops manual callbacks before sampling, including error path')
    for token in ['SetFact','ChangeEntryState','registerForEvent','Override(','GiveItem','RemoveItem','AutoSave','LoadSave','os.execute','io.popen','GetStock(','FillVendorInventory','GetItemsForSale','GetVendorObject(']:
        check(token not in source,'no forbidden mutation/query token '+token)
    check(source.count('ObserveAfter(hook[1],hook[2]')==1 and 'function P.Arm()' in source and 'if not armed then return end' in source,'observer callback inert unless explicitly armed')
    inv=read(ROOT/'research/sidejobs_s21_failed/inventory_02.json')['jobs']
    check(len(data['jobs'])==len({x['id'] for x in data['jobs']})==58,'exact 58 distinct catalogue roots')
    check({x['id']:x['root'] for x in data['jobs']}=={x['id']:x['journal_path'] for x in inv},'catalogue exact whitelist identities')
    check(sum(len(x['journals']) for x in data['jobs'])==manifest['journals']==740,'740 journal rows')
    check(sum(len(x['facts']) for x in data['jobs'])==manifest['facts']==2936,'2936 native fact rows')
    check({x['id'] for x in data['items']}=={'Items.YakuzaTattoo','Items.AdvancedYakuzaTattoo'},'two narrowly scoped native reward item queries')
    probe=read(ROOT/'research/sidejobs_s26/cassius/probe_tests_01.json')
    check(probe['lua_sha256']==sha(probe_path) and probe['status']=='PASS_LUAJIT_READ_ONLY_OPT_IN_PROBE' and probe['cases']>=30 and probe['mutation_calls']==0,'independent probe receipt binds source and 30 mutation-free cases')
    deploy=ROOT/'prealpha/sidejobs_s26/restart/deploy.ps1';text=deploy.read_text(encoding='utf-8-sig')
    for token in ["'data.json|init.lua'", "S26_CAPTURE_ADD_ONLY", "Scope $txn.files", "installer_sha256 -cne (Hash $PSCommandPath)", "CopyExact", "capture_reports_preserved=$true", "$FailAfterFirst", "Closed;CopyExact", "foreach($p in $m.source_pins.PSObject.Properties)", "$tests.build_sha256 -cne (Hash $manifestPath)"]:
        check(token in text,'deployer retained '+token)
    helper=ROOT/'prealpha/graphics_gd2/tools/deploy.ps1'
    check(sha(helper)=='1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307','pinned safety helper identity')
    check(".Replace('if($rel -ceq $relative)','if($rel -cin $relatives)')" in text,'snapshot excludes only exact two added files')
    result={'status':'PASS_READ_ONLY_CAPTURE_AND_DEPLOYMENT_CODE_REVIEW_NOT_LIVE',
      'build':base.relative_to(ROOT).as_posix()+'/build.json','build_sha256':sha(base/'build.json'),
      'checks':len(checks),'check_names':checks,'source_pins':len(manifest['source_pins']),
      'deployer_sha256':sha(deploy),'fixture_tester_sha256':sha(ROOT/'prealpha/sidejobs_s26/restart/test_deploy.py'),
      'reviewer_sha256':sha(Path(__file__)),
      'fixed_review_findings':['analyze.py test dependency is pinned in final manifest; original capture_01 superseded','capture_04 uses source-backed stable EntityID.hash and regressions instead of temporary userdata string identity; capture_03 superseded'],
      'scope':'Read-only helper and installer code/proof binding. Main must separately obtain complete matching fixture PASS and unsandboxed actual closed-game Validate/Install/ValidateRollback.',
      'limits':['Unknown or inaccessible getters are recorded, not replaced by fabricated state.',
                'Private native stock/UI field access is live-unverified; empty collection versus unavailable access remains distinct.',
                'No graph-retirement or reward-history proof; candidate dispositions never authorize restart.',
                'Stable repeated reads are not an atomic engine transaction.',
                'Observers are inert after Stop/Capture but remain registered until game/module teardown.'],
      'game_writes':False,'save_writes':False,'runtime_changes':False}
    out=ROOT/f'research/sidejobs_s26/services/capture_review_{revision}.json';assert not out.exists()
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('status','build_sha256','checks','source_pins','deployer_sha256','fixture_tester_sha256')}))
if __name__=='__main__':main(sys.argv[1])

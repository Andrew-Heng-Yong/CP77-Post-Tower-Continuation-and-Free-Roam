"""Bounded one-config fixtures + existing Lua source profile test; no real install."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys
H=Path(__file__).resolve().parent;P=H.parent;Q10=P.parent/'quest_restoration_qr10'
PS=r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
sys.path.insert(0,str(Q10));import test_diagnostics as lua_tests
FACT='phonecall_player_with_muamar_el_capitan_reyes'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def main():
    out=H/'fixtures/run_01';assert not out.exists();out.mkdir(parents=True);checks=[];calls=[]
    script=H/'deploy_profile.ps1';script_sha=sha(script);base=read(H/'diagnostics_manifest_01.json')
    profile=read(H/'package'/base['files'][0]['path'])
    l,g,m=lua_tests.runtime((Q10/'candidate_02/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/init.lua').read_text(),config=profile)
    g.loaded();path=m.start('D00E','synthetic El Capitan',120)
    assert m.status()['state']=='RECORDING'and g.calls.fact==1
    g.facts[FACT]=1;lua_tests.tick(g);g.facts[FACT]=0;lua_tests.tick(g);m.stop('SYNTHETIC_STOP')
    changes=lua_tests.events(g,path,'FACT_SAMPLE_CHANGE')
    assert len(changes)==2 and all(r['data']['fact']==FACT and r['profile']=='D00E'for r in changes)
    assert g.registerCalls==0 and not lua_tests.events(g,path,'FACT_DELIVERY')
    checks.extend(['D00E actual Lua source starts with one baseline getter','El Capitan changes sampled in both directions','no native subscription/event claim'])
    old=read(Path(base['game_root'])/base['files'][0]['path']);new=copy.deepcopy(profile);new['profiles'].pop('D00E');assert new==old
    checks.append('only profiles/D00E added; existing config preserved')
    def make(name):
        r=out/name;r.mkdir();j=copy.deepcopy(base);j['package_root']=str(r/'package');j['proofs']=[]
        for x in j['files']:
            put(r/'game'/x['path'],(Path(base['game_root'])/x['path']).read_bytes());put(r/'package'/x['path'],(H/'package'/x['path']).read_bytes())
        for x in j['required_files']:
            b=(Path(base['game_root'])/x['path']).read_bytes()if x['path'].endswith('/init.lua')else('SYNTHETIC:'+x['path']).encode()
            p=r/'game'/x['path'];put(p,b);x['bytes']=len(b);x['sha256']=sha(p)
        for x in j['protected_saves']+j['working_save_files']:
            p=r/'saves'/x['path'];put(p,('SYNTHETIC:'+x['path']).encode());x['sha256']=sha(p);x['bytes']=p.stat().st_size
        put(r/'game/unknown_mod.txt',b'KEEP');put(r/'game'/Path(j['files'][0]['path']).parent/'QR10_capture_keep.jsonl',b'KEEP_LOG')
        (r/'manifest.json').write_text(json.dumps(j,indent=2)+'\n');return r,j
    def snapshot(r):return{p.relative_to(r).as_posix():sha(p)for p in r.rglob('*')if p.is_file()}
    def call(r,action,extra=(),ok=True):
        args=[PS,'-NoProfile','-File',str(script),'-Action',action,'-FixtureRoot',str(r),'-FixtureManifest',str(r/'manifest.json'),'-FixtureManifestSHA',sha(r/'manifest.json'),*extra]
        z=subprocess.run(args,capture_output=True,text=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        calls.append({'case':r.name,'action':action,'extra':list(extra),'exit':z.returncode,'stdout':z.stdout,'stderr':z.stderr[-3000:]})
        assert(z.returncode==0)==ok,(r.name,action,z.stdout,z.stderr)
    r,j=make('normal');before_game=snapshot(r/'game');before_saves=snapshot(r/'saves')
    call(r,'Preflight');call(r,'Install');call(r,'Verify');call(r,'ValidateRollback')
    changed=[p for p,v in snapshot(r/'game').items()if before_game.get(p)!=v]
    assert changed==[j['files'][0]['path']]and snapshot(r/'saves')==before_saves
    checks.append('one-file normal install + verify + rollback-ready; saves/Lua/Core/logs preserved')
    call(r,'Rollback');call(r,'Verify',['-ExpectedState','Before'])
    assert snapshot(r/'game')==before_game and snapshot(r/'saves')==before_saves
    checks.append('rollback restores exact previous configuration only')
    r,j=make('crash');a=snapshot(r/'game');s=snapshot(r/'saves')
    call(r,'Install',['-FailurePoint','CrashAfterFirstReplace'],ok=False);call(r,'Recover');call(r,'Verify',['-ExpectedState','Before'])
    assert snapshot(r/'game')==a and snapshot(r/'saves')==s;checks.append('hard interruption restores previous profile with verified recovery')
    r,j=make('unknown');put(r/'game'/j['files'][0]['path'],b'UNKNOWN_CONFIG');a=snapshot(r/'game');call(r,'Install',ok=False)
    assert snapshot(r/'game')==a and not(r/'recovery').exists();checks.append('unknown installed config refused unchanged')
    r,j=make('lua_drift');x=next(x for x in j['required_files']if x['path'].endswith('/init.lua'));put(r/'game'/x['path'],b'UNKNOWN_LUA');a=snapshot(r/'game');call(r,'Install',ok=False)
    assert snapshot(r/'game')==a and not(r/'recovery').exists();checks.append('Lua drift refused before writes')
    r,j=make('scope');j['files'][0]['path']='r6/scripts/unauthorized.reds';(r/'manifest.json').write_text(json.dumps(j));a=snapshot(r/'game');call(r,'Install',ok=False)
    assert snapshot(r/'game')==a and not(r/'recovery').exists();checks.append('non-watch path refused')
    assert sha(script)==script_sha
    result={'status':'PASS_OFFLINE_PROFILE_AND_TRANSACTIONS','checks':checks,'actions':len(calls),'commands':calls,
        'installer_sha256':script_sha,'manifest_sha256':sha(H/'diagnostics_manifest_01.json'),'watch_sha256':sha(H/'package'/base['files'][0]['path']),
        'real_game_writes':0,'native_callback_delivery':'UNSUPPORTED_NOT_VERIFIED','live_sampling':'NOT_TESTED'}
    dest=H/'test_result_01.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({'status':result['status'],'checks':len(checks),'actions':len(calls)})
if __name__=='__main__':main()

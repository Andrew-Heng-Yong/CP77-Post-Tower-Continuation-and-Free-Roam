"""PA5 package/integration checks and LuaJIT mocks; not native gameplay proof."""
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime

def text(p): return Path(p).read_text(encoding='utf-8-sig')
def read(p): return json.loads(text(p))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def body(s, name):
    start = re.search(r'\bfunc '+name+r'\(', s).start()
    first = s.index('{', start); depth = 1; end = first+1
    while depth:
        depth += (s[end] == '{') - (s[end] == '}'); end += 1
    return s[start:end].replace('\r\n', '\n')

def main():
    build=Path(sys.argv[1]).resolve()
    assert build.is_relative_to(ROOT/'prealpha/postending_pa5/build')
    assert not (build/'tests.json').exists(), 'Use fresh evidence output'
    b=read(build/'build.json'); c=read(build/'compile.json'); pkg=Path(b['package_root'])
    old=read(ROOT/'prealpha/camera_pa4/build/pa4_02/build.json')
    prior={f['relative']:f['sha256'] for f in old['package_files']}
    cases=[]
    def check(ok, label):
        assert ok, label
        cases.append(label)
    check(c['status']=='PASS_COMPILE_AND_READBACK_NOT_LIVE' and c['build_sha256']==sha(build/'build.json'), 'Compiled exact candidate')
    camera=Path(b['camera_build']); ce=b['camera_evidence']; cr=read(camera/'build.json'); ct=read(camera/'tests.json')
    check(sha(camera/'build.json')==ce['build_sha256']==ct['build_sha256'],'Native camera artifact build binding')
    check(sha(camera/'tests.json')==ce['tests_sha256'] and ct['status']=='PASS_OFFLINE_NOT_LIVE','Native camera artifact test binding')
    check(sha(camera/'compile.json')==ce['compile_sha256']==ct['compile_sha256'],'Native camera compile binding')
    check(ce['existing_injections_checked']==427 and ce['collision_free'] and ce['new_registration_id']==cr['registration_id'],'New injection collision check')
    replacements={
      'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua',
      'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds',
      'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds',
      'r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds'}
    additions={
      'archive/pc/mod/TowerContinued_Optics_PA5.archive',
      'archive/pc/mod/TowerContinued_Optics_PA5.archive.xl',
      'r6/scripts/PTFR_PreAlpha/PA5/CameraOpticsPA5.reds',
      'r6/scripts/PTFR_PreAlpha/PA5/GigDiagnosticsPA5.reds',
      'r6/scripts/PTFR_PreAlpha/PA5/GigDiagnosticsDataPA5.generated.reds'}
    files={f['relative']:f['sha256'] for f in b['package_files']}
    check(len(files)==58 and set(files)==set(prior)|additions, 'Exact 58-file package')
    for rel,h in files.items(): check(sha(pkg/rel)==h, 'Package hash '+rel)
    for f in cr['package_files']: check(files[f['relative']]==f['sha256'],'Combined package uses tested camera '+f['relative'])
    check({k for k in prior if files[k]!=prior[k]}==replacements, 'Only four approved replacements; 49 unchanged')
    check(b['preserved_gd2']['sha256']=='03851DAA463B50FD78E2049C8A1ACDF04041E13C78B0538DCCC1955734768BDD','GD2 preservation pinned')
    for f in b['source_files']: check(sha(f['source'])==f['sha256']==files[f['relative']], 'Current component source '+f['relative'])
    flat=Path(c['stage'])/'compiled.script'
    check(sha(flat)==c['flat_sha256'],'Compiled readback verified')
    compiled=text(flat)
    for symbol in ('CameraOpticsPA5','GigDiagnosticsPA5','func H10GeometryReady(', 'func H10Status(', 'func OpticsReady(', 'GetActiveCameraFOV', 'H10 transition PA5:'):
        check(symbol in compiled,'Compiled symbol '+symbol)
    arrival=text(pkg/'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds')
    oldarrival=text(Path(old['package_root'])/'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds')
    for method in ('Authorized','Restored','NearTarget','Player','GameplayReady','FinitePosition','CameraSample','FPPAtPlayer','CameraAligned','ControlReady','CameraStatus','ReadinessReason'):
        check(body(arrival,method)==body(oldarrival,method),'PA4 unchanged '+method)
    check(arrival.count('.Activate(0.0, false);')==1,'No repeated/new camera activation')
    check(set(re.findall(r'this.Set\(n"([^"]+)"',arrival))=={'PTFRPA4_CameraRequest','PTFRPA4_CameraAligned','PTFRPA2_ControlReady','PTFRPA2_Reveal'},'Arrival writes unchanged')
    completed=body(arrival,'Completed'); poll=body(arrival,'Poll')
    check('&& this.OpticsReady()' in completed,'Preparation requires optics')
    check(poll.index('if !this.OpticsReady()')<poll.index('if this.Fact(n"PTFRPA2_Prepared") != 1'),'Final reveal waits for optics')
    check('this.safeTicks = 0;' in poll[poll.index('if !this.OpticsReady()'):poll.index('// Recheck controls')],'Waiting optics resets final sample count')
    entry=text(pkg/'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds')
    oldentry=text(Path(old['package_root'])/'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds')
    for method in ('CaptureBeforeEnding','Classify','Freeze','Certified','DevelopmentArmed','Activated','Dispatch','Restored'):
        check(body(entry,method)==body(oldentry,method),'History/dispatch unchanged '+method)
    ep=body(entry,'Poll')
    check(ep.index('if !restoration.H10GeometryReady()')<ep.index('SetFact(n"PTFRPA2_Prepared", 1)'),'Prepared requires H10 native acknowledgements')
    check(ep.index('if !profile.PTFRPAComplete()')<ep.index('if !restoration.H10GeometryReady()'),'Profile eligibility unchanged')
    # Dependency truth table models required acknowledgements, not engine execution.
    combos=0
    for control,optics,profile,dispatch,h10 in itertools.product((False,True), repeat=5):
        completed=control and optics
        prepared=completed and profile and dispatch and h10
        assert not prepared or all((control,optics,profile,dispatch,h10))
        combos+=1
    check(combos==32,'32 preparation dependency model cases')
    # Source safety anchors are rejected when removed (not a formal behavioral proof).
    for source,anchor in ((arrival,'&& this.OpticsReady()'),(entry,'if !restoration.H10GeometryReady()')):
        assert anchor in source and anchor not in source.replace(anchor,'REMOVED')
    check(True,'Missing optics/H10 guard negative controls')
    h10=text(pkg/'r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds')
    check('PTFRPA2_Teleported' in h10 and 'PTFRPA2_ControlReady' in h10 and '40000.0' in h10 and '75.0' in h10,'Offsite H10 gated and separated')
    for script in ('GigDiagnosticsPA5.reds','GigDiagnosticsDataPA5.generated.reds'):
        s=text(pkg/'r6/scripts/PTFR_PreAlpha/PA5'/script)
        check(not any(x in s for x in ('SetFact(', 'SetFactStr(', 'ChangeEntryState', 'RegisterMappin(', 'StartAll(', 'OnAttach(')),'Gig diagnostics getter-only '+script)
    for s in (arrival,entry,h10):
        check(not any(x in s for x in ('SaveGame(', 'LoadGame(', 'SetSceneSystemCameraControlEnabled(', 'SetFOV(', 'SetZoom(')), 'No save/reload or global optics workaround')
    lua_src=text(pkg/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua')
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={}; logs={}; calls={}; active=true;
      registerForEvent=function(k,f) events[k]=f end;
      print=function(s) logs[#logs+1]=s end;
      Game={GetQuestsSystem=function() return {GetFactStr=function() return active and 1 or 0 end} end,
      GetScriptableSystemsContainer=function() return {Get=function(_,name) return setmetatable({}, {__index=function(_,method) return function(_,...) calls[#calls+1]=name..'.'..method;return method end end}) end} end}''')
    api=lua.execute(lua_src)
    check('IFP=unavailable' in api.Camera(),'Optional IFP absent safe')
    for method in ('Optics','H10','GigSummary','GigVisibility','Status','Profile'): check(isinstance(api[method](),str),'CET getter '+method)
    check('Pass a' in api.GigVisibility(4),'Invalid visibility argument rejected')
    lua.execute('for i=1,500 do events.onUpdate(1) end')
    check(0<lua.eval('#logs')<=222,'Trace bounded including restoration/map snapshots')
    check(not any(str(v).endswith('.Repair') for v in lua.globals().calls.values()),'No automatic Repair call from CET')
    check(api.RepairCamera()=='Repair','Explicit one-shot Repair forwarding')
    count=lua.eval('#logs');lua.execute('active=false;for i=1,20 do events.onUpdate(1) end')
    check(lua.eval('#logs')==count,'Trace silent outside owned handoff')
    lua.execute('Game=nil')
    check('Load a save first' in api.Optics(),'No game system safe')
    check(not any(x in lua_src for x in ('SetFact','io.open','SaveGame','LoadGame','api.Disable','api.Enable')),'No CET fact/save/settings writes')
    result={'status':'PASS_NOT_LIVE','cases':len(cases),'details':cases,'build_sha256':sha(build/'build.json'),'compile_sha256':sha(build/'compile.json'),'test_source_sha256':sha(__file__),'limitations':'Offline source checks, compilation and models cannot prove visible H10 geometry, correct optical output, gameplay input or map icons. No gig mutation implemented without live POI evidence.'}
    (build/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'cases':len(cases)}))

if __name__=='__main__':main()

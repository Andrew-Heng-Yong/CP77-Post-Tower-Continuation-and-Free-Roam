"""PA4 artifact checks, LuaJIT mocks and explicitly non-engine state models."""
import hashlib
import itertools
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime

def text(p): return Path(p).read_text(encoding='utf-8-sig')
def read(p): return json.loads(text(p))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()

class Model:
    """Models the documented control flow; does not execute REDscript/native APIs."""
    def __init__(self, request=0, control=0):
        self.request, self.control = request, control
        self.aligned_fact, self.calls, self.ticks, self.reveal = 0, 0, 0, 0
    def tick(self, *, active=True, safe=True, near=True, valid=True, fpp_near=True,
             aligned=False, prepared=False, player_changed=False):
        if not active: return
        if player_changed: self.ticks = 0
        actual = valid and fpp_near and aligned
        if not self.control:
            if not safe or not near: self.ticks = 0; return
            if not actual and not self.request:
                if not valid or not fpp_near: self.ticks = 0; return
                self.request = 1; self.calls += 1; self.ticks = 0; return
            if not actual: self.ticks = 0; return
            self.ticks += 1
            if self.ticks >= 4:
                self.control = self.aligned_fact = 1; self.ticks = 0
            return
        if not prepared or not safe or not actual: self.ticks = 0; return
        self.ticks += 1
        if self.ticks >= 8: self.reveal = 1

def source_guards(s):
    anchors = [
        'epoch != this.epoch', 'if !this.Authorized()',
        'this.Fact(n"PTFRPA2_Finished") == 1', 'this.Fact(n"PTFRPA2_Fault") > 0',
        'if this.Fact(n"PTFRPA2_Teleported") != 1',
        'if this.Fact(n"PTFRPA3_CoverReleased") != 1',
        'if !this.GameplayReady(player) || !this.NearTarget(player)',
        'if !this.CameraAligned(player) && this.Fact(n"PTFRPA4_CameraRequest") == 0',
        '!this.CameraSample(player, active, fpp, dot) || !this.FPPAtPlayer(player, fpp)',
        'if this.sampledPlayer != player { this.safeTicks = 0;',
        'this.Set(n"PTFRPA4_CameraRequest", 1);',
        'player.GetFPPCameraComponent().Activate(0.0, false);',
        'this.safeTicks += 1; if this.safeTicks < 4',
        'this.safeTicks += 1; if this.safeTicks < 8',
        'if this.Fact(n"PTFRPA2_Prepared") != 1 { this.safeTicks = 0; return; }',
        'return this.GameplayReady(player) && this.CameraAligned(player);',
        'players.IsInFreeCamera() || players.GetLocalPlayerControlledGameObject() != player',
        't"GameplayRestriction.NoCameraControl"',
        'Vector4.DistanceSquared(active, fpp) <= 0.5625 && dot >= 0.97',
        'dot >= -1.001 && dot <= 1.001',
    ]
    assert all(a in s for a in anchors), 'Missing source guard'
    assert s.index('this.Set(n"PTFRPA4_CameraRequest", 1);') < s.index('.Activate(0.0, false);')
    assert s.count('.Activate(0.0, false);') == 1
    assert set(re.findall(r'this.Set\(n"([^"]+)"', s)) == {
        'PTFRPA4_CameraRequest','PTFRPA4_CameraAligned','PTFRPA2_ControlReady','PTFRPA2_Reveal'}
    for banned in ('SetSceneSystemCameraControlEnabled(', 'SetIsHighPriority(', 'Deactivate(',
                   'AbandonBlendCamera(', 'SceneDisableBlendingToStaticPosition(', 'SaveGame(',
                   'LoadGame(', 'RemoveStatusEffect(', 'Teleport(', 'LocalPlayerControlExistingObject('):
        assert banned not in s, banned
    return anchors

def main():
    build = Path(sys.argv[1]).resolve()
    assert build.is_relative_to(ROOT / 'prealpha/camera_pa4/build')
    assert not (build / 'tests.json').exists(), 'Never overwrite test evidence'
    b, c = read(build/'build.json'), read(build/'compile.json')
    old = read(ROOT/'prealpha/handoff_pa3/build/pa3_01/build.json')
    cases = []
    def check(value, label):
        assert value, label
        cases.append(label)
    check(c['status'] == 'PASS_COMPILE_AND_READBACK_NOT_LIVE' and c['build_sha256'] == sha(build/'build.json'), 'Exact build compiled and read back')
    pkg = Path(b['package_root']); prior = {f['relative']: f['sha256'] for f in old['package_files']}
    allowed = {'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds', 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua'}
    check(len(b['package_files']) == 53 and {f['relative'] for f in b['package_files']} == set(prior), '53-file set unchanged')
    changed = set()
    for f in b['package_files']:
        assert sha(pkg/f['relative']) == f['sha256']
        if f['sha256'] != prior[f['relative']]: changed.add(f['relative'])
    check(changed == allowed, 'Only Arrival and CET changed; archive and other51 files byte-identical')
    source = ROOT/'prealpha/camera_pa4/scripts/PreAlphaArrivalPA1.reds'
    lua_source = ROOT/'prealpha/camera_pa4/cet/init.lua'
    check(sha(source) == sha(pkg/'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds'), 'Current source matches compiled candidate')
    check(sha(lua_source) == sha(pkg/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua'), 'Current CET matches package')
    flat = Path(c['stage'])/'compiled.script'
    check(sha(flat) == c['flat_sha256'], 'Compiled readback hash valid')
    for symbol in ('func FPPAtPlayer(', 'func CameraAligned(', 'func CameraSample(', 'PTFRPA4_CameraRequest', 'PTFRPA4_CameraAligned', 'GetFPPCameraComponent().Activate', 'H10 transition PA4:'):
        check(symbol in text(flat), 'Compiled evidence: '+symbol)
    s = text(source); anchors = source_guards(s)
    for a in anchors:
        try: source_guards(s.replace(a, 'REMOVED_GUARD'))
        except AssertionError: pass
        else: raise AssertionError('Negative control missed '+a)
    check(True, f'{len(anchors)} removed-guard negative controls rejected')

    # Exhaustive once-only admission combinations, no live engine assumptions.
    combos = 0
    for active,safe,near,valid,fpp_near,aligned in itertools.product((False,True),repeat=6):
        m = Model(); m.tick(active=active,safe=safe,near=near,valid=valid,fpp_near=fpp_near,aligned=aligned)
        assert m.calls == int(active and safe and near and valid and fpp_near and not aligned)
        assert m.control == 0
        combos += 1
    check(True, f'{combos} admission model cases')
    m=Model()
    for _ in range(4): m.tick(aligned=True)
    check(m.control == 1 and m.calls == m.request == 0, 'Already aligned: four samples, no activation')
    m=Model(); m.tick()
    check(m.calls == m.request == 1 and not m.control, 'Issuing request is not acknowledged success')
    for _ in range(500): m.tick()
    check(m.calls == 1 and not m.control, 'Unsuccessful activation never retried or acknowledged')
    m=Model(request=m.request)
    for _ in range(5): m.tick()
    check(m.calls == 0 and not m.control, 'Saved request survives modeled reload without replay')
    for _ in range(3): m.tick(aligned=True)
    m.tick(safe=False,aligned=True)
    for _ in range(3): m.tick(aligned=True)
    check(not m.control, 'Unsafe sample resets initial consecutive count')
    m.tick(aligned=True)
    check(m.control == m.aligned_fact == 1 and m.ticks == 0, 'Stable alignment acknowledges after four fresh samples')
    for _ in range(10): m.tick(aligned=True,prepared=False)
    for _ in range(7): m.tick(aligned=True,prepared=True)
    check(not m.reveal, 'Final stage does not inherit initial sample count')
    m.tick(aligned=True,prepared=True,safe=False)
    for _ in range(7): m.tick(aligned=True,prepared=True)
    check(not m.reveal, 'Final unsafe interruption restarts eight-sample count')
    m.tick(aligned=True,prepared=True)
    check(m.reveal == 1, 'Final stage accepts eight current safe alignment samples')
    m=Model()
    for _ in range(3): m.tick(aligned=True)
    m.tick(aligned=True,player_changed=True)
    check(not m.control and m.ticks == 1, 'Player identity change resets sample count')
    def geometry(active,fpp,player,dot):
        finite = all(abs(v)<1000000 for p in (active,fpp,player) for v in p)
        return finite and -1.001<=dot<=1.001 and sum((fpp[i]-player[i])**2 for i in (0,1))<=16 and abs(fpp[2]-player[2])<=3 and sum((active[i]-fpp[i])**2 for i in range(3))<=.5625 and dot>=.97
    check(geometry((0,0,1.7),(0,0,1.7),(0,0,0),1), 'Aligned geometry accepted')
    for pos,dot in (((9,0,1.7),1),((math.nan,0,1.7),1),((0,math.inf,1.7),1),((0,0,1.7),math.nan),((0,0,1.7),.9),((0,0,1.7),math.inf)):
        assert not geometry(pos,(0,0,1.7),(0,0,0),dot)
    check(not geometry((9,0,1.7),(9,0,1.7),(0,0,0),1), 'Active/FPP agreement far from V still rejected')
    check(True, 'NaN/infinity/distant/misoriented negative geometry samples rejected')

    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('events={}; logs={}; active=true; registerForEvent=function(k,f) events[k]=f end; print=function(s) logs[#logs+1]=s end; Game={GetQuestsSystem=function() return {GetFactStr=function() return active and 1 or 0 end} end, GetScriptableSystemsContainer=function() return {Get=function() return {Status=function() return "Status" end} end} end}')
    api=lua.execute(text(lua_source))
    check('IFP=unavailable' in api.Camera(), 'Missing optional IFP safely handled')
    lua.execute('GetMod=function() return {api={GetCameraState=function() return {mode="native",ownsCamera=false,inputLocked=false} end}} end')
    check('IFP mode=native ownsCamera=false inputLocked=false' in api.Camera(), 'IFP state read without mutation')
    lua.execute('GetMod=function() error("not available") end')
    check('IFP=unavailable' in api.Camera(), 'IFP diagnostic exception contained')
    lua.execute('for i=1,500 do events.onUpdate(1) end')
    check(0 < lua.eval('#logs') <= 180, 'Automatic diagnostic trace bounded')
    n=lua.eval('#logs'); lua.execute('active=false; for i=1,20 do events.onUpdate(1) end')
    check(lua.eval('#logs') == n, 'No transition trace outside owned handoff')
    check(not any(x in text(lua_source) for x in ('SetFact','api.Disable','api.Enable','io.open','SaveGame','LoadGame')), 'CET diagnostics perform no gameplay or disk writes')
    result={'status':'PASS_NOT_LIVE','cases':len(cases),'details':cases,'build_sha256':sha(build/'build.json'),'compile_sha256':sha(build/'compile.json'),'runtime_source_sha256':sha(source),'test_source_sha256':sha(__file__),'limitations':'Models/mocks do not prove native camera selection, camera input, gameplay or save persistence. Live credits checkpoint test required. No shader investigation or save/reload automation.'}
    (build/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__ == '__main__': main()

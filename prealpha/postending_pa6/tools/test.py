"""Integrated PA6 artifact/source/Lua checks; does not simulate engine gameplay."""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime
def text(p): return Path(p).read_text(encoding='utf-8-sig')
def read(p): return json.loads(text(p))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()

def main():
    build=Path(sys.argv[1]).resolve()
    assert build.is_relative_to(ROOT/'prealpha/postending_pa6/build')
    assert not (build/'tests.json').exists(),'Use fresh evidence output'
    b=read(build/'build.json');c=read(build/'compile.json');pkg=Path(b['package_root'])
    old=read(ROOT/'prealpha/postending_pa5/build/pa5_03/build.json')
    checks=[]
    def check(ok,label):
        assert ok,label
        checks.append(label)
    check(c['status']=='PASS_COMPILE_AND_READBACK_NOT_LIVE' and c['build_sha256']==sha(build/'build.json'),'Combined compile exact build binding')
    expected={f['relative']:f['sha256'] for f in b['package_files']}
    prior={f['relative']:f['sha256'] for f in old['package_files']}
    repl={'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua','r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds','r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds'}
    addition='archive/pc/mod/0_TowerContinued_RogueLipsync_PA6.archive'
    check(len(prior)==58 and len(expected)==59,'Exact58 to59 package scope')
    check({p.relative_to(pkg).as_posix() for p in pkg.rglob('*') if p.is_file()}==set(expected),'No unexpected package files')
    check(set(expected)-set(prior)=={addition} and set(prior)-set(expected)==set(),'Exactly one addition, no removals')
    check({p for p in prior if prior[p]!=expected[p]}==repl,'Exactly three approved replacements')
    for rel,digest in expected.items():check(sha(pkg/rel)==digest,'Package hash '+rel)
    for row in b['source_files']:check(sha(row['source'])==row['sha256']==expected[row['relative']],'Source/package binding '+row['relative'])
    check(b['unchanged_files']==55 and b['archive_unchanged'],'Main and optics archives unchanged')
    rogue=Path(b['rogue_build']);rr=read(rogue/'build.json');rt=read(rogue/'tests.json');re=b['rogue_evidence']
    check(sha(rogue/'build.json')==re['build_sha256']==rt['build_sha256'],'Rogue exact-delta test/build binding')
    check(rt['status']=='PASS_EXACT_FAULT_REPAIR_OFFLINE_NOT_LIVE' and sha(rogue/'tests.json')==re['tests_sha256'],'Rogue test evidence bound')
    check(sha(rogue/'collision_audit.json')==re['collision_audit_sha256'] and read(rogue/'collision_audit.json')==b['archive_inventory'],'Archive priority audit bound')
    check(sha(pkg/addition)==rr['archive_sha256'],'Exact packed one-resource repair')
    check(rr['resource_count']==1 and rr['key']=='4595725825309208210','Exact local Rogue scene identity')
    check(len(b['archive_inventory'])==70 and sum(x['target_hits'] for x in b['archive_inventory'])==1,'Seventy source archives audited, one target collision')
    h10=pkg/'r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds'
    ht=read(ROOT/'research/postending_pa6/h10/tests.json')
    check(ht['status']=='PASS_SOURCE_AND_NATIVE_CONTRACT_NOT_LIVE' and sha(h10)==ht['source_sha256'],'H10 candidate bound to99 native/guard checks')
    lr=read(ROOT/'research/postending_pa6/logging/tests_01.json')
    lua_path=pkg/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua'
    check(lr['status']=='PASS_OFFLINE_NOT_LIVE' and sha(lua_path)==lr['files']['init.lua'],'Quiet CET bound to51 component checks')
    quiet=text(ROOT/'prealpha/postending_pa6/logging/PreAlphaEntry.reds').rstrip()
    check(sha(ROOT/'prealpha/postending_pa6/logging/PreAlphaEntry.reds')==lr['files']['PreAlphaEntry.reds'],'Logging Entry source bound')
    entry=text(pkg/'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds').rstrip()
    gate='    if !restoration.H10ActionsArmed() { this.detail = "Waiting for H10 interaction owner admission: " + restoration.H10Status(); return; }'
    check(entry.count(gate)==1 and entry.replace('\n'+gate,'')==quiet,'Integrated Entry exact delta is action admission gate only')
    check(entry.index('H10GeometryReady()')<entry.index('H10ActionsArmed()')<entry.index('SetFact(n"PTFRPA2_Prepared", 1)'),'Preparation requires both geometry and action permission')
    hs=text(h10)
    helper=hs[hs.index('public func H10ActionsArmed()'):hs.index('public func H10Status()')]
    check('PTFRB0H10P_Active' not in helper and 'PTFRPA2_Prepared' not in helper,'Street admission never waits for inside scene or Prepared')
    check('PTFRB0H10P_Enabled' in helper and 'PTFRB0H10P_Interrupted' in helper,'Native permission and interruption acknowledged')
    flat=text(Path(c['stage'])/'compiled.script')
    for symbol in ('func H10ActionsArmed(', 'Waiting for H10 interaction owner admission', 'class PTFR.ActivityStateR3.CameraOpticsPA5', 'class PTFR.ActivityStateR3.NativeGigsU9'):
        check(symbol in flat,'Combined compiled readback '+symbol)
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={}; logs={}; facts={}; calls=0;
      registerForEvent=function(k,f) events[k]=f end
      print=function(s) logs[#logs+1]=s end
      Game={GetQuestsSystem=function() return {GetFactStr=function(_,k) return facts[k] or 0 end} end,
      GetScriptableSystemsContainer=function() return {Get=function(_,name) return setmetatable({}, {__index=function(_,method) return function() calls=calls+1;return method..calls end end}) end} end}
      advance=function(n) for i=1,n do events.onUpdate(1) end end''')
    api=lua.execute(text(lua_path));lua.execute('advance(1200)')
    check(lua.eval('#logs')==0 and lua.eval('calls')==0,'Twenty minute default quiet; no verbose diagnostic polling')
    lua.execute('facts.PTFRPA2_Finished=1;facts.PTFRPA5O_Done=1;advance(1200)')
    check(lua.eval('#logs')==0,'Quiet after completed restoration')
    for m in ('Status','H10','Optics','GigVisibility'):check(isinstance(api[m](),str),'Manual diagnostic '+m)
    lua.execute('facts.PTFRPA2_Fault=1;advance(500);facts.PTFRPA5O_Fault=2;advance(500)')
    check(lua.eval('#logs')==2,'Owned fault notices exactly once each')
    api.Trace(180);lua.execute('advance(500)')
    check(2<lua.eval('#logs')<=224 and 'off' in api.TraceStatus(),'Explicit verbose trace bounded and stops')
    count=lua.eval('#logs');lua.execute('advance(1000)');check(lua.eval('#logs')==count,'No spontaneous trace restart')
    check(not any(x in text(lua_path) for x in ('SetFact','io.open','SaveGame(','LoadGame(','os.execute')),'No console/global/gameplay workaround')
    result={'status':'PASS_NOT_LIVE','cases':len(checks),'details':checks,'build_sha256':sha(build/'build.json'),'compile_sha256':sha(build/'compile.json'),'test_source_sha256':sha(__file__),'limitations':'Offline checks do not prove native resource selection, Rogue stability, H10 prompts, or save persistence. Native camera and four-marker user passes recorded separately.'}
    (build/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'cases':len(checks)}))

if __name__=='__main__':main()

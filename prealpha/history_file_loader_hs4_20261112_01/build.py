"""Build a two-file, global-latest HS4 successor without modifying the game."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
from difflib import unified_diff

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'history_capture_hs3_20261112_01'
BASELINE=BASE/'deployment_01/installed_manifest_01.json'
PIN='374B0E9E20240DB13BB9878E03280E9282857D99293D8008CABE387952ACF4D7'
RED='r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds'
LUA='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua'
ARCHIVE='archive/pc/mod/zzzz_PTFR_Combined.archive'

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,data):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,indent=2);f.write('\n')
def plain(p):
    for x in (p,*p.parents):assert not x.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,x
def one(text,a,b):
    assert text.count(a)==1,a[:160]
    return text.replace(a,b,1)
def baseline():
    assert sha(BASELINE)==PIN
    m=read(BASELINE);assert m['core_epoch']=='HS3_NATIVE_HISTORY_CAPTURE'
    game=Path(m['game_root'])
    for r in m['core_files']+m['required_files']:
        p=game/r['path'];plain(p);assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'],p
    return m,game

def edit_red(old):
    legacy=(HERE/'global_legacy_members.reds').read_text()
    members=(HERE/'global_capture_members.reds').read_text().replace('  // PACKET_READERS_HS4',(HERE/'packet_readers.reds').read_text())
    text=one(old,'public class SnapshotStateHS1 extends ScriptableSystem {','public class SnapshotStateHS1 extends ScriptableSystem {\n'+legacy)
    text=one(text,'  private func NativeHistoryCurrentHS3() -> Bool {','''  private func NativeHistoryCurrentHS3() -> Bool {
    let history=CaptureArchiveHS3.Get(this.GetGameInstance());
    if IsDefined(history) && history.GlobalFileReadyHS4() { return true; }''')
    text=one(text,'return !this.faulted && this.ready && this.frozen && this.exported;',
        'return !this.faulted && this.ready && this.frozen && this.exported && this.HistoryFileReadyHS4();')
    text=one(text,'public class CaptureArchiveHS3 extends ScriptableSystem {',
        (HERE/'global_requests.reds').read_text()+'\npublic class CaptureArchiveHS3 extends ScriptableSystem {\n'+members)
    text=one(text,'private func OnDetach() -> Void { this.running=false;this.epoch+=1;this.exported=false;this.jsonReady=false; }',
        'private func OnDetach() -> Void { this.ResetLatestHS4();this.running=false;this.epoch+=1;this.exported=false;this.jsonReady=false; }')
    text=one(text,'this.epoch+=1;this.exported=false;this.observedTicket=0;this.reportedMiss=0;this.ClearJSON();this.ResetCapture();',
        'this.epoch+=1;this.exported=false;this.observedTicket=0;this.reportedMiss=0;this.ClearJSON();this.ResetCapture();this.ResetLatestHS4();')
    text=one(text,'if this.committed && this.committedTicket==ticket && this.route==route && this.Shape() && legacy.NativeTicketHS3()==ticket {',
        'if !this.importedGlobalHS4 && this.committed && this.committedTicket==ticket && this.route==route && this.Shape() && legacy.NativeTicketHS3()==ticket {')
    text=one(text,'this.fileToken=n"";this.exported=false;this.ClearJSON();this.committed=true;this.ResetCapture();',
        'this.fileToken=n"";this.exported=false;this.ClearJSON();this.committed=true;this.ResetCapture();\n    this.importedGlobalHS4=false;this.nativeExportPendingHS4=true;this.ResetLatestHS4();')
    text=one(text,'    let ticket=this.Fact(n"PTFRHS3_GateTicket");let route=this.Fact(n"PTFRHS3_GateRoute");\n    if !this.GateOpen(ticket,route) {',
        '''    let ticket=this.Fact(n"PTFRHS3_GateTicket");let route=this.Fact(n"PTFRHS3_GateRoute");
    let exportLegacy=SnapshotStateHS1.Get(this.GetGameInstance());
    if this.nativeExportPendingHS4 && this.exported && IsDefined(exportLegacy) && exportLegacy.Exported() &&
      exportLegacy.NativeTicketHS3()==this.committedTicket { this.nativeExportPendingHS4=false; }
    if !this.GateOpen(ticket,route) {''')
    text=one(text,'this.clientLeaseHS4=n"";this.requireLatestHS4=false;this.fileLoadedHS4=false;this.ClearImportHS4();',
        'this.clientLeaseHS4=n"";this.requireLatestHS4=this.nativeExportPendingHS4;this.fileLoadedHS4=false;this.ClearImportHS4();')
    old_guard='this.committedTicket!=this.Fact(n"PTFRHS3_GateTicket")'
    assert text.count(old_guard)==2
    text=text.replace(old_guard,'(!this.GlobalFileReadyHS4() && '+old_guard+')')
    # All previously shipped persisted identities stay in their original order.
    old_fields=re.findall(r'\bpersistent let [^;]+;',old)
    new_fields=[x for x in re.findall(r'\bpersistent let [^;]+;',text) if not any(n in x for n in ('nativeExportPendingHS4:','importedGlobalHS4:'))]
    assert old_fields==new_fields
    return text

def compile_overlay(game,package,out):
    assert not out.exists()
    sources={p.resolve() for rel in ('r6/scripts','red4ext/plugins') for p in (game/rel).rglob('*.reds')}
    registry=None
    for p in sorted((game/'r6/logs').glob('redscript*.log'),key=lambda p:p.stat().st_mtime_ns,reverse=True):
        raw=p.read_text(encoding='utf-8-sig',errors='replace')
        registered={(game/'r6/scripts'/x.strip()).resolve() for x in raw.splitlines() if x.strip().lower().endswith('.reds')}
        if 'Compilation complete' in raw and registered==sources:registry=p;break
    assert registry is not None,'No completed registered-input log matches the full current source inventory'
    registry_hash=sha(registry)
    compiler=game/'engine/tools/scc.exe';caches=[game/'r6/cache'/x for x in ('final.redscripts','final.redscripts.ts')]
    pins={}
    for p in sorted(sources|{compiler,*caches}):plain(p);pins[p.relative_to(game).as_posix()]=sha(p)
    (out/'cache').mkdir(parents=True)
    for p in caches:shutil.copyfile(p,out/'cache'/p.name)
    staged={}
    for p in sorted(sources):
        rel=p.relative_to(game).as_posix();src=package/rel if rel==RED else p;dest=out/'scripts'/rel
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);staged[rel]=sha(dest)
    paths=out/'compile_paths.txt';paths.write_bytes(b'');target=out/'cache/compiled.redscripts'
    command=[compiler,'-compile',out/'scripts','-compilePathsFile',paths,'-customCacheDir',out/'cache','-outputCacheFile',target,out/'cache/final.redscripts']
    result=subprocess.run(list(map(str,command)),capture_output=True,encoding='utf-8',errors='replace',timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
    log=result.stdout+result.stderr;(out/'scc.log').write_text(log,encoding='utf-8')
    assert sha(registry)==registry_hash and all(sha(game/p)==h for p,h in pins.items())
    passed=result.returncode==0 and 'Compilation complete' in log and target.is_file()
    write(out/'result.json',{'status':'PASS' if passed else 'FAIL','source_count':len(staged),'input_pins':pins,'staged_hashes':staged,
        'registry':str(registry),'registry_sha256':registry_hash,'compiled_sha256':sha(target) if passed else None})
    if not passed:raise RuntimeError(log[-13000:])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,default=1);a=ap.parse_args()
    out=HERE/f'candidate_{a.attempt:02}';assert not out.exists()
    m,game=baseline();old=(game/RED).read_text(encoding='utf-8')
    catalogue=read(BASE/'evidence_01/catalogue.json');assert sha(BASE/'evidence_01/catalogue.json')==read(BASE/'checkpoint.json')['artifacts']['evidence_01/catalogue.json']
    fragment=(HERE/'latest.lua').read_text().replace('__FP1__','43C49F8FA1833C3FB2EF34381A2847CDF771B2EC86A01CFD9CB03702B76A8C6F')
    fragment=fragment.replace('__FP3__',catalogue['fingerprint']).replace('__COUNT3__',str(sum(len(catalogue[k]) for k in ('journals','facts','items'))))
    lua=(game/LUA).read_text(encoding='utf-8')
    lua=one(lua,'registerForEvent("onUpdate",function(dt)',fragment+'\nregisterForEvent("onUpdate",function(dt)')
    lua=one(lua,'time=time+dt;for _,c in ipairs(channels) do update(c) end',
        'time=time+dt;if not latestUpdate() then for _,c in ipairs(channels) do update(c) end end')
    lua=one(lua,'registerForEvent("onShutdown",function() for _,c in ipairs(channels) do c.work=nil end end)',
        'registerForEvent("onShutdown",function() latest=nil;for _,c in ipairs(channels) do c.work=nil end end)')
    edited={RED:edit_red(old),LUA:lua};package=out/'package';patch=[]
    for r in m['core_files']:
        rel=r['path'];dest=package/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        if rel in edited:
            dest.write_text(edited[rel],encoding='utf-8',newline='\n')
            patch.extend(unified_diff((game/rel).read_text(encoding='utf-8').splitlines(keepends=True),edited[rel].splitlines(keepends=True),'a/'+rel,'b/'+rel))
        else:shutil.copyfile(game/rel,dest);assert sha(dest)==r['sha256']
    (out/'source.patch').write_text(''.join(patch),encoding='utf-8')
    compile_overlay(game,package,HERE/f'compile_{a.attempt:02}')
    rows=[{'path':r['path'],'bytes':(package/r['path']).stat().st_size,'sha256':sha(package/r['path'])} for r in m['core_files']]
    write(out/'manifest.json',{'core_epoch':'HS4_GLOBAL_LATEST_HISTORY','predecessor_epoch':m['core_epoch'],'baseline_sha256':sha(BASELINE),
        'core_files':rows,'required_files':m['required_files'],'changed_paths':[RED,LUA],'archive_unchanged':sha(package/ARCHIVE)==m['archive_sha256'],
        'compile_sha256':sha(HERE/f'compile_{a.attempt:02}/result.json'),'installed':False,'game_writes':0,'save_writes':0})
    baseline();print(f'Compiled candidate_{a.attempt:02}; only snapshot REDscript and CET loader changed.')

if __name__=='__main__':main()

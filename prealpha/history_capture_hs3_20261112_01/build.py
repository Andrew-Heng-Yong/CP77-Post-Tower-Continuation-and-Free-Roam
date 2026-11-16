"""Stage a complete successor and compile registered scripts only in the workspace."""
import argparse
import json
import re
import shutil
import subprocess
from difflib import unified_diff
from common import HERE, BASE, ROOT, MANIFEST, RED, LUA, ARCHIVE, baseline, read, sha, write, one, plain


def quote(s): return json.dumps(s, ensure_ascii=True)


def lookup(name, values):
    """Balanced dispatch avoids a linear scan of thousands of definitions."""
    lines = []
    def emit(label, lo, hi, public=False):
        head = f'  {"public" if public else "private"} static func {label}(i: Int32) -> String {{'
        if hi-lo <= 32:
            body = '\n'.join(f'    if i=={i} {{ return {quote(values[i])}; }}' for i in range(lo,hi))
            lines.append(head+'\n'+body+'\n    return "";\n  }')
        else:
            mid=(lo+hi)//2; left=label+'A';right=label+'B'
            lines.append(head+f'\n    if i<{mid} {{ return SnapshotDataHS3.{left}(i); }}\n    return SnapshotDataHS3.{right}(i);\n  }}')
            emit(left,lo,mid);emit(right,mid,hi)
    emit(name,0,len(values),True)
    return '\n'.join(lines)


def definitions(data):
    journal=data['journals'];facts=data['facts'];items=data['items']
    rows=[{'kind':'journal',**x} for x in journal]+[{'kind':'fact','name':x} for x in facts]+[{'kind':'item_quantity','id':x} for x in items]
    header = f'''public abstract class SnapshotDataHS3 {{
  public static func Fingerprint() -> CName {{ return n"{data['fingerprint']}"; }}
  public static func JournalCount() -> Int32 {{ return {len(journal)}; }}
  public static func FactCount() -> Int32 {{ return {len(facts)}; }}
  public static func ItemCount() -> Int32 {{ return {len(items)}; }}
  public static func Count() -> Int32 {{ return {len(rows)}; }}
'''
    return header+'\n'.join(lookup(n,v) for n,v in [
        ('Path',[x['path'] for x in journal]), ('Class',[x['class'] for x in journal]),
        ('FactName',facts),('Item',items),('Definition',[json.dumps(x,separators=(',',':'),ensure_ascii=False) for x in rows])])+'\n}\n'


def edit_legacy(source):
    text=one(source,'public class SnapshotStateHS1 extends ScriptableSystem {',
             'public class SnapshotStateHS1 extends ScriptableSystem {\n'+(HERE/'legacy_members.reds').read_text())
    # Keep formerly exposed methods callable, but retire the local test import.
    start=text.index('  public func CanCompareRetainedHistory()')
    end=text.index('  private func HasAdmissionRow(',start)
    text=text[:start]+'''  public func CanCompareRetainedHistory() -> Bool { return false; }
  public func RetainedHistoryRowJSON(i: Int32) -> String { return ""; }
  public func AckFileWithRetainedHistory(epoch: Int32,revision: Int32,token: String,retainedRevision: Int32) -> Bool { return false; }

'''+text[end:]
    text=one(text,'    this.useRetainedHistory = false;','    this.useRetainedHistory = false;\n    this.exportLeaseHS3=n"";')
    text=one(text,'    if !this.Ready() || i < 0 || i >= ArraySize(this.rows) { return false; }',
             '    if !this.Ready() || !this.NativeHistoryCurrentHS3() || i < 0 || i >= ArraySize(this.rows) { return false; }')
    start=text.index('    if !this.faulted && this.frozen && !this.Boundary() {')
    end=text.index('    this.Register(); if this.running { this.Schedule(); }',start)
    text=text[:start]+'''    // A frozen certificate belongs to the loaded save. Early zero-valued
    // boundary reads are not evidence that it belongs to another branch.
    // Unfrozen legacy rows remain evidence only; Poll cannot promote them
    // after a cutoff. A genuine native HS3 gate can capture a new baseline.
'''+text[end:]
    text=one(text,'    this.useRetainedHistory=useRetained;','    if useRetained { return false; }\n    this.useRetainedHistory=false;')
    text=one(text,'      this.retainedHistoryCandidate=Equals(this.origin,n"post_ending_fallback") && this.Tower() && this.Shape(this.previousRows);',
             '      this.retainedHistoryCandidate=false;')
    text=one(text,'  let recovery=SnapshotRecoveryHS1.Get(gameInstance);if IsDefined(recovery) { recovery.Restored(); }',
             '  let recovery=SnapshotRecoveryHS1.Get(gameInstance);if IsDefined(recovery) { recovery.Restored(); }\n'
             '  let history=CaptureArchiveHS3.Get(gameInstance);if IsDefined(history) { history.Restored(); }')
    original=re.findall(r'\bpersistent let [^;]+;',source)
    revised=re.findall(r'\bpersistent let [^;]+;',text)
    assert [x for x in revised if 'nativeTicketHS3:' not in x]==original
    assert text.split('public abstract class SnapshotDataHS1 {',1)[1].split('// ORIGINAL: r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotStateHS1.reds',1)[0] == source.split('public abstract class SnapshotDataHS1 {',1)[1].split('// ORIGINAL: r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotStateHS1.reds',1)[0]
    return text


def compile_overlay(game, package, out):
    assert not out.exists(), 'Fresh compile output required'
    registry=game/'r6/logs/redscript_rCURRENT.log';plain(registry)
    registry_hash=sha(registry)
    registered={(game/'r6/scripts'/line.strip()).resolve() for line in registry.read_text(encoding='utf-8-sig').splitlines() if line.strip().lower().endswith('.reds')}
    discovered={p.resolve() for rel in ('r6/scripts','red4ext/plugins') for p in (game/rel).rglob('*.reds')}
    assert registered==discovered and game/RED in registered
    compiler=game/'engine/tools/scc.exe';caches=[game/'r6/cache'/x for x in ('final.redscripts','final.redscripts.ts')]
    pins={}
    for path in sorted(registered|{compiler,*caches}):
        plain(path);pins[path.relative_to(game).as_posix()]=sha(path)
    (out/'cache').mkdir(parents=True)
    for path in caches: shutil.copyfile(path,out/'cache'/path.name)
    staged={}
    for path in sorted(registered):
        relative=path.relative_to(game).as_posix();src=package/relative if relative==RED else path
        dest=out/'scripts'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);staged[relative]=sha(dest)
        assert staged[relative]==(sha(src) if relative==RED else pins[relative])
    paths=out/'compile_paths.txt';paths.write_bytes(b'')
    target=out/'cache/compiled.redscripts'
    command=[compiler,'-compile',out/'scripts','-compilePathsFile',paths,'-customCacheDir',out/'cache',
             '-outputCacheFile',target,out/'cache/final.redscripts']
    result=subprocess.run(list(map(str,command)),capture_output=True,encoding='utf-8',errors='replace',timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
    log=result.stdout+result.stderr;(out/'scc.log').write_text(log,encoding='utf-8')
    assert sha(registry)==registry_hash and all(sha(game/p)==h for p,h in pins.items())
    passed=result.returncode==0 and 'Compilation complete' in log and target.is_file()
    write(out/'result.json',{'status':'PASS' if passed else 'FAIL','source_count':len(staged),'input_pins':pins,
                           'registry_sha256':registry_hash,'staged_hashes':staged,'compiled_sha256':sha(target) if passed else None})
    if not passed: raise RuntimeError(log[-12000:])
    return len(staged)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,default=1);a=ap.parse_args()
    out=HERE/f'candidate_{a.attempt:02}';compile_out=HERE/f'compile_{a.attempt:02}'
    assert not out.exists() and not compile_out.exists()
    m,game=baseline();plan=read(HERE/'evidence_01/plan.json')
    assert plan['baseline_sha256']==sha(MANIFEST) and plan['catalogue_sha256']==sha(HERE/'evidence_01/catalogue.json')
    data=read(HERE/'evidence_01/catalogue.json');original=(game/RED).read_text(encoding='utf-8')
    runtime=(HERE/'capture_hs3.reds').read_text(encoding='utf-8')
    edited={RED:edit_legacy(original)+'\n'+definitions(data)+'\n'+runtime,
            LUA:(HERE/'export.lua').read_text(encoding='utf-8').replace('__HS3_COUNT__',str(len(data['journals'])+len(data['facts'])+len(data['items'])))}
    assert '20261111T224622Z_159_1' not in edited[LUA] and 'retainedComparison' not in edited[LUA]
    package=out/'package';patch=[]
    for row in m['core_files']:
        rel=row['path'];dest=package/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        if rel==ARCHIVE: continue  # A fresh fully-read-back successor is packed separately.
        if rel in edited:
            dest.write_text(edited[rel],encoding='utf-8',newline='\n')
            patch.extend(unified_diff((game/rel).read_text(encoding='utf-8').splitlines(keepends=True),
                                     edited[rel].splitlines(keepends=True),'a/'+rel,'b/'+rel))
        else:
            shutil.copyfile(game/rel,dest);assert sha(dest)==row['sha256']
    (out/'source.patch').write_text(''.join(patch),encoding='utf-8')
    count=compile_overlay(game,package,compile_out)
    write(out/'scripts.json',{'status':'PASS_OFFLINE_COMPILE','sources':count,'baseline_sha256':sha(MANIFEST),
                             'changed_files':{p:sha(package/p) for p in edited},'catalogue_fingerprint':data['fingerprint'],
                             'legacy_indices_and_fields_preserved':True,'game_writes':0,'save_writes':0})
    print(json.dumps({'candidate':str(out),'sources':count,'status':'PASS_OFFLINE_COMPILE'}))


if __name__=='__main__':main()

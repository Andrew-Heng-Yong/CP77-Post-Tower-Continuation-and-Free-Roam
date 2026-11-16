"""Independent selected-package and actual-source predicate checks for HS4."""
import json
import re
from build import HERE, BASE, BASELINE, RED, LUA, ARCHIVE, baseline, read, sha, write


def main():
    out=HERE/'verification_03';assert not out.exists();out.mkdir()
    m,game=baseline();package=HERE/'candidate_02/package'
    old=(game/RED).read_text(encoding='utf-8');new=(package/RED).read_text(encoding='utf-8')
    checks=[]
    def check(name,value):assert value,name;checks.append(name)
    added=('nativeExportPendingHS4:','importedGlobalHS4:')
    check('Every original persistent field retained with only two new Boolean bookkeeping fields',
        re.findall(r'\bpersistent let [^;]+;',old)==[x for x in re.findall(r'\bpersistent let [^;]+;',new) if not any(y in x for y in added)] and
        all(('private persistent let '+x+' Bool;') in new for x in added))
    for start,end in [('public abstract class SnapshotDataHS1 {','// ORIGINAL: r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotStateHS1.reds'),
                      ('public abstract class SnapshotDataHS3 {','public struct CaptureJournalHS3 {')]:
        check(start+' remains byte-identical',old.split(start,1)[1].split(end,1)[0]==new.split(start,1)[1].split(end,1)[0])
    check('Archive and XL registrations unchanged',sha(package/ARCHIVE)==m['archive_sha256'] and
        sha(package/(ARCHIVE+'.xl'))==sha(game/(ARCHIVE+'.xl')))
    manifest=read(HERE/'candidate_02/manifest.json')
    paths={p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file()}
    check('Exact 51-path package',paths=={r['path'] for r in m['core_files']} and len(paths)==51)
    changed=set()
    for r in manifest['core_files']:
        p=package/r['path'];assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
        if sha(p)!=sha(game/r['path']):changed.add(r['path'])
    check('Only snapshot REDscript and CET loader differ',changed=={RED,LUA})
    compiled=read(HERE/'compile_02/result.json')
    check('All 148 current registered sources compile for this exact script',compiled['status']=='PASS' and compiled['source_count']==148 and compiled['staged_hashes'][RED]==sha(package/RED))
    proof=read(HERE/'verification_02/latest_fixtures.json')
    check('20 actual-Lua fixtures bind this exact loader',proof['count']==20 and proof['candidate_sha256']==sha(package/LUA) and proof['tool_sha256']==sha(HERE/'test_latest.py'))
    additions='\n'.join((HERE/name).read_text() for name in ('global_capture_members.reds','global_legacy_members.reds','packet_readers.reds'))
    check('Import additions never write native facts/journals/items/owners',not any(x in additions for x in ('.SetFact(','.SetFactStr(','.ChangeEntryState(','.GiveItem(','.RemoveItem(','.ResetKillCount(','.Reactivate(')))
    check('No former function-returned struct field crash pattern',not re.search(r'\.(ReadRow|ReadJournal|AdmissionRow)\([^\n]*?\)\.(states|facts|state|counter)',new))
    check('Saved import marker prevents an imported baseline acknowledging a new native gate',
        'if !this.importedGlobalHS4 && this.committed && this.committedTicket==ticket' in new and 'this.importedGlobalHS4=true;' in new)
    shortcut=new.split('if !this.importedGlobalHS4 && this.committed && this.committedTicket==ticket',1)[1].split('\n    }',1)[0]
    check('Native acknowledgement remains after the guarded shortcut', 'SetFact(n"PTFRHS3_GateResult",1)' in shortcut)
    native=new.split('private func OnCapturePollHS3(',1)[1].split('private func BoolJSON',1)[0]
    commit=native.index('this.importedGlobalHS4=false;this.nativeExportPendingHS4=true;this.ResetLatestHS4();')
    check('Fresh capture resets imported marker and holds file loading before native acknowledgement',commit<native.index('SetFact(n"PTFRHS3_GateResult",1)',commit))
    check('Native export hold needs both exact capture channels acknowledged',
        'this.nativeExportPendingHS4 && this.exported && IsDefined(exportLegacy) && exportLegacy.Exported() &&' in native and
        'exportLegacy.NativeTicketHS3()==this.committedTicket { this.nativeExportPendingHS4=false; }' in native and
        new.count('this.nativeExportPendingHS4=false;')==1)
    may=new.split('public func MayLoadLatestHS4() -> Bool {',1)[1].split('\n  }',1)[0]
    check('Global load blocked during the native gate or a pending native export',
        '!this.nativeExportPendingHS4 && this.Fact(n"PTFRHS3_GateOpen")==0' in may)
    pub=new.split('private func OnFileFinishRequestHS4(',1)[1].split('\n  }',1)[0]
    check('Complete staged row counts checked before either baseline is published',
        pub.index('this.legacyCursorHS4!=SnapshotDataHS1.Count()')<pub.index('legacy.ApplyGlobalHistoryHS4')<pub.index('this.journals=this.importedJournalsHS4'))
    check('Requests reject save-switch leases and native-gate changes',
        'this.ClientHS4(epoch,lease) && this.MayLoadLatestHS4() && !this.importFaultHS4' in new and
        'this.running && epoch==this.epoch && NotEquals(lease,"") && Equals(this.clientLeaseHS4,StringToName(lease))' in new)
    # Execute the actual scalar packet validation expression at its boundaries.
    predicate=new.split('private func JournalValuesHS4(',1)[1].split('return ',1)[1].split(';',1)[0]
    expr=compile(predicate.replace('&&',' and ').replace('||',' or '),'<actual JournalValuesHS4>','eval')
    def accepts(state,counter,optional,tracked):return eval(expr,{'__builtins__':{}},locals())
    check('Actual packet predicate preserves unknowns, Active delivery and counter 97',accepts(-1,-1,-1,-1) and accepts(2,97,0,1))
    check('Actual packet predicate rejects state/counter/flag overflow ranges',not any((accepts(5,0,0,0),accepts(-2,0,0,0),accepts(2,-2,0,0),accepts(2,0,2,0),accepts(2,0,0,2))))
    # Restore never trusts persistent imported arrays for the new file-loaded flag.
    check('Every restore invalidates current file-load readiness and old queued operations',
        'this.ClearJSON();this.ResetCapture();this.ResetLatestHS4();' in new and
        'this.clientLeaseHS4=n"";this.requireLatestHS4=this.nativeExportPendingHS4;this.fileLoadedHS4=false;this.ClearImportHS4();' in new)
    write(out/'verification.json',{'status':'PASS_BOUNDED_GLOBAL_LATEST_SOURCE_AND_PACKAGE','checks':checks,'count':len(checks),
        'candidate':'candidate_02','tool_sha256':sha(__file__),'candidate_script_sha256':sha(package/RED),'game_writes':0,'save_writes':0,
        'limits':'Source/predicate/fixture checks do not certify native engine scheduling, save serialization or resumed quest ownership.'})
    sources=[p for p in HERE.iterdir() if p.is_file() and p.name!='checkpoint.json']
    artifacts=['candidate_02/manifest.json','compile_02/result.json','verification_02/latest_fixtures.json','verification_03/verification.json']
    write(HERE/'checkpoint.json',{'status':'IMPLEMENTED_OFFLINE_VERIFIED_GLOBAL_LATEST','candidate':'candidate_02','baseline_manifest_sha256':sha(BASELINE),
        'selection_rule':'Global latest valid complete pre-ending capture; no per-character/run binding, explicitly requested by user.',
        'artifacts':{str(p):sha(HERE/p) for p in artifacts},'sources':{p.name:sha(p) for p in sources},
        'compiled_sources':148,'actual_lua_fixtures':20,'source_checks':len(checks),'deployment':'NOT_YET_PREPARED','gameplay':'PENDING'})
    baseline();print(json.dumps({'status':'PASS_BOUNDED_GLOBAL_LATEST_SOURCE_AND_PACKAGE','checks':len(checks)}))

if __name__=='__main__':main()

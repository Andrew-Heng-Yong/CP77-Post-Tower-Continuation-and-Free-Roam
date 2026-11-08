"""Create fresh QR14 transaction/test sources from inspected QR11 predecessors."""
from pathlib import Path
from prepare import sha

H = Path(__file__).resolve().parent
OLD = H.parent / 'quest_restoration_qr11'

def replace(s, before, after):
    assert before in s, before
    return s.replace(before, after)

def main():
    out = H / 'deploy_core.ps1'
    assert not out.exists()
    s = (OLD / 'deploy_diagnostics.ps1').read_text(encoding='utf-8-sig')
    s = replace(s, "[ValidateSet('Diagnostics')][string]$Component='Diagnostics'", "[ValidateSet('Core')][string]$Component='Core'")
    s = replace(s, "# QR11 preparation: real mutations require separate user authorization. Fixture mutation stays in QR11/fixtures.",
        "# QR14 preparation: real mutations require separate user authorization. Fixtures stay in QR14/fixtures.\n# Derived from inspected QR11 transaction; only three existing Core leaves may change.")
    s = replace(s, "$PinnedDiagnosticsManifestSHA='8B42EAC8C161256534DB26F859A62447E8A9921104929B10ADFF83020C1B2DD0'",
        "$PinnedCoreManifestSHA='" + sha(H / 'core_manifest_01.json') + "'")
    s = s.replace('Another QR11 deployment action', 'Another PTFR deployment action')
    s = s.replace('PTFR_QR11_JOURNAL_V1', 'PTFR_QR14_JOURNAL_V1')
    s = s.replace("'diagnostics_manifest_01.json'", "'core_manifest_01.json'")
    s = s.replace('$expectedManifestSHA=$PinnedDiagnosticsManifestSHA', '$expectedManifestSHA=$PinnedCoreManifestSHA')
    s = s.replace("'PTFR_QR11_DIAGNOSTICS_V1'", "'PTFR_QR14_CORE_V1'")
    s = s.replace("$manifest.source_epoch -cne 'QR8:02'", "$manifest.source_epoch -cne 'QR13:02' -or $manifest.predecessor_epoch -cne 'QR8:02'")
    s = s.replace("'recovery/diagnostics'", "'recovery/core'").replace("'recovery/diagnostics_qr10d01_01'", "'recovery/core_qr13_02_01'")
    start = s.index("$wanted=@('bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/init.lua'")
    end = s.index("$script:journalPath=", start)
    s = s[:start] + """$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive','r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds')
if($manifest.files.Count -ne 51 -or $changes.Count -ne 3 -or @($manifest.files|Where-Object {$null -eq $_.before}).Count -or (@($changes.path|Sort-Object)-join ',') -cne (@($wanted|Sort-Object)-join ',')){throw 'Core51/three-existing-leaf scope drift'}
if(@($manifest.required_files|Where-Object {$managedSet.Contains($_.path)}).Count){throw 'Dependency overlaps managed paths'}
""" + s[end:]
    s = replace(s, " foreach($proof in $manifest.proofs){CheckFile $proof.path $proof.sha256}",
        " foreach($proof in $manifest.proofs){CheckFile $proof.path $proof.sha256}\n foreach($p in $manifest.compile_inputs.Keys){CheckFile $p $manifest.compile_inputs[$p]}")
    s = replace(s, ' CheckFile (Safe $worker $ready.fixture_result) $ready.fixture_result_sha256 -Fresh',
        " CheckFile (Safe $worker $ready.fixture_result) $ready.fixture_result_sha256 -Fresh\n CheckFile (Safe $worker $ready.independent_review) $ready.independent_review_sha256 -Fresh")
    s = replace(s, "'AfterFirstReplace','BeforeReceipt'", "'AfterFirstReplace','AfterSecondReplace','BeforeReceipt'")
    s = replace(s, "'CrashAfterFirstReplace','CrashBeforeReceipt'", "'CrashAfterFirstReplace','CrashAfterSecondReplace','CrashBeforeReceipt'")
    s = replace(s, "if($count -eq 1){Fault 'AfterFirstReplace'}", "if($count -eq 1){Fault 'AfterFirstReplace'};if($count -eq 2){Fault 'AfterSecondReplace'}")
    s = s.replace('# A two-file replacement', '# A three-file replacement').replace('globally atomic pair', 'globally atomic set')
    s = s.replace('No save backup or save restore action exists in this diagnostic installer.', 'No save backup or save restore action exists in this Core installer; prior master backups remain untouched.')
    out.write_text(s, encoding='utf-8')

    test = (OLD / 'test_deployment.py').read_text(encoding='utf-8-sig')
    test = test.replace('QR11/fixtures', 'QR14/fixtures').replace('Two real diagnostic payloads; synthetic Core/dependencies/save bytes.',
        'Broad state-machine cases use synthetic Core51 bytes; one integration case uses all actual QR8/QR13 package files. Saves/dependencies are synthetic.')
    test = test.replace("H/'deploy_diagnostics.ps1'", "H/'deploy_core.ps1'")
    test = test.replace("'diagnostics_manifest_01.json'", "'core_manifest_01.json'")
    test = replace(test, 'def make(name):', 'def make(name, actual=False):')
    a = test.index("        for row in m['files']:")
    b = test.index("        for row in m['required_files']:", a)
    test = test[:a] + """        m['compile_inputs']={};m['zip']='';m['zip_sha256']=None
        for row in m['files']:
            new=Path(base['package_root'])/row['path']
            old=H.parent/'quest_restoration_qr8/candidate_01/package'/row['path']
            old_data=old.read_bytes()if actual else ('SYNTHETIC_BEFORE:'+row['path']).encode()
            new_data=new.read_bytes()if actual else (('SYNTHETIC_AFTER:'if row['before']!=row['after']else'SYNTHETIC_BEFORE:')+row['path']).encode()
            put(root/'game'/row['path'],old_data);put(root/'package'/row['path'],new_data)
            row['before']=sha(root/'game'/row['path']);row['before_bytes']=len(old_data)
            row['after']=sha(root/'package'/row['path']);row['after_bytes']=len(new_data)
""" + test[b:]
    test = test.replace("root/'recovery/diagnostics", "root/'recovery/core").replace("r/'recovery/diagnostics", "r/'recovery/core")
    test = test.replace("for x in m['files']for side,field", "for x in m['files']if x['before']!=x['after']for side,field")
    test = test.replace("['AfterFirstBackup','AfterBackup','AfterStage','AfterFirstReplace','BeforeReceipt']", "['AfterFirstBackup','AfterBackup','AfterStage','AfterFirstReplace','AfterSecondReplace','BeforeReceipt']")
    test = test.replace("['AfterJournal','AfterFirstBackup','AfterBackup','AfterStage','AfterFirstReplace','BeforeReceipt']", "['AfterJournal','AfterFirstBackup','AfterBackup','AfterStage','AfterFirstReplace','AfterSecondReplace','BeforeReceipt']")
    test = test.replace('normal install exact two payloads', 'normal install exact three changed leaves / Core51')
    test = test.replace('rollback restores only B04', 'rollback restores only QR8 changed leaves')
    test = test.replace('restores B04:', 'restores QR8:').replace('action-start D01:', 'action-start QR13:')
    test = test.replace("'payloads':'Actual pinned QR10D01 candidate02 + QR9B04 diagnostics; other game/Core/save contents synthetic.'", "'payloads':'State-machine cases synthetic Core51; separate integration case actual pinned QR8/QR13 Core51. All saves/dependencies synthetic.'")
    point = test.index("    assert sha(SCRIPT)==source_sha,")
    test = test[:point] + """    r,m=make('actual_Core51',actual=True);before=protected(r,m)
    call(r,'Preflight');call(r,'Install');call(r,'Verify');call(r,'ValidateRollback')
    ck('actual full Core51 integration: exact QR13 bytes, three replacements',managed(r,m,'after')and len(list((r/'recovery/core/old').rglob('*.*')))==3)
    call(r,'Rollback');call(r,'Verify',['-ExpectedState','Before'])
    ck('actual full Core51 integration: exact QR8 rollback and all protections',managed(r,m,'before')and protected(r,m)==before)
""" + test[point:]
    (H / 'test_deployment.py').write_text(test, encoding='utf-8')
    print({'created': [str(out), str(H / 'test_deployment.py')], 'predecessor_sha256': sha(OLD / 'deploy_diagnostics.ps1')})

if __name__ == '__main__':
    main()

"""Fresh QR11 preparation. Reads installed files; writes only this new task."""
from pathlib import Path
import datetime, hashlib, json, sys
H=Path(__file__).resolve().parent;W=H.parents[1];Q10=H.parent/'quest_restoration_qr10';Q9=H.parent/'quest_restoration_qr9'
sys.path.insert(0,str(Q10))
from capture_baseline import sha,meta
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--resume',action='store_true');args=ap.parse_args()
    assert args.resume or not (H/'baseline.json').exists(),'Fresh output only'
    assert not (H/'deploy_diagnostics.ps1').exists(),'Never overwrite generated installer'
    old=read(Q10/'baseline.json');game=Path(old['game_root']);save=Path(old['save_root'])
    for p,digest in old['protected_sha256'].items():assert sha(p)==digest,p
    q10=read(Q10/'completion.json')
    for row in q10['artifacts']:assert sha(row['path'])==row['sha256'],row['path']
    saves={str(save/p):sha(save/p)for p,r in meta(save).items()if r['kind']=='file'}
    assert saves==old['save_sha256'],'Save drift since QR10: inspect rather than replace saves'
    save_rows={}
    for slot in ('ManualSave-23','ManualSave-24'):
        m=read(save/slot/'metadata.9.json')['Data']['metadata']
        save_rows[slot]={'path':str(save/slot),'metadata':{k:m.get(k)for k in ['name','timestampString','playthroughID','level','debugString','isPointOfNoReturn','isEndGameSave','playTime','finishedQuests']},
            'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size}for p in (save/slot).iterdir()if p.is_file()}}
    assert save_rows['ManualSave-24']['metadata']['name']=='ManualSave-24'
    assert save_rows['ManualSave-24']['metadata']['timestampString']=='16:37:02, 2.11.2026'
    assert save_rows['ManualSave-23']['metadata']['playthroughID']==save_rows['ManualSave-24']['metadata']['playthroughID']
    baseline={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'game_root':str(game),'save_root':str(save),
        'save_sha256':saves,'save_metadata':meta(save),'game_metadata':meta(game),'QR9_metadata':meta(Q9),'QR10_metadata':meta(Q10),
        'protected_sha256':old['protected_sha256'],'selected_saves':save_rows,'core_files':old['core_files'],'external_dependencies':old['external_dependencies'],
        'scope':'Offline installer fixtures + real read-only preflight; no real Install/Rollback/Recover, game/API launch, CUA, save/fact edits.'}
    if (H/'baseline.json').exists():
        pinned=read(H/'baseline.json')
        assert all(pinned[k]==baseline[k]for k in ('save_sha256','game_metadata','QR9_metadata','QR10_metadata'))
    else:(H/'baseline.json').write_text(json.dumps(baseline,indent=2)+'\n',encoding='utf-8')
    c=read(Q10/'manifest_02.json');required=[]
    for r in old['core_files']:required.append({'path':r['path'],'sha256':r['after'],'bytes':(game/r['path']).stat().st_size,'active_only':False})
    for r in old['external_dependencies']:required.append({'path':r['path'],'sha256':r['sha256'],'bytes':(game/r['path']).stat().st_size,'active_only':False})
    required.append({'path':'bin/x64/Cyberpunk2077.exe','sha256':'D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4','bytes':(game/'bin/x64/Cyberpunk2077.exe').stat().st_size,'active_only':False})
    proofs=[Q10/'manifest_02.json',Q10/'completion.json',Q10/'review/addendum_result_02.json',Q9/'worker_a/core_manifest_02.json',Q9/'worker_a/diagnostics_manifest_01.json',Q9/'selected_master.json']
    master=read(Q9/'selected_master.json')
    backup=Q9/'worker_a/recovery/core_qr8_02_01/master_before/ManualSave-23'
    proofs.extend(backup/name for name in master['files'])
    manifest={'schema':'PTFR_QR11_DIAGNOSTICS_V1','component':'Diagnostics','source_epoch':'QR8:02','game_root':str(game),'save_root':str(save),
        'package_root':str(Q10/'candidate_02'),'zip':'','zip_sha256':None,
        'files':[{'path':r['path'],'before':r['before_sha256'],'after':r['after_sha256'],
            'before_bytes':(game/r['path']).stat().st_size,'after_bytes':r['bytes']}for r in c['files']],
        'required_files':required,'proofs':[{'path':str(p),'sha256':sha(p)}for p in proofs],
        'process_names':['Cyberpunk2077','REDlauncher','REDprelauncher'],
        'protected_saves':[{'path':'ManualSave-23/'+name,**r}for name,r in master['files'].items()],
        'working_save_files':[{'path':'ManualSave-24/'+name,**r}for name,r in save_rows['ManualSave-24']['files'].items()],
        'scope':'Exactly two existing diagnostic leaves. Never change Core, saves, unrelated mods or logs.'}
    mp=H/'diagnostics_manifest_01.json'
    if mp.exists():assert read(mp)==manifest
    else:mp.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    old_script=Q9/'worker_a/deploy_qr9_guarded.ps1'
    assert sha(old_script)=='CE020172988081100199A35C9FAA9131444DB4DED52893480F2BA746EFFDA39E'
    s=old_script.read_text(encoding='utf-8-sig')
    def rep(a,b):
        nonlocal s
        assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
    rep("[ValidateSet('Core','Diagnostics')][string]$Component='Core'","[ValidateSet('Diagnostics')][string]$Component='Diagnostics'")
    rep(' [switch]$BackupMaster,\n','')
    s=s.replace('QR9','QR11')
    rep("$PinnedCoreManifestSHA='06CD479C47E32403371E360092648431EAE1BC93DEE3E61BD6822560133CBCF1'\n",'')
    rep("$PinnedDiagnosticsManifestSHA='C41A1547DB7B33F0F97B68ADC7509E937A6487B85D95E34F7AAFBF83991C38E1'",f"$PinnedDiagnosticsManifestSHA='{sha(mp)}'")
    rep("$lockRoot=if($fixture){$FixtureRoot}else{$worker}","$lockRoot=if($fixture){$FixtureRoot}else{Join-Path (Split-Path $worker -Parent) 'quest_restoration_qr9/worker_a'}")
    rep("$lockPath=Safe $lockRoot 'installer.lock'","$lockPath=Safe $lockRoot 'installer.lock'\n if(-not $fixture -and -not(Test-Path -LiteralPath $lockPath -PathType Leaf)){throw 'Shared existing QR9 deployment lock is missing; review before mutation'}")
    rep('if(Test-Path -LiteralPath $current){$i=Get-Item -LiteralPath $current -Force;if($i.Attributes -band [IO.FileAttributes]::ReparsePoint)',
        '$i=Get-Item -LiteralPath $current -Force -ErrorAction SilentlyContinue;if($null -ne $i){if($i.Attributes -band [IO.FileAttributes]::ReparsePoint)')
    rep("  $i=Get-Item -LiteralPath $current -Force -ErrorAction SilentlyContinue;if($null -ne $i){if($i.Attributes -band [IO.FileAttributes]::ReparsePoint){throw ('Linked path refused: '+$current)}}",
        "  $attributes=$null\n  try{$attributes=[IO.File]::GetAttributes($current)}\n  catch [IO.FileNotFoundException]{}\n  catch [IO.DirectoryNotFoundException]{}\n  if($null -ne $attributes -and ($attributes -band [IO.FileAttributes]::ReparsePoint)){throw ('Linked path refused: '+$current)}")
    rep("$segment.EndsWith(' ')","$segment.EndsWith(' ') -or $segment -match '^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\\.|$)'")
    rep(" if(-not $Fresh -and $script:hashCache.ContainsKey($key) -and $script:hashCache[$key].stamp -eq $stamp){return $script:hashCache[$key].hash}\n",'')
    # Remove irrelevant Core/master backup API. All save operations are checks only.
    start=s.index('function MasterPlan {');end=s.index('function ApplyState(',start)
    s=s[:start]+'''function CheckProtectedSaves {
 foreach($row in $manifest.protected_saves){CheckFile (Safe $save $row.path) $row.sha256 $row.bytes -Fresh}
}
function CheckWorkingSave {
 foreach($row in $manifest.working_save_files){CheckFile (Safe $save $row.path) $row.sha256 $row.bytes -Fresh}
}
function CheckReady {
 if($fixture){return}
 $rp=Safe $worker 'readiness.json';$ready=Get-Content -LiteralPath $rp -Raw|ConvertFrom-Json -AsHashtable
 if($ready.status -cne 'READY_NOT_INSTALLED' -or $ready.manifest_sha256 -cne $manifestSHA -or $ready.installer_sha256 -cne (FileHash $PSCommandPath -Fresh)){throw 'Readiness does not bind this exact manifest/installer'}
 CheckFile (Safe $worker $ready.fixture_result) $ready.fixture_result_sha256 -Fresh
}
''' +s[end:]
    rep("$manifestFile=Join-Path $worker $(if($Component -eq 'Core'){'core_manifest_02.json'}else{'diagnostics_manifest_01.json'})","$manifestFile=Join-Path $worker 'diagnostics_manifest_01.json'")
    rep("$expectedManifestSHA=if($Component -eq 'Core'){$PinnedCoreManifestSHA}else{$PinnedDiagnosticsManifestSHA}","$expectedManifestSHA=$PinnedDiagnosticsManifestSHA")
    s=s.replace('PTFR_QR11_COMPONENT_V1','PTFR_QR11_DIAGNOSTICS_V1')
    rep("'recovery/'+$Component.ToLowerInvariant()+'_qr8_02_01'","'recovery/diagnostics_qr10d01_01'")
    rep("'recovery/'+$Component.ToLowerInvariant()","'recovery/diagnostics'")
    start=s.index("if($Component -eq 'Core'){");end=s.index('$script:journalPath=Safe',start)
    s=s[:start]+'''$wanted=@('bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/watch.json')
if($manifest.files.Count -ne 2 -or $changes.Count -ne 2 -or @($manifest.files|Where-Object {$null -eq $_.before}).Count -or (@($manifest.files.path|Sort-Object)-join ',') -cne (@($wanted|Sort-Object)-join ',')){throw 'Two-existing-diagnostic-leaf scope drift'}
''' +s[end:]
    rep("if($BackupMaster -and ($Component -ne 'Core' -or $Action -notin @('Preflight','Install'))){throw 'BackupMaster is only a reviewed Core Preflight/Install option'}\n",'')
    rep('LockMutations\nClosed','LockMutations\nClosed\nCheckProtectedSaves\nCheckReady')
    rep('CheckPackage;CheckDependencies \'After\';CheckManaged \'Before\'','CheckPackage;CheckDependencies \'After\';CheckManaged \'Before\';CheckWorkingSave')
    rep('$protection=ProtectionSnapshot;$masterPlan=if($BackupMaster){MasterPlan}else{$null}','$protection=ProtectionSnapshot')
    s=s.replace('optional_master_backup_plan=$masterPlan;','').replace("'BackupMaster would copy only the three exact selected master files into recovery during a later explicitly authorized user Install. No backup was copied by Preflight.'","'No save backup or save restore action exists in this diagnostic installer.'")
    rep('  if($BackupMaster){CreateMasterBackup}\n','')
    rep('CheckMasterBackup\n','CheckProtectedSaves\n')
    rep("'AfterBackup','AfterFirstReplace'","'AfterJournal','AfterFirstBackup','AfterBackup','AfterFirstReplace'")
    rep("'CrashAfterBackup','CrashAfterFirstReplace'","'CrashAfterJournal','CrashAfterFirstBackup','CrashAfterBackup','CrashAfterStage','CrashAfterRollbackStage','CrashAfterFirstReplace'")
    rep(' WriteJournal\n try{',' WriteJournal;Fault \'AfterJournal\'\n try{')
    rep("  foreach($row in $changes){\n   if($null", "  $backupCount=0\n  foreach($row in $changes){\n   if($null")
    rep("CheckFile $new $row.after $row.after_bytes\n  }", "CheckFile $new $row.after $row.after_bytes\n   $backupCount++;if($backupCount -eq 1){Fault 'AfterFirstBackup'}\n  }")
    rep("if($state -eq 'After' -and $script:journal.operation -eq 'Install'){Fault 'AfterStage'}", "if($state -eq 'After' -and $script:journal.operation -eq 'Install'){Fault 'AfterStage'}\n if($state -eq 'Before' -and $script:journal.operation -eq 'Rollback'){Fault 'AfterRollbackStage'}")
    # Validate canonical report paths too, including Win32 device names.
    s=s.replace('$rp=Beneath $worker $ReportFile',"$rp=Safe $worker ([IO.Path]::GetRelativePath($worker,(Full $ReportFile)).Replace('\\','/'))")
    s=s.replace('# Prepared tools only. Codex must never invoke real Install/Rollback/Recover in QR11.', '# QR11 preparation: real mutations require separate user authorization. Fixture mutation stays in QR11/fixtures.')
    (H/'deploy_diagnostics.ps1').write_text(s,encoding='utf-8',newline='\n')
    (H/'save_selection.json').write_text(json.dumps(save_rows,indent=2)+'\n',encoding='utf-8')
    print({'manifest_sha256':sha(mp),'installer_sha256':sha(H/'deploy_diagnostics.ps1'),'save_files':len(saves),'required_files':len(required),'runtime_writes':0})

if __name__=='__main__':main()

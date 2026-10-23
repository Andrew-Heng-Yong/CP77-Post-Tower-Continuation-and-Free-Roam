param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game must be closed'}
$journalGame=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$journalAudit=Join-Path $WorkspaceRoot 'research\tower_journal_cleanup'
$journalSources=@((Join-Path $WorkspaceRoot 'redscript\PTFR_TowerJournal\TowerJournalCleanup.reds'),(Join-Path $WorkspaceRoot 'diagnostics\PTFR_TowerJournal\init.lua'))
$journalTargets=@((Join-Path $journalGame 'r6\scripts\PTFR_TowerJournal\TowerJournalCleanup.reds'),(Join-Path $journalGame 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_TowerJournal\init.lua'))
foreach($journalTarget in $journalTargets){
 if(-not [IO.Path]::GetFullPath($journalTarget).StartsWith($journalGame+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Out-of-root target'}
 if(Test-Path -LiteralPath $journalTarget){throw "Existing target; no overwrite: $journalTarget"}
}
& 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' (Join-Path $PSScriptRoot 'test_tower_journal.py')
if($LASTEXITCODE -ne 0){throw 'Scope/bridge audit failed'}
$journalLint=@(& (Join-Path $WorkspaceRoot 'research\finalboards_dismissal\tooling\redscript-cli.exe') lint -s $journalSources[0] -b (Join-Path $journalGame 'r6\cache\final.redscripts') 2>&1)
$journalLint|ForEach-Object {Write-Host $_}
if($LASTEXITCODE -ne 0 -or -not ($journalLint -match 'Lint successful') -or ($journalLint -match '\bERROR\b')){throw 'Compilation failed'}
$journalExisting=[ordered]@{}
foreach($journalDir in 'archive\pc\mod','r6\scripts','bin\x64\plugins\cyber_engine_tweaks\mods'){
 foreach($journalFile in Get-ChildItem -LiteralPath (Join-Path $journalGame $journalDir) -Recurse -File|Where-Object {$_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_'}){
  $journalExisting[$journalFile.FullName]=(Get-FileHash -LiteralPath $journalFile.FullName).Hash
 }
}
if(Get-ChildItem -LiteralPath (Join-Path $journalGame 'r6\scripts') -Recurse -Filter '*.reds'|Select-String -SimpleMatch 'class PTFRTowerJournalCleanup') {throw 'Type already installed elsewhere'}
$journalPlan=@{status='VALIDATED_MANUAL_JOURNAL_CANDIDATE';sources=$journalSources;files=$journalTargets;sha256=@($journalSources|ForEach-Object {(Get-FileHash -LiteralPath $_).Hash});preserved_files=$journalExisting.Count;automatic=$false;live_tested=$false;save_files_modified=$false}
if($ValidateOnly){$journalPlan|ConvertTo-Json -Depth 5;return}
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started; abort'}
for($journalIndex=0;$journalIndex -lt $journalSources.Count;$journalIndex++){
 $journalParent=Split-Path -Parent $journalTargets[$journalIndex]
 New-Item -ItemType Directory -Force -Path $journalParent|Out-Null
 [IO.File]::Copy($journalSources[$journalIndex],$journalTargets[$journalIndex],$false)
 if((Get-FileHash -LiteralPath $journalTargets[$journalIndex]).Hash -ne $journalPlan.sha256[$journalIndex]){throw 'Installed hash mismatch'}
}
foreach($journalPath in $journalExisting.Keys){if((Get-FileHash -LiteralPath $journalPath).Hash -ne $journalExisting[$journalPath]){throw "Prior file changed: $journalPath"}}
$journalPlan.status='INSTALLED_MANUAL_JOURNAL_CANDIDATE'
$journalPlan.utc=[DateTime]::UtcNow.ToString('o')
[IO.File]::WriteAllText((Join-Path $journalAudit 'install_receipt.json'),($journalPlan|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$journalPlan|ConvertTo-Json -Depth 5

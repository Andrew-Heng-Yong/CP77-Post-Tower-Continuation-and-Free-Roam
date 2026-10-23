param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game must be closed'}
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $WorkspaceRoot 'research\b0_world_interactions\coaster_animation_audit'
$prior=Get-Content (Join-Path $WorkspaceRoot 'research\b0_world_interactions\coaster_repeat_gesture\install_receipt.json') -Raw|ConvertFrom-Json
foreach($i in 0,1,2){if((Get-FileHash -LiteralPath $prior.files[$i]).Hash -ne $prior.sha256[$i]){throw 'Installed revision5 differs; abort'}}
$lua=$prior.files[2]
$script=Join-Path $game 'r6\scripts\PTFR_Coaster_AnimationAudit\CoasterAnimationAudit.reds'
$scriptSource=Join-Path $WorkspaceRoot 'diagnostics\PTFR_Coaster_AnimationAudit\CoasterAnimationAudit.reds'
$luaSource=Join-Path $WorkspaceRoot 'archive\b0_world_interactions\cet\init.lua'
if(Test-Path -LiteralPath $script){throw 'Observer already installed'}
foreach($target in $lua,$script){if(-not [IO.Path]::GetFullPath($target).StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Out-of-root target'}}
& (Join-Path $WorkspaceRoot 'research\finalboards_dismissal\tooling\redscript-cli.exe') lint -s $scriptSource -b (Join-Path $game 'r6\cache\final.redscripts.modded')
if($LASTEXITCODE -ne 0){throw 'Observer compile failed'}
& 'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' (Join-Path $WorkspaceRoot 'tools\test_world_interactions_lua.py')
if($LASTEXITCODE -ne 0){throw 'Logger tests failed'}
$protected=[ordered]@{}
foreach($dir in 'archive\pc\mod','r6\scripts','bin\x64\plugins\cyber_engine_tweaks\mods'){
 foreach($f in Get-ChildItem (Join-Path $game $dir) -Recurse -File|Where-Object {($_.Name -like '*TowerContinued*' -or $_.FullName -match '[\\/]PTFR_') -and $_.FullName -ne $lua}){$protected[$f.FullName]=(Get-FileHash -LiteralPath $f.FullName).Hash}
}
$backup=Join-Path $audit ('deployment_backup_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))
New-Item -ItemType Directory -Path $backup -ErrorAction Stop|Out-Null
[IO.File]::Copy($lua,(Join-Path $backup 'init.lua'),$false)
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started; abort'}
try{
 New-Item -ItemType Directory -Force -Path (Split-Path -Parent $script)|Out-Null
 [IO.File]::Copy($scriptSource,$script,$false)
 [IO.File]::Copy($luaSource,$lua,$true)
 if((Get-FileHash $script).Hash -ne (Get-FileHash $scriptSource).Hash -or (Get-FileHash $lua).Hash -ne (Get-FileHash $luaSource).Hash){throw 'Deployment hash mismatch'}
 foreach($p in $protected.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $protected[$p]){throw "Protected file changed: $p"}}
}catch{
 [IO.File]::Copy((Join-Path $backup 'init.lua'),$lua,$true)
 if(Test-Path -LiteralPath $script){Move-Item -LiteralPath $script -Destination (Join-Path $backup 'failed_observer.reds')}
 throw
}
$receipt=@{status='INSTALLED_READ_ONLY_COASTER_ANIMATION_OBSERVER';utc=[DateTime]::UtcNow.ToString('o');files=@($script,$lua);sha256=@((Get-FileHash $script).Hash,(Get-FileHash $lua).Hash);backup=$backup;preserved_files=$protected.Count;native_archive_sha256=(Get-FileHash $prior.files[0]).Hash;native_archive_unchanged=$true;gameplay_writes=$false;save_files_modified=$false;live_callback_registration_verified=$false}
[IO.File]::WriteAllText((Join-Path $audit 'install_receipt.json'),($receipt|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 5

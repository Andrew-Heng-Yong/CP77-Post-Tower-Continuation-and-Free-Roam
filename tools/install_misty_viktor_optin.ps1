param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue){throw 'Game running'}
$gameRoot=[IO.Path]::GetFullPath('C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$test=Get-Content -LiteralPath (Join-Path $audit 'optin_tests.json') -Raw|ConvertFrom-Json
$manifest=Get-Content -LiteralPath (Join-Path $audit 'optin_manifest.json') -Raw|ConvertFrom-Json
if($test.status -ne 'PASS_OFFLINE_OPTIN_PRIVATE_VARIANT_NATIVE_AND_LUA51_NOT_LIVE' -or $test.archive_sha256 -ne $manifest.sha256){throw 'Missing or stale tests'}
$items=@(
  @{source=$manifest.archive;relative='archive\pc\mod\TowerContinued_MistyViktorShellOptIn.archive';sha=$test.archive_sha256},
  @{source=($manifest.archive+'.xl');relative='archive\pc\mod\TowerContinued_MistyViktorShellOptIn.archive.xl';sha=$test.xl_sha256},
  @{source=(Join-Path $WorkspaceRoot 'diagnostics\PTFR_MistyViktor_World\init.lua');relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_MistyViktor_World\init.lua';sha=$test.probe_sha256}
)
foreach($item in $items){
  $target=[IO.Path]::GetFullPath((Join-Path $gameRoot $item.relative))
  if(-not $target.StartsWith($gameRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Target outside game root'}
  if(Test-Path -LiteralPath $target){throw "Refusing overwrite: $target"}
  if((Get-FileHash -LiteralPath $item.source).Hash -ne $item.sha){throw 'Source changed after test'}
}
$protected=[Collections.Generic.List[string]]::new()
foreach($file in (Get-ChildItem -LiteralPath (Join-Path $gameRoot 'archive\pc\mod') -Filter 'TowerContinued*' -File)){$protected.Add($file.FullName)}
foreach($directory in (Get-ChildItem -LiteralPath (Join-Path $gameRoot 'r6\scripts') -Filter 'PTFR*' -Directory)){
  foreach($file in (Get-ChildItem -LiteralPath $directory.FullName -Recurse -File)){$protected.Add($file.FullName)}
}
foreach($directory in (Get-ChildItem -LiteralPath (Join-Path $gameRoot 'bin\x64\plugins\cyber_engine_tweaks\mods') -Filter 'PTFR*' -Directory)){
  $lua=Join-Path $directory.FullName 'init.lua';if(Test-Path -LiteralPath $lua){$protected.Add($lua)}
}
$before=@{};foreach($path in $protected){$before[$path]=(Get-FileHash -LiteralPath $path).Hash}
if(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue){throw 'Game started: installation deferred'}
$installed=@()
foreach($item in $items){
  $target=Join-Path $gameRoot $item.relative
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)|Out-Null
  Copy-Item -LiteralPath $item.source -Destination $target
  if((Get-FileHash -LiteralPath $target).Hash -ne $item.sha){throw 'Installed hash mismatch'}
  $installed+=@{relative=$item.relative;sha256=$item.sha}
}
foreach($path in $protected){if((Get-FileHash -LiteralPath $path).Hash -ne $before[$path]){throw "Prior project file changed: $path"}}
$receipt=[ordered]@{status='INSTALLED_IDLE_OPTIN_GEOMETRY_CANDIDATE';utc=[DateTime]::UtcNow.ToString('o');files=$installed;prior_project_files_preserved=$protected.Count;prior_hashes=$before;vanilla_overwrites=0;gameplay_commands_executed=0;save_files_modified=$false;live_tested=$false;rollback='Remove only these three additive files while the game is closed; no prior file was replaced.'}
[IO.File]::WriteAllText((Join-Path $audit 'install_receipt.json'),($receipt|ConvertTo-Json -Depth 5))
[pscustomobject]@{status=$receipt.status;utc=$receipt.utc;added=$installed.Count;preserved=$protected.Count;live_tested=$false}|ConvertTo-Json

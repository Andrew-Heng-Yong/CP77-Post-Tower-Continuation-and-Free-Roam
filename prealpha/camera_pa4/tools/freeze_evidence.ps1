Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$out=Join-Path $ws 'research/pre_alpha_camera_pa4/live_pa3_and_checkpoint'
if(Test-Path -LiteralPath $out){throw 'Evidence already frozen; no overwrite'}
if(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue){throw 'Close game before freezing logs'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$save='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-18'
$rows=@()
New-Item -ItemType Directory -Path $out|Out-Null
foreach($source in @(
 (Join-Path $save 'sav.dat'),(Join-Path $save 'metadata.9.json'),(Join-Path $save 'screenshot.png'),
 (Join-Path $game 'bin/x64/plugins/cyber_engine_tweaks/scripting.log'),
 (Join-Path $game 'bin/x64/plugins/cyber_engine_tweaks/gamelog.log'),
 (Join-Path $game 'bin/x64/plugins/cyber_engine_tweaks/mods/ImmersiveFirstPerson/ImmersiveFirstPerson.log')
)){
 $relative=if($source.StartsWith($save+'\')){'AutoSave-18/'+[IO.Path]::GetFileName($source)}else{'logs/'+[IO.Path]::GetFileName($source)}
 $dest=Join-Path $out $relative
 New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null
 $before=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
 Copy-Item -LiteralPath $source -Destination $dest
 $copied=(Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash
 if($before -cne $copied -or $before -cne (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash){throw 'Copy/source drift'}
 $rows+=@{source=$source;copy=$relative;sha256=$copied}
}
$meta=(Get-Content (Join-Path $save 'metadata.9.json') -Raw|ConvertFrom-Json).Data.metadata
if($meta.timestampString -cne '13:16:51, 13.10.2026' -or ($rows|Where-Object copy -eq 'AutoSave-18/sav.dat').sha256 -cne '7F6A9D621BAEAC273AF83C8289479876808645365E69BF2B377D67515EAD2D37'){throw 'Unexpected checkpoint'}
$report=@{utc=[DateTime]::UtcNow.ToString('o');files=$rows;slot='AutoSave-18';timestamp=$meta.timestampString;level=$meta.level;forced=$meta.isForced;checkpoint=$meta.isCheckpoint;user_confirmed_credits_replay=$true;active_save_modified=$false;limitations='Metadata still tracks Walk with Misty; user confirms credits replay. No scene-state fabrication. No save/reload automation.'}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),($report|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$report|ConvertTo-Json -Depth 10

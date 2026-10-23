param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[switch]$Restore,[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($Restore -and $ValidateOnly){throw 'Choose rollback OR validation'}
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\');$audit=Join-Path $workspace 'research\afterlife_world\idles_r3'
$r=Get-Content (Join-Path $audit 'install_receipt.json') -Raw|ConvertFrom-Json -Depth 10
if($r.status -ne 'INSTALLED_AFTERLIFE_IDLES_R3_LIVE_PENDING' -or $r.files.Count -ne 4 -or $r.replacements -ne 0){throw 'Unexpected R3 receipt'}
$game=[IO.Path]::GetFullPath($r.game_root).TrimEnd('\')
function Within([string]$p,[string]$root){$v=[IO.Path]::GetFullPath($p);if(-not $v.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Path escaped intended root'};return $v}
function Closed {if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Close Cyberpunk before rollback'}}
function Match([string]$p,[string]$h){if((Get-FileHash -LiteralPath $p).Hash -ne $h){throw "Hash mismatch: $p"}}
$allowed=@('archive\pc\mod\TowerContinued_AfterlifeIdlesR3.archive','archive\pc\mod\TowerContinued_AfterlifeIdlesR3.archive.xl','r6\scripts\PTFR_Afterlife_Idles_R3\AfterlifeIdlesR3.reds','bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_Behavior_Audit\init.lua')
if(@(Compare-Object $allowed @($r.files.relative)).Count){throw 'Rollback scope changed'}
Closed
foreach($p in $r.files){Match (Within (Join-Path $game $p.relative) $game) $p.sha256}
if(-not $Restore){@{status='R3_ROLLBACK_PREFLIGHT_ONLY';recoverable_removals=4;game_unchanged=$true}|ConvertTo-Json;return}
$stash=Within (Join-Path $audit ('removed_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
$moved=[Collections.Generic.List[object]]::new()
try{
 foreach($p in $r.files){Closed;$from=Within (Join-Path $game $p.relative) $game;$to=Within (Join-Path $stash $p.relative) $stash;Match $from $p.sha256;New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null;Move-Item -LiteralPath $from -Destination $to;$moved.Add($p);Match $to $p.sha256}
}catch{
 $failure=$_.Exception.Message
 Closed
 foreach($p in $moved){$from=Within (Join-Path $stash $p.relative) $stash;$to=Within (Join-Path $game $p.relative) $game;if(Test-Path -LiteralPath $to){throw 'Recovery destination appeared; inspect rollback stash'};Match $from $p.sha256;Move-Item -LiteralPath $from -Destination $to}
 throw $failure
}
$result=@{status='R3_REMOVED_RECOVERABLY';stash=$stash;removed=4;accepted_r2_untouched=$true}
[IO.File]::WriteAllText((Join-Path $audit 'rollback_receipt.json'),($result|ConvertTo-Json),[Text.UTF8Encoding]::new($false));$result|ConvertTo-Json

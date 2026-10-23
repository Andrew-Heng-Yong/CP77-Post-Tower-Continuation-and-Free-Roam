param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue){throw 'Game running: installation deferred'}
$gameRoot=[IO.Path]::GetFullPath('C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
$source=Join-Path $WorkspaceRoot 'diagnostics\PTFR_RadioMemorial_Audit\init.lua'
$target=[IO.Path]::GetFullPath((Join-Path $gameRoot 'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_RadioMemorial_Audit\init.lua'))
if(-not $target.StartsWith($gameRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Target outside game root'}
if(Test-Path -LiteralPath $target){throw 'Target exists: refusing overwrite'}
$report=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\radio_memorial_validation\tests.json') -Raw | ConvertFrom-Json
if($report.status -ne 'STATIC_NATIVE_PRESERVATION_AND_PROBE_PASS_LIVE_OUTPUT_UNVERIFIED'){throw 'Missing tests'}
if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $report.probe_sha256){throw 'Probe changed after tests'}
$protected=@(
  'archive\pc\mod\TowerContinued_WorldInteractions.archive',
  'archive\pc\mod\TowerContinued_WorldInteractions.archive.xl',
  'bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_WorldInteractions_Audit\init.lua',
  'r6\scripts\PTFR_Coaster_AnimationAudit\CoasterAnimationAudit.reds'
)
$prior=@{}
foreach($rel in $protected){$prior[$rel]=(Get-FileHash -LiteralPath (Join-Path $gameRoot $rel) -Algorithm SHA256).Hash}
$expected=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\b0_world_interactions\coaster_direct_entry\install_receipt.json') -Raw | ConvertFrom-Json
for($i=0;$i -lt $protected.Count;$i++){if($prior[$protected[$i]] -ne $expected.sha256[$i]){throw "Shared baseline differs: $($protected[$i])"}}
if(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue){throw 'Game started: installation deferred'}
New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
Copy-Item -LiteralPath $source -Destination $target
$actual=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
if($actual -ne $report.probe_sha256){throw 'Installed probe hash mismatch'}
foreach($rel in $protected){if((Get-FileHash -LiteralPath (Join-Path $gameRoot $rel) -Algorithm SHA256).Hash -ne $prior[$rel]){throw "Protected file changed: $rel"}}
$receipt=[ordered]@{status='INSTALLED_READ_ONLY_RADIO_MEMORIAL_PROBE';utc=[DateTime]::UtcNow.ToString('o');target=$target;sha256=$actual;protected_hashes=$prior;native_resources_changed=0;story_fact_writes=0;save_files_modified=$false;live_tested=$false}
$out=Join-Path $WorkspaceRoot 'research\radio_memorial_validation\install_receipt.json'
[IO.File]::WriteAllText($out,($receipt|ConvertTo-Json -Depth 5))
$receipt|ConvertTo-Json -Depth 5

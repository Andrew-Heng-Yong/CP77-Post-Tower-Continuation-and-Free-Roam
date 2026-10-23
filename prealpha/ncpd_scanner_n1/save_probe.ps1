param([string]$SavePath='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-6\sav.dat')
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$code=Get-Content (Join-Path $ws 'tools/read_afterlife_savefacts.ps1') -Raw
$catalog=Get-Content (Join-Path $ws 'research/ncpd_scanner_n1/catalog_v1.json') -Raw|ConvertFrom-Json
$names=@('PostTowerFreeRoamActive','PTFRP0_DR13','PTFRPA2_Finished','PTFRPA2_Fault','PTFRU9_Support_Issued','q307_active','q307_done','q307_finished','q307_2079','q307_main_game_killed','q307_ep1_killed','q115_point_of_no_return','sts_wat_lch_tier_1','ma_token','wat_achievement','q101_enable_side_content','holo_ncpd_dispatcher_calls_v_start_activate','holo_ncpd_dispatcher_calls_v_end_activate','holo_ncpd_dispatcher_calls_v_reset_counter','holo_ncpd_dispatcher_calls_v_start_done','holo_ncpd_dispatcher_calls_v_end_done')
foreach($r in $catalog.rows){if($r.PSObject.Properties.Name -contains 'facts'){$names+=@($r.facts)}}
$names=@($names|Sort-Object -Unique)
$expr='$names=@('+ (($names|ForEach-Object {"'$_'"}) -join ',') + ')'
$code=[regex]::Replace($code,'(?m)^\$names=@\([^\r\n]+', [Text.RegularExpressions.MatchEvaluator]{param($m) $expr})
$out='research/ncpd_scanner_n1/save_facts_auto6.json'
if(Test-Path (Join-Path $ws $out)){throw 'Evidence exists'}
. ([scriptblock]::Create($code)) -SavePath $SavePath -OutputPath $out | Out-Null
$r=Get-Content (Join-Path $ws $out) -Raw|ConvertFrom-Json
@{status=$r.status;sha256=$r.sha256;facts=$r.facts.PSObject.Properties|Where-Object {$_.Name -match 'ma_wat_lch_0[123]|PTFRPA2_Finished|holo_ncpd|sts_wat_lch_tier|wat_achievement|ma_token'}|ForEach-Object {@{name=$_.Name;values=$_.Value}}}|ConvertTo-Json -Depth 8

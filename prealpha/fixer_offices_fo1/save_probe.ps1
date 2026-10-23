param([string]$SavePath='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-5\sav.dat')
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
# Reuse the read-only parser; replace only its explicit fact selection/output.
$code=Get-Content (Join-Path $root 'tools/read_afterlife_savefacts.ps1') -Raw
$names=@('PostTowerFreeRoamActive','PTFRP0_DR13','PTFRPA2_Finished','PTFRPA2_Fault','PTFRU9_Support_Issued','PTFRU9_Support_Fault','q307_active','q307_done','q307_finished','q307_2079','q307_main_game_killed','q307_ep1_killed','q115_point_of_no_return','q305_johnny_scene_active','wakako_default_on','reggie_default_on','padre_default_on','dyno_default_on','dakota_default_on','el_capitan_default_on','mr_hands_default_on','mr_hands_default_ep1','el_capitan_default_off_ep1','sa_ep1_courier_outro_disable_muamar_default','sq021_done','sq021_finished','sq021_reward_received')
$expr='$names=@('+ (($names|ForEach-Object {"'$_'"}) -join ',') + ')'
$code=[regex]::Replace($code,'(?m)^\$names=@\([^\r\n]+', [Text.RegularExpressions.MatchEvaluator]{param($m) $expr})
$out='research/fixer_offices_fo1/save_facts.json'
if(Test-Path (Join-Path $root $out)){throw 'Evidence exists'}
. ([scriptblock]::Create($code)) -SavePath $SavePath -OutputPath $out

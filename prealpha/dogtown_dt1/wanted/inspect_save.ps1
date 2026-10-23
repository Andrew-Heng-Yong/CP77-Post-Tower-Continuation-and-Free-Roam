param([string]$Output='research/dogtown_dt1/wanted/saved_prevention_01.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$wk='C:/Users/Ayong/Documents/WolvenKit-8.20.0'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $a))}
# These are explicitly persistent in the stock script. Nonpersistent fields such
# as PlayerHLS/Debug_ProcessReason must not be presented as saved runtime state.
$fields=@('IgnoreSecurityAreasByQuest','ForceEternalGreyStars','BlockOnFootSpawnByQuest','BlockVehicleSpawnByQuest','BlockReconDroneSpawnByQuest','CrimeScoreMultiplierByQuest','PreventionQuestEventSources','SystemLockSources','SystemEnabled')
function Primitive($v){
 if($null -eq $v){return $null}
 if($v -is [Collections.IEnumerable] -and $v -isnot [string]){return ,@($v|ForEach-Object {Primitive $_})}
 return $v.ToString()
}
$defaults=[ordered]@{};$empty=[WolvenKit.RED4.Types.PreventionSystem]::new()
foreach($f in $fields){$defaults[$f]=Primitive $empty.$f}
$samples=@()
foreach($slot in @('AutoSave-1','AutoSave-0')){
 $p=Join-Path $root "research/dogtown_dt1/live_20261017_01/$slot/sav.dat"
 $before=(Get-FileHash $p).Hash;$s=[IO.File]::Open($p,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try{
  $reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($s);$save=$null
  if($reader.ReadFile([ref]$save).ToString() -ne 'NoError'){throw 'Save read failed'}
  $package=@($save.Nodes|Where-Object {$_.Name -eq 'ScriptableSystemsContainer'})
  if($package.Count -ne 1){throw 'Unexpected scriptable package count'}
  $systems=@($package[0].Value.Content.Chunks|Where-Object {$_ -is [WolvenKit.RED4.Types.PreventionSystem]})
  if($systems.Count -ne 1){throw 'Unexpected prevention-system count'}
  $values=[ordered]@{};foreach($f in $fields){$values[$f]=Primitive $systems[0].$f}
  $samples+=@{slot=$slot;path=$p;sha256=$before;persistent_fields_decoded=$values;unique_systems=$systems.Count}
 }finally{$s.Dispose()}
 if((Get-FileHash $p).Hash -ne $before){throw 'Source changed'}
}
$out=Join-Path $root $Output;if(Test-Path $out){throw 'Report exists'}
@{status='READ_ONLY_DECODED_PERSISTENT_FIELDS_NOT_LIVE';samples=$samples;constructor_defaults=$defaults;field_presence_tracked=$false;limitations=@('WolvenKit defaults are reported explicitly; this inspector does not instrument binary field presence.','No nonpersistent fields, current HLS, heat limiter, district or free-area state are inferred from save-object constructor values.','Source-named locks are empty in decoded state, not proof no lock will be added during runtime.');source_pins=@{'research/finalboards_dismissal/decompiled/core/systems/preventionSystem.script'=(Get-FileHash (Join-Path $root 'research/finalboards_dismissal/decompiled/core/systems/preventionSystem.script')).Hash;'parser_dll'=(Get-FileHash (Join-Path $wk 'WolvenKit.RED4.dll')).Hash};game_writes=0;save_writes=0}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $out -Encoding utf8
Write-Output $out

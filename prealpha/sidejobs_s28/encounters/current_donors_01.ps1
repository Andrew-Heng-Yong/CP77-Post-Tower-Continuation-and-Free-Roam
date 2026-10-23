Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
$out=Join-Path $ws 'research/sidejobs_s28/encounters/current_donors_01'
if(Test-Path -LiteralPath $out){throw 'Immutable audit exists'}
New-Item -ItemType Directory $out|Out-Null
$componentRel='prealpha/sidejobs_s28/encounters/build/encounters_07/component.json';$component=Get-Content (Join-Path $ws $componentRel) -Raw|ConvertFrom-Json -Depth 100
$sourcePins=[ordered]@{};$sources=@{};$historical=@($component.historical_comparison_sources);$historicalChecks=@();$rows=@();$archives=@()
foreach($pin in $component.source_pins.PSObject.Properties){
 $actual=(Get-FileHash -LiteralPath (Join-Path $ws $pin.Name)).Hash
 if($actual -cne $pin.Value){throw ('Pinned source changed '+$pin.Name)}
 $sourcePins[$pin.Name]=$actual
 if($pin.Name -in $historical){$historicalChecks+=,@{source=$pin.Name;sha256=$actual;purpose='Explicit historical patch comparison only'};continue}
 if($pin.Name -match '/raw/((base|ep1)/.+\.(quest|questphase|scene|workspot))$'){
  $dep=$Matches[1].Replace('/','\');if(!$sources.ContainsKey($dep)){$sources[$dep]=@()};$sources[$dep]+=,@{source=$pin.Name;sha256=$actual;archive=$null}
 }
}
$inventoryRel='research/sidejobs_s28/vehicles/world_03/inventory.json';$inventory=Get-Content (Join-Path $ws $inventoryRel) -Raw|ConvertFrom-Json -Depth 100;$sourcePins[$inventoryRel]=(Get-FileHash (Join-Path $ws $inventoryRel)).Hash
$world=@($inventory.rows|Where-Object {$_.raw -ceq 'research/sidejobs_s28/vehicles/world_03/raw/ep1_1_nightcity_always_loaded_1.streamingsector'})
if($world.Count -ne 1 -or $sourcePins[$world[0].raw] -cne $world[0].raw_sha256){throw 'Johnny source inventory mismatch'}
$w=$world[0];$sources[$w.depot]=@(@{source=$w.raw;sha256=$w.raw_sha256;archive=$w.archive})
$sourcePins[$componentRel]=(Get-FileHash (Join-Path $ws $componentRel)).Hash
$sourcePins['prealpha/sidejobs_s28/encounters/current_donors_01.ps1']=(Get-FileHash $PSCommandPath).Hash
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$keys=@{};foreach($dep in $sources.Keys){$keys[$dep]=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($dep)}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc'
$files=@(Get-ChildItem -LiteralPath (Join-Path $game 'content') -File -Filter '*.archive')+@(Get-ChildItem -LiteralPath (Join-Path $game 'ep1') -File -Filter '*.archive')
foreach($file in $files){
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw ('Official archive unreadable '+$file.FullName)}
 $used=$false
 foreach($dep in $sources.Keys){
  if(!$arc.Files.ContainsKey($keys[$dep])){continue}
  $expected=@($sources[$dep]|Where-Object {$null -eq $_.archive -or $_.archive -ieq $file.FullName});if(!$expected.Count){continue};$used=$true
  $m=[IO.MemoryStream]::new();try{$arc.Files[$keys[$dep]].Extract($m);$bytes=$m.ToArray()}finally{$m.Dispose()};$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
  $matches=@($expected|Where-Object {$_.sha256 -ceq $h});$rawRel=$null;$jsonRel=$null
  if(!$matches.Count){
   $rawRel='research/sidejobs_s28/encounters/current_donors_01/'+$file.BaseName+'/raw/'+$dep.Replace('\','/');$jsonRel=$rawRel.Replace('/raw/','/json/')+'.json';New-Item -ItemType Directory -Force (Split-Path (Join-Path $ws $rawRel)),(Split-Path (Join-Path $ws $jsonRel))|Out-Null;[IO.File]::WriteAllBytes((Join-Path $ws $rawRel),$bytes);Export-Cr2wJson (Read-Cr2wFile (Join-Path $ws $rawRel)) (Join-Path $ws $jsonRel)
  }
  $rows+=,@{depot=$dep;archive=$file.FullName;source_records=$expected;current_sha256=$h;exact=($matches.Count -gt 0);current_raw=$rawRel;current_json=$jsonRel}
 }
 if($used){$archives+=,@{path=$file.FullName;length=$file.Length;last_write_utc=$file.LastWriteTimeUtc.ToString('o');sha256=(Get-FileHash -LiteralPath $file.FullName).Hash}}
}
$missing=@($sources.Keys|Where-Object {$_ -cnotin @($rows.depot)})
$result=[ordered]@{status=if($missing.Count -eq 0 -and @($rows|Where-Object {!$_.exact}).Count -eq 0){'PASS_CURRENT_OFFICIAL_ENCOUNTER_SOURCE_BYTES'}else{'SOURCE_DIFFERENCES_REQUIRE_REVIEW'};component=$componentRel;component_sha256=$sourcePins[$componentRel];source_pins=$sourcePins;selected=$sources.Count;found=@($rows.depot|Sort-Object -Unique).Count;missing=$missing;mismatches=@($rows|Where-Object {!$_.exact}).Count;rows=$rows;archives=$archives;historical_comparisons=$historicalChecks;tool_sha256=(Get-FileHash (Join-Path $wk 'WolvenKit.RED4.dll')).Hash;game_writes=0;save_writes=0;scope='Current official native content equality only. No compiler/toolchain tests. Journal metadata, packed archive integration and live behavior are separate.'}
[IO.File]::WriteAllText((Join-Path $out 'report.json'),($result|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false))
@{status=$result.status;selected=$result.selected;found=$result.found;mismatches=$result.mismatches;missing=$missing}|ConvertTo-Json

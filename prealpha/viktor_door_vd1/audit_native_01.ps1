$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'native_review_03'
if(Test-Path -LiteralPath $out){throw 'Preserve prior evidence'}
[void][IO.Directory]::CreateDirectory($out)
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$depots=@('ep1\quest\main_quests\q307\phases\q307_06_viktor.questphase','ep1\quest\main_quests\q307\scenes\q307_06_viktor.scene','base\worlds\03_night_city\_compiled\default\exterior_-25_19_0_0.streamingsector','towercontinued\misty_viktor_world\access_r11.questphase','towercontinued\viktor_door_vd1\clinic_access.questphase')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$queries=@{};foreach($dep in $depots){$queries[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($dep)]=$dep}
$hits=[Collections.Generic.List[object]]::new()
$inventory=[Collections.Generic.List[object]]::new()
foreach($path in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Recurse -Filter '*.archive' -File){
 $a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw ('Unreadable archive '+$path.FullName)}
 $rel=[IO.Path]::GetRelativePath($game,$path.FullName).Replace('\','/')
 $inventory.Add(@{path=$rel;bytes=$path.Length;modified_utc=$path.LastWriteTimeUtc.ToString('o')})
 foreach($key in $queries.Keys){if($a.Files.ContainsKey([uint64]$key)){
  $dep=$queries[$key];$target=Join-Path $out ('source/'+$path.BaseName+'/'+$dep)
  [void][IO.Directory]::CreateDirectory((Split-Path $target -Parent))
  $ms=[IO.MemoryStream]::new();try{$a.Files[[uint64]$key].Extract($ms);[IO.File]::WriteAllBytes($target,$ms.ToArray())}finally{$ms.Dispose()}
  $hits.Add(@{archive=$rel;depot=$dep;source=$target;sha256=(Get-FileHash -LiteralPath $target).Hash})
 }}
}
foreach($dep in @($depots[0],$depots[1],$depots[3])){if(@($hits|Where-Object depot -CEQ $dep).Count -ne 1){throw ('Ambiguous provider '+$dep)}}
$sectorProviders=@($hits|Where-Object depot -CEQ $depots[2]|ForEach-Object archive|Sort-Object)
$expectedSectorProviders=@('archive/pc/content/basegame_3_nightcity.archive','archive/pc/ep1/ep1_1_nightcity.archive')
if(@(Compare-Object $sectorProviders $expectedSectorProviders).Count){throw 'Unexpected sector override'}
if(@($hits|Where-Object depot -CEQ $depots[4]).Count){throw 'New private depot already exists'}
foreach($hit in $hits){if(!$hit.depot.EndsWith('.streamingsector')){Export-Cr2wJson (Read-Cr2wFile $hit.source) ($hit.source+'.json')}}
$result=@{status='PASS_NATIVE_PROVIDERS_NEW_DEPOT_FREE';sector_provider='archive/pc/ep1/ep1_1_nightcity.archive';sector_decode='Not decoded: WK9.1 cannot cast an unknown DynamicBaseClass worldNode. Native sector bytes preserved; no sector modification proposed.';archive_count=$inventory.Count;inventory=@($inventory.ToArray());providers=@($hits.ToArray());game_writes=0;save_writes=0}
$result|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $out 'providers.json') -Encoding utf8NoBOM
$result|Select-Object status,archive_count,game_writes|ConvertTo-Json

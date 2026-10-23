param([string]$Revision='s23_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($Revision -cnotmatch '^s23_\d{2}$'){throw 'Invalid revision'}
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$build=Join-Path $PSScriptRoot ('build/'+$Revision);$manifest=Join-Path $build 'build.json';$dest=Join-Path $build 'resource_check.json'
if(Test-Path -LiteralPath $dest){throw 'Immutable evidence exists'}
$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
function SHA($p){return (Get-FileHash -LiteralPath $p).Hash}
function ResourceHash($entry){$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}}
$native=@{};$wanted=@{};$pins=@{}
foreach($p in $m.source_pins.PSObject.Properties){
 if([IO.Path]::IsPathRooted($p.Name) -or $p.Name -match '(^|/)\.\.(/|$)'){throw 'Unsafe source pin'}
 $full=Join-Path $workspace $p.Name;if((SHA $full) -cne $p.Value){throw "Source drift: $($p.Name)"};$pins[$full]=$p.Value
 if($p.Name -match '^research/.+/raw/((base|ep1)/.+)$'){
  $depot=$Matches[1].Replace('/','\')
  if($native.ContainsKey($depot) -and $native[$depot] -cne $p.Value){throw 'Conflicting official extraction'}
  $native[$depot]=$p.Value;$wanted[$depot]=$p.Value
 }
}
if($native.Count -lt 15 -or @($m.resources.PSObject.Properties).Count -lt 20 -or @($m.boots).Count -lt 15){throw 'Incomplete bundle scope'}
foreach($p in $m.resources.PSObject.Properties){
 if($p.Name -notlike 'towercontinued\*' -or $native.ContainsKey($p.Name)){throw 'Official override forbidden'}
 if((SHA (Join-Path (Join-Path $build 'source') $p.Name)) -cne $p.Value){throw 'Resource drift'}
 $wanted[$p.Name]=$p.Value
}
$cleanup='towercontinued\gig_phone_u9\fixer_cleanup.questphase';$wilson='towercontinued\b0_wilson_vendor\owner.questphase'
if(@($m.official_overrides).Count -ne 0 -or (@($m.mod_overrides|Sort-Object) -join '|') -cne (@($cleanup,$wilson|Sort-Object) -join '|')){throw 'Unexpected override scope'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$modRoot=Join-Path $game 'archive/pc/mod'
if(Test-Path -LiteralPath (Join-Path $modRoot 'modlist.txt')){throw 'Explicit load order requires review'}
$xlPins=@{};$xls=@(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.xl')
if(@($m.installed_xl_pins.PSObject.Properties).Count -ne $xls.Count -or $xls.Count -eq 0){throw 'Installed XL set count changed'}
foreach($p in $m.installed_xl_pins.PSObject.Properties){
 if($p.Name -cnotin $xls.FullName -or (SHA $p.Name) -cne $p.Value){throw 'Installed XL identity/hash changed'}
 $xlPins[$p.Name]=$p.Value
}
foreach($entry in $m.installed_injections){if($xlPins[(Join-Path $modRoot $entry.source)] -cne $entry.source_sha256){throw 'Injection inventory source mismatch'}}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$keys=@{}
foreach($depot in $wanted.Keys){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot);if($keys.ContainsKey($key) -and $keys[$key] -cne $depot){throw 'FNV collision'};$keys[$key]=$depot}
$archivePins=@{};$collisions=@();$found=@{};$officialRows=@()
$mods=@(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.archive'|Sort-Object Name)
foreach($file in $mods){
 $hash=SHA $file.FullName;$archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Bad installed archive'}
 foreach($key in $archive.Files.Keys){if($keys.ContainsKey([uint64]$key)){
  $depot=$keys[[uint64]$key]
  $allowed=if($depot -ceq $cleanup){@('000_TowerContinued_SideJobs_S22.archive','00_TowerContinued_Courier_C1.archive','0_TowerContinued_NCPD_N1.archive','TowerContinued_PreAlpha.archive')}elseif($depot -ceq $wilson){@('TowerContinued_PreAlpha.archive')}else{@()}
  if($file.Name -cnotin $allowed){throw "Installed conflict: $($file.Name) $depot"}
  $collisions+=,@{archive=$file.Name;depot=$depot;resource_sha256=ResourceHash $archive.Files[$key]}
 }}
 if((SHA $file.FullName) -cne $hash){throw 'Archive changed during audit'};$archivePins[$file.FullName]=$hash
}
$donors=@{
 $cleanup=@{archive='000_TowerContinued_SideJobs_S22.archive';sha=(SHA (Join-Path $workspace 'prealpha/sidejobs_s221/build/s221_01/source/towercontinued/gig_phone_u9/fixer_cleanup.questphase'))}
 $wilson=@{archive='TowerContinued_PreAlpha.archive';sha='62803881CEF5F389DD6E2FF339C6B8D246EBEDFE5CC892C36686DBB940DD2283'}
}
foreach($depot in $donors.Keys){
 $rows=@($collisions|Where-Object {$_.depot -ceq $depot});$donor=$donors[$depot]
 $order=[string[]]@($rows.archive);[Array]::Sort($order,[StringComparer]::OrdinalIgnoreCase)
 if($order.Count -eq 0 -or $order[0] -cne $donor.archive){throw 'Current winning donor differs'}
 $row=@($rows|Where-Object {$_.archive -ceq $donor.archive})
 if($row.Count -ne 1 -or $row[0].resource_sha256 -cne $donor.sha){throw 'Current donor bytes differ'}
 $order=[string[]](@('0000_TowerContinued_SideJobs_S23.archive')+@($rows.archive));[Array]::Sort($order,[StringComparer]::OrdinalIgnoreCase)
 if($order[0] -cne '0000_TowerContinued_SideJobs_S23.archive'){throw 'New override is not first'}
}
$official=@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter 'basegame_*.archive' -File).FullName)+@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter 'ep1_*.archive' -File).FullName)
foreach($path in $official){
 $before=Get-Item -LiteralPath $path;$archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Bad official archive'}
 foreach($key in $archive.Files.Keys){if($keys.ContainsKey([uint64]$key)){
  $depot=$keys[[uint64]$key]
  if(!$native.ContainsKey($depot)){throw 'Mod resource collides with official game'}
  if((ResourceHash $archive.Files[$key]) -cne $native[$depot]){throw "Official bytes differ: $depot"}
  $found[$depot]=$native[$depot]
 }}
 $after=Get-Item -LiteralPath $path;if($before.Length -ne $after.Length -or $before.LastWriteTimeUtc -ne $after.LastWriteTimeUtc){throw 'Official archive changed'}
 $officialRows+=,@{path=$path;length=$after.Length;last_write_utc=$after.LastWriteTimeUtc.ToString('o')}
}
foreach($depot in $native.Keys){if(!$found.ContainsKey($depot)){throw "Official resource not found: $depot"}}
foreach($p in $pins.GetEnumerator()){if((SHA $p.Key) -cne $p.Value){throw 'Source changed during audit'}}
foreach($p in $archivePins.GetEnumerator()){if((SHA $p.Key) -cne $p.Value){throw 'Installed archive changed during audit'}}
if(@(Compare-Object @($mods.Name) @(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.archive'|Sort-Object Name|ForEach-Object Name)).Count -ne 0){throw 'Installed archive set changed'}
foreach($p in $xlPins.GetEnumerator()){if((SHA $p.Key) -cne $p.Value){throw 'Installed XL changed during audit'}}
if((@($xlPins.Keys|Sort-Object)-join '|') -cne (@(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.xl'|ForEach-Object FullName|Sort-Object)-join '|')){throw 'Installed XL set changed during audit'}
$r=@{status='PASS_RESOURCE_AUDIT';build_sha256=SHA $manifest;checker_sha256=SHA $PSCommandPath;official_comparisons=$native.Count;official_resources=$found;official_archives=$officialRows;installed_archives=$mods.Count;archive_pins=$archivePins;xl_pins=$xlPins;collisions=$collisions;new_overrides_first=$true;modlist_absent=$true;official_overrides=@();live_pending=$true}
[IO.File]::WriteAllText($dest,($r|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$r.status;official_comparisons=$native.Count;installed_archives=$mods.Count;expected_collisions=$collisions.Count}|ConvertTo-Json

param([string]$Revision='s22_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($Revision -cnotmatch '^s22_\d{2}$'){throw 'Invalid revision'}
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$build=Join-Path $PSScriptRoot ('build/'+$Revision);$manifest=Join-Path $build 'build.json';$dest=Join-Path $build 'resource_check.json'
if(Test-Path $dest){throw 'Evidence already exists'}
$m=Get-Content $manifest -Raw|ConvertFrom-Json
function SHA($p){return (Get-FileHash -LiteralPath $p).Hash}
function ResourceHash($entry){$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}}
$native=@{};$wanted=@{};$pins=@{}
foreach($p in $m.source_pins.PSObject.Properties){
 if([IO.Path]::IsPathRooted($p.Name) -or $p.Name -match '(^|/)\.\.(/|$)'){throw 'Unsafe source pin'}
 $full=Join-Path $workspace $p.Name;if((SHA $full) -cne $p.Value){throw "Source drift: $($p.Name)"};$pins[$full]=$p.Value
 if($p.Name -match '^research/.+/raw/((base|ep1)/.+)$'){$depot=$Matches[1].Replace('/','\');if($native.ContainsKey($depot) -and $native[$depot] -cne $p.Value){throw 'Conflicting official extraction'};$native[$depot]=$p.Value;$wanted[$depot]=$p.Value}
}
if($native.Count -lt 15 -or @($m.resources.PSObject.Properties).Count -ne 8 -or @($m.boots).Count -ne 5){throw 'Incomplete bundle scope'}
foreach($p in $m.resources.PSObject.Properties){if($p.Name -notlike 'towercontinued\*' -or $native.ContainsKey($p.Name)){throw 'Official override forbidden'};if((SHA (Join-Path (Join-Path $build 'source') $p.Name)) -cne $p.Value){throw 'Resource drift'};$wanted[$p.Name]=$p.Value}
if(@($m.official_overrides).Count -ne 0 -or @($m.mod_overrides).Count -ne 1 -or $m.mod_overrides[0] -cne 'towercontinued\gig_phone_u9\fixer_cleanup.questphase'){throw 'Unexpected override scope'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$modRoot=Join-Path $game 'archive/pc/mod'
if(Test-Path (Join-Path $modRoot 'modlist.txt')){throw 'Explicit load order requires review'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$keys=@{}
foreach($depot in $wanted.Keys){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot);if($keys.ContainsKey($key) -and $keys[$key] -cne $depot){throw 'FNV collision'};$keys[$key]=$depot}
$archivePins=@{};$collisions=@();$found=@{};$officialRows=@()
$mods=@(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.archive'|Sort-Object Name)
foreach($file in $mods){
 $hash=SHA $file.FullName;$archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Bad installed archive'}
 foreach($key in $archive.Files.Keys){if($keys.ContainsKey([uint64]$key)){
  $depot=$keys[[uint64]$key]
  if($depot -cne 'towercontinued\gig_phone_u9\fixer_cleanup.questphase'){throw "Installed conflict: $($file.Name) $depot"}
  if($file.Name -cnotin @('00_TowerContinued_Courier_C1.archive','0_TowerContinued_NCPD_N1.archive','TowerContinued_PreAlpha.archive')){throw "Unreviewed cleanup override: $($file.Name)"}
  $collisions+=,@{archive=$file.Name;depot=$depot;resource_sha256=ResourceHash $archive.Files[$key]}
 }}
 if((SHA $file.FullName) -cne $hash){throw 'Archive changed during audit'};$archivePins[$file.FullName]=$hash
}
$c1=@($collisions|Where-Object {$_.archive -ceq '00_TowerContinued_Courier_C1.archive'})
if($c1.Count -ne 1 -or $c1[0].resource_sha256 -cne '910CEE6F3FCDBD61116B6B08303FBCAAB7037B6BC3E890239A2BE121F17579ED'){throw 'Current cleanup donor differs'}
$order=[string[]](@('000_TowerContinued_SideJobs_S22.archive')+@($collisions.archive));[Array]::Sort($order,[StringComparer]::OrdinalIgnoreCase)
if($order[0] -cne '000_TowerContinued_SideJobs_S22.archive'){throw 'New cleanup is not first'}
foreach($rel in @('archive/pc/content/basegame_4_gamedata.archive','archive/pc/ep1/ep1_2_gamedata.archive')){
 $path=Join-Path $game $rel;$before=Get-Item -LiteralPath $path;$archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Bad official archive'}
 foreach($depot in $native.Keys){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot);if($archive.Files.ContainsKey($key)){if((ResourceHash $archive.Files[$key]) -cne $native[$depot]){throw "Official bytes differ: $depot"};$found[$depot]=$native[$depot]}}
 foreach($p in $m.resources.PSObject.Properties){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p.Name);if($archive.Files.ContainsKey($key)){throw 'New resource collides with official game'}}
 $after=Get-Item -LiteralPath $path;if($before.Length -ne $after.Length -or $before.LastWriteTimeUtc -ne $after.LastWriteTimeUtc){throw 'Official archive changed'}
 $officialRows+=,@{path=$path;length=$after.Length;last_write_utc=$after.LastWriteTimeUtc.ToString('o')}
}
foreach($depot in $native.Keys){if(!$found.ContainsKey($depot)){throw "Official resource not found: $depot"}}
foreach($p in $pins.GetEnumerator()){if((SHA $p.Key) -cne $p.Value){throw 'Source changed during audit'}}
foreach($p in $archivePins.GetEnumerator()){if((SHA $p.Key) -cne $p.Value){throw 'Installed archive changed during audit'}}
if(@(Compare-Object @($mods.Name) @(Get-ChildItem $modRoot -File -Filter '*.archive'|Sort-Object Name|ForEach-Object Name)).Count -ne 0){throw 'Installed archive set changed'}
$r=@{status='PASS_RESOURCE_AUDIT';build_sha256=SHA $manifest;checker_sha256=SHA $PSCommandPath;official_comparisons=$native.Count;official_resources=$found;official_archives=$officialRows;installed_archives=$mods.Count;archive_pins=$archivePins;collisions=$collisions;new_cleanup_first=$true;modlist_absent=$true;official_overrides=@();live_pending=$true}
[IO.File]::WriteAllText($dest,($r|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$r.status;official_comparisons=$native.Count;installed_archives=$mods.Count;expected_collisions=$collisions.Count}|ConvertTo-Json

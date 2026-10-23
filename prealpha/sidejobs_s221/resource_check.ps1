param([string]$Revision='s221_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($Revision -cnotmatch '^s221_\d{2}$'){throw 'Invalid revision'}
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$build=Join-Path $PSScriptRoot ('build/'+$Revision);$manifest=Join-Path $build 'build.json';$dest=Join-Path $build 'resource_check.json'
if(Test-Path -LiteralPath $dest){throw 'Evidence exists'}
$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
$old=Get-Content -LiteralPath (Join-Path $workspace $m.prior_manifest) -Raw|ConvertFrom-Json
function SHA($p){return (Get-FileHash -LiteralPath $p).Hash}
function ResourceHash($entry){$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}}
$native=@{};$wanted=@{};$pins=@{}
foreach($p in $m.source_pins.PSObject.Properties){
 if([IO.Path]::IsPathRooted($p.Name) -or $p.Name -match '(^|/)\.\.(/|$)'){throw 'Unsafe source pin'}
 $full=Join-Path $workspace $p.Name;if((SHA $full) -cne $p.Value){throw "Source drift: $($p.Name)"};$pins[$full]=$p.Value
 if($p.Name -match '^research/.+/raw/((base|ep1)/.+)$'){$depot=$Matches[1].Replace('/','\');if($native.ContainsKey($depot) -and $native[$depot] -cne $p.Value){throw 'Conflicting stock extraction'};$native[$depot]=$p.Value;$wanted[$depot]=$p.Value}
}
if($native.Count -ne 57 -or @($m.resources.PSObject.Properties).Count -ne 8){throw 'Scope mismatch'}
foreach($p in $m.resources.PSObject.Properties){if($p.Name -notlike 'towercontinued\*' -or $native.ContainsKey($p.Name)){throw 'Official override forbidden'};$wanted[$p.Name]=$p.Value}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$modRoot=Join-Path $game 'archive/pc/mod'
if(Test-Path -LiteralPath (Join-Path $modRoot 'modlist.txt')){throw 'Explicit load order needs review'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$keys=@{}
foreach($depot in $wanted.Keys){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot);if($keys.ContainsKey($key) -and $keys[$key] -cne $depot){throw 'FNV collision'};$keys[$key]=$depot}
$archivePins=@{};$collisions=@();$found=@{};$installedReadbacks=0
$mods=@(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.archive'|Sort-Object Name)
foreach($file in $mods){
 $hash=SHA $file.FullName;$archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Bad installed archive'}
 foreach($key in $archive.Files.Keys){if($keys.ContainsKey([uint64]$key)){
  $depot=$keys[[uint64]$key];$actual=ResourceHash $archive.Files[$key]
  if($file.Name -ceq '000_TowerContinued_SideJobs_S22.archive'){
   if($hash -cne $m.old_sha256 -or $actual -cne $old.resources.$depot){throw 'Installed S22 donor differs'};$installedReadbacks++
  }else{
   if($depot -cne 'towercontinued\gig_phone_u9\fixer_cleanup.questphase' -or $file.Name -cnotin @('00_TowerContinued_Courier_C1.archive','0_TowerContinued_NCPD_N1.archive','TowerContinued_PreAlpha.archive')){throw "Unreviewed collision: $($file.Name) $depot"}
   $collisions+=,@{archive=$file.Name;depot=$depot;resource_sha256=$actual}
  }
 }}
 if((SHA $file.FullName) -cne $hash){throw 'Archive changed during audit'};$archivePins[$file.FullName]=$hash
}
if($installedReadbacks -ne 8 -or $collisions.Count -ne 3){throw 'Installed resource scope changed'}
$order=[string[]](@('000_TowerContinued_SideJobs_S22.archive')+@($collisions.archive));[Array]::Sort($order,[StringComparer]::OrdinalIgnoreCase)
if($order[0] -cne '000_TowerContinued_SideJobs_S22.archive'){throw 'Cleanup priority changed'}
$official=@()
foreach($rel in @('archive/pc/content/basegame_4_gamedata.archive','archive/pc/ep1/ep1_2_gamedata.archive')){
 $path=Join-Path $game $rel;$before=Get-Item -LiteralPath $path;$archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Bad official archive'}
 foreach($depot in $native.Keys){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot);if($archive.Files.ContainsKey($key)){if((ResourceHash $archive.Files[$key]) -cne $native[$depot]){throw "Official bytes differ: $depot"};$found[$depot]=$native[$depot]}}
 foreach($p in $m.resources.PSObject.Properties){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p.Name);if($archive.Files.ContainsKey($key)){throw 'Official collision'}}
 $after=Get-Item -LiteralPath $path;if($before.Length -ne $after.Length -or $before.LastWriteTimeUtc -ne $after.LastWriteTimeUtc){throw 'Official archive changed'}
 $official+=,@{path=$path;length=$after.Length;last_write_utc=$after.LastWriteTimeUtc.ToString('o')}
}
if($found.Count -ne $native.Count){throw 'Missing official source'}
foreach($p in $pins.GetEnumerator()){if((SHA $p.Key) -cne $p.Value){throw 'Source changed during audit'}}
foreach($p in $archivePins.GetEnumerator()){if((SHA $p.Key) -cne $p.Value){throw 'Installed archive changed'}}
if(@(Compare-Object @($mods.Name) @(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.archive'|Sort-Object Name|ForEach-Object Name)).Count){throw 'Archive set changed'}
$r=@{status='PASS_RESOURCE_AUDIT';build_sha256=SHA $manifest;checker_sha256=SHA $PSCommandPath;official_comparisons=$native.Count;official_resources=$found;official_archives=$official;installed_archives=$mods.Count;archive_pins=$archivePins;collisions=$collisions;installed_readbacks=$installedReadbacks;new_cleanup_first=$true;modlist_absent=$true;official_overrides=@();live_pending=$true}
[IO.File]::WriteAllText($dest,($r|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$r.status;official_comparisons=$native.Count;installed_archives=$mods.Count;installed_readbacks=$installedReadbacks}|ConvertTo-Json

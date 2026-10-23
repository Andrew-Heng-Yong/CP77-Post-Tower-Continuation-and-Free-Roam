param([string]$Revision='p1_07')
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly
$build=Join-Path $PSScriptRoot ('build/'+$Revision);$dest=Join-Path $build 'resource_check.json'
if(Test-Path $dest){throw 'Evidence pinned'}
$m=Get-Content (Join-Path $build 'build.json') -Raw|ConvertFrom-Json
$native=@{};$keys=@{};$new=@{}
foreach($p in $m.source_pins.PSObject.Properties){if($p.Name -match '^research/.+/raw/(.+)$'){$d=$Matches[1].Replace('/','\');$native[$d]=$p.Value;$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d)]=$d}}
foreach($p in $m.resources.PSObject.Properties){$k=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p.Name);$keys[$k]=$p.Name;$new[$k]=$true}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
if(Test-Path (Join-Path $game 'archive/pc/mod/modlist.txt')){throw 'Explicit priority list requires audit'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$mods=@();$found=@();$seen=@{}
foreach($a in Get-ChildItem (Join-Path $game 'archive/pc/mod') -File -Filter '*.archive'){
 $hash=(Get-FileHash $a.FullName).Hash;$arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($a.FullName,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($k in $arc.Files.Keys){if($keys.ContainsKey([uint64]$k)){throw "Installed collision: $($a.Name) $($keys[[uint64]$k])"}}
 if((Get-FileHash $a.FullName).Hash -cne $hash){throw 'Archive changed'};$mods+=,@{name=$a.Name;sha256=$hash}
}
foreach($a in Get-ChildItem (Join-Path $game 'archive/pc/content'),(Join-Path $game 'archive/pc/ep1') -File -Filter '*gamedata*.archive'){
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($a.FullName,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Official archive read failed'}
 foreach($k in $keys.Keys){if($arc.Files.ContainsKey($k)){
  if($new.ContainsKey($k)){throw 'Unexpected official override'}
  $p=$keys[$k];$mem=[IO.MemoryStream]::new();try{$arc.Files[$k].Extract($mem);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
  if($hash -cne $native[$p]){throw "Official source mismatch $p"};if($seen.ContainsKey($p)){throw 'Multiple official sources require priority audit'};$seen[$p]=$true;$found+=,@{depot=$p;sha256=$hash;archive=$a.FullName}
 }}
}
if($seen.Count -ne $native.Count){throw 'Not every native source verified'}
$report=@{status='PASS_NOT_LIVE';build_sha256=(Get-FileHash (Join-Path $build 'build.json')).Hash;checker_sha256=(Get-FileHash $PSCommandPath).Hash;official=$found;native_count=$native.Count;installed_archives=$mods;overrides=@();modlist_absent=$true;official_overrides=@()}
[IO.File]::WriteAllText($dest,($report|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
@{status=$report.status;official_resources=$found.Count;installed_archives=$mods.Count;overrides=0}|ConvertTo-Json

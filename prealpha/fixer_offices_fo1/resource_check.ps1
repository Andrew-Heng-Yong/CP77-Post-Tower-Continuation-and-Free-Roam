param([string]$Revision='fo1_01')
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly
$build=Join-Path $PSScriptRoot ('build/'+$Revision)
$dest=Join-Path $build 'resource_check.json';if(Test-Path $dest){throw 'Evidence pinned'}
$manifest=Get-Content (Join-Path $build 'build.json') -Raw|ConvertFrom-Json
$wanted=@{}
foreach($p in $manifest.source_pins.PSObject.Properties){
 if($p.Name -match '^research/fixer_offices_fo1/(parents|scenes)/raw/(.+)$'){$wanted[$Matches[2].Replace('/','\')]=$p.Value}
}
foreach($p in $manifest.resources.PSObject.Properties){$wanted[$p.Name]=$null}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$keys=@{};foreach($p in $wanted.Keys){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p)]=$p}
$mods=@();$found=@();$overrides=@()
foreach($a in Get-ChildItem (Join-Path $game 'archive/pc/mod') -File -Filter '*.archive'){
 $before=(Get-FileHash $a.FullName).Hash;$arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($a.FullName,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($k in $arc.Files.Keys){if($keys.ContainsKey([uint64]$k)){$overrides+=,@{archive=$a.Name;resource=$keys[[uint64]$k]}}}
 if((Get-FileHash $a.FullName).Hash -cne $before){throw 'Archive changed during audit'}
 $mods+=,@{name=$a.Name;sha256=$before}
}
if($overrides.Count){throw ('Native/new resource override found: '+($overrides|ConvertTo-Json -Compress))}
foreach($folder in @('parents','scenes')){
 $inventory=Get-Content (Join-Path $workspace "research/fixer_offices_fo1/$folder/inventory.json") -Raw|ConvertFrom-Json
 foreach($group in $inventory|Group-Object Archive){
  $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($group.Name,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Official archive read failed'}
  foreach($r in $group.Group){
   $k=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r.ResourcePath);$mem=[IO.MemoryStream]::new()
   try{$arc.Files[$k].Extract($mem);$sha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
   if($sha -cne $wanted[$r.ResourcePath]){throw "Official bytes differ $($r.ResourcePath)"}
   $found+=,@{depot=$r.ResourcePath;sha256=$sha;archive=$group.Name}
  }
 }
}
$report=@{status='PASS_NOT_LIVE';build_sha256=(Get-FileHash (Join-Path $build 'build.json')).Hash;checker_sha256=(Get-FileHash $PSCommandPath).Hash;official=$found;installed_archives=$mods;overrides=$overrides}
[IO.File]::WriteAllText($dest,($report|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
@{status=$report.status;official_resources=$found.Count;installed_archives=$mods.Count;overrides=$overrides.Count}|ConvertTo-Json

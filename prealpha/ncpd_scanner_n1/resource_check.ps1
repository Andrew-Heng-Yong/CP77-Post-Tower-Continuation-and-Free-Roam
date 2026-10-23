param([string]$Revision='n1_01')
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly
$build=Join-Path $PSScriptRoot ('build/'+$Revision)
$dest=Join-Path $build 'resource_check.json';if(Test-Path $dest){throw 'Evidence pinned'}
$manifest=Get-Content (Join-Path $build 'build.json') -Raw|ConvertFrom-Json
$wanted=@{}
foreach($p in $manifest.source_pins.PSObject.Properties){
 if($p.Name -match '^research/(ncpd_scanner_n1|gig_restoration/gig_phone_u9)/.+/raw/(.+)$'){$wanted[$Matches[2].Replace('/','\')]=$p.Value}
}
$native=@{};foreach($k in $wanted.Keys){$native[$k]=$wanted[$k]}
foreach($p in $manifest.resources.PSObject.Properties){$wanted[$p.Name]=$null}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
if(Test-Path (Join-Path $game 'archive/pc/mod/modlist.txt')){throw 'Explicit load order needs separate audit'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$keys=@{};foreach($p in $wanted.Keys){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p)]=$p}
$mods=@();$found=@();$overrides=@()
$expected='towercontinued\gig_phone_u9\fixer_cleanup.questphase'
foreach($a in Get-ChildItem (Join-Path $game 'archive/pc/mod') -File -Filter '*.archive'){
 $before=(Get-FileHash $a.FullName).Hash;$arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($a.FullName,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($k in $arc.Files.Keys){if($keys.ContainsKey([uint64]$k)){
  $resource=$keys[[uint64]$k]
  if($resource -cne $expected -or $a.Name -cne 'TowerContinued_PreAlpha.archive'){throw "Unexpected override: $($a.Name) $resource"}
  $mem=[IO.MemoryStream]::new();try{$arc.Files[$k].Extract($mem);$sha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
  if($sha -cne (Get-FileHash (Join-Path $workspace $manifest.previous_cleanup)).Hash){throw 'Installed U9 cleanup does not match source'}
  $overrides+=,@{archive=$a.Name;resource=$resource;old_sha256=$sha}
 }}
 if((Get-FileHash $a.FullName).Hash -cne $before){throw 'Archive changed during audit'}
 $mods+=,@{name=$a.Name;sha256=$before}
}
if($overrides.Count -ne 1){throw 'Expected exactly one mod-owned cleanup override'}
# Recompare all copied/referenced native phase/scene sources against their exact
# current official archive bytes. No native source is overridden by this patch.
$official=Join-Path $game 'archive/pc/content/basegame_4_gamedata.archive';$arc=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($official,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Official archive read failed'}
foreach($p in $native.Keys){
 $k=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p);$mem=[IO.MemoryStream]::new()
 try{$arc.Files[$k].Extract($mem);$sha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
 if($sha -cne $native[$p]){throw "Official bytes differ $p"}
 $found+=,@{depot=$p;sha256=$sha;archive=$official}
}
$report=@{status='PASS_NOT_LIVE';build_sha256=(Get-FileHash (Join-Path $build 'build.json')).Hash;checker_sha256=(Get-FileHash $PSCommandPath).Hash;official=$found;installed_archives=$mods;overrides=$overrides;modlist_absent=$true;priority='0_TowerContinued_NCPD_N1.archive precedes TowerContinued_PreAlpha.archive; default first-match order';official_overrides=@()}
[IO.File]::WriteAllText($dest,($report|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
@{status=$report.status;official_resources=$found.Count;installed_archives=$mods.Count;expected_mod_override=$overrides.Count}|ConvertTo-Json

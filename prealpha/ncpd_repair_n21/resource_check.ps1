param([string]$Revision='n21_01')
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly
$build=Join-Path $PSScriptRoot ('build/'+$Revision)
$dest=Join-Path $build 'resource_check.json';if(Test-Path $dest){throw 'Preserve evidence'}
$manifest=Get-Content (Join-Path $build 'build.json') -Raw|ConvertFrom-Json
$old=Get-Content (Join-Path $workspace 'prealpha/ncpd_scanners_n2/build/n2_05/build.json') -Raw|ConvertFrom-Json
$native=@{}
foreach($p in $old.source_pins.PSObject.Properties){
 if($p.Name -match '^research/(ncpd_scanner_n1|ncpd_scanners_n2)/.+/raw/(.+)$'){$native[$Matches[2].Replace('/','\')]=$p.Value}
}
$wanted=@{};foreach($k in $native.Keys){$wanted[$k]=$native[$k]}
foreach($p in $manifest.resources.PSObject.Properties){$wanted[$p.Name]=$null}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
if(Test-Path (Join-Path $game 'archive/pc/mod/modlist.txt')){throw 'Explicit load order needs separate audit'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$keys=@{};foreach($p in $wanted.Keys){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p)]=$p}
$mods=@();$found=@()
foreach($a in Get-ChildItem (Join-Path $game 'archive/pc/mod') -File -Filter '*.archive'){
 $before=(Get-FileHash $a.FullName).Hash;$arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($a.FullName,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($k in $arc.Files.Keys){if($keys.ContainsKey([uint64]$k)){throw "Unexpected native/new-resource collision: $($a.Name) $($keys[[uint64]$k])"}}
 if((Get-FileHash $a.FullName).Hash -cne $before){throw 'Archive changed during audit'}
 $mods+=,@{name=$a.Name;sha256=$before}
}
$official=Join-Path $game 'archive/pc/content/basegame_4_gamedata.archive';$arc=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($official,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Official read failed'}
foreach($p in $native.Keys){
 $k=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p);$mem=[IO.MemoryStream]::new()
 try{$arc.Files[$k].Extract($mem);$sha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
 if($sha -cne $native[$p]){throw "Official bytes differ $p"};$found+=,@{depot=$p;sha256=$sha}
}
$report=@{status='PASS_NOT_LIVE';build_sha256=(Get-FileHash (Join-Path $build 'build.json')).Hash;checker_sha256=(Get-FileHash $PSCommandPath).Hash;official=$found;installed_archives=$mods;overrides=@();modlist_absent=$true;official_overrides=@()}
[IO.File]::WriteAllText($dest,($report|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
@{status=$report.status;official_resources=$found.Count;installed_archives=$mods.Count;overrides=0}|ConvertTo-Json

$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$base=Get-Content -LiteralPath (Join-Path $ws 'prealpha/world_support_wa3/candidate_02/install_manifest_01.json') -Raw|ConvertFrom-Json
$m=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'candidate_02/install_manifest_01.json') -Raw|ConvertFrom-Json
$new=@($m.external_archives|Where-Object {$_.path -cnotin @($base.archive_paths)})
if($new.Count -ne 5){throw 'Unexpected added archive set'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$own=@{};$source=Join-Path $PSScriptRoot 'candidate_02/archive_source'
foreach($f in Get-ChildItem -LiteralPath $source -Recurse -File){$name=[IO.Path]::GetRelativePath($source,$f.FullName).Replace('/','\');$own[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($name)]=$name}
if($own.Count -ne 1563){throw 'Own member set changed'}
$hits=@()
foreach($p in $new){
 $file=Join-Path $m.game_root $p.path
 if((Get-FileHash -LiteralPath $file).Hash -cne $p.sha256){throw 'External archive drift'}
 $archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($key in $archive.Files.Keys){if($own.ContainsKey($key)){$hits+=@{path=$p.path;depot=$own[$key]}}}
}
if($hits.Count){throw ('New archive resource collision '+($hits|ConvertTo-Json -Compress))}
@{status='PASS';added_archives=5;own_resources=1563;collisions=0;game_writes=0}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'candidate_02/new_archive_winners_02.json') -Encoding utf8
@{status='PASS';added_archives=5;collisions=0}|ConvertTo-Json

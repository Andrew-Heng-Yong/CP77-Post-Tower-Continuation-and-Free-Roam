# Add one private cleanup phase; preserve all 1,748 installed resource payloads.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$work=Join-Path $PSScriptRoot 'work'
$pins=Get-Content -LiteralPath (Join-Path $work 'inputs.json') -Raw|ConvertFrom-Json -AsHashtable
$proof=Get-Content -LiteralPath (Join-Path $work 'assessment.json') -Raw|ConvertFrom-Json -AsHashtable
$phase=Get-Content -LiteralPath (Join-Path $work 'graph_01/manifest.json') -Raw|ConvertFrom-Json -AsHashtable
$compiled=Get-Content -LiteralPath (Join-Path $work 'compile_01/assessment.json') -Raw|ConvertFrom-Json -AsHashtable
$out=Join-Path $work 'archive_01'
if(Test-Path -LiteralPath $out){throw 'Fresh archive output required'}
$installed=Join-Path $pins.game 'archive/pc/mod/zzzz_PTFR_Combined.archive'
if($proof.status -cne 'PASS' -or $compiled.status -cne 'PASS' -or $proof.phase_sha256 -cne $phase.sha256 -or (Get-FileHash -LiteralPath $phase.path).Hash -cne $phase.sha256 -or (Get-FileHash -LiteralPath $installed).Hash -cne $pins.archive_sha256){throw 'Qualified input drift'}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
function OpenArc([string]$path){$a=$null;if($reader.ReadArchive($path,$hs,[ref]$a).ToString() -cne 'NoError'){throw "Unreadable archive: $path"};return $a}
function Key([string]$depot){[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)}
function MemberHash($entry){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);$m.Position=0;[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m))}finally{$m.Dispose()}}
function Plain([string]$path){for($item=Get-Item -LiteralPath $path -Force;$null -ne $item;){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Linked path: $path"};$item=if($item -is [IO.FileInfo]){$item.Directory}else{$item.Parent}}}
$newKey=Key $pins.depot;$parentDepot='ep1\quest\ep1.quest';$parentKey=Key $parentDepot
$archives=@();$parents=@()
[void][IO.Directory]::CreateDirectory($out)
foreach($relative in @('archive/pc','mods')){
 $folder=Join-Path $pins.game $relative;if(-not(Test-Path -LiteralPath $folder)){continue}
 Plain $folder
 if(@(Get-ChildItem -LiteralPath $folder -Recurse -Force -Attributes ReparsePoint).Count){throw 'Linked archive tree'}
 foreach($f in Get-ChildItem -LiteralPath $folder -Recurse -File -Filter '*.archive'){
  $stamp=@($f.Length,$f.LastWriteTimeUtc.Ticks);$a=OpenArc $f.FullName
  if($a.Files.ContainsKey($newKey)){throw "New depot already has a provider: $($f.FullName)"}
  if($a.Files.ContainsKey($parentKey)){
   $raw=Join-Path $out ('parents/'+$f.BaseName+'/'+$parentDepot);[void][IO.Directory]::CreateDirectory((Split-Path $raw -Parent))
   $m=[IO.MemoryStream]::new();try{$a.Files[$parentKey].Extract($m);[IO.File]::WriteAllBytes($raw,$m.ToArray())}finally{$m.Dispose()}
   Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')
   $parents+=,@{archive=$f.FullName;depot=$parentDepot;path=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$raw+'.json';json_sha256=(Get-FileHash -LiteralPath ($raw+'.json')).Hash}
  }
  $f.Refresh();if($f.Length -ne $stamp[0] -or $f.LastWriteTimeUtc.Ticks -ne $stamp[1]){throw 'Provider changed during lookup'}
  $archives+=,@{path=$f.FullName;bytes=$f.Length;mtime=$f.LastWriteTimeUtc.Ticks}
 }
}
if($parents.Count -ne 1 -or [IO.Path]::GetFileName($parents[0].archive) -cne 'ep1_2_gamedata.archive'){throw 'Native parent provider requires review'}
$current=OpenArc $installed
Plain $pins.archive_source
if(@(Get-ChildItem -LiteralPath $pins.archive_source -Recurse -Force -Attributes ReparsePoint).Count){throw 'Linked donor tree'}
$source=Join-Path $out 'source';[void][IO.Directory]::CreateDirectory($source)
$expected=@{}
foreach($file in Get-ChildItem -LiteralPath $pins.archive_source -Recurse -File){
 $depot=[IO.Path]::GetRelativePath($pins.archive_source,$file.FullName);$key=Key $depot
 if($expected.ContainsKey($key) -or -not $pins.members.Contains($depot) -or -not $current.Files.ContainsKey($key)){throw "Unexpected donor: $depot"}
 $h=(Get-FileHash -LiteralPath $file.FullName).Hash
 if($h -cne $pins.members[$depot] -or $h -cne (MemberHash $current.Files[$key])){throw "Source/current payload drift: $depot"}
 $dest=Join-Path $source $depot;[void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent));[IO.File]::Copy($file.FullName,$dest,$false)
 $expected[$key]=@{depot=$depot;sha256=$h}
}
if($expected.Count -ne 1748 -or $current.Files.Count -ne 1748){throw 'Current full archive inventory drift'}
$dest=Join-Path $source $pins.depot;[void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent));[IO.File]::Copy($phase.path,$dest,$false)
$expected[$newKey]=@{depot=$pins.depot;sha256=$phase.sha256}
$packed=Join-Path $out 'zzzz_PTFR_Combined.archive';$stream=[IO.File]::Open($packed,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try{if(-not([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Packing failed'}}finally{$stream.Dispose()}
$readback=OpenArc $packed
if($readback.Files.Count -ne 1749){throw 'Packed member inventory drift'}
foreach($key in $expected.Keys){if(-not $readback.Files.ContainsKey($key) -or (MemberHash $readback.Files[$key]) -cne $expected[$key].sha256){throw "Packed member drift: $($expected[$key].depot)"}}
if((Get-FileHash -LiteralPath $installed).Hash -cne $pins.archive_sha256){throw 'Installed baseline changed during packing'}
@{status='MEMBERS_VERIFIED';archive_sha256=(Get-FileHash -LiteralPath $packed).Hash;scanned_archives=$archives.Count;archive_inventory=$archives;new_depot=$pins.depot;unchanged_members=1748;members=@($expected.Values|Sort-Object depot);native_parents=$parents;native_resource_changes=0}|ConvertTo-Json -Depth 7|Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output 'Verified all 1,749 packed resources: 1,748 byte-identical and one new private cleanup phase.'

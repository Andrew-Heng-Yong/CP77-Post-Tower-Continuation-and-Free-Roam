param([Parameter(Mandatory=$true)][string]$Candidate,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$workspace=(Get-Location).Path
$candidatePath=(Resolve-Path -LiteralPath $Candidate).Path
if(-not(Test-Path -LiteralPath (Join-Path $candidatePath 'package_manifest.json'))){throw 'Final package manifest required; wait for root packer completion'}
if(Test-Path -LiteralPath $Output){throw 'Fresh archive-review output required'}
New-Item -ItemType Directory -Path $Output|Out-Null
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$source=(Resolve-Path -LiteralPath (Join-Path $candidatePath 'archive_source')).Path
$archivePath=Join-Path $candidatePath 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
$expected=@{}
foreach($file in Get-ChildItem -LiteralPath $source -Recurse -File){
 $depot=[IO.Path]::GetRelativePath($source,$file.FullName).Replace('/','\')
 $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
 if($expected.ContainsKey([string]$key)){throw 'Source depot FNV collision'}
 $expected[[string]$key]=@{depot=$depot;source_sha256=(Get-FileHash -LiteralPath $file.FullName).Hash;source=$file.FullName}
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Read of final candidate archive failed'}
if($archive.Files.Count -ne $expected.Count){throw 'Packed/source resource-count mismatch'}
$rows=@()
foreach($entry in $archive.Files.GetEnumerator()){
 $key=[string]$entry.Key
 if(-not $expected.ContainsKey($key)){throw 'Unlisted packed resource key'}
 $e=$expected[$key];$memory=[IO.MemoryStream]::new()
 try{$entry.Value.Extract($memory);$actual=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}finally{$memory.Dispose()}
 if($actual -cne $e.source_sha256){throw ('Packed payload differs from staged source: '+$e.depot)}
 $rows+=@{key=$key;depot=$e.depot;packed_sha256=$actual;source_sha256=$e.source_sha256;source=$e.source}
}
$result=@{status='PASS_INDEPENDENT_FINAL_ARCHIVE_READBACK';candidate=$candidatePath;archive=$archivePath;archive_sha256=(Get-FileHash -LiteralPath $archivePath).Hash;resources=$rows;count=$rows.Count;scope='Read candidate archive into memory; no rebuild, extraction to runtime, game, install or save writes'}
$result|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $Output 'readback.json') -Encoding utf8
Write-Output ('Independently verified '+$rows.Count+' packed resource keys/payloads')

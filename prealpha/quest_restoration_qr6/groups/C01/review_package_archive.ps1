param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=(Get-Location).Path
$epoch=Get-Content -LiteralPath (Join-Path $workspace 'prealpha/quest_restoration_qr6/source_epoch_00.json') -Raw|ConvertFrom-Json
$target=[IO.Path]::GetFullPath((Join-Path $workspace $Output))
if(-not $target.StartsWith((Join-Path $workspace 'prealpha/quest_restoration_qr6/groups/C01/reviews/'),[StringComparison]::OrdinalIgnoreCase)){throw 'Review output containment'}
if(Test-Path -LiteralPath $target){throw 'Fresh review output required'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$source=Join-Path $epoch.candidate 'archive_source';$archivePath=Join-Path $epoch.candidate 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
$sources=@{}
foreach($f in [IO.Directory]::EnumerateFiles($source,'*',[IO.SearchOption]::AllDirectories)){
 $depot=[IO.Path]::GetRelativePath($source,$f).Replace('/','\');$key=[string][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
 if($sources.ContainsKey($key)){throw 'Source depot FNV collision'}
 $sources[$key]=@{depot=$depot;source=$f;sha256=(Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash}
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Archive read failed'}
if($archive.Files.Count -ne $sources.Count){throw 'Member/source count differs'}
$out=@()
foreach($entry in $archive.Files.GetEnumerator()){
 $key=[string]$entry.Key
 if(-not $sources.ContainsKey($key)){throw ('Unexpected archive payload key '+$key)}
 $mem=[IO.MemoryStream]::new()
 try{$entry.Value.Extract($mem);$bytes=$mem.ToArray();$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes));$length=$bytes.Length}finally{$mem.Dispose()}
 if($hash -cne $sources[$key].sha256){throw ('Packed bytes differ from actual staged source '+$sources[$key].depot)}
 $out+=@{key=$key;depot=$sources[$key].depot;source=$sources[$key].source;source_sha256=$sources[$key].sha256;packed_sha256=$hash;bytes=$length}
}
New-Item -ItemType Directory -Path $target|Out-Null
$result=@{status='PASS_READ_ONLY_ALL_ARCHIVE_MEMBER_MEMORY_READBACKS';archive=$archivePath;archive_sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash;candidate=$epoch.candidate;resources=$out;count=$out.Count;writes='Only this JSON review output; no candidate, package, game, save or resource serialization writes'}
[IO.File]::WriteAllText((Join-Path $target 'readback.json'),($result|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
@{resources=$out.Count;archive_sha256=$result.archive_sha256;output=$target}|ConvertTo-Json -Compress

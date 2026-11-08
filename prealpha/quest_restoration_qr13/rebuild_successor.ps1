param([Parameter(Mandatory=$true)][string]$Epoch)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$e=Get-Content -LiteralPath $Epoch -Raw|ConvertFrom-Json -Depth 100
$candidate=[IO.Path]::GetFullPath($e.candidate)
if(-not $candidate.StartsWith([IO.Path]::GetFullPath($PSScriptRoot)+[IO.Path]::DirectorySeparatorChar)){throw 'QR13 candidate containment required'}
$source=Join-Path $candidate 'archive_source';$package=Join-Path $candidate 'package';$result=Join-Path $candidate 'rebuild_01.json'
if(Test-Path -LiteralPath $result){throw 'Preserve prior rebuild'}
if($e.package_state -cne 'SOURCE_AND_SCRIPTS_VERIFIED_PACKAGE_PENDING'){throw 'Final source/REDscript approval required'}
foreach($root in @($source,$package)){
 if((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked root'}
 if(@(Get-ChildItem -LiteralPath $root -Recurse -Force|Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'Linked candidate input'}
}
$expected=@{};foreach($r in $e.source_resources.PSObject.Properties){$expected[$r.Name]=$r.Value}
$files=@(Get-ChildItem -LiteralPath $source -File -Recurse);if($files.Count -ne $expected.Count){throw 'Source inventory mismatch'}
foreach($f in $files){$dep=[IO.Path]::GetRelativePath($source,$f.FullName);if(-not $expected.ContainsKey($dep) -or(Get-FileHash -LiteralPath $f.FullName).Hash -cne $expected[$dep]){throw "Unapproved source $dep"}}
$pfiles=@(Get-ChildItem -LiteralPath $package -File -Recurse);if($pfiles.Count -ne @($e.package_prebuild_sha256.PSObject.Properties).Count){throw 'Package input inventory mismatch'}
foreach($r in $e.package_prebuild_sha256.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $package $r.Name)).Hash -cne $r.Value){throw "Unapproved package input $($r.Name)"}}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive';$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Packing failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError'){throw 'Packed archive unreadable'}
if($packed.Files.Count -ne $expected.Count){throw 'Packed member inventory mismatch'}
$rows=@();$keys=@{}
foreach($dep in($expected.Keys|Sort-Object)){
 $key=[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($dep);if($keys.ContainsKey($key.ToString())){throw 'Depot FNV collision'};$keys[$key.ToString()]=$dep
 if(-not $packed.Files.ContainsKey($key)){throw "Missing packed depot $dep"}
 $mem=[IO.MemoryStream]::new();try{$packed.Files[$key].Extract($mem);$actual=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
 if($actual -cne $expected[$dep]){throw "Packed payload mismatch $dep"};$rows+=@{depot=$dep;key=$key.ToString();sha256=$actual}
}
@{status='PASS_QR13_FULL_CONSOLIDATED_ARCHIVE_READBACK';epoch=$Epoch;epoch_sha256=(Get-FileHash -LiteralPath $Epoch).Hash;source_count=$files.Count;readback_count=$rows.Count;resources=$rows;archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;xl_sha256=(Get-FileHash -LiteralPath ($archive+'.xl')).Hash;game_writes=0;save_writes=0;installed=$false}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $result -Encoding utf8NoBOM
@{status='PASS_QR13_FULL_CONSOLIDATED_ARCHIVE_READBACK';payloads=$rows.Count;installed=$false}|ConvertTo-Json

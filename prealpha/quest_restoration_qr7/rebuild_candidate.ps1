Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_01';$result=Join-Path $C 'rebuild_01.json'
if(Test-Path -LiteralPath $result){throw 'Preserve completed build; use fresh successor if inputs change'}
$epoch=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'source_epoch_03.json') -Raw|ConvertFrom-Json -Depth 100
$baseline=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'source_epoch_00.json') -Raw|ConvertFrom-Json -Depth 100
if($epoch.epoch_key -cne 'QR7:03' -or $epoch.package_state -cne 'SOURCE_FROZEN_ARCHIVE_PENDING_REBUILD'){throw 'Unexpected source epoch'}
$source=Join-Path $C 'archive_source';$package=Join-Path $C 'package'
foreach($root in @($source,$package)){
 if(-not [IO.Path]::GetFullPath($root).StartsWith([IO.Path]::GetFullPath($C)+[IO.Path]::DirectorySeparatorChar)){throw 'Containment failed'}
 if((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked source root'}
 if(@(Get-ChildItem -LiteralPath $root -Recurse -Force|Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'Linked build input'}
}
$expected=@{};foreach($prop in $epoch.source_resources.PSObject.Properties){$expected[$prop.Name]=$prop.Value}
$found=@{};foreach($f in Get-ChildItem -LiteralPath $source -File -Recurse){
 $dep=[IO.Path]::GetRelativePath($source,$f.FullName);$h=(Get-FileHash -LiteralPath $f.FullName).Hash
 if(-not $expected.ContainsKey($dep) -or $expected[$dep] -cne $h){throw "Unapproved source: $dep"};$found[$dep]=$h
}
if($found.Count -ne $expected.Count){throw 'Missing source inputs'}
foreach($row in $baseline.package_files){
 $f=Join-Path $package $row.path;$want=$row.sha256
 if($row.path -eq 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl' -or $row.path -eq 'archive\pc\mod\zzzz_PTFR_Combined.archive.xl'){$want=$epoch.xl_sha256}
 if((Get-FileHash -LiteralPath $f).Hash -cne $want){throw "Unapproved prebuild package change: $($row.path)"}
}
if(@(Get-ChildItem -LiteralPath $package -Recurse -File).Count -ne $baseline.package_files.Count){throw 'Unexpected package members'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Packing failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError'){throw 'Archive unreadable'}
if($packed.Files.Count -ne $expected.Count){throw 'Archive member inventory differs'}
$rows=@();$keys=@{}
foreach($dep in ($expected.Keys|Sort-Object)){
 $key=[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($dep)
 if($keys.ContainsKey($key.ToString())){throw 'Source FNV collision'};$keys[$key.ToString()]=$dep
 if(-not $packed.Files.ContainsKey($key)){throw "Missing packed depot $dep"}
 $mem=[IO.MemoryStream]::new()
 try{$packed.Files[$key].Extract($mem);$actual=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
 if($actual -cne $expected[$dep]){throw "Packed payload mismatch $dep"}
 $rows+=,@{depot=$dep;key=$key.ToString();sha256=$actual}
}
@{status='PASS_FULL_CONSOLIDATED_REBUILD_NOT_INSTALLED';epoch='QR7:03';source_count=$found.Count;readback_count=$rows.Count;resources=$rows;archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;xl_sha256=$epoch.xl_sha256;source_epoch_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'source_epoch_03.json')).Hash;game_writes=0;save_writes=0;installed=$false}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $result -Encoding utf8NoBOM
'PASS_FULL_CONSOLIDATED_REBUILD_NOT_INSTALLED'

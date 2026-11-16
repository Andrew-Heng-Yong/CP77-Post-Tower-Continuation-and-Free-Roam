Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'input_03/plan.json') -Raw | ConvertFrom-Json -Depth 100
$verification=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'validation_05/scene_verification.json') -Raw | ConvertFrom-Json -Depth 40
if($verification.status -cne 'PASS_JP1_COOKED_SEMANTIC_ALLOWLIST_AND_PICKUP_FLOW' -or $verification.plan_sha256 -cne (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'input_03/plan.json')).Hash){throw 'Unverified scene plan'}
$source=Join-Path $plan.candidate_directory 'archive_source'
$archiveOutput=Join-Path $plan.candidate_directory 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
$proof=Join-Path $PSScriptRoot 'validation_05/archive_readback.json'
if((Test-Path -LiteralPath $archiveOutput) -or (Test-Path -LiteralPath $proof)){throw 'Fresh archive and proof required'}
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$expected=@{}
foreach($f in Get-ChildItem -LiteralPath $source -Recurse -File){
    if($f.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked source refused'}
    $depot=[IO.Path]::GetRelativePath($source,$f.FullName).Replace('/','\')
    $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot).ToString()
    if($expected.ContainsKey($key)){throw 'Resource-depot collision'}
    $expected[$key]=@{depot=$depot;sha256=(Get-FileHash -LiteralPath $f.FullName).Hash}
}
if($expected.Count -ne 1581){throw 'Wrong full consolidated source inventory'}
$stream=[IO.File]::Create($archiveOutput)
try{
    $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
    if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive pack failed'}
}finally{$stream.Dispose()}
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$archive=$null
if($reader.ReadArchive($archiveOutput,$hashService,[ref]$archive).ToString() -cne 'NoError'){throw 'Archive reopen failed'}
if($archive.Files.Count -ne $expected.Count){throw 'Archive inventory mismatch'}
$rows=@(foreach($entry in $archive.Files.GetEnumerator()){
    $key=$entry.Key.ToString();if(-not $expected.ContainsKey($key)){throw 'Unexpected archive member'}
    $memory=[IO.MemoryStream]::new()
    try{[void]$entry.Value.Extract($memory);$digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}
    finally{$memory.Dispose()}
    if($digest -cne $expected[$key].sha256){throw 'Archive payload readback mismatch'}
    @{key=$key;depot=$expected[$key].depot;sha256=$digest}
})
@{status='PASS_ALL_JP1_ARCHIVE_MEMBERS';archive_sha256=(Get-FileHash -LiteralPath $archiveOutput).Hash;
  resources=$rows;game_writes=0;save_writes=0} | ConvertTo-Json -Depth 10 |
    Set-Content -LiteralPath $proof -Encoding utf8NoBOM
Write-Output "Packed and verified all $($rows.Count) consolidated payloads"

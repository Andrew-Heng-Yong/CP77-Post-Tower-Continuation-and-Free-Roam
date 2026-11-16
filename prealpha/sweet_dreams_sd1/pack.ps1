Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'input_02/plan.json') -Raw|ConvertFrom-Json -Depth 45
$proof=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'verification.json') -Raw|ConvertFrom-Json -Depth 30
if($proof.status -cne 'PASS_SD1_COOKED_PRESENTATION_AND_COMPLETION_CONTRACTS' -or $proof.plan_sha256 -cne (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'input_02/plan.json')).Hash){throw 'Unverified input plan'}
$source=Join-Path $plan.candidate 'archive_source'
$target=Join-Path $plan.candidate 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
$proofPath=Join-Path $PSScriptRoot 'archive_readback.json'
if((Test-Path -LiteralPath $target) -or (Test-Path -LiteralPath $proofPath)){throw 'Fresh archive/proof required'}
$hashes=[WolvenKit.Common.Services.HashService]::new();$hashes.Load();$expected=@{}
foreach($f in Get-ChildItem -LiteralPath $source -Recurse -File){
 if($f.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked source refused'}
 $depot=[IO.Path]::GetRelativePath($source,$f.FullName).Replace('/','\')
 $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot).ToString()
 if($expected.ContainsKey($key)){throw 'Depot-key collision'}
 $expected[$key]=@{depot=$depot;sha256=(Get-FileHash -LiteralPath $f.FullName).Hash}
}
if($expected.Count -ne 1581){throw 'Wrong full source inventory'}
$stream=[IO.File]::Create($target)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashes,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Packing failed'}}finally{$stream.Dispose()}
$archive=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($target,$hashes,[ref]$archive).ToString() -cne 'NoError' -or $archive.Files.Count -ne 1581){throw 'Archive reopen/inventory failed'}
$rows=@(foreach($entry in $archive.Files.GetEnumerator()){
 $key=$entry.Key.ToString();if(-not $expected.ContainsKey($key)){throw 'Unexpected member'}
 $memory=[IO.MemoryStream]::new()
 try{[void]$entry.Value.Extract($memory);$digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}finally{$memory.Dispose()}
 if($digest -cne $expected[$key].sha256){throw 'Payload readback mismatch'}
 @{depot=$expected[$key].depot;key=$key;sha256=$digest}
})
@{status='PASS_ALL_SD1_ARCHIVE_MEMBERS';archive_sha256=(Get-FileHash -LiteralPath $target).Hash;resources=$rows;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $proofPath -Encoding utf8NoBOM
Write-Output "Packed and verified all $($rows.Count) payloads."

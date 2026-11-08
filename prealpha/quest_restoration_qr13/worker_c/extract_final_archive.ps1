param([Parameter(Mandatory=$true)][string]$Inputs,[Parameter(Mandatory=$true)][string]$Output)
# Independent read/extraction only. No ArchiveWriter, installer or candidate writes.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=(Get-Location).Path;$worker=[IO.Path]::GetFullPath($PSScriptRoot)
$taskOut=[IO.Path]::GetFullPath((Join-Path $workspace $Output))
if(-not $taskOut.StartsWith($worker+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Worker-C-contained output required'}
if(Test-Path -LiteralPath $taskOut){throw 'Fresh output required'}
foreach($target in @($worker,(Split-Path $taskOut -Parent))){
 $check=$target
 while($check -and (Test-Path -LiteralPath $check)){
  if((Get-Item -LiteralPath $check).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked output refused'}
  $next=Split-Path $check -Parent;if($next -eq $check){break};$check=$next
 }
}
$pins=Get-Content -LiteralPath $Inputs -Raw|ConvertFrom-Json -Depth 100
if($pins.status -cne 'FROZEN_INDEPENDENT_QR13_FINAL_PACKAGE_INPUTS'){throw 'Independent input freeze required'}
if((Get-FileHash -LiteralPath $pins.epoch).Hash -cne $pins.epoch_sha256){throw 'Frozen epoch changed'}
$file=Get-Item -LiteralPath $pins.archive
if($file.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked archive refused'}
$before=@($file.Length,$file.LastWriteTimeUtc.Ticks);$archiveSHA=(Get-FileHash -LiteralPath $file.FullName).Hash
if($archiveSHA -cne $pins.archive_sha256){throw 'Final archive drift'}
New-Item -ItemType Directory -Path $taskOut|Out-Null
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$expected=@{}
foreach($p in $pins.expected_resources.PSObject.Properties){
 $key=[string][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p.Name)
 if($expected.ContainsKey($key)){throw 'Independent expected depot FNV collision'}
 $expected[$key]=@{depot=$p.Name;sha256=$p.Value}
}
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load();$archive=$null
$readStatus=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hashService,[ref]$archive).ToString()
if($readStatus -cne 'NoError'){throw 'Archive index unreadable'}
$memberDir=Join-Path $taskOut 'members';New-Item -ItemType Directory -Path $memberDir|Out-Null
$rows=@()
foreach($entry in $archive.Files.GetEnumerator()){
 $key=[string]$entry.Key;$raw=Join-Path $memberDir ($key+'.bin');$mem=[IO.MemoryStream]::new()
 try{$entry.Value.Extract($mem);[IO.File]::WriteAllBytes($raw,$mem.ToArray())}finally{$mem.Dispose()}
 $known=$expected.ContainsKey($key);$row=@{fnv64=$key;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;bytes=(Get-Item -LiteralPath $raw).Length;expected_key=$known}
 if($known){
  $row.depot=$expected[$key].depot
  if($pins.changed_resources -contains $row.depot){
   $json=$raw+'.json';Export-Cr2wJson (Read-Cr2wFile $raw) $json
   $row.json=$json;$row.json_sha256=(Get-FileHash -LiteralPath $json).Hash;$row.typed_status='ACTUAL_FINAL_ARCHIVE_MEMBER_READ_BACK'
  }
 }
 $rows+=,$row
}
$file.Refresh()
if($file.Length -ne $before[0] -or $file.LastWriteTimeUtc.Ticks -ne $before[1] -or (Get-FileHash -LiteralPath $file.FullName).Hash -cne $archiveSHA){throw 'Archive changed during extraction'}
@{status='INDEPENDENT_COMPLETE_FINAL_ARCHIVE_EXTRACTED';inputs=[IO.Path]::GetFullPath($Inputs);inputs_sha256=(Get-FileHash -LiteralPath $Inputs).Hash;archive=$file.FullName;archive_sha256=$archiveSHA;archive_bytes=$before[0];read_status=$readStatus;members=$rows;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;candidate_writes=0;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 25|Set-Content -LiteralPath (Join-Path $taskOut 'manifest.json') -Encoding utf8NoBOM
Write-Output ('Independently extracted all '+$rows.Count+' actual final archive members')

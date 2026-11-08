param([Parameter(Mandatory=$true)][string]$Inputs,[Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$taskRoot=(Get-Location).Path;$worker=[IO.Path]::GetFullPath($PSScriptRoot)
$taskOut=[IO.Path]::GetFullPath((Join-Path $taskRoot $Output))
if(-not $taskOut.StartsWith($worker+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Private worker containment required'}
if(Test-Path -LiteralPath $taskOut){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $taskOut|Out-Null
. (Join-Path $taskRoot 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $taskRoot 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$pins=Get-Content -LiteralPath $Inputs -Raw|ConvertFrom-Json
$file=Get-Item -LiteralPath $pins.archive;$before=@($file.Length,$file.LastWriteTimeUtc.Ticks);$archiveSHA=(Get-FileHash -LiteralPath $file.FullName).Hash
if($archiveSHA -ne $pins.archive_sha256){throw 'Final archive drift'}
$expected=@{}
foreach($p in $pins.canonical_resources.PSObject.Properties){
 $key=[string][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p.Name)
 if($expected.ContainsKey($key)){throw 'Canonical depot FNV collision'}
 $expected[$key]=@{depot=$p.Name;sha256=$p.Value}
}
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load();$archive=$null
$readStatus=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hashService,[ref]$archive).ToString()
if($readStatus -ne 'NoError'){throw 'Archive index unreadable'}
$memberDir=Join-Path $taskOut 'members';New-Item -ItemType Directory -Path $memberDir|Out-Null
$rows=@()
foreach($entry in $archive.Files.GetEnumerator()){
 $key=[string]$entry.Key;$raw=Join-Path $memberDir ($key+'.bin');$memory=[IO.MemoryStream]::new()
 try{$entry.Value.Extract($memory);[IO.File]::WriteAllBytes($raw,$memory.ToArray())}finally{$memory.Dispose()}
 $known=$expected.ContainsKey($key);$row=@{fnv64=$key;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;bytes=(Get-Item -LiteralPath $raw).Length;canonical_key=$known}
 if($known){
  $row.depot=$expected[$key].depot
  if($pins.changed -contains $row.depot){
   $json=$raw+'.json';Export-Cr2wJson (Read-Cr2wFile $raw) $json;$row.json=$json;$row.json_sha256=(Get-FileHash -LiteralPath $json).Hash;$row.typed_status='FRESH_ACTUAL_FINAL_ARCHIVE_MEMBER'
  }
 }
 $rows+=,$row
}
$file.Refresh();if($file.Length -ne $before[0] -or $file.LastWriteTimeUtc.Ticks -ne $before[1]){throw 'Archive changed during extraction'}
@{status='INDEPENDENT_WHOLE_FINAL_ARCHIVE_EXTRACTION';input=$Inputs;input_sha256=(Get-FileHash -LiteralPath $Inputs).Hash;archive=$pins.archive;archive_sha256=$archiveSHA;archive_size=$before[0];archive_mtime_utc_ticks=$before[1];read_status=$readStatus;members=$rows;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;candidate_writes=0;game_writes=0}|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $taskOut 'manifest.json') -Encoding utf8NoBOM
Write-Output ('Extracted every '+$rows.Count+' archive member independently')

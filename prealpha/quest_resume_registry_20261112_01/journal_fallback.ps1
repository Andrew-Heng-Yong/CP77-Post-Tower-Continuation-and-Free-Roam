# Read the exact current base journal with the already-present older decoder.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'evidence_03'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
$rows=@(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_02/resources.jsonl') | ForEach-Object {$_ | ConvertFrom-Json})
$original=@($rows | Where-Object {$_.depot -ceq 'base\journal\cooked_journal.journal'})[0]
$toolRoot='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $toolRoot
New-Item -ItemType Directory -Path $out | Out-Null
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$archive=$null
$code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($original.archive,$hashService,[ref]$archive)
if($code.ToString() -cne 'NoError'){throw 'Archive read failed'}
$memory=[IO.MemoryStream]::new()
try{$archive.Files[[uint64]$original.key].Extract($memory);$bytes=$memory.ToArray()}finally{$memory.Dispose()}
$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
if($hash -cne $original.sha256){throw 'Current journal changed'}
$row=[ordered]@{archive=$original.archive;archive_index=$original.archive_index;role=$original.role;depot=$original.depot;key=$original.key;extension=$original.extension;sha256=$hash;json=$null;json_sha256=$null;root_type=$original.root_type;status='PENDING';error=$null;imports=$original.imports;decoder_sha256=(Get-FileHash -LiteralPath (Join-Path $toolRoot 'WolvenKit.RED4.dll')).Hash}
try{
 $memory=[IO.MemoryStream]::new($bytes,$false)
 try{
  $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory);$resource=$null
  $code=$reader.ReadFile([ref]$resource,$true)
  if($code.ToString() -cne 'NoError'){throw "Journal decode failed: $code"}
  $jsonPath=Join-Path $out 'base_journal.json'
  Export-Cr2wJson $resource $jsonPath
  $row.json=$jsonPath;$row.json_sha256=(Get-FileHash -LiteralPath $jsonPath).Hash;$row.status='EXPORTED_CURRENT_ALTERNATE_DECODER'
 }finally{$memory.Dispose()}
}catch{$row.status='OPAQUE';$row.error=$_.Exception.Message}
$row | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath (Join-Path $out 'journal_fallback.json') -Encoding utf8NoBOM
@{status=$row.status;error=$row.error;sha256=$hash} | ConvertTo-Json -Compress

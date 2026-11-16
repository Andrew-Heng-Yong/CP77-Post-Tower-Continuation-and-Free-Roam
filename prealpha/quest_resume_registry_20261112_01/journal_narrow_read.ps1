# Read-only journal recovery. Every tolerated default error must first fail
# strictly at the same byte position with the exact map-pin property name.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'evidence_05'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
$toolRoot=Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $toolRoot
New-Item -ItemType Directory -Path $out | Out-Null
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$sources=@(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_02/resources.jsonl') | ForEach-Object {$_ | ConvertFrom-Json} | Where-Object {$_.depot -ceq 'base\journal\cooked_journal.journal'})
$results=[Collections.Generic.List[object]]::new()
foreach($source in $sources){
 $row=[ordered]@{archive=$source.archive;depot=$source.depot;sha256=$source.sha256;status='OPAQUE';json=$null;json_sha256=$null;anomalies=@();error=$null}
 $archive=$null
 $code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($source.archive,$hashService,[ref]$archive)
 if($code.ToString() -cne 'NoError'){throw 'Archive read failed'}
 $memory=[IO.MemoryStream]::new()
 try{$archive.Files[[uint64]$source.key].Extract($memory);$bytes=$memory.ToArray()}finally{$memory.Dispose()}
 if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $source.sha256){throw 'Journal source changed'}
 $script:knownPositions=[Collections.Generic.HashSet[long]]::new()
 $anomalies=[Collections.Generic.List[object]]::new()
 for($attempt=0;$attempt -le 12;$attempt++){
  $memory=[IO.MemoryStream]::new($bytes,$false)
  try{
   $script:journalReader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory)
   $script:observedPositions=[Collections.Generic.HashSet[long]]::new()
   $script:journalReader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($event)
    if($event -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs] -and $script:knownPositions.Contains($script:journalReader.Position)){
     [void]$script:observedPositions.Add($script:journalReader.Position)
     return $true
    }
    return $false
   })
   $resource=$null;$code=$script:journalReader.ReadFile([ref]$resource,$true)
   if($code.ToString() -cne 'NoError'){throw "Journal read failed: $code"}
   if(-not $script:knownPositions.SetEquals($script:observedPositions)){throw 'Known anomalies were not all observed'}
   $jsonPath=Join-Path $out ($source.archive_index.ToString()+'_base_journal.json')
   Export-Cr2wJson $resource $jsonPath
   $row.status='READ_WITH_PINNED_MAP_PIN_DEFAULT_ANOMALIES';$row.json=$jsonPath;$row.json_sha256=(Get-FileHash -LiteralPath $jsonPath).Hash
   break
  }catch{
   $message=$_.Exception.ToString();$position=$script:journalReader.Position
   if($message -cmatch 'Invalid default val for: "gameJournalQuestMapPin.mappinData"' -and -not $script:knownPositions.Contains($position)){
    [void]$script:knownPositions.Add($position)
    $anomalies.Add(@{field='gameJournalQuestMapPin.mappinData';position=$position;strict_error=$_.Exception.Message})
    if($attempt -eq 12){$row.error='Bounded retry limit; no accepted complete export'}
   }else{$row.error=$_.Exception.Message;break}
  }finally{$memory.Dispose()}
 }
 $row.anomalies=$anomalies.ToArray();$results.Add($row)
 Write-Output (@{archive_index=$source.archive_index;status=$row.status;anomalies=$anomalies.Count;error=$row.error}|ConvertTo-Json -Compress)
}
@{rows=$results.ToArray();decoder_sha256=(Get-FileHash -LiteralPath (Join-Path $toolRoot 'WolvenKit.RED4.dll')).Hash;tool_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;game_writes=0;binary_writes=0;limits='Only the exact map-pin default exceptions discovered by strict parsing at recorded byte positions are tolerated. Map-pin payloads remain unqualified. Exported journal IDs/classes are source inventory, not safe-stage or active-provider proof.'}|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $out 'journal_decode.json') -Encoding utf8NoBOM

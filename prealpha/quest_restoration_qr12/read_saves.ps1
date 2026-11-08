param([int]$Start=0,[int]$Count=12,[Parameter(Mandatory=$true)][string]$Tag)
# Offline managed WolvenKit reader only. No writer/game API, no save stream writes.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath($PSScriptRoot)
if($Tag -notmatch '^[A-Za-z0-9_]{1,80}$' -or $Tag -match '^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$' -or $Count -lt 1 -or $Count -gt 16 -or $Start -lt 0){throw 'Bounded fresh non-device batch name required'}
$dest=Join-Path $taskRoot ($Tag+'.json');if(Test-Path -LiteralPath $dest){throw 'Fresh output only'}
$wk='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
$parserHash=(Get-FileHash -LiteralPath (Join-Path $wk 'WolvenKit.RED4.dll') -Algorithm SHA256).Hash
if($parserHash -cne 'E607F058C74822B157CAE97F827310C4353CB323D440AE1E3A591307717645FD'){throw 'Previously verified parser bytes changed'}
foreach($assembly in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $assembly))}
$catalogue=Get-Content -LiteralPath (Join-Path $taskRoot 'catalogue.json') -Raw|ConvertFrom-Json
$jobs=(Get-Content -LiteralPath (Join-Path $taskRoot 'parse_jobs.json') -Raw|ConvertFrom-Json).jobs
$hashMethod=@([WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]})
if($hashMethod.Count -ne 1){throw 'Fact hash method ambiguous'}
$wanted=@{}
foreach($name in $catalogue.facts){$fact=[WolvenKit.RED4.Save.Fact]::op_Implicit([string]$name);$key=[uint32]$hashMethod[0].Invoke($null,[object[]]@($fact));if($wanted.ContainsKey($key)){throw 'Fact hash collision'};$wanted[$key]=[string]$name}
$journalHashes=@{}
foreach($j in $catalogue.journals){$key=[WolvenKit.Core.Murmur3.Murmur32]::Hash([string]$j.path,[uint32]0x5EEDBA5E,[Text.Encoding]::UTF8);if($journalHashes.ContainsKey($key)){throw 'Selected journal hash collision'};$journalHashes[$key]=[string]$j.path}
$results=[Collections.Generic.List[object]]::new()
for($i=$Start;$i -lt [Math]::Min($Start+$Count,$jobs.Count);$i++){
 $job=$jobs[$i];$source=[string]$job.source;$before=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
 if($before -cne $job.sha256){throw ('Source changed since inventory: '+$source)}
 if($job.metadata -and (Get-FileHash -LiteralPath $job.metadata -Algorithm SHA256).Hash -cne $job.metadata_sha256){throw 'Metadata drift'}
 $ms=[IO.MemoryStream]::new();$fs=$null;$row=[ordered]@{index=$i;source=$source;sha256=$before;status='UNKNOWN';parse_result=$null;error=$null;facts=@{};journal_raw_matches=@();nodes=@();owner_surface=@();unchanged_after_read=$false}
 try{
  # Permit ordinary OS writer/replacement sharing; snapshot consistency is hash-checked.
  $fs=[IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete));$fs.CopyTo($ms);$fs.Dispose();$fs=$null
  $copied=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()));if($copied -cne $before){throw 'Unstable in-memory snapshot'};$ms.Position=0
  $save=$null;$reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($ms);$parsed=$reader.ReadFile([ref]$save).ToString();$row.parse_result=$parsed
  if($parsed -cne 'NoError'){throw ('Parser returned '+$parsed)}
  $pending=[Collections.Generic.Stack[object]]::new();foreach($n in $save.Nodes){$pending.Push(@{node=$n;path=$n.Name})}
  $tables=0;$entries=0;$journal=[Collections.Generic.List[object]]::new();$nodeRows=[Collections.Generic.List[object]]::new();$owners=[Collections.Generic.List[object]]::new()
  while($pending.Count){
   $item=$pending.Pop();$n=$item.node;$type=if($null -ne $n.Value){$n.Value.GetType().FullName}else{'NULL'}
   if($item.path -notmatch '/'){$nodeRows.Add(@{name=[string]$n.Name;type=$type;size=$n.Size})}
   if([string]$n.Name -match 'quest|script|persist'){
    $props=if($null -ne $n.Value){@($n.Value.GetType().GetProperties()|ForEach-Object {@{name=$_.Name;type=$_.PropertyType.FullName}})}else{@()}
    $owners.Add(@{path=$item.path;type=$type;size=$n.Size;properties=$props;interpretation='Saved parser surface only; not executing-owner/liveness proof'})
   }
   if($n.Value -is [WolvenKit.RED4.Save.FactsTable]){
    $tables++
    foreach($entry in $n.Value.FactEntries){
     $entries++;$key=[uint32]$hashMethod[0].Invoke($null,[object[]]@($entry.FactName))
     if($wanted.ContainsKey($key)){
      $name=$wanted[$key];if(-not $row.facts.ContainsKey($name)){$row.facts[$name]=[Collections.Generic.List[object]]::new()}
      $row.facts[$name].Add(@{table_path=$item.path;table_ordinal=$tables;value_u32=[uint32]$entry.Value;hash=[string]$key})
     }
    }
   }
   if([string]$n.Name -ceq 'JournalManager'){
    foreach($entry in $n.Value.Entries){
     $raw=[byte[]]$entry.UnkownBytes
     if($raw.Length -ge 4){$key=[BitConverter]::ToUInt32($raw,0);if($journalHashes.ContainsKey($key)){$journal.Add(@{path=$journalHashes[$key];hash=[string]$key;raw=[Convert]::ToHexString($raw);bytes=$raw.Length;state='OPAQUE_NOT_DECODED'})}}
    }
   }
   foreach($child in $n.Children){$pending.Push(@{node=$child;path=($item.path+'/'+$child.Name)})}
  }
  $row.status='PARSED_SAVED_FACTS_AND_OPAQUE_SURFACES';$row.fact_tables=$tables;$row.fact_entries=$entries;$row.nodes=@($nodeRows.ToArray());$row.journal_raw_matches=@($journal.ToArray());$row.owner_surface=@($owners.ToArray())
 }catch{$row.status='UNKNOWN_PARSER_OR_FORMAT_BLOCKER';$row.error=$_.Exception.Message}
 finally{if($null -ne $fs){$fs.Dispose()};$ms.Dispose()}
 if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -cne $before){throw 'Source changed during parse; report discarded'}
 if($job.metadata -and (Get-FileHash -LiteralPath $job.metadata -Algorithm SHA256).Hash -cne $job.metadata_sha256){throw 'Metadata changed during parse'}
 $row.unchanged_after_read=$true;$results.Add($row)
 Write-Output ('Read '+$i+' '+[IO.Path]::GetFileName([IO.Path]::GetDirectoryName($source))+' '+$row.status)
}
$out=@{method='Offline MemoryStream snapshot from explicitly read-only source; pinned previously verified WolvenKit reader';parser_sha256=$parserHash;start=$Start;count=$results.Count;results=@($results.ToArray());
 limits=@('Missing fact rows mean serialized absence, not asserted runtime zero.','All matching fact-table values retained; table precedence not guessed.','Journal hash/raw records are not journal-state labels.','Quest/script/persist node surfaces are not active owner, exact saved graph stage, liveness or entitlement proof.');source_writes=0;game_API_calls=0}
[IO.File]::WriteAllText($dest,($out|ConvertTo-Json -Depth 35),[Text.UTF8Encoding]::new($false))

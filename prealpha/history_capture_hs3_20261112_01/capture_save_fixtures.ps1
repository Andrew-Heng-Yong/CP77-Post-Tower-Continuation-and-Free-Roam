# Read-only source fixtures; no save writer, game API or deployment.
param([int]$Attempt=1)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot ('fixtures_saves_{0:d2}' -f $Attempt)
if(Test-Path -LiteralPath $out){throw 'Fresh save fixture output required'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$catalogue=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/catalogue.json') -Raw|ConvertFrom-Json
$saveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077'
$toHash=@([WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]})
if($toHash.Count -ne 1){throw 'Ambiguous fact hashing'}
$names=@($catalogue.facts)+@('PTFRHS3_GateOpen','PTFRHS3_GateTicket','PTFRHS3_GateRoute','PTFRHS3_GateResult','q307_debug_reset','q307_confirm_av_start')|Sort-Object -Unique
$wanted=@{}
foreach($name in $names){
 $f=[WolvenKit.RED4.Save.Fact]::op_Implicit([string]$name);$key=[uint32]$toHash[0].Invoke($null,[object[]]@($f))
 if(-not $wanted.ContainsKey($key)){$wanted[$key]=[Collections.Generic.List[string]]::new()};$wanted[$key].Add($name)
}
$journalPaths=@($catalogue.journals.path|Sort-Object -Unique)
$journalKeys=@{}
foreach($path in $journalPaths){
 $key=[WolvenKit.Core.Murmur3.Murmur32]::Hash($path,[uint32]0x5EEDBA5E,[Text.Encoding]::UTF8)
 if(-not $journalKeys.ContainsKey($key)){$journalKeys[$key]=[Collections.Generic.List[string]]::new()};$journalKeys[$key].Add($path)
}
New-Item -ItemType Directory -Path $out|Out-Null
$results=[Collections.Generic.List[object]]::new()
foreach($slot in @('ManualSave-26','AutoSave-2','AutoSave-16','ManualSave-27')){
 $source=Join-Path $saveRoot ($slot+'/sav.dat');$meta=Join-Path $saveRoot ($slot+'/metadata.9.json')
 foreach($path in @($source,$meta)){
  for($item=Get-Item -LiteralPath $path;$null -ne $item;){
   if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked save input refused'}
   if($item -is [IO.FileInfo]){$item=$item.Directory}else{$item=$item.Parent}
  }
 }
 $pins=@{sav_dat=(Get-FileHash -LiteralPath $source).Hash;metadata=(Get-FileHash -LiteralPath $meta).Hash}
 $memory=[IO.MemoryStream]::new();$file=[IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try{$file.CopyTo($memory)}finally{$file.Dispose()}
 if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -cne $pins.sav_dat){throw 'Save changed before read'}
 $memory.Position=0;$save=$null
 try{$parsed=([WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)).ReadFile([ref]$save).ToString()}finally{$memory.Dispose()}
 if($parsed -cne 'NoError'){throw "Save parse failed: $slot : $parsed"}
 $quest=@($save.Nodes|Where-Object Name -ceq 'questSystem');if($quest.Count -ne 1){throw 'Native quest root missing/ambiguous'}
 $db=@($quest[0].Children|Where-Object Name -ceq 'FactsDB');if($db.Count -ne 1 -or $db[0].Children.Count -ne 10){throw 'Unexpected native fact store layout'}
 $table=$db[0].Children[0].Value;if($table -isnot [WolvenKit.RED4.Save.FactsTable]){throw 'Unexpected native named fact table'}
 $values=[ordered]@{};foreach($name in $names){$values[$name]=$null}
 $seen=[Collections.Generic.HashSet[uint32]]::new()
 foreach($entry in $table.FactEntries){
  $key=[uint32]$toHash[0].Invoke($null,[object[]]@($entry.FactName));if(-not $seen.Add($key)){throw 'Duplicate named fact hash'}
  if($wanted.ContainsKey($key)){foreach($name in $wanted[$key]){$values[$name]=[uint32]$entry.Value}}
 }
 $jn=@($save.Nodes|Where-Object Name -ceq 'JournalManager');if($jn.Count -ne 1){throw 'Journal root missing/ambiguous'}
 $records=[Collections.Generic.List[object]]::new()
 foreach($entry in $jn[0].Value.Entries){
  $raw=[byte[]]$entry.UnkownBytes;if($raw.Length -ne 15){throw 'Unexpected journal record width'}
  $key=[BitConverter]::ToUInt32($raw,0)
  if($journalKeys.ContainsKey($key)){$records.Add(@{hash_u32=$key;paths=$journalKeys[$key].ToArray();raw15=[Convert]::ToHexString($raw);uint32_at_4=[BitConverter]::ToUInt32($raw,4)})}
 }
 $containers=@($save.Nodes|Where-Object Name -ceq 'ScriptableSystemsContainer');if($containers.Count -ne 1){throw 'Script system container missing/ambiguous'}
 $systems=[Collections.Generic.List[string]]::new()
 foreach($chunk in $containers[0].Value.Content.Chunks){
  $type=$chunk.GetType().FullName;if($chunk -is [WolvenKit.RED4.Types.IDynamicClass]){$type=$chunk.ClassName.ToString()}
  if($type -in @('PTFR.HistorySnapshotHS1.SnapshotStateHS1','PTFR.HistorySnapshotHS1.CaptureArchiveHS3')){
   $systems.Add($type)
   $json=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($chunk,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
   [IO.File]::WriteAllText((Join-Path $out ($slot+'_'+$type+'.json')),$json,[Text.UTF8Encoding]::new($false))
  }
 }
 $metadata=(Get-Content -LiteralPath $meta -Raw|ConvertFrom-Json).Data.metadata
 if((Get-FileHash -LiteralPath $source).Hash -cne $pins.sav_dat -or (Get-FileHash -LiteralPath $meta).Hash -cne $pins.metadata){throw 'Save input changed during extraction'}
 $row=@{slot=$slot;source=$source;sha256=$pins.sav_dat;metadata_sha256=$pins.metadata;tracked=$metadata.trackedQuestEntry;checkpoint=$metadata.debugString;facts=$values;journal_matches=$records.ToArray();journal_record_count=$jn[0].Value.Entries.Count;snapshot_systems=$systems.ToArray();source_unchanged=$true}
 $row|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $out ($slot+'.json')) -Encoding utf8NoBOM
 $results.Add(@{slot=$slot;sha256=$pins.sav_dat;tracked=$metadata.trackedQuestEntry;journal_matches=$records.Count;systems=$systems.ToArray()})
}
@{status='PASS_READ_ONLY_SAVE_FIXTURE_EXTRACTION';saves=$results.ToArray();source_writes=0;game_calls=0;game_writes=0;tool_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;catalogue_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/catalogue.json')).Hash;parser_sha256=(Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.FactsTable].Assembly.Location)).Hash;fact_name_hash_collisions=@($wanted.GetEnumerator()|Where-Object {$_.Value.Count -gt 1}|ForEach-Object {@{hash_u32=$_.Key;names=$_.Value.ToArray()}});journal_path_hash_collisions=@($journalKeys.GetEnumerator()|Where-Object {$_.Value.Count -gt 1}|ForEach-Object {@{hash_u32=$_.Key;paths=$_.Value.ToArray()}});limits='Named facts only from physical native table 1. Null means absent serialized entry. Journal raw records are retained, no counter/optional/timer or owner decoder is claimed. No current runtime state, new HS3 capture, serialization or gameplay test is asserted.'}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
Write-Output "Read-only extraction complete: $($results.Count) save fixtures."

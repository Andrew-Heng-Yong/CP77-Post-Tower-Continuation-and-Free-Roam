# Fresh successor archive. Only two official quest phases receive a capture gate.
param([int]$Attempt=1,[int]$Candidate=2)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/plan.json') -Raw | ConvertFrom-Json
$baselinePath=Join-Path $workspace 'prealpha/quest_history_autoload_20261112_01/deployment_01/installed_manifest_01.json'
if((Get-FileHash -LiteralPath $baselinePath).Hash -cne $plan.baseline_sha256){throw 'Baseline manifest changed'}
$baseline=Get-Content -LiteralPath $baselinePath -Raw|ConvertFrom-Json
$out=Join-Path $PSScriptRoot ('archive_{0:d2}' -f $Attempt)
$target=Join-Path $PSScriptRoot ('candidate_{0:d2}/package/archive/pc/mod/zzzz_PTFR_Combined.archive' -f $Candidate)
if((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $target)){throw 'Fresh archive outputs required'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
function OpenArchive([string]$Path){
 $a=$null;$code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($Path,$hashService,[ref]$a)
 if($code.ToString() -cne 'NoError'){throw "Archive unreadable: $Path"};return $a
}
function RawBytes($Entry){$s=[IO.MemoryStream]::new();try{$Entry.Extract($s);return ,$s.ToArray()}finally{$s.Dispose()}}
function ByteHash([byte[]]$Bytes){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes))}
function Key([string]$Depot){return [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($Depot)}
function Plain([string]$Path){
 for($p=[IO.FileInfo]::new($Path);$null -ne $p;){
  if($p.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Linked input refused: $Path"}
  if($p -is [IO.FileInfo]){$p=$p.Directory}else{$p=$p.Parent}
 }
}
foreach($r in @($baseline.core_files)+@($baseline.required_files)){
 $p=Join-Path $plan.game_root $r.path;Plain $p
 if((Get-Item -LiteralPath $p).Length -ne $r.bytes -or (Get-FileHash -LiteralPath $p).Hash -cne $r.sha256){throw "Installed baseline changed: $p"}
}
New-Item -ItemType Directory -Path $out | Out-Null
$archiveRoot=Join-Path $plan.game_root 'archive/pc'
if(@(Get-ChildItem -LiteralPath $archiveRoot -Recurse -Force -Attributes ReparsePoint).Count){throw 'Linked archive tree refused'}
$archives=@(Get-ChildItem -LiteralPath $archiveRoot -Recurse -File -Filter '*.archive')
$redmods=Join-Path $plan.game_root 'mods';if(Test-Path -LiteralPath $redmods){$archives+=@(Get-ChildItem -LiteralPath $redmods -Recurse -File -Filter '*.archive')}
$providers=[Collections.Generic.List[object]]::new()
foreach($file in $archives){
 Plain $file.FullName;$stamp=@($file.Length,$file.LastWriteTimeUtc.Ticks);$a=OpenArchive $file.FullName
 foreach($gate in $plan.gates){
  $key=[uint64]$gate.key
  if($a.Files.ContainsKey($key)){
   $bytes=RawBytes $a.Files[$key];$h=ByteHash $bytes
   if($file.FullName -cne $gate.archive -or $h -cne $gate.sha256){throw "Unreviewed provider for $($gate.depot): $file"}
   $raw=Join-Path $out ($gate.route.ToString()+'_before.questphase');[IO.File]::WriteAllBytes($raw,$bytes)
   $providers.Add(@{depot=$gate.depot;archive=$file.FullName;sha256=$h;raw=$raw})
  }
 }
 $file.Refresh();if($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]){throw 'Archive changed during provider check'}
}
if($providers.Count -ne 2){throw 'Missing native capture provider'}

# Bind the full donor by payload equality to the actual installed archive.
$source=Join-Path $out 'archive_source';New-Item -ItemType Directory -Path $source | Out-Null
$donor=Join-Path $workspace 'prealpha/tower_recovery_20261111_01/archive_01/archive_source'
if(@(Get-ChildItem -LiteralPath $donor -Recurse -Force -Attributes ReparsePoint).Count){throw 'Linked donor refused'}
$current=OpenArchive (Join-Path $plan.game_root 'archive/pc/mod/zzzz_PTFR_Combined.archive')
$expected=@{};$old=@{}
foreach($file in Get-ChildItem -LiteralPath $donor -Recurse -File){
 Plain $file.FullName;$depot=[IO.Path]::GetRelativePath($donor,$file.FullName).Replace('/','\');$key=Key $depot
 if($expected.ContainsKey($key) -or -not $current.Files.ContainsKey($key)){throw "Donor inventory mismatch: $depot"}
 $h=(Get-FileHash -LiteralPath $file.FullName).Hash
 if((ByteHash (RawBytes $current.Files[$key])) -cne $h){throw "Donor is not the installed payload: $depot"}
 $dest=Join-Path $source $depot;New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null
 [IO.File]::Copy($file.FullName,$dest,$false);$expected[$key]=@{depot=$depot;sha256=$h};$old[$key]=$h
}
if($expected.Count -ne $current.Files.Count -or $expected.Count -ne 1738){throw 'Incomplete installed source donor'}

function TypedEdges($Graph){
 $owners=@{}
 foreach($nh in $Graph.Nodes){foreach($sh in $nh.Chunk.Sockets){$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($sh.Chunk)]=@([int]::Parse($nh.Chunk.Id.ToString()),$sh.Chunk.Name.ToString())}}
 $rows=[Collections.Generic.List[object]]::new()
 foreach($nh in $Graph.Nodes){foreach($sh in $nh.Chunk.Sockets){foreach($ch in $sh.Chunk.Connections){
  $c=$ch.Chunk;if([object]::ReferenceEquals($c.Source.Chunk,$sh.Chunk)){
   $a=$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Source.Chunk)];$b=$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Destination.Chunk)]
   $rows.Add(@($a[0],$a[1],$b[0],$b[1]))
  }
 }}}
 return ,$rows
}
$changes=[Collections.Generic.List[object]]::new()
foreach($gate in $plan.gates){
 $raw=Join-Path $out ($gate.route.ToString()+'_before.questphase');$resource=Read-Cr2wFile $raw
 Export-Cr2wJson $resource (Join-Path $out ($gate.route.ToString()+'_before.json'))
 $graph=$resource.RootChunk.Graph.Chunk
 foreach($id in ($gate.graph -split '/'|Select-Object -Skip 1)){$graph=(Get-QuestNode $graph ([int]$id)).PhaseGraph.Chunk}
 $edges=TypedEdges $graph
 $matched=@($edges|Where-Object {$_[0] -eq $gate.from -and $_[1] -ceq 'Out' -and $_[2] -eq $gate.to -and $_[3] -ceq 'In'})
 if($matched.Count -ne 1){throw 'Native insertion edge changed'}
 foreach($id in 60000..60006){if(@($graph.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq $id.ToString()}).Count){throw 'Native node identity collision'}}
 $nodes=@(
  (New-SetFactNode 60000 'PTFRHS3_GateResult' 0),
  (New-SetFactNode 60001 'PTFRHS3_GateRoute' $gate.route),
  (New-SetFactNode 60002 'PTFRHS3_GateTicket' 1),
  (New-SetFactNode 60003 'PTFRHS3_GateOpen' 1)
 )
 $nodes[2].Type.Chunk.SetExactValue=$false
 $logical=[WolvenKit.RED4.Types.questLogicalCondition]::new();$logical.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
 Add-RedHandle $logical.Conditions (New-FactCondition 'PTFRHS3_GateResult' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))
 $delay=[WolvenKit.RED4.Types.questRealtimeDelay_ConditionType]::new();$delay.Seconds=[uint32]30
 $timeCondition=[WolvenKit.RED4.Types.questTimeCondition]::new();Set-RedHandleProperty $timeCondition 'Type' $delay
 Add-RedHandle $logical.Conditions $timeCondition
 $wait=[WolvenKit.RED4.Types.questPauseConditionNodeDefinition]::new();$wait.Id=[uint16]60004
 Set-RedHandleProperty $wait 'Condition' $logical
 [void](New-QuestSocket $wait 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
 [void](New-QuestSocket $wait 'In' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
 [void](New-QuestSocket $wait 'Out' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
 $nodes+=@($wait,(New-SetFactNode 60005 'PTFRHS3_GateOpen' 0),(New-SetFactNode 60006 'PTFRHS3_GatePassed' 1))
 foreach($node in $nodes){Add-RedHandle $graph.Nodes $node}
 $rebuilt=[Collections.Generic.List[object]]::new()
 foreach($e in $edges){if(-not ($e[0] -eq $gate.from -and $e[1] -ceq 'Out' -and $e[2] -eq $gate.to -and $e[3] -ceq 'In')){$rebuilt.Add($e)}}
 $rebuilt.Add(@($gate.from,'Out',60000,'In'))
 foreach($id in 60000..60005){$rebuilt.Add(@($id,'Out',($id+1),'In'))}
 $rebuilt.Add(@(60006,'Out',$gate.to,'In'))
 foreach($nh in $graph.Nodes){foreach($sh in $nh.Chunk.Sockets){$sh.Chunk.Connections.Clear()}}
 foreach($e in $rebuilt){
  [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $graph $e[2]) $e[3]))
 }
 $dest=Join-Path $source $gate.depot;Write-Cr2wFile $resource $dest
 $after=Read-Cr2wFile $dest;Export-Cr2wJson $after (Join-Path $out ($gate.route.ToString()+'_after.json'))
 $h=(Get-FileHash -LiteralPath $dest).Hash;$key=Key $gate.depot
 if($expected.ContainsKey($key)){throw 'Unexpected existing native override'}
 $expected[$key]=@{depot=$gate.depot;sha256=$h}
 $changes.Add(@{depot=$gate.depot;graph=$gate.graph;route=$gate.route;before=$gate.sha256;after=$h;nodes=@(60000..60006);old_edge=@($gate.from,'Out',$gate.to,'In')})
}
$stream=[IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try{
 $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new())
 if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive packing failed'}
}finally{$stream.Dispose()}
$packed=OpenArchive $target
if($packed.Files.Count -ne $expected.Count){throw 'Packed member inventory changed'}
$readback=@(foreach($entry in $packed.Files.GetEnumerator()){
 $pin=$expected[$entry.Key]
 if(-not $pin -or (ByteHash (RawBytes $entry.Value)) -cne $pin.sha256){throw 'Packed payload mismatch'}
 @{depot=$pin.depot;key=$entry.Key.ToString();sha256=$pin.sha256;retained=$old.ContainsKey($entry.Key)}
})
@{status='PASS_PAYLOAD_READBACK_SEMANTIC_DIFF_PENDING';archive_sha256=(Get-FileHash -LiteralPath $target).Hash;providers=$providers.ToArray();changes=$changes.ToArray();resources=$readback;retained=1738;members=$readback.Count;game_writes=0;save_writes=0;plan_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/plan.json')).Hash;tool_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}|ConvertTo-Json -Depth 18|Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Packed and read back $($readback.Count) members; all 1738 existing payloads retained."

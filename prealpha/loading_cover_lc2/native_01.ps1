$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'candidate_01'
$source=Join-Path $out 'native_source'
if(Test-Path -LiteralPath $source){throw 'Fresh native source required'}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$rel='archive/pc/mod/TowerContinued_PreAlpha.archive';$installed=Join-Path $game $rel
$expected='9D9AF716B78187B2A02790CB9B57D6C87E953D9790D57513888991AAC5C2CBCC'
if((Get-FileHash -LiteralPath $installed).Hash -cne $expected){throw 'Current L1/HS1 baseline changed'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function OpenArchive($path){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive read failed'};return $a}
function Bytes($entry){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);return ,$m.ToArray()}finally{$m.Dispose()}}
function HashBytes($b){[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($b))}
$ar=OpenArchive $installed
if($ar.Files.Count -ne 616){throw 'Unexpected baseline resource count'}
$members=(Get-Content -LiteralPath (Join-Path $ws 'prealpha/handoff_pa3/build/pa3_01/build.json') -Raw|ConvertFrom-Json).members
$names=@{};foreach($m in $members){$names[[uint64]$m.key]=$m.depot}
$before=@{}
foreach($e in $ar.Files.Values){
 $name=$names[$e.Key];if(!$name){throw 'Unknown depot'}
 if([IO.Path]::IsPathRooted($name) -or $name.Contains(':') -or $name -match '(^|[/\\])\.\.([/\\]|$)'){throw 'Unsafe depot'}
 if([WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($name) -ne $e.Key){throw 'Depot key mismatch'}
 $p=[IO.Path]::GetFullPath((Join-Path $source $name));if(!$p.StartsWith([IO.Path]::GetFullPath($source)+'\')){throw 'Depot escapes output'}
 New-Item -ItemType Directory -Path (Split-Path $p -Parent) -Force|Out-Null
 $data=Bytes $e;[IO.File]::WriteAllBytes($p,$data);$before[$name]=HashBytes $data
}
$depot='base\quest\main_quests\epilogue\final_boards.questphase';$path=Join-Path $source $depot
if($before[$depot] -cne '4A52C9A4D7C73F4074052EE220BFC3E631DB830477D163FECAA16F9940102536'){throw 'Current native phase binding differs'}
$f=Read-Cr2wFile $path;$old=Read-Cr2wFile $path;$g=$f.RootChunk.Graph.Chunk
# LC1 accidentally evaluated CoverReady once immediately after resetting it.
# Keep the owner ID and input/cut sockets; change only 181 to a native waiter.
$oldNode=Get-QuestNode $g 181
if($oldNode.GetType().Name -cne 'questConditionNodeDefinition'){throw 'Unexpected node 181 type'}
$wait=[WolvenKit.RED4.Types.questPauseConditionNodeDefinition]::new()
$wait.Id=[uint16]181
Set-RedHandleProperty -Owner $wait -PropertyName 'Condition' -Chunk $oldNode.Condition.Chunk
foreach($handle in $oldNode.Sockets){
 $socket=$handle.Chunk
 if($socket.Name.ToString() -eq 'False'){
  if($socket.Connections.Count -ne 0){throw 'False branch unexpectedly has an owner'}
  continue
 }
 if($socket.Name.ToString() -eq 'True'){$socket.Name='Out'}
 Add-RedHandle $wait.Sockets $socket
}
for($i=0;$i -lt $g.Nodes.Count;$i++){if([object]::ReferenceEquals($g.Nodes[$i].Chunk,$oldNode)){$g.Nodes[$i].Chunk=$wait}}
Write-Cr2wFile $f $path
$read=Read-Cr2wFile $path;$cg=$read.RootChunk.Graph.Chunk
$oldEdges=@(Get-GraphEdges $old.RootChunk.Graph.Chunk);$newEdges=@(Get-GraphEdges $cg)
$removed=@($oldEdges|Where-Object {$_ -notin $newEdges});$added=@($newEdges|Where-Object {$_ -notin $oldEdges})
if($removed.Count -ne 1 -or $removed[0] -cne '181.True -> 176.In' -or $added.Count -ne 1 -or $added[0] -cne '181.Out -> 176.In'){throw 'Unexpected waiter graph change'}
foreach($h in $old.RootChunk.Graph.Chunk.Nodes){
 if($h.Chunk.Id.ToString() -eq '181'){continue}
 if((Get-NodeWithoutConnectionsJson $h.Chunk) -cne (Get-NodeWithoutConnectionsJson (Get-QuestNode $cg ([int]::Parse($h.Chunk.Id.ToString()))))){throw 'Unrelated native payload changed'}
}
if((Get-QuestNode $cg 181).GetType().Name -cne 'questPauseConditionNodeDefinition'){throw 'Waiter was not serialized'}
$sockets=@($cg.Nodes|ForEach-Object {$_.Chunk.Sockets}|ForEach-Object {$_.Chunk})
foreach($s in $sockets){foreach($h in $s.Connections){$c=$h.Chunk;foreach($end in @($c.Source.Chunk,$c.Destination.Chunk)){if(@($sockets|Where-Object {[object]::ReferenceEquals($_,$end)}).Count -ne 1 -or @($end.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk,$c)}).Count -ne 1){throw 'Broken native socket reciprocity'}}}}
Export-Cr2wJson $read (Join-Path $out 'native_phase.json')
$dest=Join-Path $out ('package/'+$rel);New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force|Out-Null
$stream=[IO.File]::Create($dest)
try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=OpenArchive $dest;if($packed.Files.Count -ne 616){throw 'Packed count differs'}
foreach($e in $packed.Files.Values){$name=$names[$e.Key];$actual=HashBytes (Bytes $e);if($actual -cne (Get-FileHash -LiteralPath (Join-Path $source $name)).Hash){throw 'Packed readback differs'};if($name -cne $depot -and $actual -cne $before[$name]){throw 'Unrelated resource changed'}}
$bp=Join-Path $out ('before/'+$rel);New-Item -ItemType Directory -Path (Split-Path $bp -Parent) -Force|Out-Null;Copy-Item -LiteralPath $installed -Destination $bp
if((Get-FileHash -LiteralPath $installed).Hash -cne $expected){throw 'Installed main changed during build'}
$report=[ordered]@{status='PASS_NATIVE_SPLICE_PACKED_NOT_LIVE';target=$rel;before=$expected;after=(Get-FileHash -LiteralPath $dest).Hash;resource_count=616;unchanged_resources=615;old_payloads_preserved_except_181=$true;waiter_node_id=181;waiter_type='questPauseConditionNodeDefinition';removed_edges=$removed;added_edges=$added;all_edges=$newEdges;phase_sha256=(Get-FileHash -LiteralPath $path).Hash;preserved_lighting_sha256=$before['base\worlds\03_night_city\_compiled\default\exterior_-25_18_0_0.streamingsector'];game_writes=0}
$report|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'native_01.json') -Encoding utf8
$report|Select-Object status,before,after,unchanged_resources,preserved_lighting_sha256|ConvertTo-Json

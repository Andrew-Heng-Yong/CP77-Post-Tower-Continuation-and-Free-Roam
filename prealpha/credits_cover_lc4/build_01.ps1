$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$base=Join-Path $ws 'prealpha/world_support_wa3/candidate_02'
$out=Join-Path $PSScriptRoot 'candidate_02'
if(Test-Path -LiteralPath $out){throw 'Fresh candidate required'}
$source=Join-Path $out 'archive_source'
$package=Join-Path $out 'package'
$depot='base\quest\main_quests\epilogue\final_boards.questphase'
$board='ep1\quest\main_quests\q307\phases\q307_ending_board.questphase'
$manifest=Get-Content -LiteralPath (Join-Path $base 'install_manifest_01.json') -Raw|ConvertFrom-Json -Depth 80
$proof=Get-Content -LiteralPath (Join-Path $base 'package_proof_01.json') -Raw|ConvertFrom-Json -Depth 80
if($manifest.archive_members -ne 1563 -or $proof.checked_members.Count -ne 1563){throw 'WA3 base changed'}
if((Get-FileHash -LiteralPath (Join-Path $base 'package/archive/pc/mod/zzzz_PTFR_Combined.archive')).Hash -cne 'F497AB45129BDF11DF06963060CC0B00292D09117301772326E74644E46BF42B'){throw 'Base archive changed'}
New-Item -ItemType Directory -Path $out|Out-Null
Copy-Item -LiteralPath (Join-Path $base 'archive_source') -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $base 'package') -Destination $package -Recurse
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$old=Read-Cr2wFile (Join-Path $source $depot)
$file=Read-Cr2wFile (Join-Path $source $depot)
$graph=$file.RootChunk.Graph.Chunk
$boardfile=Read-Cr2wFile (Join-Path $source $board)
$boardgraph=$boardfile.RootChunk.Graph.Chunk
function Put($n){if(@($graph.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq $n.Id.ToString()}).Count){throw 'Node collision'};Add-RedHandle $graph.Nodes $n;return $n}
function Clone($n,[int]$id){$c=$n.DeepCopy();$c.Id=[uint16]$id;foreach($s in $c.Sockets){$s.Chunk.Connections.Clear()};[void](Put $c);return $c}
function Link([int]$a,[string]$s,[int]$b,[string]$d='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $a) $s) (Get-QuestSocket (Get-QuestNode $graph $b) $d))}
function Unlink([int]$a,[string]$s,[int]$b,[string]$d='In'){
 $src=Get-QuestSocket (Get-QuestNode $graph $a) $s;$dst=Get-QuestSocket (Get-QuestNode $graph $b) $d
 $hits=@($src.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk.Destination.Chunk,$dst)})
 if($hits.Count -ne 1){throw 'Expected edge absent'};$c=$hits[0].Chunk
 foreach($sock in @($src,$dst)){for($i=$sock.Connections.Count-1;$i -ge 0;$i--){if([object]::ReferenceEquals($sock.Connections[$i].Chunk,$c)){$sock.Connections.RemoveAt($i)}}}
}
# The original Tower-specific completion edge and its fact guard are the admission precedent.
# Two checks use its identical payload. Nothing in between writes their fact inputs.
if(@((Get-GraphEdges $graph)|Where-Object {$_ -ceq '100.Out -> 27.In'}).Count -ne 1 -or @((Get-GraphEdges $graph)|Where-Object {$_ -ceq '27.Out -> 28.In'}).Count -ne 1){throw 'Credits seam changed'}
[void](Clone (Get-QuestNode $graph 101) 182)
[void](Clone (Get-QuestNode $boardgraph 7) 183)
[void](Clone (Get-QuestNode $graph 101) 184)
[void](Put (New-SetFactNode 185 'PTFRLC4_CreditsBlackHeld' 1))
Unlink 100 Out 27
Unlink 27 Out 28
Link 100 Out 182
Link 182 True 183
Link 182 False 27
Link 183 Out 27
Link 27 Out 184
Link 184 True 185
Link 184 False 28
Write-Cr2wFile $file (Join-Path $source $depot)
$check=Read-Cr2wFile (Join-Path $source $depot)
$after=@(Get-GraphEdges $check.RootChunk.Graph.Chunk)
$before=@(Get-GraphEdges $old.RootChunk.Graph.Chunk)
$removed=@($before|Where-Object {$_ -notin $after})
$added=@($after|Where-Object {$_ -notin $before})
$wantRemoved=@('100.Out -> 27.In','27.Out -> 28.In')
$wantAdded=@('100.Out -> 182.In','182.True -> 183.In','182.False -> 27.In','183.Out -> 27.In','27.Out -> 184.In','184.True -> 185.In','184.False -> 28.In')
if(@(Compare-Object $wantRemoved $removed).Count -or @(Compare-Object $wantAdded $added).Count){throw 'Unexpected graph delta'}
foreach($node in $old.RootChunk.Graph.Chunk.Nodes){$id=[int]::Parse($node.Chunk.Id.ToString());if((Get-NodeWithoutConnectionsJson $node.Chunk) -cne (Get-NodeWithoutConnectionsJson (Get-QuestNode $check.RootChunk.Graph.Chunk $id))){throw "Existing payload $id changed"}}
foreach($socket in @($check.RootChunk.Graph.Chunk.Nodes|ForEach-Object {$_.Chunk.Sockets}|ForEach-Object {$_.Chunk})){foreach($conn in $socket.Connections){foreach($end in @($conn.Chunk.Source.Chunk,$conn.Chunk.Destination.Chunk)){if(@($end.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk,$conn.Chunk)}).Count -ne 1){throw 'Nonreciprocal socket'}}}}
$g=$check.RootChunk.Graph.Chunk
if((Get-QuestNode $g 183).Type.Chunk.FadeIn.ToString() -cne 'False' -or (Get-QuestNode $g 183).Type.Chunk.Duration.ToString() -cne '0'){throw 'Black fade changed'}
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$hashservice=[WolvenKit.Common.Services.HashService]::new();$hashservice.Load()
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashservice,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive packing failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hashservice,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
if($packed.Files.Count -ne 1563){throw 'Archive member count changed'}
$changed=[Collections.Generic.List[object]]::new()
foreach($row in $proof.checked_members){
 $name=[string]$row.depot;$path=Join-Path $source $name
 $hash=(Get-FileHash -LiteralPath $path).Hash
 if($name -cne $depot -and $hash -cne $row.sha256){throw "Source member changed: $name"}
 $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($name)
 if(!$packed.Files.ContainsKey([uint64]$key)){throw "Packed member missing: $name"}
 $ms=[IO.MemoryStream]::new();try{$packed.Files[[uint64]$key].Extract($ms);$got=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()}
 if($got -cne $hash){throw "Packed member differs: $name"}
 if($name -ceq $depot){$changed.Add(@{depot=$name;before=$row.sha256;after=$hash})}
}
if($changed.Count -ne 1 -or $changed[0].after -ceq $changed[0].before){throw 'Target was not changed once'}
$baseFiles=@{};foreach($f in $manifest.package_files){$baseFiles[$f.path]=$f.after}
$files=@(Get-ChildItem -LiteralPath $package -Recurse -File|ForEach-Object {$rel=[IO.Path]::GetRelativePath($package,$_.FullName).Replace('\','/');@{path=$rel;before=$baseFiles[$rel];after=(Get-FileHash -LiteralPath $_.FullName).Hash;bytes=$_.Length}})
if($files.Count -ne 51 -or @($files|Where-Object {$_.before -cne $_.after}).Count -ne 1){throw 'Full package scope changed'}
$report=[ordered]@{status='BUILT_SINGLE_CREDITS_RESOURCE_READBACK_PASS';base_archive_sha256='F497AB45129BDF11DF06963060CC0B00292D09117301772326E74644E46BF42B';archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;archive_members=1563;old_member_bytes_unchanged=1562;changed_members=@($changed.ToArray());removed_edges=$removed;added_edges=$added;package_files=$files;game_writes=0;save_writes=0}
$report|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $out 'build_01.json') -Encoding utf8
$report|Select-Object status,archive_sha256,archive_members,old_member_bytes_unchanged|ConvertTo-Json

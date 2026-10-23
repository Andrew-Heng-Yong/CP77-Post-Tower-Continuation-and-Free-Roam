param([Parameter(Mandatory)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$out=[IO.Path]::GetFullPath($Output)
if(!$out.StartsWith($ws+'\prealpha\handoff_pa3\build\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $out)){throw 'Fresh PA3 build directory required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Json([string]$p,$v){[IO.File]::WriteAllText($p,($v|ConvertTo-Json -Depth 35),[Text.UTF8Encoding]::new($false))}
$base=Join-Path $ws 'prealpha/transition/build/pa2_candidate_03'
if((Hash (Join-Path $base 'build.json')) -cne 'F3B5F705B51F65E1533822F076BFDEE45C6E06D4E9E41F2D886950F3442A568E'){throw 'Pinned PA2 report drift'}
$old=Get-Content (Join-Path $base 'build.json') -Raw|ConvertFrom-Json
$members=(Get-Content (Join-Path $ws 'prealpha/build/20261013T021845834Z/build.json') -Raw|ConvertFrom-Json).members
foreach($f in $old.package_files){if((Hash (Join-Path $old.package_root $f.relative)) -cne $f.sha256){throw 'Pinned PA2 package drift'}}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archiveRel='archive/pc/mod/TowerContinued_PreAlpha.archive'
$baselineArchive=$null;([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive((Join-Path $old.package_root $archiveRel),$hs,[ref]$baselineArchive)|Out-Null
if($baselineArchive.Files.Count -ne 616 -or $members.Count -ne 616){throw 'Baseline resource count drift'}
$beforeHashes=@{}
foreach($r in $members){
 $mem=[IO.MemoryStream]::new();try{$baselineArchive.Files[[uint64]$r.key].Extract($mem);$expected=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
 if((Hash (Join-Path $base ('source/'+$r.depot))) -cne $expected){throw 'PA2 source differs from pinned archive'}
 $beforeHashes[$r.depot]=$expected
}
New-Item -ItemType Directory $out|Out-Null
Copy-Item -LiteralPath (Join-Path $base 'package') -Destination (Join-Path $out 'package') -Recurse
Copy-Item -LiteralPath (Join-Path $base 'source') -Destination (Join-Path $out 'source') -Recurse
$depot='base\quest\main_quests\epilogue\final_boards.questphase';$p=Join-Path $out ('source/'+$depot)
$file=Read-Cr2wFile $p;$original=Read-Cr2wFile $p;$g=$file.RootChunk.Graph.Chunk
function Put($n){if(@($g.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq $n.Id.ToString()}).Count){throw 'Node collision'};Add-RedHandle $g.Nodes $n;return $n}
function Clone([int]$from,[int]$id){$c=(Get-QuestNode $g $from).DeepCopy();$c.Id=[uint16]$id;foreach($s in $c.Sockets){$s.Chunk.Connections.Clear()};return Put $c}
function Link([int]$a,[string]$s,[int]$b,[string]$d='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $s) (Get-QuestSocket (Get-QuestNode $g $b) $d))}
function Unlink([int]$a,[string]$s,[int]$b){
 $src=Get-QuestSocket (Get-QuestNode $g $a) $s;$dst=Get-QuestSocket (Get-QuestNode $g $b) 'In'
 $hits=@($src.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk.Destination.Chunk,$dst)})
 if($hits.Count -ne 1){throw 'Unexpected splice edge'};$c=$hits[0].Chunk
 foreach($socket in @($src,$dst)){for($i=$socket.Connections.Count-1;$i -ge 0;$i--){if([object]::ReferenceEquals($socket.Connections[$i].Chunk,$c)){$socket.Connections.RemoveAt($i)}}}
}
# PA2's native blackout retained Tier5 until fade-in on its failure branch.
# End that cover unconditionally BEFORE starting either readiness waiter.
Unlink 146 Out 150;Unlink 146 Out 151
$fade=Clone 159 176 # Native fade-in, identical payload/duration0.5.
$delay=Clone 144 177;$delay.Condition.Chunk.Type.Chunk.Seconds=[uint32]1
[void](Clone 145 178) # Reassert native Tier1 AFTER fade-in has had time to finish.
[void](Put (New-SetFactNode 179 'PTFRPA3_CoverReleased' 1))
Link 146 Out 176;Link 176 Out 177;Link 177 Out 178;Link 178 Out 179
Link 179 Out 150;Link 179 Out 151
# Successful preparation does not trigger another native fade/tier transition.
# Keep old159 payload unreachable, preserving baseline and serialized node IDs.
Unlink 174 True 159;Link 174 True 161
Write-Cr2wFile $file $p
$read=Read-Cr2wFile $p;$cg=$read.RootChunk.Graph.Chunk
$before=@(Get-GraphEdges $original.RootChunk.Graph.Chunk);$after=@(Get-GraphEdges $cg)
$removed=@('146.Out -> 150.In','146.Out -> 151.In','174.True -> 159.In')
$added=@('146.Out -> 176.In','176.Out -> 177.In','177.Out -> 178.In','178.Out -> 179.In','179.Out -> 150.In','179.Out -> 151.In','174.True -> 161.In')
if(@(Compare-Object $removed @($before|Where-Object {$_ -notin $after})).Count -or @(Compare-Object $added @($after|Where-Object {$_ -notin $before})).Count){throw 'Unexpected graph delta'}
foreach($h in $original.RootChunk.Graph.Chunk.Nodes){if((Get-NodeWithoutConnectionsJson $h.Chunk) -cne (Get-NodeWithoutConnectionsJson (Get-QuestNode $cg ([int]::Parse($h.Chunk.Id.ToString()))))){throw 'Existing node payload changed'}}
foreach($edge in $after){Assert-ContainsExactlyOnce $after $edge PA3}
$sockets=@($cg.Nodes|ForEach-Object {$_.Chunk.Sockets}|ForEach-Object {$_.Chunk})
foreach($s in $sockets){foreach($h in $s.Connections){$c=$h.Chunk;foreach($end in @($c.Source.Chunk,$c.Destination.Chunk)){if(@($sockets|Where-Object {[object]::ReferenceEquals($_,$end)}).Count -ne 1 -or @($end.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk,$c)}).Count -ne 1){throw 'Broken native graph connection'}}}}
Export-Cr2wJson $read (Join-Path $out 'final.patched.json')
Json (Join-Path $out 'graph.json') @{removed_edges=$removed;added_edges=$added;all_edges=$after;old_nodes=83;new_nodes=$cg.Nodes.Count;unchanged_prior_payloads=$true;source=$depot}
$archive=Join-Path $out ('package/'+$archiveRel);$stream=[IO.File]::Create($archive)
try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$ar=$null;([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$ar)|Out-Null
if($ar.Files.Count -ne 616){throw 'Packed resource count drift'}
$packed=@()
foreach($r in $members){
 $hash=Hash (Join-Path $out ('source/'+$r.depot))
 if($r.depot -cne $depot -and $hash -cne $beforeHashes[$r.depot]){throw 'Unrelated resource changed'}
 $mem=[IO.MemoryStream]::new();try{$ar.Files[[uint64]$r.key].Extract($mem);$got=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
 if($hash -cne $got){throw 'Packed readback mismatch'}
 $packed+=@{depot=$r.depot;key=$r.key;sha256=$hash}
}
$scriptRel='r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds'
Copy-Item -LiteralPath (Join-Path $ws 'prealpha/handoff_pa3/scripts/PreAlphaArrivalPA1.reds') -Destination (Join-Path $out ('package/'+$scriptRel))
$package=Join-Path $out 'package'
$files=@(Get-ChildItem $package -Recurse -File|ForEach-Object {@{relative=[IO.Path]::GetRelativePath($package,$_.FullName).Replace('\','/');sha256=Hash $_.FullName;bytes=$_.Length}})
$changes=@();foreach($f in $files){$prior=@($old.package_files|Where-Object {$_.relative -ceq $f.relative});if($prior.Count -ne 1){throw 'File set changed'};if($prior[0].sha256 -cne $f.sha256){$changes+=@{relative=$f.relative;old_sha256=$prior[0].sha256;new_sha256=$f.sha256}}}
if($files.Count -ne 53 -or $changes.Count -ne 2 -or @($changes|Where-Object {$_.relative -cnotin @($archiveRel,$scriptRel)}).Count){throw 'Unexpected package delta'}
Json (Join-Path $out 'build.json') @{status='BUILT_PACKED_READBACK_PASS_COMPILE_PENDING';output=$out;package_root=$package;package_files=$files;changes=$changes;resources=616;members=$packed;prior_build=$base;all_prior_payloads_preserved=$true;only_resource_changed=$depot}
Write-Output ('BUILD_PASS='+$out)

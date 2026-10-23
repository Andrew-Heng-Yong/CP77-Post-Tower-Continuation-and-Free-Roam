param([Parameter(Mandatory)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$out=[IO.Path]::GetFullPath($Output)
if(!$out.StartsWith($ws+'\prealpha\transition\build\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $out)){throw 'Fresh PA2 build directory required'}
$base=Join-Path $ws 'prealpha/build/20261013T021845834Z'
$old=Get-Content (Join-Path $base 'build.json') -Raw|ConvertFrom-Json
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Json([string]$p,$v){[IO.File]::WriteAllText($p,($v|ConvertTo-Json -Depth 35),[Text.UTF8Encoding]::new($false))}
foreach($f in $old.package_files){if((Hash (Join-Path $old.package_root $f.relative)) -cne $f.sha256){throw 'Pinned PA1 package drift'}}
foreach($r in $old.members){if((Hash (Join-Path $base ('source/'+$r.depot))) -cne $r.sha256){throw 'Pinned resource drift'}}
New-Item -ItemType Directory $out|Out-Null
Copy-Item -LiteralPath (Join-Path $base 'package') -Destination (Join-Path $out 'package') -Recurse
Copy-Item -LiteralPath (Join-Path $base 'source') -Destination (Join-Path $out 'source') -Recurse
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$depot='base\quest\main_quests\epilogue\final_boards.questphase'
$p=Join-Path $out ('source/'+$depot)
$file=Read-Cr2wFile $p;$original=Read-Cr2wFile $p;$g=$file.RootChunk.Graph.Chunk
$board=Read-Cr2wFile (Join-Path $base 'source/ep1/quest/main_quests/q307/phases/q307_ending_board.questphase')
$bg=$board.RootChunk.Graph.Chunk
function Put($n){if(@($g.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq $n.Id.ToString()}).Count){throw 'Node collision'};Add-RedHandle $g.Nodes $n;return $n}
function Clone($n,[int]$id){$c=$n.DeepCopy();$c.Id=[uint16]$id;foreach($s in $c.Sockets){$s.Chunk.Connections.Clear()};return Put $c}
function Link([int]$a,[string]$s,[int]$b,[string]$d='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $s) (Get-QuestSocket (Get-QuestNode $g $b) $d))}
function Unlink([int]$a,[string]$s,[int]$b){
 $src=Get-QuestSocket (Get-QuestNode $g $a) $s;$dst=Get-QuestSocket (Get-QuestNode $g $b) 'In'
 $hits=@($src.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk.Destination.Chunk,$dst)})
 if($hits.Count -ne 1){throw 'Unexpected splice edge'};$c=$hits[0].Chunk
 foreach($socket in @($src,$dst)){for($i=$socket.Connections.Count-1;$i -ge 0;$i--){if([object]::ReferenceEquals($socket.Connections[$i].Chunk,$c)){$socket.Connections.RemoveAt($i)}}}
}
function Fact([int]$id,[string]$name,[int]$value){[void](Put (New-SetFactNode $id $name $value))}
function Delay([int]$id,[int]$ms){$n=Clone (Get-QuestNode $bg 11) $id;$t=$n.Condition.Chunk.Type.Chunk;$t.Hours=[uint32]0;$t.Minutes=[uint32]0;$t.Seconds=[uint32][Math]::Floor($ms/1000);$t.Miliseconds=[uint32]($ms%1000)}
function TestFact([int]$id,[string]$name){[void](Put (New-ConditionNode $id (New-FactCondition $name 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))))}
function WaitFact([int]$id,[string]$name){$n=Clone (Get-QuestNode $bg 13) $id;Set-RedHandleProperty $n 'Condition' (New-FactCondition $name 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
# Native wait-vs-timeout race uses the original board's XOR/cut-control idiom.
# The cut cancels both pending waiters before selecting success or recovery.
function Race([int]$start,[string]$name,[int]$success,[int]$baseId,[int]$faultCode,[int]$timeout){
 WaitFact $baseId $name;Delay ($baseId+1) $timeout
 [void](Put (New-XorNode ($baseId+2) 2));[void](Clone (Get-QuestNode $bg 6) ($baseId+3))
 TestFact ($baseId+4) $name;Fact ($baseId+5) 'PTFRPA2_Fault' $faultCode
 Link $start Out $baseId;Link $start Out ($baseId+1)
 Link $baseId Out ($baseId+2) In1;Link ($baseId+1) Out ($baseId+2) In2
 Link ($baseId+2) Out1 ($baseId+3);Link ($baseId+3) CutSource $baseId CutDestination;Link ($baseId+3) CutSource ($baseId+1) CutDestination
 Link ($baseId+3) Out ($baseId+4);Link ($baseId+4) True $success;Link ($baseId+4) False ($baseId+5);Link ($baseId+5) Out 160
}
# No changes before P0's twice-confirmed credits-closed + genuine Tower guard.
Unlink 109 Out 110
Fact 140 'PTFRPA2_Started' 1
$fade=Clone (Get-QuestNode $bg 7) 141;$fade.Type.Chunk.Duration=[float]0.25
Delay 142 300
Link 109 Out 140;Link 140 Out 141;Link 141 Out 142;Link 142 Out 110
# Existing native Tier1/show/six source-scoped restriction/content releases run.
# Stock teleport node: exact q307 player reference/reset-look payload, H10 target,
# no heal, no forced save, no global FastTravelSystem restriction reset.
Unlink 128 Out 129
$tp=Clone (Get-QuestNode $bg 22) 143
$tp.Params.Chunk.DestinationRef.Chunk.EntityReference.Reference=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('$/03_night_city/c_watson/little_china/loc_megabuilding_a_prefab4KCU2IQ/loc_megabuilding_a_questdesign_prefabT5LKYXQ/#q001_pr_v_room/#cp77_spwn_performance_test')
$tp.Params.Chunk.HealAtTeleport=[WolvenKit.RED4.Types.CBool]::op_Implicit($false)
Delay 144 1000
$tier=Clone (Get-QuestNode $g 111) 145;$tier.Type.Chunk.ForceEmptyHands=[WolvenKit.RED4.Types.CBool]::op_Implicit($false)
Fact 146 'PTFRPA2_Teleported' 1
Link 128 Out 143;Link 143 Out 144;Link 144 Out 145;Link 145 Out 146
$reveal=Clone (Get-QuestNode $g 28) 159;$reveal.Type.Chunk.Duration=[float]0.5
$failure=Clone (Get-QuestNode $g 28) 160;$failure.Type.Chunk.Duration=[float]0.5
Fact 161 'PTFRPA2_Finished' 1;Link 159 Out 161
# Only verified H10/full-control readiness may publish PostTowerFreeRoamActive.
Race 146 'PTFRPA2_ControlReady' 129 150 1 60000
# Existing 129/130 activation now starts services/profile AFTER arrival/control.
# Native blackout remains until profile/admission + fresh control acknowledgement.
# Existing one-rank-per-second refund journals are intentionally not accelerated.
# Allow large valid builds to settle; this is a maximum, not a fixed loading time.
Race 130 'PTFRPA2_Reveal' 159 170 2 180000
Write-Cr2wFile $file $p
$read=Read-Cr2wFile $p;$cg=$read.RootChunk.Graph.Chunk
$removed=@('109.Out -> 110.In','128.Out -> 129.In')
$before=@(Get-GraphEdges $original.RootChunk.Graph.Chunk);$after=@(Get-GraphEdges $cg)
if(@(Compare-Object $removed @($before|Where-Object {$_ -notin $after})).Count){throw 'Unexpected removed edge'}
foreach($h in $original.RootChunk.Graph.Chunk.Nodes){if((Get-NodeWithoutConnectionsJson $h.Chunk) -cne (Get-NodeWithoutConnectionsJson (Get-QuestNode $cg ([int]::Parse($h.Chunk.Id.ToString()))))){throw 'Prior node payload changed'}}
foreach($edge in (Get-GraphEdges $g)){Assert-ContainsExactlyOnce $after $edge PA2}
$sockets=@($cg.Nodes|ForEach-Object {$_.Chunk.Sockets}|ForEach-Object {$_.Chunk})
foreach($s in $sockets){foreach($h in $s.Connections){$c=$h.Chunk;foreach($end in @($c.Source.Chunk,$c.Destination.Chunk)){if(@($sockets|Where-Object {[object]::ReferenceEquals($_,$end)}).Count -ne 1 -or @($end.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk,$c)}).Count -ne 1){throw 'Broken native graph connection'}}}}
Export-Cr2wJson $read (Join-Path $out 'final.patched.json')
Json (Join-Path $out 'graph.json') @{removed_edges=$removed;added_edges=@($after|Where-Object {$_ -notin $before});old_nodes=$original.RootChunk.Graph.Chunk.Nodes.Count;new_nodes=$cg.Nodes.Count;source=$depot;native_teleport_payload=(Get-NodeWithoutConnectionsJson (Get-QuestNode $cg 143)|ConvertFrom-Json -Depth 100);unchanged_prior_payloads=$true}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=Join-Path $out 'package/archive/pc/mod/TowerContinued_PreAlpha.archive'
$stream=[IO.File]::Create($archive)
try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Archive pack failed'}}finally{$stream.Dispose()}
$ar=$null;([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$ar)|Out-Null
if($ar.Files.Count -ne $old.members.Count){throw 'Resource count drift'}
foreach($r in $old.members){
 $src=Join-Path $out ('source/'+$r.depot);$hash=Hash $src
 if($r.depot -cne $depot -and $hash -cne $r.sha256){throw 'Unrelated packed resource changed'}
 $mem=[IO.MemoryStream]::new();try{$ar.Files[[uint64]$r.key].Extract($mem);$got=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
 if($hash -cne $got){throw 'Packed readback mismatch'}
}
$changes=@()
foreach($name in @('PreAlphaEntry.reds','PreAlphaArrivalPA1.reds')){Copy-Item -LiteralPath (Join-Path $ws ('prealpha/transition/scripts/'+$name)) -Destination (Join-Path $out ('package/r6/scripts/PTFR_PreAlpha/PA1/'+$name))}
Copy-Item -LiteralPath (Join-Path $ws 'prealpha/transition/cet/init.lua') -Destination (Join-Path $out 'package/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua')
$package=Join-Path $out 'package'
$files=@(Get-ChildItem $package -Recurse -File|ForEach-Object {@{relative=[IO.Path]::GetRelativePath($package,$_.FullName).Replace('\','/');sha256=Hash $_.FullName;bytes=$_.Length}})
foreach($f in $files){$prior=@($old.package_files|Where-Object {$_.relative -ceq $f.relative});if($prior.Count -ne 1){throw 'File set changed'};if($prior[0].sha256 -cne $f.sha256){$changes+=@{relative=$f.relative;old_sha256=$prior[0].sha256;new_sha256=$f.sha256}}}
if($changes.Count -ne 4 -or $files.Count -ne 53){throw 'Unexpected replacement count'}
Json (Join-Path $out 'build.json') @{status='BUILT_PACKED_READBACK_PASS_COMPILE_PENDING';output=$out;package_root=$package;package_files=$files;changes=$changes;resources=$old.members.Count;prior_build=$base;all_prior_payloads_preserved=$true;only_resource_changed=$depot}
Write-Output ('BUILD_PASS='+$out)

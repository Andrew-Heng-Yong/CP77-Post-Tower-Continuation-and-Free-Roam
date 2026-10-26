$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_01';$source=Join-Path $C 'native_source_01'
if(Test-Path -LiteralPath $C){throw 'Use successor candidate'}
. (Join-Path $W 'tools/build_phase2a.ps1') -WorkspaceRoot $W -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$rel='archive/pc/mod/000000_TowerContinued_SideJobs_S25.archive';$installed=Join-Path $game $rel
$evidence=Get-Content -LiteralPath (Join-Path $W 'diagnostics/scene_membership_20261025_01/native_01/manifest.json') -Raw|ConvertFrom-Json
$expected=($evidence|Where-Object {$_.archive -eq $installed}|Select-Object -First 1).archive_sha256
if(!$expected -or (Get-FileHash -LiteralPath $installed).Hash -cne $expected){throw 'Installed baseline drift'}
function OpenArc($p){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Read failed'};return $a}
function Bytes($e){$s=[IO.MemoryStream]::new();try{$e.Extract($s);return ,$s.ToArray()}finally{$s.Dispose()}}
function HashBytes($b){[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($b))}
$arc=OpenArc $installed;$before=@{};$names=@{}
foreach($e in $arc.Files.Values){
 $name=$e.Name
 if([IO.Path]::IsPathRooted($name) -or $name.Contains(':') -or $name -match '(^|[/\\])\.\.([/\\]|$)'){throw 'Unsafe depot'}
 if([WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($name) -ne $e.Key){throw 'Unknown depot'}
 $p=[IO.Path]::GetFullPath((Join-Path $source $name))
 if(!$p.StartsWith([IO.Path]::GetFullPath($source)+'\')){throw 'Path escape'}
 New-Item -ItemType Directory -Force -Path (Split-Path $p -Parent)|Out-Null
 $b=Bytes $e;[IO.File]::WriteAllBytes($p,$b);$before[$name]=HashBytes $b;$names[$e.Key]=$name
}
$depot='towercontinued\b0_story_services\fred.questphase';$p=Join-Path $source $depot
if($before[$depot] -cne '06DE4B05E7325614D9DB4AE7FB17D3F1C1D35D1AF188AF1B587F7325E999A2AF'){throw 'Fred source changed'}
$file=Read-Cr2wFile $p
Export-Cr2wJson $file (Join-Path $C 'fred_before.questphase.json')
$outer=(Get-QuestNode $file.RootChunk.Graph.Chunk 5).PhaseGraph.Chunk
$g=(Get-QuestNode $outer 14).PhaseGraph.Chunk
function Logic($op,$conditions){$x=[WolvenKit.RED4.Types.questLogicalCondition]::new();$x.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op;foreach($c in $conditions){Add-RedHandle $x.Conditions $c};return $x}
function Fact($name,$value,$op){return New-FactCondition $name $value ([Enum]::Parse([WolvenKit.RED4.Types.Enums+EComparisonType],$op))}
function Fresh {return (Get-QuestNode $g 301).Condition.Chunk.DeepCopy()}
function Ordinary {return Logic 'OR' @((Fact 'PTFRS25_MQ025_FRESH_Issued' 1 'NotEqual'),(Fact 'PTFRS25_MQ025_FRESH_Fault' 0 'NotEqual'))}
$oldNear=(Get-QuestNode $g 4).Condition.Chunk.DeepCopy()
$oldFar=(Get-QuestNode $g 5).Condition.Chunk.DeepCopy()
function NearService {$n=$oldNear.DeepCopy();$n.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue=[single]8;return $n}
function FarService {$n=$oldNear.DeepCopy();$n.Type.Chunk.ComparisonType=[WolvenKit.RED4.Types.Enums+EComparisonType]::Greater;$n.Type.Chunk.DistanceDefinition2.Chunk.DistanceValue=[single]12;return $n}
function Admission {return Logic 'OR' @((Logic 'AND' @((Fresh),$oldNear.DeepCopy())),(Logic 'AND' @((Ordinary),(NearService))))}
function Clear($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function Add($n){if(@($g.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq $n.Id.ToString()}).Count){throw 'Duplicate node'};Add-RedHandle $g.Nodes $n}
function Link($a,$sock,$b,$dest='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $sock) (Get-QuestSocket (Get-QuestNode $g $b) $dest))}
# Preserve existing node types and IDs, including the active saved departure wait.
# Its close-range branch cuts only the private service scene and its pending
# admission. The NPC spawn owner and original boxing scene stay independent.
$edges=[Collections.Generic.List[object]]::new()
foreach($h in $g.Nodes){$n=$h.Chunk;foreach($sh in $n.Sockets){$s=$sh.Chunk;if($s.Type.ToString() -notin @('Output','CutSource')){continue};foreach($ch in $s.Connections){
 $dest=$ch.Chunk.Destination.Chunk
 $target=@($g.Nodes|Where-Object {$node=$_;@($node.Chunk.Sockets|Where-Object {[object]::ReferenceEquals($_.Chunk,$dest)}).Count -gt 0})
 if($target.Count -ne 1){throw 'Ambiguous edge'}
 $edges.Add(@([int]$n.Id.ToString(),$s.Name.ToString(),[int]$target[0].Chunk.Id.ToString(),$dest.Name.ToString()))
}}}
$originalEdges=$edges.ToArray()
Set-RedHandleProperty (Get-QuestNode $g 4) Condition (Admission)
Set-RedHandleProperty (Get-QuestNode $g 5) Condition (Logic 'OR' @($oldFar.DeepCopy(),(Logic 'AND' @((Ordinary),(FarService)))))
Add (New-ConditionNode 400 $oldFar.DeepCopy())
$cut=[WolvenKit.RED4.Types.questCutControlNodeDefinition]::new();$cut.Id=[uint16]401
foreach($s in @(@('In','Input'),@('Out','Output'),@('CutSource','CutSource'))){[void](New-QuestSocket $cut $s[0] ([Enum]::Parse([WolvenKit.RED4.Types.Enums+questSocketType],$s[1])))}
Add $cut
$wait=(Get-QuestNode $g 4).DeepCopy();$wait.Id=[uint16]402;Clear $wait
Set-RedHandleProperty $wait Condition (Logic 'OR' @((Admission),$oldFar.DeepCopy()));Add $wait
Add (New-ConditionNode 403 $oldFar.DeepCopy())
foreach($h in $g.Nodes){Clear $h.Chunk}
$changed=0
foreach($e in $originalEdges){$b=$e[2];if($e[0] -eq 5 -and $e[1] -eq 'Out'){
 if($b -ne 6 -or $e[3] -ne 'In'){throw 'Departure edge drift'};$b=400;$changed++
};Link $e[0] $e[1] $b $e[3]}
if($changed -ne 1){throw 'Unexpected edge edits'}
Link 400 True 6;Link 400 False 401
Link 401 CutSource 3 CutDestination;Link 401 CutSource 4 CutDestination;Link 401 Out 402
Link 402 Out 403;Link 403 True 6;Link 403 False 4;Link 403 False 5
Write-Cr2wFile $file $p
Export-Cr2wJson (Read-Cr2wFile $p) (Join-Path $C 'fred_after.questphase.json')
$dest=Join-Path $C ('package/'+$rel);New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null
$s=[IO.File]::Create($dest);try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$s)){throw 'Pack failed'}}finally{$s.Dispose()}
$packed=OpenArc $dest;if($packed.Files.Count -ne $arc.Files.Count){throw 'Resource count drift'};$unchanged=0
foreach($e in $packed.Files.Values){$name=$names[$e.Key];if(!$name){throw 'Unexpected resource'};$actual=HashBytes (Bytes $e)
 if($actual -cne (Get-FileHash -LiteralPath (Join-Path $source $name)).Hash){throw 'Packed readback mismatch'}
 if($name -cne $depot){if($actual -cne $before[$name]){throw 'Unrelated resource changed'};$unchanged++}
}
$bp=Join-Path $C ('before/'+$rel);New-Item -ItemType Directory -Force -Path (Split-Path $bp -Parent)|Out-Null;Copy-Item -LiteralPath $installed -Destination $bp
if((Get-FileHash -LiteralPath $bp).Hash -cne $expected -or (Get-FileHash -LiteralPath $installed).Hash -cne $expected){throw 'Input drift'}
$report=@{status='FS1_BUILT_NOT_LIVE';target=$rel;before=$expected;after=(Get-FileHash -LiteralPath $dest).Hash;changed_resource=$depot;resource_before=$before[$depot];resource_after=(Get-FileHash -LiteralPath $p).Hash;resources=$arc.Files.Count;unchanged_resources=$unchanged;original_resource_hashes=$before;old_edges=$originalEdges;added_nodes=@(400,401,402,403);changed_edges=1;game_writes=0}
$report|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $C 'build_01.json') -Encoding utf8
$report|Select-Object status,before,after,unchanged_resources,resource_after|ConvertTo-Json

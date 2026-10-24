$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$C=Join-Path $PSScriptRoot 'candidate_01';$source=Join-Path $C 'native_source_02'
if(Test-Path $source){throw 'Use successor'}
. (Join-Path $W 'tools/build_phase2a.ps1') -WorkspaceRoot $W -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$G='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$rel='archive/pc/mod/0000_TowerContinued_SideJobs_S23.archive';$installed=Join-Path $G $rel
$evidence=Get-Content (Join-Path $C 'native_inspect_01/resources.json') -Raw|ConvertFrom-Json
$expected=($evidence|Where-Object {$_.archive -eq $installed}|Select-Object -First 1).archive_sha256
if((Get-FileHash $installed).Hash -cne $expected){throw 'Baseline drift'}
function OpenArc($p){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Read failed'};return $a}
function Bytes($e){$s=[IO.MemoryStream]::new();try{$e.Extract($s);return ,$s.ToArray()}finally{$s.Dispose()}}
function HashBytes($b){[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($b))}
$arc=OpenArc $installed;$before=@{};$names=@{}
foreach($e in $arc.Files.Values){
 $name=$e.Name;if([IO.Path]::IsPathRooted($name) -or $name.Contains(':') -or $name -match '(^|[/\\])\.\.([/\\]|$)'){throw 'Unsafe path'}
 if([WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($name) -ne $e.Key){throw 'Unknown depot'}
 $p=Join-Path $source $name;New-Item -ItemType Directory -Force -Path (Split-Path $p -Parent)|Out-Null;$b=Bytes $e;[IO.File]::WriteAllBytes($p,$b);$before[$name]=HashBytes $b;$names[$e.Key]=$name
}
$depot='towercontinued\sidejobs_s23\base_b\mq011.questphase';$file=Read-Cr2wFile (Join-Path $source $depot);$g=$file.RootChunk.Graph.Chunk
function Eq($name,$v){return New-FactCondition $name $v ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)}
function Logic($op,$conditions){$x=[WolvenKit.RED4.Types.questLogicalCondition]::new();$x.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::$op;foreach($c in $conditions){Add-RedHandle $x.Conditions $c};return $x}
function Add($n){if(@($g.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq $n.Id.ToString()}).Count){throw 'Duplicate ID'};Add-RedHandle $g.Nodes $n}
function Pause($id,$condition){$n=(Get-QuestNode $g 1011).DeepCopy();$n.Id=[uint16]$id;foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()};Set-RedHandleProperty $n Condition $condition;return $n}
function Link($a,$sock,$b,$dest='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $sock) (Get-QuestSocket (Get-QuestNode $g $b) $dest))}
# Capture the exact directed edges before changing three entry routes. Payloads
# of every original native parent wait, guard, child, and all reward nodes stay.
$edges=[Collections.Generic.List[object]]::new()
foreach($h in $g.Nodes){$n=$h.Chunk;foreach($sh in $n.Sockets){$s=$sh.Chunk;if($s.Type.ToString() -ne 'Output'){continue};foreach($ch in $s.Connections){$conn=$ch.Chunk;$dest=$conn.Destination.Chunk;$target=@($g.Nodes|Where-Object { $node=$_; @($node.Chunk.Sockets|Where-Object {[object]::ReferenceEquals($_.Chunk,$dest)}).Count -gt 0 });if($target.Count -ne 1){throw 'Edge target ambiguous'};$edges.Add(@([int]$n.Id.ToString(),$s.Name.ToString(),[int]$target[0].Chunk.Id.ToString(),$dest.Name.ToString()))}}}
$originalEdges=$edges.ToArray()
$released=(Get-QuestNode $g 1011).Condition.Chunk.DeepCopy()
# Already-saved old wait1011 remains a pre-parent path. If H2 safely released
# its idle reservation, it can continue without racing the resumed vendor.
Set-RedHandleProperty (Get-QuestNode $g 1011) Condition (Logic 'OR' @($released.DeepCopy(),(Logic 'AND' @((Eq 'PTFRB0WV_QuestOwns' 0),(Eq 'PTFRH2_WV_LeaseRequested' 0)))))
Add (New-SetFactNode 1014 'PTFRB0WV_QuestOwns' 0)
foreach($base in @(1110,1120)){
 Add (New-SetFactNode $base 'PTFRH2_WV_LeaseRequested' 1)
 Add (New-SetFactNode ($base+1) 'PTFRB0WV_QuestOwns' 1)
 Add (Pause ($base+2) $released.DeepCopy())
}
Add (New-SetFactNode 1113 'PTFRH2_WV_LeaseRequested' 0)
foreach($h in $g.Nodes){foreach($sh in $h.Chunk.Sockets){$sh.Chunk.Connections.Clear()}}
$changed=0
foreach($edge in $originalEdges){
 $a=$edge[0];$sock=$edge[1];$b=$edge[2];$dest=$edge[3]
 if($a -eq 1003){if($b -ne 1010){throw 'Entry route drift'};$b=54;$changed++}
 elseif($a -eq 1011){if($b -ne 54){throw 'Old lease continuation drift'};$b=1014;$changed++}
 elseif($a -eq 93){if($b -ne 1004){throw 'Native content wait route drift'};$b=1110;$changed++}
 elseif($a -eq 184 -and $sock -eq 'False'){if($b -ne 1104){throw 'Standalone route drift'};$b=1120;$changed++}
 elseif($a -eq 1013){if($b -ne 1002){throw 'Refusal route drift'};$b=1113;$changed++}
 Link $a $sock $b $dest
}
if($changed -ne 5){throw 'Unexpected edit count'}
Link 1014 Out 54;Link 1110 Out 1111;Link 1111 Out 1112;Link 1112 Out 1004
Link 1120 Out 1121;Link 1121 Out 1122;Link 1122 Out 1104;Link 1113 Out 1002
$p=Join-Path $source $depot;Write-Cr2wFile $file $p
New-Item -ItemType Directory -Path (Join-Path $C 'native_readback_02')|Out-Null
Export-Cr2wJson (Read-Cr2wFile $p) (Join-Path $C 'native_readback_02/mq011.questphase.json')
$dest=Join-Path $C ('package/'+$rel);New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null
$s=[IO.File]::Create($dest);try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$s)){throw 'Pack failed'}}finally{$s.Dispose()}
$packed=OpenArc $dest;if($packed.Files.Count -ne $arc.Files.Count){throw 'Count differs'};$unchanged=0
foreach($e in $packed.Files.Values){$name=$names[$e.Key];if(!$name){throw 'Unexpected resource'};$actual=HashBytes (Bytes $e);if($actual -cne (Get-FileHash (Join-Path $source $name)).Hash){throw 'Packed data differs'};if($name -cne $depot){if($actual -cne $before[$name]){throw 'Unrelated resource changed'};$unchanged++}}
$bp=Join-Path $C ('before/'+$rel);New-Item -ItemType Directory -Force -Path (Split-Path $bp -Parent)|Out-Null;Copy-Item $installed $bp
if((Get-FileHash $bp).Hash -cne $expected -or (Get-FileHash $installed).Hash -cne $expected){throw 'Input drift'}
$result=@{status='BUILT_H2_LEASE_CONTINUATION_NOT_LIVE';target=$rel;before=$expected;after=(Get-FileHash $dest).Hash;changed_resource=$depot;original_resource_hashes=$before;unchanged_resources=$unchanged;old_edges=$originalEdges;added_nodes=@(1014,1110,1111,1112,1113,1120,1121,1122);changed_edges=5}
$result|ConvertTo-Json -Depth 15|Set-Content (Join-Path $C 'native_02.json') -Encoding utf8
$result|Select-Object status,before,after,unchanged_resources|ConvertTo-Json


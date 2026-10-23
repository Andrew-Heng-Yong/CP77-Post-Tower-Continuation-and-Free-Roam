param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\b0_tv_media'
$source=Join-Path $WorkspaceRoot 'archive\b0_tv_media\source'
$build=Join-Path $WorkspaceRoot 'build\TVMedia'
New-Item -ItemType Directory -Force -Path $audit,$source,$build|Out-Null
$file=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_tv_restore\extracted\raw\base\media\tv\tv_content.questphase')
Export-Cr2wJson $file (Join-Path $audit 'original.json')
$g=$file.RootChunk.Graph.Chunk
function Link($graph,$a,$socket,$b,$inputName='In'){
 [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $a) $socket) (Get-QuestSocket (Get-QuestNode $graph $b) $inputName))
}
function Unlink($graph,$a,$socket,$b,$inputName='In'){
 $s=Get-QuestSocket (Get-QuestNode $graph $a) $socket;$d=Get-QuestSocket (Get-QuestNode $graph $b) $inputName
 $matches=@($s.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk.Destination.Chunk,$d)})
 if($matches.Count -ne 1){throw 'Edge not unique'}
 $connection=$matches[0].Chunk
 foreach($sock in @($s,$d)){for($i=$sock.Connections.Count-1;$i -ge 0;$i--){if([object]::ReferenceEquals($sock.Connections[$i].Chunk,$connection)){$sock.Connections.RemoveAt($i)}}}
}
# Keep original native channel owner/termination topology. Replace only its
# unconditional global tv_on initializer; both first entry and re-entry guard.
$init=Get-QuestNode $g 15;$init.Type.Chunk.FactName='PTFRTVM_Registered'
Unlink $g 15 Out 14 In1;Link $g 15 Out 11
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRTV_Applied=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;PTFRBASE_Suspended=0;PTFRTVM_Suspended=0;PTFRTVM_QuestOwns=0}
foreach($f in $facts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $f $facts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
Add-RedHandle $guard.Conditions (Get-QuestNode $g 11).Condition.Chunk.DeepCopy()
Set-RedHandleProperty (Get-QuestNode $g 11) Condition $guard
Add-RedHandle $g.Nodes (New-SetFactNode 16 'PTFRTVM_Running' 1)
Add-RedHandle $g.Nodes (New-SetFactNode 17 'PTFRTVM_Running' 0)
$counter=New-SetFactNode 18 'PTFRTVM_Starts' 1;$counter.Type.Chunk.SetExactValue=$false;Add-RedHandle $g.Nodes $counter
Unlink $g 11 Out 14 In1;Link $g 11 Out 16;Link $g 16 Out 18;Link $g 18 Out 14 In1
Unlink $g 14 Out1 11;Link $g 14 Out1 17;Link $g 17 Out 11
# Vanilla child terminates its six channel phases when tv_on becomes zero.
# Extend that same native termination route for explicit future-owner handoff
# and guard invalidation; do not implement a separate competing cancellation.
$child=(Get-QuestNode $g 14).PhaseGraph.Chunk
$stop=[WolvenKit.RED4.Types.questLogicalCondition]::new();$stop.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
Add-RedHandle $stop.Conditions (Get-QuestNode $child 7).Condition.Chunk.DeepCopy()
foreach($f in $facts.Keys){Add-RedHandle $stop.Conditions (New-FactCondition $f $facts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual))}
Set-RedHandleProperty (Get-QuestNode $child 7) Condition $stop
$depot='towercontinued\tv_media\controller.questphase'
Write-Cr2wFile $file (Join-Path $source $depot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit 'controller.json')
$gate=Read-Cr2wFile (Join-Path $WorkspaceRoot 'archive\b0_ordinary_mirrors_c5_red_dirt\source\towercontinued\ordinary_mirrors_c5_red_dirt\m42_gate.questphase')
if($gate.RootChunk.PhasePrefabs.Count -ne 0){throw 'Gate must not acquire prefabs'}
Set-RedHandleProperty (Get-QuestNode $gate.RootChunk.Graph.Chunk 1) Condition $guard.DeepCopy()
$ownerNode=Get-QuestNode $gate.RootChunk.Graph.Chunk 2
$rp=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)
$ownerNode.PhaseResource=[Activator]::CreateInstance($ownerNode.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($rp))
$gateDepot='towercontinued\tv_media\gate.questphase'
Write-Cr2wFile $gate (Join-Path $source $gateDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $gateDepot)) (Join-Path $audit 'gate.json')
$crc=65535
foreach($b in [Text.Encoding]::UTF8.GetBytes($gateDepot+':1')){$x=($crc -shr 8) -bxor $b;$x=$x -bxor ($x -shr 4);$crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535}
$ep1=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
if(@($ep1.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq "$crc"}).Count){throw 'Parent registration collision'}
$xl=Join-Path $WorkspaceRoot 'archive\b0_tv_media\TowerContinued_TVMedia.archive.xl'
[IO.File]::WriteAllLines($xl,@('# Native post-Tower media owner; no story root restart.','quest:','  phases:',"    - path: $gateDepot",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out'),[Text.UTF8Encoding]::new($false))
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $build 'TowerContinued_TVMedia.archive'
$stream=[IO.File]::Create($archive)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive write failed'}}finally{$stream.Dispose()}
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$packed=$null
if($reader.ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
if(@(Compare-Object @($depot,$gateDepot|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Unexpected resources'}
Copy-Item $xl ($archive+'.xl') -Force
$manifest=@{status='AUTOMATIC_MEDIA_CANDIDATE';resource=$depot;gate=$gateDepot;registration_id=$crc;guards=$facts;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash;vanilla_replacements=@();new_polling=$false;tv_on_writer=$false;channels=@($child.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'questPhaseNodeDefinition'}|ForEach-Object {$_.Chunk.PhaseResource.DepotPath.ToString()})}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 5

param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[switch]$RelationshipHomes)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$family=if($RelationshipHomes){'relationship_mirrors'}else{'remaining_mirrors'}
$package=if($RelationshipHomes){'RelationshipMirrors'}else{'RemainingMirrors'}
$audit=Join-Path $WorkspaceRoot ("research\b0_"+$family)
$vanillaAudit=Join-Path $WorkspaceRoot 'research\b0_remaining_mirrors'
$source=Join-Path $WorkspaceRoot ("archive\b0_$family\source")
$build=Join-Path $WorkspaceRoot ("build\"+$package)
New-Item -ItemType Directory -Force -Path $audit,$source,$build|Out-Null
$inventory=Get-Content (Join-Path $vanillaAudit 'inventory.json') -Raw|ConvertFrom-Json
$selected=if($RelationshipHomes){@(7,10,13,20)}else{@(4,6,12,14,15,19,24,37)}
$mirror=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_mirror_investigation\extracted\raw\base\open_world\scenes\mirrors\mirror_interactions_control.questphase')
$outer=(Get-QuestNode $mirror.RootChunk.Graph.Chunk 42).PhaseGraph.Chunk
$foundation=Read-Cr2wFile (Join-Path $WorkspaceRoot 'archive\b0_ordinary_mirrors_c5_red_dirt\source\towercontinued\ordinary_mirrors_c5_red_dirt\m42_gate.questphase')
$pauseTemplate=Get-QuestNode $foundation.RootChunk.Graph.Chunk 1
$opt=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
function Phase($graph){
 $r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$r.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
 Set-RedHandleProperty $r Graph $graph
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$r;return $f
}
function Link($g,$a,$socket,$b,$inputName='In'){
 [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $socket) (Get-QuestSocket (Get-QuestNode $g $b) $inputName))
}
function TransformFile($file,$short,$full,$handshake){
 $dto=[WolvenKit.Common.Conversion.RedFileDto]::new($file,$false)
 $j=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto,$script:opt)
 $j=$j.Replace('"$value": "'+$short+'"','"$value": "'+$full+'"')
 if($handshake){$j=$j.Replace('"factName": "mirror_scene_shady_ripper_exit"','"factName": "PTFRRM12_Exit"')}
 return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$j,$script:opt).Data
}
function Guard($id){
 $g=$script:pauseTemplate.Condition.Chunk.DeepCopy()
 for($i=$g.Conditions.Count-1;$i -ge 0;$i--){
  $c=$g.Conditions[$i].Chunk
  if($c.GetType().Name -eq 'questFactsDBCondition' -and $c.Type.Chunk.FactName.ToString() -in @('PTFRBM42_Enabled','PTFRBM42_Interrupted','sq011_mirror_off ')){$g.Conditions.RemoveAt($i)}
 }
 Add-RedHandle $g.Conditions (New-FactCondition ("PTFRRM${id}_Suspended") 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
 if($id -eq 6){foreach($f in 'nomad_camp_01_active_combat','sq027_camp_abandoned','sq027_camp_moved'){
  Add-RedHandle $g.Conditions (New-FactCondition $f 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::LessOrEqual))
 }}
 if($id -eq 37){Add-RedHandle $g.Conditions (New-FactCondition 'sts_wbr_hil_01_mirror_enabled' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))}
 if($id -eq 7){Add-RedHandle $g.Conditions (New-FactCondition 'nomad_camp_02_active_default' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))}
 return $g
}
$records=[System.Collections.Generic.List[object]]::new()
$resources=[System.Collections.Generic.List[string]]::new()
$xl=[System.Collections.Generic.List[string]]::new();$xl.Add('# Guarded world mirrors; retain exact vanilla leaf behavior.');$xl.Add('quest:');$xl.Add('  phases:')
foreach($id in $selected){
 $info=@($inventory|Where-Object id -EQ $id)[0]
 if($info.sectors.Count -ne 1){throw "Site ${id}: unresolved descriptor"}
 $sector=Read-Cr2wFile (Join-Path $vanillaAudit ('extracted\raw\'+$info.sectors[0]))
 $short=$info.triggers[0]
 $matches=@($sector.RootChunk.NodeData.Data|Where-Object {$_.QuestPrefabRefHash.ToString().EndsWith('/'+$short)})
 if($matches.Count -ne 1){throw "Site ${id}: trigger not unique"}
 $full=$matches[0].QuestPrefabRefHash.ToString()
 $prefab=@($mirror.RootChunk.PhasePrefabs|Where-Object {$_.PrefabNodeRef.ToString() -eq $info.prefab})
 if($prefab.Count -ne 1){throw "Site ${id}: prefab unresolved"}
 # Serialize the original shared graph before copying. Generic DeepCopy breaks
 # connection/socket object identity on cyclic quest graphs.
 $leaf=(Get-QuestNode $outer $id).PhaseGraph.Chunk
 $owner=Phase $leaf
 Export-Cr2wJson $owner (Join-Path $audit "m${id}_original_owner.json")
 $owner=TransformFile $owner $short $full ($id -eq 12)
 $leaf=$owner.RootChunk.Graph.Chunk
 $scene=Read-Cr2wFile (Join-Path $vanillaAudit ('extracted\raw\'+$info.scene))
 Export-Cr2wJson $scene (Join-Path $audit "m${id}_original_scene.json")
 $scene=TransformFile $scene $short $full ($id -eq 12)
 # Preserve all original nodes/edges, including gates, exits, deletion markers
 # and one-shot behavior. Only augment the existing local trigger wait.
 $guarded=0
 foreach($n in $leaf.Nodes){
  if($n.Chunk.GetType().Name -ne 'questPauseConditionNodeDefinition'){continue}
  $condition=$n.Chunk.Condition.Chunk
  if($condition.GetType().Name -eq 'questTriggerCondition' -and $condition.Type.ToString() -eq 'IsInside'){
   $g=Guard $id;Add-RedHandle $g.Conditions $condition.DeepCopy();Set-RedHandleProperty $n.Chunk Condition $g;$guarded++
  }
 }
 if($guarded -ne 1){throw "Site ${id}: expected exactly one local entry guard"}
 $sceneNodes=@($leaf.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'questSceneNodeDefinition'})
 if($sceneNodes.Count -ne 1){throw "Site ${id}: scene count changed"}
 $stem="m$id";$gateDepot="towercontinued\$family\${stem}_gate.questphase";$ownerDepot="towercontinued\$family\${stem}_owner.questphase";$sceneDepot="towercontinued\$family\${stem}.scene"
 $rp=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
 $sn=$sceneNodes[0].Chunk
 $sn.SceneFile=[Activator]::CreateInstance($sn.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($rp))
 $owner.RootChunk.PhasePrefabs.Add($prefab[0].DeepCopy())
 $gate=(TransformFile $foundation '__unused' '__unused' $false).RootChunk;$gg=$gate.Graph.Chunk
 Set-RedHandleProperty (Get-QuestNode $gg 1) Condition (Guard $id)
 $child=Get-QuestNode $gg 2;$rp=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerDepot)
 $child.PhaseResource=[Activator]::CreateInstance($child.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($rp))
 $gf=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$gf.RootChunk=$gate
 foreach($spec in @(@($gateDepot,$gf,'gate'),@($ownerDepot,$owner,'owner'),@($sceneDepot,$scene,'scene'))){
  Write-Cr2wFile $spec[1] (Join-Path $source $spec[0])
  Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $spec[0])) (Join-Path $audit ("m${id}_"+$spec[2]+'.json'))
  $resources.Add($spec[0])
 }
 $crc=65535
 foreach($b in [Text.Encoding]::UTF8.GetBytes($gateDepot+':1')){$x=($crc -shr 8) -bxor $b;$x=$x -bxor ($x -shr 4);$crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535}
 $xl.Add("    - path: $gateDepot");$xl.Add('      parent: ep1\quest\ep1.quest');$xl.Add('      input:');$xl.Add('        node: [1]');$xl.Add('        socket: Out')
 $records.Add(@{id=$id;scene=$info.scene;trigger=$full;registration_id=$crc;scene_nodes=$scene.RootChunk.SceneGraph.Chunk.Graph.Count;leaf_nodes=$leaf.Nodes.Count;handshake_namespaced=($id -eq 12)})
}
$ep1=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
foreach($r in $records){if(@($ep1.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq "$($r.registration_id)"}).Count){throw 'Registration collision'}}
$xlPath=Join-Path $WorkspaceRoot "archive\b0_$family\TowerContinued_$package.archive.xl"
[IO.File]::WriteAllLines($xlPath,$xl,[Text.UTF8Encoding]::new($false))
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $build "TowerContinued_$package.archive"
$stream=[IO.File]::Create($archive)
try{$w=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new());if(-not $w.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive failed'}}finally{$stream.Dispose()}
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new();$packed=$null
if($reader.ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'Archive reopen failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Archive manifest mismatch'}
Copy-Item $xlPath ($archive+'.xl') -Force
$deferred=if($RelationshipHomes){@(9)}else{@(7,9,10,13,16,17,18,20)}
$manifest=@{status='AUTOMATIC_CANDIDATES';sites=@($records);resources=@($resources);sha256=(Get-FileHash $archive).Hash;vanilla_replacements=@();new_polling=$false;deferred_ids=@($deferred)}
if($RelationshipHomes){$manifest.scope='Original relationship-home mirror behavior; no home access or ownership changes';$manifest.ending_only_excluded_ids=@(16,17,18)}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 4

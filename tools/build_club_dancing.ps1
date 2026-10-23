param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\b0_club_dancing'
$source=Join-Path $WorkspaceRoot 'archive\b0_club_dancing\source'
$build=Join-Path $WorkspaceRoot 'build\ClubDancing'
New-Item -ItemType Directory -Force -Path $source,$build|Out-Null
$original=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_world_interactions\extracted\raw\base\open_world\scenes\dancefloors\dancefloors.questphase')
$foundation=Read-Cr2wFile (Join-Path $WorkspaceRoot 'archive\b0_ordinary_mirrors_c5_red_dirt\source\towercontinued\ordinary_mirrors_c5_red_dirt\m42_gate.questphase')
$facts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_active=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q305_johnny_scene_active=0;q115_point_of_no_return=0;PTFRBASE_Suspended=0;PTFRDANCE_Suspended=0;PTFRDANCE_QuestOwns=0}
$sites=@(
 @{key='riot';id=46;fact='riot_dancefloor_on';sector='quest_36bb6b7ddcc1f478';entry=12;init=11;marker='#dancefloor_sm_riot'},
 @{key='empathy';id=44;fact='emphaty_dancefloor_on';sector='quest_f8fcf630df89ede2';entry=13;init=12;marker='#dancefloor_sm_empathy'},
 @{key='7th_hell';id=48;fact='7th_hell_dancefloor_on';sector='quest_2942b8f72d916e24';entry=13;init=11;marker='#dancefloor_7th_sm_hell'},
 @{key='totentanz';id=50;fact='totentanz_dancefloor_on';sector='quest_2524d47b00419116';entry=12;init=11;marker='#dancefloor_sm_totentanz'}
)
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
function Transform($file,$short,$full){
 $j=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize([WolvenKit.Common.Conversion.RedFileDto]::new($file,$false),$script:options)
 $j=$j.Replace('"$value": "'+$short+'"','"$value": "'+$full+'"')
 return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$j,$script:options).Data
}
function Guard($site){
 $g=[WolvenKit.RED4.Types.questLogicalCondition]::new();$g.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 foreach($f in $script:facts.Keys){Add-RedHandle $g.Conditions (New-FactCondition $f $script:facts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
 Add-RedHandle $g.Conditions (New-FactCondition $site.fact 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual))
 Add-RedHandle $g.Conditions (New-FactCondition ("PTFRDANCE_"+$site.key+'_Suspended') 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
 return $g
}
function Link($g,$a,$socket,$b,$inputName='In'){
 [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $socket) (Get-QuestSocket (Get-QuestNode $g $b) $inputName))
}
function Unlink($g,$a,$socket,$b,$inputName='In'){
 $s=Get-QuestSocket (Get-QuestNode $g $a) $socket;$d=Get-QuestSocket (Get-QuestNode $g $b) $inputName
 $m=@($s.Connections|Where-Object {[object]::ReferenceEquals($_.Chunk.Destination.Chunk,$d)})
 if($m.Count -ne 1){throw 'Expected one edge'};$c=$m[0].Chunk
 foreach($sock in @($s,$d)){for($i=$sock.Connections.Count-1;$i -ge 0;$i--){if([object]::ReferenceEquals($sock.Connections[$i].Chunk,$c)){$sock.Connections.RemoveAt($i)}}}
}
$records=[Collections.Generic.List[object]]::new();$resources=[Collections.Generic.List[string]]::new()
$xl=[Collections.Generic.List[string]]::new();$xl.Add('# Four public dance floors, original availability preserved.');$xl.Add('quest:');$xl.Add('  phases:')
foreach($site in $sites){
 $key=$site.key;$prefix="PTFRDANCE_${key}_";$short="#dancefloor_tr_$key"
 $sector=Read-Cr2wFile (Join-Path $audit ("world\raw\base\worlds\03_night_city\_compiled\default\"+$site.sector+'.streamingsector'))
 if($sector.RootChunk.Nodes.Count -ne 1 -or $sector.RootChunk.Nodes[0].Chunk.GetType().Name -ne 'worldTriggerAreaNode'){throw 'Unexpected dance prefab contents'}
 $matches=@($sector.RootChunk.NodeData.Data|Where-Object {$_.QuestPrefabRefHash.ToString().EndsWith('/'+$short)})
 if($matches.Count -ne 1){throw 'Trigger not unique'};$d=$matches[0];$full=$d.QuestPrefabRefHash.ToString()
 $r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$r.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
 Set-RedHandleProperty $r Graph (Get-QuestNode $original.RootChunk.Graph.Chunk $site.id).PhaseGraph.Chunk
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$r
 Export-Cr2wJson $file (Join-Path $audit ($key+'_original_owner.json'))
 $file=Transform $file $short $full;$g=$file.RootChunk.Graph.Chunk
 # Do not repeat vanilla unconditional availability initialization. Saved
 # quest decisions continue to control each floor, including closed gates.
 (Get-QuestNode $g $site.init).Type.Chunk.FactName=$prefix+'Registered'
 $guard=Guard $site;$entry=Get-QuestNode $g $site.entry
 Add-RedHandle $guard.Conditions $entry.Condition.Chunk.DeepCopy();Set-RedHandleProperty $entry Condition $guard
 # Use the existing native termination route for local availability or a
 # future cooperative owner handoff. Actual release remains a live-test item.
 $stop=[WolvenKit.RED4.Types.questLogicalCondition]::new();$stop.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
 Add-RedHandle $stop.Conditions (Get-QuestNode $g 4).Condition.Chunk.DeepCopy()
 foreach($f in $facts.Keys){Add-RedHandle $stop.Conditions (New-FactCondition $f $facts[$f] ([WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual))}
 Add-RedHandle $stop.Conditions (New-FactCondition ($prefix+'Suspended') 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual))
 Set-RedHandleProperty (Get-QuestNode $g 4) Condition $stop
 $sceneNode=Get-QuestNode $g 9;$originalScene=$sceneNode.SceneFile.DepotPath.ToString()
 $scene=Read-Cr2wFile (Join-Path $audit ('extracted\raw\'+$originalScene))
 Export-Cr2wJson $scene (Join-Path $audit ($key+'_original_scene.json'));$scene=Transform $scene $short $full
 $sceneDepot="towercontinued\club_dancing\$key.scene";$ownerDepot="towercontinued\club_dancing\${key}_owner.questphase";$gateDepot="towercontinued\club_dancing\${key}_gate.questphase"
 $rp=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($sceneDepot)
 $sceneNode.SceneFile=[Activator]::CreateInstance($sceneNode.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($rp))
 # Counters describe scene requests/normal returns, not successful dance clicks.
 foreach($spec in @(@(20,'Requests'),@(21,'Returns'))){$n=New-SetFactNode $spec[0] ($prefix+$spec[1]) 1;$n.Type.Chunk.SetExactValue=$false;Add-RedHandle $g.Nodes $n}
 Unlink $g $site.entry Out 9 ("dancefloor_${key}_in");Link $g $site.entry Out 20;Link $g 20 Out 9 ("dancefloor_${key}_in")
 Unlink $g 9 ("dancefloor_${key}_out") 10;Link $g 9 ("dancefloor_${key}_out") 21;Link $g 21 Out 10
 $prefab=@($original.RootChunk.PhasePrefabs|Where-Object {$_.PrefabNodeRef.ToString() -eq "#dancefloor_$key"})
 if($prefab.Count -ne 1){throw 'Missing prefab'};$file.RootChunk.PhasePrefabs.Add($prefab[0].DeepCopy())
 $gate=Transform $foundation '__unused' '__unused';$gg=$gate.RootChunk.Graph.Chunk
 if($gate.RootChunk.PhasePrefabs.Count -ne 0){throw 'Gate owns prefab'}
 Set-RedHandleProperty (Get-QuestNode $gg 1) Condition (Guard $site)
 $child=Get-QuestNode $gg 2;$rp=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit($ownerDepot)
 $child.PhaseResource=[Activator]::CreateInstance($child.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@($rp))
 foreach($spec in @(@($gateDepot,$gate,'gate'),@($ownerDepot,$file,'owner'),@($sceneDepot,$scene,'scene'))){Write-Cr2wFile $spec[1] (Join-Path $source $spec[0]);Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $spec[0])) (Join-Path $audit ($key+'_'+$spec[2]+'.json'));$resources.Add($spec[0])}
 $crc=65535;foreach($b in [Text.Encoding]::UTF8.GetBytes($gateDepot+':1')){$x=($crc -shr 8) -bxor $b;$x=$x -bxor ($x -shr 4);$crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535}
 $xl.Add("    - path: $gateDepot");$xl.Add('      parent: ep1\quest\ep1.quest');$xl.Add('      input:');$xl.Add('        node: [1]');$xl.Add('        socket: Out')
 $records.Add(@{key=$key;original_leaf=$site.id;availability=$site.fact;entry=$site.entry;init=$site.init;prefab="#dancefloor_$key";marker=$site.marker;trigger=$full;sector=$site.sector;registration_id=$crc;xyz=@([double]$d.Position.X.ToString(),[double]$d.Position.Y.ToString(),[double]$d.Position.Z.ToString())})
}
$ep1=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
foreach($record in $records){if(@($ep1.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq "$($record.registration_id)"}).Count){throw 'Parent ID collision'}}
$xlPath=Join-Path $WorkspaceRoot 'archive\b0_club_dancing\TowerContinued_ClubDancing.archive.xl';[IO.File]::WriteAllLines($xlPath,$xl,[Text.UTF8Encoding]::new($false))
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load();$archive=Join-Path $build 'TowerContinued_ClubDancing.archive'
$stream=[IO.File]::Create($archive);try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'Reopen failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Packed resources mismatch'}
Copy-Item $xlPath ($archive+'.xl') -Force
$manifest=@{status='BUILT_AUTOMATIC_CANDIDATE';sites=@($records);guards=$facts;resources=@($resources);excluded=@('atlantis');vanilla_replacements=@();new_polling=$false;vanilla_fact_writers=$false;sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false));$manifest|ConvertTo-Json -Depth 4

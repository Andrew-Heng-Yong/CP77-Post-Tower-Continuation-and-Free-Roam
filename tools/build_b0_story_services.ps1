param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$scope=Join-Path $WorkspaceRoot 'research\b0_story_services'
$cohort=Get-Content (Join-Path $scope 'cohort.json') -Raw|ConvertFrom-Json
$source=Join-Path $WorkspaceRoot 'archive\b0_story_services\source'
$out=Join-Path $WorkspaceRoot 'build\B0_StoryServices'
$val=Join-Path $scope 'validation'
New-Item -ItemType Directory -Force -Path $source,$out,$val|Out-Null
$base=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')
function ClearSockets($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function Link($g,$a,$sock,$b,$dest='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $sock) (Get-QuestSocket (Get-QuestNode $g $b) $dest))}
function Inc($id,$fact){$n=New-SetFactNode $id $fact 1;$n.Type.Chunk.SetExactValue=$false;return $n}
function And(){ $c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND;return $c }
function Eq($f,$v){return New-FactCondition $f $v ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)}
function PhaseAt($root,$route){
 $g=$root.Graph.Chunk;$n=$null
 foreach($id in $route.Replace('root/','').Split('/')){$n=Get-QuestNode $g ([int]$id.Replace('node',''));$g=$n.PhaseGraph.Chunk}
 return $n
}
function SceneNode($r,$id){return @($r.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq $id.ToString()})[0].Chunk}
function Rewire($g,$route,$s){
 $inner=$route -eq $s.inner_route
 if($inner){foreach($n in @((Inc 200 ($s.prefix+'Entries')),(Inc 201 ($s.prefix+'Exits')),(Inc 202 ($s.prefix+'SceneRequests')))){Add-RedHandle $g.Nodes $n}}
 foreach($h in $g.Nodes){ClearSockets $h.Chunk}
 foreach($e in $s.graphs.$route.edges){
  $a=$e.source_node_id;$sock=$e.source_socket;$b=$e.destination_node_id;$dest=$e.destination_socket
  if($inner){
   if($s.entry_target -eq 0 -and $a -eq 0){$a=200;$sock='Out'}
   if($s.entry_target -ne 0 -and $b -eq $s.entry_target){$b=200;$dest='In'}
   if($b -eq $s.output_node){$b=201;$dest='In'}
   if($e.source_node_id -eq $s.scene_edge.source_node_id -and $e.destination_node_id -eq $s.scene_node -and $e.destination_socket -eq $s.scene_edge.destination_socket){$b=202;$dest='In'}
  }
  Link $g $a $sock $b $dest
 }
 if($inner){
  if($s.entry_target -eq 0){Link $g 0 Out 200}else{Link $g 200 Out $s.entry_target}
  Link $g 201 Out $s.output_node;Link $g 202 Out $s.scene_node $s.scene_edge.destination_socket
  if($s.scene_copy){
   $n=Get-QuestNode $g $s.scene_node;$rp=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit(('towercontinued\b0_story_services\'+$s.key+'.scene'))
   $n.SceneFile=[Activator]::CreateInstance($n.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($rp))
  }
 }
 foreach($h in $g.Nodes){if($h.Chunk -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $h.Chunk.PhaseGraph.Chunk){Rewire $h.Chunk.PhaseGraph.Chunk ($route+'/node'+$h.Chunk.Id.ToString()) $s}}
}
$paths=[Collections.Generic.List[string]]::new();$phasePaths=[Collections.Generic.List[string]]::new();$sources=@{}
foreach($s in $cohort.sites){
 foreach($k in @('owner','scene')){if((Get-FileHash (Join-Path $WorkspaceRoot $s.($k+'_json'))).Hash -ne $s.($k+'_sha256')){throw 'Audited source changed'}}
 if($s.scene_copy){
  $sc=Read-Cr2wFile (Join-Path $WorkspaceRoot $s.scene_raw)
  $hidden=@()
  if($s.key -eq 'fred'){
   $start=SceneNode $sc.RootChunk 1;$alt=SceneNode $sc.RootChunk 534
   $start.OutputSockets[0].Destinations.Clear()
   foreach($d in $alt.OutputSockets[0].Destinations){$start.OutputSockets[0].Destinations.Add($d.DeepCopy())}
   $hidden=@(@(3,1),@(3,2))
  }elseif($s.key -eq 'charles'){$hidden=@(,@(5,2))}
  foreach($h in $hidden){
   $n=SceneNode $sc.RootChunk $h[0];$idx=$h[1];$never=And
   Add-RedHandle $never.Conditions (Eq 'PTFRB0ST_Never' 0);Add-RedHandle $never.Conditions (Eq 'PTFRB0ST_Never' 1)
   Set-RedHandleProperty $n.Options[$idx] QuestCondition $never
   $n.OutputSockets[$idx].Destinations.Clear()
  }
  $sd='towercontinued\b0_story_services\'+$s.key+'.scene';$paths.Add($sd)
  Write-Cr2wFile $sc (Join-Path $source $sd)
  Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $sd)) (Join-Path $val ($s.key+'.scene.json'))
 }
 if(-not $sources.ContainsKey($s.owner_raw)){$sources[$s.owner_raw]=Read-Cr2wFile (Join-Path $WorkspaceRoot $s.owner_raw)}
 $phase=(PhaseAt $sources[$s.owner_raw].RootChunk $s.route).DeepCopy();$phase.Id=[uint16]5;ClearSockets $phase
 Rewire $phase.PhaseGraph.Chunk $s.route $s
 $guard=And
 foreach($f in $cohort.common_guards.PSObject.Properties){Add-RedHandle $guard.Conditions (Eq $f.Name $f.Value)}
 foreach($f in @('PTFRBASE_Suspended','PTFRB0ST_Suspended',($s.prefix+'Excluded'))){Add-RedHandle $guard.Conditions (Eq $f 0)}
 Add-RedHandle $guard.Conditions (Eq ($s.prefix+'Enabled') 1)
 Add-RedHandle $guard.Conditions (New-FactCondition $s.gate 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))
 $pause=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$pause.Id=[uint16]2;ClearSockets $pause;Set-RedHandleProperty $pause Condition $guard
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($s.prefix+'Ready') 1),$pause,(New-SetFactNode 3 ($s.prefix+'OwnerActive') 1),(Inc 4 ($s.prefix+'OwnerStarts')),$phase,(New-SetFactNode 6 ($s.prefix+'OwnerActive') 0))){Add-RedHandle $g.Nodes $n}
 foreach($e in @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',4,'In'),@(4,'Out',5,$s.input_socket),@(5,$s.output_socket,6,'In'),@(6,'Out',2,'In'))){Link $g $e[0] $e[1] $e[2] $e[3]}
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $root Graph $g
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
 $depot='towercontinued\b0_story_services\'+$s.key+'.questphase';$paths.Add($depot);$phasePaths.Add($depot)
 Write-Cr2wFile $file (Join-Path $source $depot)
 Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $val ($s.key+'.questphase.json'))
}
if(@(Get-ChildItem $source -Recurse -File).Count -ne $paths.Count){throw 'Scope drift'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=Join-Path $out 'TowerContinued_B0_StoryServices.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne $paths.Count){throw 'Readback failed'}
foreach($e in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$e.Extract($m);if($e.Name -notin $paths -or [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $e.Name)).Hash){throw 'Packed bytes mismatch'}}finally{$m.Dispose()}}
$xl=@('quest:','  phases:');foreach($p in $phasePaths){$xl+=@("    - path: $p",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')}
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot 'archive\b0_story_services\TowerContinued_B0_StoryServices.archive.xl'),($xl -join "`n")+"`n")
$report=[ordered]@{status='BUILT_NOT_LIVE_TESTED';archive=$archive;sha256=(Get-FileHash $archive).Hash;resources=$paths.ToArray();phases=$phasePaths.ToArray();cohort_sha256=(Get-FileHash (Join-Path $scope 'cohort.json')).Hash;vanilla_replacements=@();common_guards=$cohort.common_guards}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($report|ConvertTo-Json -Depth 6))
"Built $($phasePaths.Count) narrow native service owners, two isolated service scenes; no vanilla replacements"

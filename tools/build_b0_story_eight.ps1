param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$scope=Join-Path $WorkspaceRoot 'research\b0_story_eight'
$cohort=Get-Content (Join-Path $scope 'cohort.json') -Raw|ConvertFrom-Json
$source=Join-Path $WorkspaceRoot 'archive\b0_story_eight\source'
$out=Join-Path $WorkspaceRoot 'build\B0_StoryEight'
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
function Rewire($g,$route,$s){
 $plan=$s.graphs.$route
 for($i=$g.Nodes.Count-1;$i -ge 0;$i--){if([int]$g.Nodes[$i].Chunk.Id.ToString() -notin $plan.nodes){$g.Nodes.RemoveAt($i)}}
 foreach($h in $g.Nodes){ClearSockets $h.Chunk}
 $counters=@($s.counters|Where-Object route -eq $route)
 for($i=0;$i -lt $counters.Count;$i++){Add-RedHandle $g.Nodes (Inc (200+$i) ($s.prefix+$counters[$i].suffix))}
 foreach($e in $plan.edges){
  $to=$e[2];$dest=$e[3]
  for($i=0;$i -lt $counters.Count;$i++){
   if(($e -join '|') -eq ($counters[$i].edge -join '|')){$to=200+$i;$dest='In'}
  }
  Link $g $e[0] $e[1] $to $dest
 }
 for($i=0;$i -lt $counters.Count;$i++){Link $g (200+$i) Out $counters[$i].edge[2] $counters[$i].edge[3]}
 foreach($h in $g.Nodes){
  $n=$h.Chunk
  if($n -is [WolvenKit.RED4.Types.questSceneNodeDefinition]){
   if($n.SceneFile.DepotPath.ToString() -ne $s.scene){throw 'Unexpected scene dependency'}
   $rp=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit(('towercontinued\b0_story_eight\'+$s.key+'.scene'))
   $n.SceneFile=[Activator]::CreateInstance($n.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($rp))
  }
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph.Chunk){Rewire $n.PhaseGraph.Chunk ($route+'/node'+$n.Id.ToString()) $s}
 }
}
$paths=[Collections.Generic.List[string]]::new();$phasePaths=[Collections.Generic.List[string]]::new();$sources=@{}
foreach($s in $cohort.sites){
 foreach($k in @('owner','scene')){if((Get-FileHash (Join-Path $WorkspaceRoot $s.($k+'_json'))).Hash -ne $s.($k+'_sha256')){throw 'Audited source changed'}}
 $json=Get-Content (Join-Path $scope ('generated\'+$s.key+'.scene.json')) -Raw
 $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$json,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
 $sd='towercontinued\b0_story_eight\'+$s.key+'.scene';$paths.Add($sd)
 Write-Cr2wFile $dto.Data (Join-Path $source $sd)
 Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $sd)) (Join-Path $val ($s.key+'.scene.json'))
 if(-not $sources.ContainsKey($s.owner_raw)){$sources[$s.owner_raw]=Read-Cr2wFile (Join-Path $WorkspaceRoot $s.owner_raw)}
 if($s.route -eq 'root'){
  $phase=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new()
  Set-RedHandleProperty $phase PhaseGraph $sources[$s.owner_raw].RootChunk.Graph.Chunk.DeepCopy()
  [void](New-QuestSocket $phase 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
  [void](New-QuestSocket $phase 'In1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
  foreach($o in $s.output_sockets){[void](New-QuestSocket $phase $o ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))}
 }else{$phase=(PhaseAt $sources[$s.owner_raw].RootChunk $s.route).DeepCopy()}
 $phase.Id=[uint16]5;ClearSockets $phase
 Rewire $phase.PhaseGraph.Chunk $s.route $s
 $guard=And
 foreach($f in $cohort.common_guards.PSObject.Properties){Add-RedHandle $guard.Conditions (Eq $f.Name $f.Value)}
 foreach($f in @('PTFRBASE_Suspended','PTFRB0S4_Suspended',($s.prefix+'Excluded'),($s.prefix+'QuestOwns'))){Add-RedHandle $guard.Conditions (Eq $f 0)}
 Add-RedHandle $guard.Conditions (Eq ($s.prefix+'Enabled') 1)
 foreach($f in $s.guards){Add-RedHandle $guard.Conditions (New-FactCondition $f[0] $f[2] ([Enum]::Parse([WolvenKit.RED4.Types.Enums+EComparisonType],$f[1])))}
 $pause=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$pause.Id=[uint16]2;ClearSockets $pause;Set-RedHandleProperty $pause Condition $guard
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($s.prefix+'Ready') 1),$pause,(New-SetFactNode 3 ($s.prefix+'OwnerActive') 1),(Inc 4 ($s.prefix+'OwnerStarts')),$phase,(New-SetFactNode 6 ($s.prefix+'OwnerActive') 0))){Add-RedHandle $g.Nodes $n}
 foreach($e in @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',4,'In'),@(4,'Out',5,$s.input_socket),@(6,'Out',2,'In'))){Link $g $e[0] $e[1] $e[2] $e[3]}
 foreach($o in $s.output_sockets){Link $g 5 $o 6}
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $root Graph $g
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
 $depot='towercontinued\b0_story_eight\'+$s.key+'.questphase';$paths.Add($depot);$phasePaths.Add($depot)
 Write-Cr2wFile $file (Join-Path $source $depot)
 Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $val ($s.key+'.questphase.json'))
}
if(@(Get-ChildItem $source -Recurse -File).Count -ne $paths.Count){throw 'Scope drift'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=Join-Path $out 'TowerContinued_B0_StoryEight.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne $paths.Count){throw 'Readback failed'}
foreach($e in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$e.Extract($m);if($e.Name -notin $paths -or [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $e.Name)).Hash){throw 'Packed bytes mismatch'}}finally{$m.Dispose()}}
$xl=@('quest:','  phases:');foreach($p in $phasePaths){$xl+=@("    - path: $p",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')}
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot 'archive\b0_story_eight\TowerContinued_B0_StoryEight.archive.xl'),($xl -join "`n")+"`n")
$report=[ordered]@{status='BUILT_NOT_LIVE_TESTED';archive=$archive;sha256=(Get-FileHash $archive).Hash;resources=$paths.ToArray();phases=$phasePaths.ToArray();cohort_sha256=(Get-FileHash (Join-Path $scope 'cohort.json')).Hash;vanilla_replacements=@();common_guards=$cohort.common_guards}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($report|ConvertTo-Json -Depth 6))
'Built eight narrowly scoped service candidates; no vanilla resource replacements'

param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$scope=Join-Path $WorkspaceRoot 'research\b0_special_services'
$cohort=Get-Content (Join-Path $scope 'cohort.json') -Raw|ConvertFrom-Json
$source=Join-Path $WorkspaceRoot 'archive\b0_special_services\source'
$out=Join-Path $WorkspaceRoot 'build\B0_SpecialServices'
$val=Join-Path $scope 'validation'
New-Item -ItemType Directory -Force -Path $source,$out,$val|Out-Null
$base=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')
function ClearSockets($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function Link($g,$a,$sock,$b,$dest='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $a) $sock) (Get-QuestSocket (Get-QuestNode $g $b) $dest))}
function Inc($id,$fact){$n=New-SetFactNode $id $fact 1;$n.Type.Chunk.SetExactValue=$false;return $n}
function Rewire($g,$route,$s){
  $isInner=$route -eq $s.inner_route
  if($isInner){foreach($n in @((Inc 200 ($s.prefix+'Entries')),(Inc 201 ($s.prefix+'Exits')),(Inc 202 ($s.prefix+'SceneRequests')))){Add-RedHandle $g.Nodes $n}}
  foreach($h in $g.Nodes){ClearSockets $h.Chunk}
  foreach($e in $s.graphs.$route.edges){
    $a=$e.source_node_id;$sock=$e.source_socket;$b=$e.destination_node_id;$dest=$e.destination_socket
    if($isInner){
      if($a -eq $s.input_node){$a=200;$sock='Out'}
      if($b -eq $s.output_node){$b=201;$dest='In'}
      if($b -eq $s.scene_node){$b=202;$dest='In'}
    }
    Link $g $a $sock $b $dest
  }
  if($isInner){
    $sceneInputs=@($s.graphs.$route.edges|Where-Object destination_node_id -eq $s.scene_node|Select-Object -ExpandProperty destination_socket -Unique)
    if($sceneInputs.Count -ne 1){throw 'Non-single scene entry requires separate review'}
    Link $g $s.input_node Out 200;Link $g 201 Out $s.output_node;Link $g 202 Out $s.scene_node $sceneInputs[0]
  }
  foreach($h in $g.Nodes){if($h.Chunk -is [WolvenKit.RED4.Types.questPhaseNodeDefinition]){Rewire $h.Chunk.PhaseGraph.Chunk ($route+'/node'+$h.Chunk.Id.ToString()) $s}}
}
$paths=[Collections.Generic.List[string]]::new();$sources=@{}
foreach($s in $cohort.sites){
  if((Get-FileHash (Join-Path $WorkspaceRoot $s.owner_json)).Hash -ne $s.owner_sha256 -or (Get-FileHash (Join-Path $WorkspaceRoot $s.scene_json)).Hash -ne $s.scene_sha256){throw 'Audit changed'}
  if(-not $sources.ContainsKey($s.owner_raw)){$sources[$s.owner_raw]=Read-Cr2wFile (Join-Path $WorkspaceRoot $s.owner_raw)}
  $phase=(Get-QuestNode $sources[$s.owner_raw].RootChunk.Graph.Chunk $s.phase).DeepCopy();$phase.Id=[uint16]5;ClearSockets $phase
  Rewire $phase.PhaseGraph.Chunk $s.route $s
  $guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
  foreach($f in $cohort.common_guards.PSObject.Properties){Add-RedHandle $guard.Conditions (New-FactCondition $f.Name $f.Value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
  foreach($f in @('PTFRBASE_Suspended','PTFRB0SP_Suspended',($s.prefix+'Excluded'))){Add-RedHandle $guard.Conditions (New-FactCondition $f 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
  Add-RedHandle $guard.Conditions (New-FactCondition ($s.prefix+'Enabled') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
  foreach($f in @($s.gate)+@($s.extra_positive)){Add-RedHandle $guard.Conditions (New-FactCondition $f 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))}
  $pause=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$pause.Id=[uint16]2;ClearSockets $pause;Set-RedHandleProperty $pause Condition $guard
  $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
  foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($s.prefix+'Ready') 1),$pause,(New-SetFactNode 3 ($s.prefix+'OwnerActive') 1),(Inc 4 ($s.prefix+'OwnerStarts')),$phase,(New-SetFactNode 6 ($s.prefix+'OwnerActive') 0))){Add-RedHandle $g.Nodes $n}
  foreach($e in @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',4,'In'),@(4,'Out',5,$s.input_socket),@(5,$s.output_socket,6,'In'),@(6,'Out',2,'In'))){Link $g $e[0] $e[1] $e[2] $e[3]}
  $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $root Graph $g
  $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
  $depot='towercontinued\b0_special_services\'+$s.key+'.questphase';$paths.Add($depot)
  Write-Cr2wFile $file (Join-Path $source $depot)
  Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $val ($s.key+'.questphase.json'))
}
if(@(Get-ChildItem $source -Recurse -File).Count -ne $paths.Count){throw 'Scope drift'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=Join-Path $out 'TowerContinued_B0_SpecialServices.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne $paths.Count){throw 'Readback failed'}
foreach($e in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$e.Extract($m);if($e.Name -notin $paths -or [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $e.Name)).Hash){throw 'Packed bytes mismatch'}}finally{$m.Dispose()}}
$xl=@('quest:','  phases:');foreach($p in $paths){$xl+=@("    - path: $p",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')}
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot 'archive\b0_special_services\TowerContinued_B0_SpecialServices.archive.xl'),($xl -join "`n")+"`n")
$report=[ordered]@{status='BUILT_NOT_LIVE_TESTED';archive=$archive;sha256=(Get-FileHash $archive).Hash;resources=$paths.ToArray();cohort_sha256=(Get-FileHash (Join-Path $scope 'cohort.json')).Hash;vanilla_replacements=@();scene_replacements=@();common_guards=$cohort.common_guards}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($report|ConvertTo-Json -Depth 6))
"Built $($paths.Count) narrow native owners; no vanilla replacement"

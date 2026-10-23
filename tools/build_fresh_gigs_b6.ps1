param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\gig_restoration\fresh_b6';$out=Join-Path $WorkspaceRoot 'build\FreshGigsB6';$source=Join-Path $out 'source'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed evidence pinned'}
$review=Get-Content (Join-Path $audit 'source_review.json') -Raw|ConvertFrom-Json
foreach($p in $review.pins.PSObject.Properties){if((Get-FileHash (Join-Path $WorkspaceRoot $p.Name)).Hash -ne $p.Value){throw 'Source changed'}}
New-Item -ItemType Directory -Force $source|Out-Null
# Import ONLY the previously reviewed graph helper definitions. Never execute
# the installed B5 builder main or regenerate its pinned artifacts/evidence.
$helperPath=Join-Path $PSScriptRoot 'build_fresh_gigs_b5.ps1'
$helperHash=(Get-FileHash $helperPath).Hash
$helper=Get-Content $helperPath -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$prefix='towercontinued\fresh_b6\';$tag='PTFRB6_J2';$roots=@{};$map=@{}
foreach($res in $review.resources){
 $name=if($res.prefabs.Count -gt 0){'native'}elseif($res.depot -match '_combat'){ 'gpl' }else{'ow'}
 $file=Read-Cr2wFile (Join-Path $WorkspaceRoot $res.raw);$roots[$name]=$file.RootChunk.DeepCopy();RewireB5 $roots[$name].Graph.Chunk $file.RootChunk.Graph.Chunk
 $map[$res.depot]=$prefix+'j2_'+$name+'.questphase'
}
foreach($root in $roots.Values){
 $pending=[Collections.Generic.Queue[object]]::new();$pending.Enqueue($root.Graph.Chunk)
 while($pending.Count){$g=$pending.Dequeue();foreach($h in $g.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questPhaseNodeDefinition'){
  if($null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){$pending.Enqueue($n.PhaseGraph.Chunk)}
  $dep=$n.PhaseResource.DepotPath.ToString();if($null -ne $dep -and $map.ContainsKey($dep)){$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($map[$dep])}
 }}}
}
$play=NestedB5 $roots.ow.Graph.Chunk @(3);RedirectB5 $play 170 'Start 0' 112 'Active'
$cleanup=NestedB5 $roots.ow.Graph.Chunk @(6);RedirectB5 $cleanup 46 'Start 0' 59 'Active'
RewardB5 $cleanup 33 $tag;AccountB5 $cleanup 36 $tag
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();Set-RedHandleProperty $root Graph $g
$parentRaw=$review.parent.binding.source.Replace('/json/','/raw/').Substring(0,$review.parent.binding.source.Length-5)
$parent=Read-Cr2wFile (Join-Path $WorkspaceRoot $parentRaw)
$child=(Get-QuestNode $parent.RootChunk.Graph.Chunk 7).DeepCopy();$child.Id=[uint16]7;ClearB5 $child
$child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($prefix+'j2_native.questphase')
$guard=AllB5 ([ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRB6_J2_Request=1;PTFRB6_J2_Started=0;PTFRB6_J2_Fault=0;PTFRB6_J2_RewardClaim=0;PTFRB6_J2_AccountClaim=0;jpn_02_start=0;jpn_02_finished=0})
foreach($n in @((New-InputNode 0 'In1'),(New-OutputNode 1 'Out1'),(New-SetFactNode 2 ($tag+'_Ready') 1),(New-SetFactNode 3 ($tag+'_Revision') 1),(PauseB5 4 $guard),(New-SetFactNode 5 ($tag+'_Started') 1),(New-SetFactNode 6 ($tag+'_OwnerFinished') 1),$child)){AddNodeB5 $g $n}
RebuildB5 $g @(@(0,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',4,'In'),@(4,'Out',5,'In'),@(5,'Out',7,'In1'),@(7,'Out1',6,'In'),@(6,'Out',1,'In'))
$roots.boot=$root;$resources=@()
foreach($name in @('native','ow','gpl','boot')){
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$roots[$name];$depot=$prefix+'j2_'+$name+'.questphase';$resources+=,$depot
 Write-Cr2wFile $file (Join-Path $source $depot);Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit ('j2_'+$name+'.questphase.json'))
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_FreshB6.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Archive scope changed'}
foreach($entry in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $entry.Name)).Hash){throw 'Packed mismatch'}}finally{$m.Dispose()}}
$result=[ordered]@{status='BUILT_B6_ONE_ADDITIONAL_NATIVE_FRESH_OWNER_LIVE_PENDING';id=$review.id;archive_sha256=(Get-FileHash $archive).Hash;source_review_sha256=(Get-FileHash (Join-Path $audit 'source_review.json')).Hash;graph_helper_sha256=$helperHash;resources=$resources;packed_readback=$true;vanilla_replacements=@();completed_replay=$false;native_cleanup_retained=$true}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($result|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
[pscustomobject]$result|Select-Object status,archive_sha256,packed_readback|ConvertTo-Json

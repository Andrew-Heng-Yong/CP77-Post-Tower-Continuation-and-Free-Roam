# Called only by the uninstalled U9 special builder. Original gang gameplay,
# cancellation, phone messages and return loops are copied without redesign.
function Build-RetaliationS9 {
 param([string]$WorkspaceRoot,[string]$OutputRoot,[string]$AuditRoot)
 $prefix='research/gig_restoration/lifecycle_sources/'
 $nativePath='base/open_world/street_stories/street_stories_gang_retaliation.questphase'
 $parentPath='base/open_world/street_stories/street_stories.questphase'
 $pins=[ordered]@{
  ($prefix+'raw/'+$nativePath)='CD6998DB50FCB1671CAB54DD93A77ED32DA5AB428613BEBE1C7D092383E2C1AC'
  ($prefix+'json/'+$nativePath+'.json')='D44189D436D1913E8AF3E85A681C7112EA30593ACBE6FFCB67A1B813CAE7B97A'
  ($prefix+'raw/'+$parentPath)='4172328C26C01EDD9D20BC79C6C89D6255E452CAB40307D6278C490EB2637E1B'
  ($prefix+'json/'+$parentPath+'.json')='0AF8F5BB1E3C446A8D54E0E04107084BF7207E9A7DC521454809773B9587F5D0'
 }
 foreach($p in $pins.GetEnumerator()){R5Match (Join-Path $WorkspaceRoot $p.Key) $p.Value}
 $source=(Read-Cr2wFile (Join-Path $WorkspaceRoot ($prefix+'raw/'+$nativePath))).RootChunk
 $root=$source.DeepCopy();RewireB5 $root.Graph.Chunk $source.Graph.Chunk
 $nativeGraph=$root.Graph.Chunk
 # Each stock selector retains its complete content/district/outcome condition.
 # One owned admission predicate prevents triggering historical, unowned gigs.
 $selectors=@(
  @{graph=@(1,136);node=11;id='sts_bls_ina_03'},@{graph=@(1,136);node=17;id='sts_bls_ina_02'},
  @{graph=@(29,214);node=29;id='sts_std_arr_11'},@{graph=@(29,214);node=34;id='sts_std_rcr_03'},
  @{graph=@(31);node=242;id='sts_cct_dtn_03'},@{graph=@(33,227);node=35;id='sts_hey_gle_04'},
  @{graph=@(35,239);node=41;id='sts_wat_kab_02'},@{graph=@(35,239);node=45;id='sts_wat_nid_05'},
  @{graph=@(37,298);node=68;id='sts_wat_lch_01'},@{graph=@(37,298);node=69;id='sts_wat_lch_03'},
  @{graph=@(37,298);node=78;id='sts_wbr_hil_07'})
 foreach($s in $selectors){
  $n=Get-QuestNode (NestedB5 $nativeGraph $s.graph) $s.node
  $owned=AllB5 ([ordered]@{('PTFRU9_'+$s.id+'_Started')=1})
  Add-RedHandle $owned.Conditions $n.Condition.Chunk.DeepCopy()
  Set-RedHandleProperty $n Condition $owned
 }
 # These three separate source branches belong to excluded gigs. Disconnect only
 # their startup edge, leaving source payload and the rest of every native flow.
 $excluded=@(@{graph=@(29,214);entry=33;node=32;id='sts_std_rcr_04'},
             @{graph=@(33,227);entry=38;node=37;id='sts_hey_rey_02'},
             @{graph=@(37,298);entry=81;node=79;id='sts_wbr_jpn_12'})
 foreach($s in $excluded){
  $g=NestedB5 $nativeGraph $s.graph;$edges=@(EdgesB5 $g|ForEach-Object {$_})
  $cut=@($edges|Where-Object {$_[0] -eq 0 -and $_[1] -eq 'Out' -and $_[2] -eq $s.entry -and $_[3] -eq 'In'})
  if($cut.Count -ne 1){throw 'Excluded selector edge changed'}
  RebuildB5 $g @($edges|Where-Object {-not ($_[0] -eq 0 -and $_[2] -eq $s.entry)})
 }
 # Historical pending ambushes are not consumed/reset. Each native gang owner
 # starts once only when that gang had an empty queue at its own admission.
 $gangs=@(@{name='wraiths';entry=47;condition=46;child=1},@{name='6thstreet';entry=51;condition=50;child=29},
          @{name='animals';entry=55;condition=54;child=31},@{name='valentinos';entry=58;condition=57;child=33},
          @{name='maelstroms';entry=61;condition=60;child=35},@{name='tygerclaws';entry=63;condition=62;child=37})
 $gangEdges=@(EdgesB5 $nativeGraph|ForEach-Object {$_});$index=0
 foreach($s in $gangs){
  $tag='PTFRU9_Retaliation_'+$s.name;$base=64000+2*$index;$index++
  $admit=AllB5 ([ordered]@{($tag+'_Request')=1;($tag+'_Permit')=1;($tag+'_Issued')=0;($tag+'_Fault')=0;('sts_'+$s.name+'_retaliation')=0})
  AddNodeB5 $nativeGraph (PauseB5 $base $admit);AddNodeB5 $nativeGraph (New-SetFactNode ($base+1) ($tag+'_Issued') 1)
  $old=@($gangEdges|Where-Object {$_[0] -eq 0 -and $_[2] -eq $s.entry})
  if($old.Count -ne 1){throw 'Native gang startup changed'}
  $gangEdges=@($gangEdges|Where-Object {-not ($_[0] -eq 0 -and $_[2] -eq $s.entry)})
  $gangEdges+=,@(0,'Out',$base,'In');$gangEdges+=,@($base,'Out',($base+1),'In');$gangEdges+=,@(($base+1),'Out',$s.entry,'In')
 }
 RebuildB5 $nativeGraph $gangEdges
 # Keep original phase metadata from its actual parent, but embed the narrowed
 # source graph so the original global resource is not restarted unfiltered.
 $parent=(Read-Cr2wFile (Join-Path $WorkspaceRoot ($prefix+'raw/'+$parentPath))).RootChunk
 $child=(Get-QuestNode $parent.Graph.Chunk 22).DeepCopy();ClearB5 $child
 $child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new()
 Set-RedHandleProperty $child PhaseGraph $nativeGraph
 $outer=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 $initial=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;debug_sts_start=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0;PTFRU9_Retaliation_Request=1;PTFRU9_Retaliation_Permit=1;PTFRU9_Retaliation_Issued=0;PTFRU9_Retaliation_Fault=0;sts_gang_retaliation_cancel=0;mws_chase_active=0}
 foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 65000 'PTFRU9_Retaliation_Ready' 1),(PauseB5 65001 (AllB5 $initial)),(New-SetFactNode 65002 'PTFRU9_Retaliation_Issued' 1),$child)){AddNodeB5 $outer $n}
 RebuildB5 $outer @(@(0,'Out',65000,'In'),@(65000,'Out',65001,'In'),@(65001,'Out',65002,'In'),@(65002,'Out',22,'In1'))
 Set-RedHandleProperty $root Graph $outer
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $depot='towercontinued\special_gigs_u9\gang_retaliation.questphase'
 $target=Join-Path (Join-Path $OutputRoot 'source') $depot
 Write-Cr2wFile $f $target
 Export-Cr2wJson (Read-Cr2wFile $target) (Join-Path $AuditRoot 'gang_retaliation.json')
 return @{depot=$depot;sha256=R5Hash $target;source_pins=$pins;selectors=$selectors;excluded=$excluded;initial=$initial;gangs=$gangs;all_native_gang_children=6;shared_cancel_owners=1;terminating_wrapper_output=$false;historical_pending_preserved=$true}
}

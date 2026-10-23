# Dot-source from the S2 builder after its corrected actor identity pass.
# Keep the vanilla pose order: optional drink (lean270), nose transition,
# then an explicit Get up choice (lean0). Never silently replay the nose.
function Add-StreetkidRevision3Actions($scene,$qroot,[string]$marker) {
    $root=$scene.RootChunk; $graph=$root.SceneGraph.Chunk.Graph
    $qgraph=$qroot.SceneGraph.Chunk.Graph
    $hub=Find-SceneNode $graph 10
    $after=$hub.DeepCopy()
    $after.NodeId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2021)
    $after.Options.Clear()
    $getup=(Find-SceneNode $qgraph 105).Options[0].DeepCopy()
    if($getup.Caption.ToString() -ne 'get_up') {throw 'Original Get up choice changed'}
    $getup.ScreenplayOptionId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]770)
    $after.Options.Add($getup)
    Set-SceneDest $after.OutputSockets[0] 33
    Add-RedHandle $graph $after
    Set-SceneDest (Find-SceneNode $graph 2010).OutputSockets[0] 2021

    $drinkOption=(Find-SceneNode $qgraph 443).Options[0].DeepCopy()
    $drinkOption.ScreenplayOptionId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]514)
    $hub.Options[0].ScreenplayOptionId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]258)
    $hub.Options.Add($drinkOption)
    $out=$hub.OutputSockets[0].DeepCopy()
    $out.Stamp.Ordinal=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]1)
    Set-SceneDest $out 2020
    $hub.OutputSockets.Insert(1,$out)

    # Clone only V animation and exact glass attachment events. Do not copy
    # player_drunk, time tutorial, dialogue, bartender or quest side-effects.
    $original=Find-SceneNode $qgraph 440
    $drink=(Find-SceneNode $graph 8).DeepCopy()
    $drink.NodeId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]2020)
    $drink.Events.Clear()
    foreach($socket in $drink.OutputSockets) {$socket.Destinations.Clear()}
    $return=$hub.OutputSockets[0].Destinations[0].DeepCopy()
    $return.NodeId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]10)
    $drink.OutputSockets[0].Destinations.Add($return)
    Set-SceneTime $drink.SectionDuration 5800
    foreach($i in 0,2,3,4,14,17) {
        $event=$original.Events[$i].Chunk.DeepCopy()
        if($i -in 0,2,3) {
            $new=switch([int]$event.Performer.Id.ToString()){1281{513} 769{1} 1025{257} default{throw 'Drink performer changed'}}
            $event.Performer.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$new)
            $event.RootMotionData.OriginMarker.NodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($marker)
        }
        if($i -in 4,14) {
            $event.PropId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]0)
            foreach($fallback in $event.FallbackData) {
                $new=switch([int]$fallback.Owner.Id.ToString()){1281{513} 769{1} 1025{257} default{throw 'Drink fallback performer changed'}}
                $fallback.Owner.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$new)
            }
            if($i -eq 4) {$event.PerformerId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]513)}
        }
        Add-RedHandle $drink.Events $event
    }
    $wsSocket=@($original.OutputSockets|Where-Object {$_.Stamp.Name.ToString() -eq '3'})[0].DeepCopy()
    $drink.OutputSockets.Add($wsSocket)
    Add-RedHandle $graph $drink
    Add-RedHandle $graph (Find-SceneNode $qgraph 735).DeepCopy()
    $root.WorkspotInstances.Add(@($qroot.WorkspotInstances|Where-Object {$_.WorkspotInstanceId.Id.ToString() -eq '735'})[0].DeepCopy())

    # A scene-owned instance of the original shot glass. Its exact world
    # marker exists in the always-loaded sector; no q000 prop owner needed.
    $prop=$qroot.Props[1].DeepCopy()
    $prop.PropId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]0)
    $prop.EntityAcquisitionPlan=$qroot.Props[3].EntityAcquisitionPlan
    $prop.SpawnDespawnParams=$qroot.Props[3].SpawnDespawnParams.DeepCopy()
    $prop.SpawnDespawnParams.SpecRecordId=$prop.SpecPropRecordId
    $prop.SpawnDespawnParams.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit('p_PTFRSKS2_vodka_shot')
    $prop.SpawnDespawnParams.SpawnMarkerNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit('$/03_night_city/#c_heywood/glen/loc_sq022_el_coyote_cojo_bar_prefabKDIAKFA/#loc_sq022_el_coyote_cojo_bar_gameplay/#loc_sq022_el_coyote_cojo_bar_devices/#q000_kid_01b_vodka_shot')
    $prop.SpawnDespawnParams.ValidateSpawnPostion=[WolvenKit.RED4.Types.CBool]::op_Implicit($false)
    $root.Props.Add($prop)

    # Compact screenplay IDs are indexed as 2 + 256*n. Preserve locale blocks
    # and unsigned locstring order, including native db_db duplicate variants.
    $sit=$root.ScreenplayStore.Options[0].DeepCopy()
    $oldLoc=$root.LocStore.DeepCopy()
    $root.ScreenplayStore.Options.Clear();$root.ScreenplayStore.Options.Add($sit)
    $labels=@(@{old=3842;new=258},@{old=5122;new=514},@{old=1026;new=770})
    foreach($label in $labels) {
        $option=@($qroot.ScreenplayStore.Options|Where-Object {$_.ItemId.Id.ToString() -eq $label.old.ToString()})[0].DeepCopy()
        $option.ItemId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$label.new)
        $root.ScreenplayStore.Options.Add($option)
    }
    $rows=[Collections.Generic.List[object]]::new()
    foreach($option in $root.ScreenplayStore.Options) {
        $store=if($option.ItemId.Id.ToString() -eq '2'){$oldLoc}else{$qroot.LocStore}
        foreach($d in $store.VdEntries|Where-Object {$_.LocstringId.Ruid.ToString() -eq $option.LocstringId.Ruid.ToString()}) {
            $rows.Add(@{descriptor=$d.DeepCopy();payload=$store.VpEntries[[int]$d.VpeIndex.ToString()].DeepCopy()})
        }
    }
    $root.LocStore.VdEntries.Clear();$root.LocStore.VpEntries.Clear()
    $localeOrder=@{db_db=0;pl_pl=1;en_us=2}
    foreach($row in $rows|Sort-Object -Stable @{Expression={$localeOrder[$_.descriptor.LocaleId.ToString()]}},@{Expression={[uint64]$_.descriptor.LocstringId.Ruid.ToString()}}) {
        $row.descriptor.VpeIndex=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$root.LocStore.VpEntries.Count)
        $root.LocStore.VdEntries.Add($row.descriptor);$root.LocStore.VpEntries.Add($row.payload)
    }
    # Use original event-tag meanings for V's sex-specific animations.
    $root.ExecutionTags.Clear();$root.ExecutionTagEntries.Clear()
    foreach($t in $qroot.ExecutionTags){$root.ExecutionTags.Add($t.DeepCopy())}
    foreach($t in $qroot.ExecutionTagEntries){$root.ExecutionTagEntries.Add($t.DeepCopy())}
}

function Add-StreetkidMirrorOwnerCleanup($owner,$qgraph) {
    $g=$owner.RootChunk.Graph.Chunk
    $mirror='$/03_night_city/#c_heywood/glen/loc_sq022_el_coyote_cojo_bar_prefabKDIAKFA/#loc_sq022_el_coyote_cojo_bar_env/int_prefabMSJTYIQ/decoration_prefabXJKHK5Q/#q000_kid_coyote_mirror'
    # Variant enabled only during the opt-in scene. Both normal and interrupt
    # paths restore the original fake surface, before clearing Active.
    foreach($spec in @(@{id=20;source=757},@{id=21;source=765},@{id=22;source=765})) {
        $node=(Find-SceneNode $qgraph $spec.source).QuestNode.Chunk.DeepCopy()
        $node.Id=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$spec.id)
        foreach($s in $node.Sockets){$s.Chunk.Connections.Clear()}
        $node.Type.Chunk.Params[0].PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($mirror)
        Add-RedHandle $g.Nodes $node
    }
    # The prologue explicitly ForceOFFs this device during the nose sequence.
    # A visible real-mirror variant alone cannot undo that persisted device
    # state. Own only this device's on/off presentation for the trial.
    foreach($spec in @(@{id=23;action='ForceON'},@{id=24;action='ForceOFF'},@{id=25;action='ForceOFF'})) {
        $node=(Find-SceneNode $qgraph 1653).QuestNode.Chunk.DeepCopy()
        $node.Id=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$spec.id)
        foreach($s in $node.Sockets){$s.Chunk.Connections.Clear()}
        $p=$node.Type.Chunk.Params[0].Chunk
        $p.ObjectRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($mirror+'/#q000_kid_dvc_mirror_device')
        $p.DeviceAction=[WolvenKit.RED4.Types.CName]::op_Implicit($spec.action)
        Add-RedHandle $g.Nodes $node
    }
    function Insert-MirrorNode([int]$from,[string]$output,[int]$middle,[int]$to,[string]$targetSocket) {
        $a=Get-QuestSocket (Get-QuestNode $g $from) $output
        $b=Get-QuestSocket (Get-QuestNode $g $to) $targetSocket
        $a.Connections.Clear();$b.Connections.Clear()
        [void](Connect-QuestSockets $a (Get-QuestSocket (Get-QuestNode $g $middle) 'In'))
        [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $middle) 'Out') $b)
    }
    Insert-MirrorNode 2 'Out' 20 3 'In'
    Insert-MirrorNode 3 'out' 21 4 'In'
    Insert-MirrorNode 3 'Default INT' 22 7 'In'
    Insert-MirrorNode 20 'Out' 23 3 'in'
    Insert-MirrorNode 3 'out' 24 21 'In'
    Insert-MirrorNode 3 'Default INT' 25 22 'In'
}

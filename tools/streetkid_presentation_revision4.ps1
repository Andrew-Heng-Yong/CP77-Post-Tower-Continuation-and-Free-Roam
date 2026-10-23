# Scene-owned presentation only; no prologue facts, outfits or root owners.
function Add-StreetkidRevision4Presentation($scene,$qroot,[string]$marker,[string]$WorkspaceRoot) {
    $r=$scene.RootChunk;$g=$r.SceneGraph.Chunk.Graph;$qg=$qroot.SceneGraph.Chunk.Graph
    $ordinary=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\b0_second_mirror\vanilla\raw\base\open_world\scenes\mirrors\mirror_scene_el_cojote.scene')
    $og=$ordinary.RootChunk.SceneGraph.Chunk.Graph
    # Ordinary mirrors use the same Character.q110_tpp_{sex}_v records with
    # default appearance, not the prologue's naked/headless demo appearance.
    for($i=0;$i -lt 2;$i++) {
        if($r.Actors[$i].SpawnDespawnParams.SpecRecordId.ToString() -ne $ordinary.RootChunk.Actors[$i].SpawnDespawnParams.SpecRecordId.ToString()) {throw 'Mirror body record mismatch'}
        $r.Actors[$i].SpawnDespawnParams.Appearance=$ordinary.RootChunk.Actors[$i].SpawnDespawnParams.Appearance
        $r.Actors[$i].SpecAppearance=$ordinary.RootChunk.Actors[$i].SpecAppearance
    }
    $destinationTemplate=(Find-SceneNode $g 4).OutputSockets[0].Destinations[0].DeepCopy()
    function Link-SceneNode($node,[int]$socket,[int]$target,[int]$ordinal) {
        $s=$node.OutputSockets[$socket];$s.Destinations.Clear()
        $d=$destinationTemplate.DeepCopy()
        $d.NodeId.Id=[WolvenKit.RED4.Types.CUInt32]::op_Implicit([uint32]$target)
        $d.IsockStamp.Ordinal=[WolvenKit.RED4.Types.CUInt16]::op_Implicit([uint16]$ordinal)
        $s.Destinations.Add($d)
    }
    foreach($id in 595,1708,1709,1712,1713,1792,1794,1689,1693) {
        $node=(Find-SceneNode $qg $id).DeepCopy()
        foreach($s in $node.OutputSockets){$s.Destinations.Clear()}
        $q=$node.QuestNode.Chunk
        switch($id) {
            {$_ -in 1708,1709} {
                $path=[WolvenKit.RED4.Types.ResourcePath]::op_Implicit('towercontinued\streetkid_seat_mirror_s2\seat_mirror.scene')
                $q.Type.Chunk.SceneFile=[Activator]::CreateInstance($q.Type.Chunk.GetType().GetProperty('SceneFile').PropertyType,[object[]]@($path))
            }
            {$_ -in 1712,1713} {
                $sex=if($id -eq 1712){'male'}else{'female'}
                $q.Actions[0].Type.Chunk.EntityReference.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit("a_PTFRSKS2_v_${sex}_tpp")
            }
            {$_ -in 1792,1794} {
                $sex=if($id -eq 1794){'male'}else{'female'}
                $q.Condition.Chunk.Type.Chunk.ObjectRef.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit("a_PTFRSKS2_v_${sex}_tpp")
            }
            {$_ -in 1689,1693} {
                $sex=if($id -eq 1693){'male'}else{'female'}
                $q.EntityReference.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit("a_PTFRSKS2_v_${sex}_tpp")
                $wi=@($qroot.WorkspotInstances|Where-Object {$_.WorkspotInstanceId.Id.ToString() -eq "$id"})[0].DeepCopy()
                $wi.OriginMarker.NodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($marker)
                $r.WorkspotInstances.Add($wi)
            }
        }
        Add-RedHandle $g $node
    }
    Link-SceneNode (Find-SceneNode $g 595) 0 1708 1
    Link-SceneNode (Find-SceneNode $g 595) 1 1709 1
    foreach($chain in @(@(1708,1713,1792,1689),@(1709,1712,1794,1693))) {
        for($i=0;$i -lt 3;$i++){Link-SceneNode (Find-SceneNode $g $chain[$i]) 0 $chain[$i+1] 1}
        # Work Started, not workspot completion (the seated idle is infinite).
        Link-SceneNode (Find-SceneNode $g $chain[3]) 1 8 0
    }
    # Change Sit only after copies of its destination were used as templates.
    Link-SceneNode (Find-SceneNode $g 4) 0 595 1

    # Explicit normal-path body release, copied from the working public mirror.
    # Interrupt release additionally follows native scene ownership keepAlive0.
    foreach($id in 1049,1050,1051) {
        $node=(Find-SceneNode $og $id).DeepCopy()
        if($id -ne 1049) {
            $sex=if($id -eq 1051){'male'}else{'female'}
            $node.QuestNode.Chunk.Actions[0].Type.Chunk.EntityReference.DynamicEntityUniqueName=[WolvenKit.RED4.Types.CName]::op_Implicit("a_PTFRSKS2_v_${sex}_tpp")
            Link-SceneNode $node 0 2000 0
        }
        Add-RedHandle $g $node
    }
    Link-SceneNode (Find-SceneNode $g 33) 0 1049 1

    # Derive initial glass pose from the authored pickup hand transform and
    # stool placement. The old vodka NodeRef has no placed instance in the
    # inspected sector; the bar marker does. No guessed absolute coordinates.
    $stool=@($qroot.WorkspotInstances|Where-Object {$_.WorkspotInstanceId.Id.ToString() -eq '686'})[0].LocalTransform
    $attach=(Find-SceneNode $qg 440).Events[4].Chunk
    $fallback=@($attach.FallbackData|Where-Object {$_.Owner.Id.ToString() -eq '1281'})[0]
    $hand=@($fallback.FallbackCachedBones|Where-Object {$_.BoneName.ToString() -eq 'WeaponRight'})[0].ModelSpaceTransform
    $a=$stool.Orientation;$b=$hand.Orientation;$p=$hand.Position
    $qa=[Numerics.Quaternion]::new([float]$a.I.ToString(),[float]$a.J.ToString(),[float]$a.K.ToString(),[float]$a.R.ToString())
    $qb=[Numerics.Quaternion]::new([float]$b.I.ToString(),[float]$b.J.ToString(),[float]$b.K.ToString(),[float]$b.R.ToString())
    $v=[Numerics.Vector3]::Transform([Numerics.Vector3]::new([float]$p.X.ToString(),[float]$p.Y.ToString(),[float]$p.Z.ToString()),$qa)
    $rot=[Numerics.Quaternion]::Multiply($qa,$qb)
    $spawn=$r.Props[0].SpawnDespawnParams
    # Keep the prop acquired for the whole scene, not just its Drink section.
    $spawn.AlwaysSpawned=[WolvenKit.RED4.Types.CBool]::op_Implicit($true)
    $spawn.SpawnMarkerNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($marker)
    $spawn.ForceMaxVisibility=[WolvenKit.RED4.Types.CBool]::op_Implicit($true)
    foreach($axis in 'X','Y','Z'){$spawn.SpawnOffset.Position.$axis=[WolvenKit.RED4.Types.CFloat]::op_Implicit([float]($v.$axis+[float]$stool.Position.$axis.ToString()))}
    foreach($pair in @(@('I','X'),@('J','Y'),@('K','Z'),@('R','W'))){$spawn.SpawnOffset.Orientation.($pair[0])=[WolvenKit.RED4.Types.CFloat]::op_Implicit([float]$rot.($pair[1]))}
    # Remove the inherited Kerry COUCH header rather than invent a loc key.
    foreach($id in 4,10,2021){(Find-SceneNode $g $id).DisplayNameOverride=[WolvenKit.RED4.Types.CString]::op_Implicit('')}
}

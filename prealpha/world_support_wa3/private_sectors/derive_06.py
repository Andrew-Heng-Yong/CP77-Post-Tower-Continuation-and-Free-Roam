from pathlib import Path
H=Path(__file__).resolve().parent
for name in ['build','verify']:
    s=(H/(name+'_05.ps1')).read_text(encoding='utf-8-sig')
    for key in ['source','build_proof','block_readback','readback','verification','verify','build']:
        s=s.replace(key+'_05',key+'_06')
    s=s.replace('outside1004_filter_spec_02.json','outside1004_filter_spec_03.json').replace('remove=@(64,65)','remove=@(63,64,65)').replace('drop=@(64,65)','drop=@(63,64,65)')
    s=s.replace("AlwaysSpawned.ToString() -cne 'False'","AlwaysSpawned.ToString() -cne 'false_'").replace("AlwaysSpawned.ToString() -ceq 'False'","AlwaysSpawned.ToString() -ceq 'false_'")
    if name=='build':
        before="}elseif($spec.id -eq 1004 -and $index -eq 65){"
        after="""}elseif($spec.id -eq 1004 -and $index -eq 63){
   if($node.GetType().Name -cne 'worldInterestingConversationsAreaNode' -or $node.ConversationResources.Count -ne 1 -or $node.ConversationResources[0].Chunk.ConversationGroup.DepotPath.ToString() -cne 'base\\open_world\\scenes\\conversations\\conversation_groups\\thanks.conversations'){throw 'Unexpected thank-you trigger'}
  }elseif($spec.id -eq 1004 -and $index -eq 65){"""
        assert before in s;s=s.replace(before,after)
        anchor="$outside=Get-Content -LiteralPath (Join-Path $homeWA3 'native_review/outside1004_filter_spec_03.json') -Raw|ConvertFrom-Json -Depth 70"
        s=s.replace(anchor,anchor+"\n$outsideProof=Get-Content -LiteralPath (Join-Path $homeWA3 'native_review/outside1004_assessment_01.json') -Raw|ConvertFrom-Json -Depth 70\nif($outsideProof.status -cne 'PASS_OUTSIDE1004_FILTERED_DEPENDENCIES' -or $outsideProof.selected_filter_sha256 -cne (Get-FileHash (Join-Path $homeWA3 'native_review/outside1004_filter_spec_03.json')).Hash){throw '1004 dependency review incomplete'}")
    else:
        before="elseif($spec.id -eq 1004 -and $i -eq 65){"
        after="""elseif($spec.id -eq 1004 -and $i -eq 63){Check '1004: remove exact native global-fact-consuming thank-you trigger' ($node.GetType().Name -ceq 'worldInterestingConversationsAreaNode' -and $node.ConversationResources.Count -eq 1 -and $node.ConversationResources[0].Chunk.ConversationGroup.DepotPath.ToString() -ceq 'base\\open_world\\scenes\\conversations\\conversation_groups\\thanks.conversations')}
   elseif($spec.id -eq 1004 -and $i -eq 65){"""
        assert before in s;s=s.replace(before,after)
        s=s.replace('$pins+=$pinsExtra',"$pins+=$pinsExtra\n$pins+=@((Join-Path $PSScriptRoot '../native_review/outside1004_assessment_01.json'))")
    target=H/(name+'_06.ps1');assert not target.exists();target.write_text(s,encoding='utf-8',newline='\n')

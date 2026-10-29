from pathlib import Path
H=Path(__file__).resolve().parent
build=(H/'build_03.ps1').read_text(encoding='utf-8-sig')
for key in ['source','build_proof','block_readback','readback']:
    build=build.replace(key+'_03',key+'_04')
build=build.replace('$rows=@();$resources=@()',"$outside=Get-Content -LiteralPath (Join-Path $homeWA3 'native_review/outside1004_filter_spec_01.json') -Raw|ConvertFrom-Json -Depth 70\n$rows=@();$resources=@()")
build=build.replace('@{id=161;remove=@(38);nodes=40}', '@{id=161;remove=@(38);nodes=40},@{id=1004;remove=@(64);nodes=74}')
before=''' $owner=@($census.rows|Where-Object id -eq $spec.id)[0]
 $hits=@($extract.hits|Where-Object resource -eq $owner.resource)
 if($hits.Count -ne 1 -or $hits[0].is_mod){throw 'Ambiguous native support source'}
 $hit=$hits[0];if((Get-FileHash -LiteralPath $hit.raw).Hash -cne $hit.sha256){throw 'Native sector drift'}'''
after=''' if($spec.id -eq 1004){
  $owner=@{resolved_prefab=$outside.native_prefab;resource=$outside.sector_resource}
  $hit=@{raw=$outside.sector_raw;sha256=$outside.sector_sha256}
 }else{
  $owner=@($census.rows|Where-Object id -eq $spec.id)[0]
  $hits=@($extract.hits|Where-Object resource -eq $owner.resource)
  if($hits.Count -ne 1 -or $hits[0].is_mod){throw 'Ambiguous native support source'}
  $hit=$hits[0]
 }
 if((Get-FileHash -LiteralPath $hit.raw).Hash -cne $hit.sha256){throw 'Native sector drift'}'''
assert before in build;build=build.replace(before,after)
before="foreach($index in $spec.remove){$node=$root.Nodes[$index].Chunk;if($node.GetType().Name -cne 'worldPopulationSpawnerNode' -or $node.SpawnOnStart.ToString() -cne 'True'){throw 'Expected only automatic preview spawner removal'}}"
after="""foreach($index in $spec.remove){
  $node=$root.Nodes[$index].Chunk
  if($spec.id -eq 1004){
   if($node.GetType().Name -cne 'worldInterestingConversationsAreaNode' -or $node.Conversations.Count -ne 1 -or $node.Conversations[0].Chunk.SceneFilename.DepotPath.ToString() -cne $outside.conversation_dependency.depot){throw 'Unexpected conversation removal'}
  }elseif($node.GetType().Name -cne 'worldPopulationSpawnerNode' -or $node.SpawnOnStart.ToString() -cne 'True'){throw 'Expected only automatic preview spawner removal'}
 }"""
assert before in build;build=build.replace(before,after).replace('Descriptors.Count -ne 2','Descriptors.Count -ne 3').replace('groups=@(160,161)','groups=@(160,161,1004)')
verify=(H/'verify_03.ps1').read_text(encoding='utf-8-sig')
for key in ['source','verification','verify','build']:
    verify=verify.replace(key+'_03',key+'_04')
verify=verify.replace("exactly two descriptor registrations' ($block.RootChunk.Descriptors.Count -eq 2)","exactly three descriptor registrations' ($block.RootChunk.Descriptors.Count -eq 3)")
verify=verify.replace("@{id=161;stem='quest_0b5baaafb70a2a64';drop=@(38);expected=40;spots=34}","@{id=161;stem='quest_0b5baaafb70a2a64';drop=@(38);expected=40;spots=34},@{id=1004;stem='quest_fa6df5356603d67f';drop=@(64);expected=74;spots=61}")
verify=verify.replace("$nativePath=Join-Path $PSScriptRoot ('../extracted_01/basegame_3_nightcity.archive/'+$spec.stem+'.streamingsector')", "$nativePath=if($spec.id -eq 1004){Join-Path $PSScriptRoot ('../native_review/outside_prefab_native_02/basegame_3_nightcity.archive/'+$spec.stem+'.streamingsector')}else{Join-Path $PSScriptRoot ('../extracted_01/basegame_3_nightcity.archive/'+$spec.stem+'.streamingsector')}")
before="if($spec.drop -contains $i){Check ($spec.id.ToString()+': removed node is auto-start preview '+$i) ($node.GetType().Name -ceq 'worldPopulationSpawnerNode' -and $node.SpawnOnStart.ToString() -ceq 'True');continue}"
after="""if($spec.drop -contains $i){
   if($spec.id -eq 1004){Check '1004: remove only exact unsafe lore animation trigger' ($node.GetType().Name -ceq 'worldInterestingConversationsAreaNode' -and $node.Conversations.Count -eq 1 -and $node.Conversations[0].Chunk.SceneFilename.DepotPath.ToString() -ceq 'base\\open_world\\scenes\\lore_animations\\la_street_violence_02.scene')}
   else{Check ($spec.id.ToString()+': removed node is auto-start preview '+$i) ($node.GetType().Name -ceq 'worldPopulationSpawnerNode' -and $node.SpawnOnStart.ToString() -ceq 'True')}
   continue
  }"""
assert before in verify;verify=verify.replace(before,after)
verify=verify.replace('exactly preview placements removed','exactly selected placements removed').replace('removed_preview_nodes=$spec.drop','removed_nodes=$spec.drop')
verify=verify.replace('PASS_PRIVATE_160_161_FILTERED_SECTORS_STATIC','PASS_PRIVATE_160_161_1004_FILTERED_SECTORS_STATIC').replace('negative_controls=4','negative_controls=6')
verify=verify.replace("$rows=@();$targetDepots", "$pinsExtra=@((Join-Path $PSScriptRoot '../native_review/outside1004_filter_spec_01.json'),(Join-Path $PSScriptRoot '../native_review/lore_native_01/basegame_3_nightcity.archive/la_street_violence_02.scene'))\n$rows=@();$targetDepots")
verify=verify.replace('foreach($spec in $specs){','$pins+=$pinsExtra\nforeach($spec in $specs){')
for name,text in [('build_04.ps1',build),('verify_04.ps1',verify)]:
    assert not (H/name).exists()
    (H/name).write_text(text,encoding='utf-8',newline='\n')

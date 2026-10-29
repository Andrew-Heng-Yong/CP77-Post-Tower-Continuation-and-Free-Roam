from pathlib import Path
H=Path(__file__).resolve().parent
build=(H/'build_04.ps1').read_text(encoding='utf-8-sig')
for key in ['source','build_proof','block_readback','readback']:
    build=build.replace(key+'_04',key+'_05')
build=build.replace('outside1004_filter_spec_01.json','outside1004_filter_spec_02.json')
build=build.replace('$rows=@();$resources=@()',"$border=Get-Content -LiteralPath (Join-Path $homeWA3 'native_review/outside1000_filter_spec_01.json') -Raw|ConvertFrom-Json -Depth 70\n$rows=@();$resources=@()")
build=build.replace('@{id=1004;remove=@(64);nodes=74}', '@{id=1004;remove=@(64,65);nodes=74},@{id=1000;remove=@(26,27,28,50,51,52,53,60);nodes=61}')
build=build.replace('if($spec.id -eq 1004){\n  $owner=', 'if($spec.id -eq 1000){\n  $owner=@{resolved_prefab=$border.native_prefab;resource=$border.sector_resource}\n  $hit=@{raw=$border.sector_raw;sha256=$border.sector_sha256}\n }elseif($spec.id -eq 1004){\n  $owner=')
before="if($spec.id -eq 1004){\n   if($node.GetType().Name -cne 'worldInterestingConversationsAreaNode'"
after="""if($spec.id -eq 1000){
   $expectedType=if($index -in @(51,52,53)){'worldDeviceNode'}else{'worldTriggerAreaNode'}
   if($node.GetType().Name -cne $expectedType){throw 'Unexpected border stateful node type'}
  }elseif($spec.id -eq 1004 -and $index -eq 65){
   if($node.GetType().Name -cne 'worldAudioAttractAreaNode' -or $node.InterestingConversationsNodeRef.ToString() -cne '~/../la_street_violence_02_ic_animation'){throw 'Unexpected lore audio dependency'}
  }elseif($spec.id -eq 1004){
   if($node.GetType().Name -cne 'worldInterestingConversationsAreaNode'"""
assert before in build;build=build.replace(before,after)
before="if(@($read.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'worldPopulationSpawnerNode'}).Count){throw 'Private sector contains a population spawner'}"
after="""$spawners=@($read.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'worldPopulationSpawnerNode'})
 if($spawners.Count -ne $(if($spec.id -eq 1000){8}else{0})){throw 'Unexpected preview spawner count'}
 foreach($spawn in $spawners){if($spawn.Chunk.SpawnOnStart.ToString() -cne 'False' -or $spawn.Chunk.AlwaysSpawned.ToString() -cne 'False'){throw 'Automatic preview remains'}}"""
assert before in build;build=build.replace(before,after).replace('Descriptors.Count -ne 3','Descriptors.Count -ne 4').replace('groups=@(160,161,1004)','groups=@(160,161,1000,1004)')
verify=(H/'verify_04.ps1').read_text(encoding='utf-8-sig')
for key in ['source','verification','verify','build']:
    verify=verify.replace(key+'_04',key+'_05')
verify=verify.replace('outside1004_filter_spec_01.json','outside1004_filter_spec_02.json')
verify=verify.replace("exactly three descriptor registrations' ($block.RootChunk.Descriptors.Count -eq 3)","exactly four descriptor registrations' ($block.RootChunk.Descriptors.Count -eq 4)")
verify=verify.replace("@{id=1004;stem='quest_fa6df5356603d67f';drop=@(64);expected=74;spots=61}","@{id=1004;stem='quest_fa6df5356603d67f';drop=@(64,65);expected=74;spots=61},@{id=1000;stem='quest_769927088f9d9c0c';drop=@(26,27,28,50,51,52,53,60);expected=61;spots=41}")
verify=verify.replace('$nativePath=if($spec.id -eq 1004)','$nativePath=if($spec.id -in @(1000,1004))')
before="if($spec.id -eq 1004){Check '1004: remove only exact unsafe lore animation trigger'"
after="""if($spec.id -eq 1000){$type=if($i -in @(51,52,53)){'worldDeviceNode'}else{'worldTriggerAreaNode'};Check ('1000: exact removed stateful node type '+$i) ($node.GetType().Name -ceq $type)}
   elseif($spec.id -eq 1004 -and $i -eq 65){Check '1004: remove exact dangling audio attractor' ($node.GetType().Name -ceq 'worldAudioAttractAreaNode' -and $node.InterestingConversationsNodeRef.ToString() -ceq '~/../la_street_violence_02_ic_animation')}
   elseif($spec.id -eq 1004){Check '1004: remove only exact unsafe lore animation trigger'"""
assert before in verify;verify=verify.replace(before,after)
before="Check ($spec.id.ToString()+': no remaining population-spawner definition') (@($c.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'worldPopulationSpawnerNode'}).Count -eq 0)"
after="""$spawners=@($c.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'worldPopulationSpawnerNode'})
 Check ($spec.id.ToString()+': exact retained disabled preview count') ($spawners.Count -eq $(if($spec.id -eq 1000){8}else{0}))
 foreach($spawn in $spawners){Check '1000: retained preview cannot auto-spawn' ($spawn.Chunk.SpawnOnStart.ToString() -ceq 'False' -and $spawn.Chunk.AlwaysSpawned.ToString() -ceq 'False')}"""
assert before in verify;verify=verify.replace(before,after)
verify=verify.replace('PASS_PRIVATE_160_161_1004_FILTERED_SECTORS_STATIC','PASS_PRIVATE_160_161_1000_1004_FILTERED_SECTORS_STATIC').replace('negative_controls=6','negative_controls=8')
verify=verify.replace('$pins+=$pinsExtra',"$pins+=$pinsExtra\n$pins+=@((Join-Path $PSScriptRoot '../native_review/outside1000_filter_spec_01.json'),(Join-Path $PSScriptRoot '../native_review/border_support_assessment_01.json'))")
for name,text in [('build_05.ps1',build),('verify_05.ps1',verify)]:
    assert not (H/name).exists()
    (H/name).write_text(text,encoding='utf-8',newline='\n')

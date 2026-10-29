"""Derive a guarded WA3 successor packager and transactional fixture suite from WA2."""
from pathlib import Path
H=Path(__file__).resolve().parent
B=H.parent/'world_actions_wa2'
outputs=['package_01.ps1','package_01.py','deploy_01.ps1','test_deploy_01.py']
assert not any((H/name).exists() for name in outputs),'Preserve previously generated tools'

old_pattern=r'^towercontinued\\world_support_wa3\\[a-zA-Z0-9_\\-]+\.questphase$'
new_pattern=r'^(towercontinued\\world_support_wa3\\[a-zA-Z0-9_\\-]+\.(questphase|streamingblock)|base\\worlds\\03_night_city\\_compiled\\default\\quest_[a-f0-9]{16}\.streamingsector)$'

def base_text(name):
    text=(B/name).read_text(encoding='utf-8-sig')
    # Replace base-location references before successor labels.
    text=text.replace('prealpha/bottle_actions_ba1/candidate_01','prealpha/BASE_SUCCESSOR_SENTINEL/candidate_01')
    text=text.replace('world_actions_wa2','world_support_wa3').replace('WA2','WA3').replace('BA1','WA2').replace('1186','1212')
    text=text.replace('BASE_SUCCESSOR_SENTINEL','world_actions_wa2')
    return text

ps=base_text('package_01.ps1')
assert old_pattern in ps
ps=ps.replace(old_pattern,new_pattern)
anchor='$newFiles=@(Get-ChildItem -LiteralPath $newSource -Recurse -File|Sort-Object FullName)'
assert anchor in ps
ps=ps.replace(anchor,r'''$blockRows=@($cohort.resources|Where-Object {$_.depot.EndsWith('.streamingblock')})
$streamingBlocks=@()
if($blockRows.Count){
 if(!$cohort.PSObject.Properties['streaming_blocks']){throw 'New private blocks need explicit XL registrations'}
 $streamingBlocks=@($cohort.streaming_blocks)
 if($streamingBlocks.Count -ne $blockRows.Count -or @(Compare-Object ($streamingBlocks|Sort-Object) ($blockRows.depot|Sort-Object)).Count){throw 'Streaming block registration inventory mismatch'}
}
$sectorRows=@($cohort.resources|Where-Object {$_.depot.EndsWith('.streamingsector')})
$sectorBindings=@()
if($sectorRows.Count){
 if(!$cohort.PSObject.Properties['sector_bindings']){throw 'Private sectors need explicit engine-prefab bindings'}
 $sectorBindings=@($cohort.sector_bindings)
 if($sectorBindings.Count -ne $sectorRows.Count -or @($sectorBindings.depot|Select-Object -Unique).Count -ne $sectorRows.Count){throw 'Sector binding inventory mismatch'}
 foreach($binding in $sectorBindings){
  if($binding.prefab_ref -notlike '$/*/world_support_wa3/*'){throw 'Private sector prefab is outside WA3 namespace'}
  $hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$binding.prefab_ref)
  $expected='base\worlds\03_night_city\_compiled\default\quest_'+$hash.ToString('x16')+'.streamingsector'
  if($binding.node_ref_hash -cne $hash.ToString() -or $binding.depot -cne $expected -or !$approved.ContainsKey($expected)){throw 'Private sector does not match exact engine prefab hash'}
 }
}
'''+anchor)
anchor="$entries=''\nforeach($r in $newRows){"
assert anchor in ps
ps=ps.replace(anchor,"$phaseRows=@($newRows|Where-Object {$_.depot.EndsWith('.questphase')})\nif(!$phaseRows.Count){throw 'No approved owner phases to register'}\n$entries=''\nforeach($r in $phaseRows){")
ps=ps.replace("foreach($r in $newRows){if([regex]::Matches($newXL", "foreach($r in $phaseRows){if([regex]::Matches($newXL")
old="[IO.File]::WriteAllText($xl,$oldXL.Replace('streaming:',$entries+'streaming:'),[Text.UTF8Encoding]::new($false))"
assert old in ps
ps=ps.replace(old,"$blockEntries=''\nforeach($depot in $streamingBlocks){if($oldXL.Contains($depot)){throw 'Duplicate streaming block registration'};$blockEntries+=\"    - $depot`n\"}\nif($oldXL.Split('localization:').Count -ne 2){throw 'XL localization boundary drift'}\n[IO.File]::WriteAllText($xl,$oldXL.Replace('streaming:',$entries+'streaming:').Replace('localization:',$blockEntries+'localization:'),[Text.UTF8Encoding]::new($false))")
ps=ps.replace("if($newXL.Replace($entries,'') -cne $oldXL)", "$restoredXL=$newXL.Replace($entries,'');if($blockEntries){$restoredXL=$restoredXL.Replace($blockEntries,'')}\nif($restoredXL -cne $oldXL)")
ps=ps.replace("Copy-Item -LiteralPath $baselineSource -Destination", "foreach($depot in $streamingBlocks){if([regex]::Matches($newXL,[regex]::Escape('    - '+$depot)+\"\\r?\\n\").Count -ne 1){throw 'Streaming block is not registered exactly once'}}\nCopy-Item -LiteralPath $baselineSource -Destination")
old="$archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -Filter '*.archive' -File)"
assert old in ps
ps=ps.replace(old,"$archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Recurse -Filter '*.archive' -File)")
old=" $archivePins+=@{path=$file.FullName;sha256=(Get-FileHash -LiteralPath $file.FullName).Hash}"
assert old in ps
ps=ps.replace(old," if($file.DirectoryName -ceq (Join-Path $game 'archive/pc/mod').Replace('/','\\')){$archivePins+=@{path=$file.FullName;sha256=(Get-FileHash -LiteralPath $file.FullName).Hash}}")
ps=ps.replace('new_resources=$newRows;cohort_proof_sha256=', 'new_resources=$newRows;registered_phase_count=$phaseRows.Count;registered_block_count=$blockRows.Count;streaming_blocks=$streamingBlocks;new_sector_count=$sectorRows.Count;sector_bindings=$sectorBindings;cohort_proof_sha256=')
ps=ps.replace('$compiled.source_count -ne 64','$compiled.source_count -lt 1').replace('Fresh64-source Baseline compilation','Fresh complete-input Baseline compilation')
ps=ps.replace('baseline_sha256=$compiled.candidate_sha256;', 'baseline_sha256=$compiled.candidate_sha256;compile_source_count=$compiled.source_count;')
(H/'package_01.ps1').write_text(ps,encoding='utf-8')

py=base_text('package_01.py')
py=py.replace("H/'derive_deploy_01.py'", "H/'derive_tools_01.py'")
anchor="assert packed['new_resource_count']==len(approved)"
assert anchor in py
py=py.replace(anchor,anchor+"\nphase_depots={p for p in approved if p.endswith('.questphase')}\nsector_depots={p for p in approved if p.endswith('.streamingsector')}\nassert phase_depots and phase_depots|sector_depots==set(approved)\nassert packed['registered_phase_count']==len(phase_depots) and packed['new_sector_count']==len(sector_depots)\nassert {normalize(r['depot']) for r in packed['sector_bindings']}==sector_depots\nassert packed['sector_bindings']==cohort.get('sector_bindings',[])\nfor binding in packed['sector_bindings']:\n    assert normalize(binding['depot'])=='base\\\\worlds\\\\03_night_city\\\\_compiled\\\\default\\\\quest_'+format(int(binding['node_ref_hash']),'016x')+'.streamingsector'\n    assert binding['prefab_ref'].startswith('$/') and '/world_support_wa3/' in binding['prefab_ref']")
py=py.replace("'new_resources':packed['new_resources'],'package_files'", "'new_resources':packed['new_resources'],'registered_phase_count':packed['registered_phase_count'],'new_sector_count':packed['new_sector_count'],'sector_bindings':packed['sector_bindings'],'package_files'")
py=py.replace('Approved isolated native ambient action controllers; retain WA2 and existing W3 owners without reset.', 'Approved native NPC support owners; preserve WA2 action controllers and existing owner receipts without reset.')
py=py.replace("H/'derive_tools_01.py',H/'deploy_01.ps1',H/'test_deploy_01.py'", "H/'derive_tools_01.py',H/'deploy_01.ps1',H/'test_deploy_01.py',H/'capture_save_baseline_01.py'")
py=py[:py.index("snapshot={'status':'BEFORE_WA3_INSTALL_READ_ONLY_CAPTURE'")]+"print(json.dumps({'status':manifest['status'],'manifest_sha256':digest(mp),'zip_sha256':digest(zp),'save_baseline':'DEFERRED_UNTIL_GAME_CLOSED_BEFORE_INSTALL','fresh_compile_sources':64,'new_resources':len(approved),'archive_members':packed['archive_members']}))\n"
py=py.replace("compiled['source_count']==64", "compiled['source_count']>0 and compiled['source_count']==packed['compile_source_count']")
py=py.replace("len(current_sources)==64", "len(current_sources)==compiled['source_count']")
py=py.replace("'PASS_FRESH_64_SOURCE_COMPILE_INPUTS','source_count':64", "'PASS_FRESH_COMPLETE_SOURCE_COMPILE_INPUTS','source_count':compiled['source_count']")
py=py.replace("'compile_reused':False", "'compile_source_count':compiled['source_count'],'compile_reused':False")
py=py.replace("'fresh_compile_sources':64", "'fresh_compile_sources':compiled['source_count']")
py=py.replace("assert phase_depots and phase_depots|sector_depots==set(approved)","block_depots={p for p in approved if p.endswith('.streamingblock')}\nassert phase_depots and phase_depots|sector_depots|block_depots==set(approved)\nassert packed['registered_block_count']==len(block_depots) and set(packed['streaming_blocks'])==block_depots\nassert packed['streaming_blocks']==cohort.get('streaming_blocks',[])")
py=py.replace("'registered_phase_count':packed['registered_phase_count'],", "'registered_phase_count':packed['registered_phase_count'],'registered_block_count':packed['registered_block_count'],'streaming_blocks':packed['streaming_blocks'],")
(H/'package_01.py').write_text(py,encoding='utf-8')

deploy=base_text('deploy_01.ps1')
assert old_pattern in deploy
deploy=deploy.replace(old_pattern,new_pattern)
deploy=deploy.replace('$m.runtime_inputs.Count -ne 64', '$m.compile_source_count -lt 1 -or $m.runtime_inputs.Count -ne $m.compile_source_count')
anchor="if(!$fixture -and ($m.game_root -cne $game -or $m.backup_root -cne $backup)){throw 'Manifest roots changed'}"
assert anchor in deploy
deploy=deploy.replace(anchor,r'''$phases=@($m.new_resources|Where-Object {$_.depot.EndsWith('.questphase')})
$blocks=@($m.new_resources|Where-Object {$_.depot.EndsWith('.streamingblock')})
if($m.registered_block_count -ne $blocks.Count -or @($m.streaming_blocks).Count -ne $blocks.Count){throw 'Streaming block inventory changed'}
if($blocks.Count -and @(Compare-Object ($m.streaming_blocks|Sort-Object) ($blocks.depot|Sort-Object)).Count){throw 'Streaming block registration set changed'}
$sectors=@($m.new_resources|Where-Object {$_.depot.EndsWith('.streamingsector')})
if(!$phases.Count -or $m.registered_phase_count -ne $phases.Count -or $m.new_sector_count -ne $sectors.Count -or @($m.sector_bindings).Count -ne $sectors.Count){throw 'Phase/sector inventory changed'}
if($sectors.Count -and @(Compare-Object @($m.sector_bindings.depot|Sort-Object) @($sectors.depot|Sort-Object)).Count){throw 'Sector binding set changed'}
foreach($binding in $m.sector_bindings){
 $expected='base\worlds\03_night_city\_compiled\default\quest_'+([uint64]::Parse([string]$binding.node_ref_hash)).ToString('x16')+'.streamingsector'
 if($binding.depot -cne $expected -or $binding.prefab_ref -notlike '$/*/world_support_wa3/*'){throw 'Private prefab binding changed'}
}
'''+anchor)
(H/'deploy_01.ps1').write_text(deploy,encoding='utf-8')
test=base_text('test_deploy_01.py')
(H/'test_deploy_01.py').write_text(test,encoding='utf-8')
print('Derived WA3 three-file packaging/deployment tools; dynamic phases/sectors,23 fixture actions,six interruptions')

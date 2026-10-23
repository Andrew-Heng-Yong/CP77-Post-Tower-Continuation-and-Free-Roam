param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot)
$base='research/restriction_profiles/body_stats_design'
$recordsPath=Join-Path $workspace ($base+'/body_catalogue_records.json')
$treesPath=Join-Path $workspace ($base+'/other_perk_tree_records.json')
$records=Get-Content -LiteralPath $recordsPath -Raw|ConvertFrom-Json
$trees=Get-Content -LiteralPath $treesPath -Raw|ConvertFrom-Json
$inputs=[ordered]@{}
function Pin([string]$path){$inputs[$path]=(Get-FileHash -LiteralPath $path).Hash}
Pin $recordsPath;Pin $treesPath
foreach($audit in @($records,$trees)){
 foreach($db in $audit.database_sources){
  if((Get-FileHash -LiteralPath $db.path).Hash -ne $db.sha256){throw 'Stock database audit is stale'}
  Pin $db.path
 }
}
$loc=@{}
foreach($relative in @(
 'research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json',
 'research/misty_viktor_world/street_localization/json/ep1/localization/en-us/onscreens/onscreens.json.json',
 'research/misty_viktor_world/street_localization/json/ep1/localization/en-us/onscreens/onscreens_final.json.json'
)){
 $path=Join-Path $workspace $relative;Pin $path
 $entries=(Get-Content -LiteralPath $path -Raw|ConvertFrom-Json).Data.RootChunk.root.Data.entries
 foreach($entry in $entries){if($entry.femaleVariant){$loc[$entry.primaryKey]=$entry.femaleVariant}}
}
function Localized([string]$key){
 if(-not $key){return ''}
 $id=$key -replace '(?i)^lockey#',''
 if($loc.ContainsKey($id)){return ($loc[$id] -replace '<[^>]*>','' -replace '\\n',"`n")}
 return ''
}
$byHash=@{}
foreach($record in @($records.records)+@($records.reference_closure)){$byHash[$record.hash]=$record}
$perkByName=@{}
foreach($p in $records.records|Where-Object type -eq 'gamedataNewPerk_Record'){$perkByName[$p.name]=$p}
$active=[ordered]@{}
foreach($tree in $trees.records|Where-Object {$_.name -in @('NewPerks.CoolAttributeData','NewPerks.IntelligenceAttributeData','NewPerks.ReflexesAttributeData','NewPerks.TechnicalAbilityAttributeData')}){
 foreach($ref in $tree.fields.perks){
  $perk=$byHash[$ref.hash]
  if(-not $perk -or $perk.type -ne 'gamedataNewPerk_Record'){throw 'Unresolved active perk'}
  $active[$perk.name]=$perk
 }
}
if($active.Count -ne 146){throw 'Unexpected exposed four-tree roster'}
$smart=@('Intelligence_Inbetween_Right_2','Intelligence_Master_Perk_4','Intelligence_Right_Milestone_2','Intelligence_Right_Milestone_3','Intelligence_Right_Perk_2_1','Intelligence_Right_Perk_2_2','Intelligence_Right_Perk_3_1','Intelligence_Right_Perk_3_2')
$keepInt=@('Intelligence_Left_Milestone_1','Intelligence_Left_Perk_1_2')
$explicitCore=@('Reflexes_Inbetween_Left_3','Cool_Inbetween_Left_3','Cool_Left_Milestone_1','Tech_Inbetween_Left_3','Tech_Inbetween_Right_2','Tech_Master_Perk_2','Tech_Master_Perk_3')
$physicalRoots=@('Reflexes_Central_Milestone_2','Reflexes_Right_Milestone_2','Cool_Inbetween_Left_2','Cool_Left_Perk_3_2')
$sustainRoots=@('Cool_Central_Perk_3_2','Cool_Right_Perk_2_4','Cool_Right_Perk_3_2')
$rows=[ordered]@{}
foreach($name in $active.Keys){
 $p=$active[$name];$id=$name -replace '^NewPerks\.',''
 $category=($id -split '_')[0]
 $display=Localized $p.fields.loc_name_key
 if(-not $display -or $display -eq '!OBSOLETE'){throw "Missing active display name: $id"}
 $tag='retain';$reason='No specific implant dependency or selected enhanced-movement ability; ordinary skill/equipment abstraction is not itself proof of forbidden cyberware.'
 if($id -eq 'Intelligence_Right_Perk_2_2'){$tag='proposed_core';$reason='Explicit accuracy scaling from cyberdeck Max RAM, independent of whether the tattoo exception permits smart targeting.'}
 elseif($id -in $smart){$tag='decision_smart';$reason='Smart targeting/RAM synergy; policy must reconcile the explicitly approved Casius tattoo exception before any refund.'}
 elseif(($category -eq 'Intelligence' -and $id -notin $keepInt) -or $id -in $explicitCore -or ($category -eq 'Tech' -and $id -like 'Tech_Central_*' -and $id -ne 'Tech_Central_Perk_2_3')){
  $tag='proposed_core';$reason='Quickhack/Monowire, cyberware capacity/augmentation or explicit combat-implant operation; recommended policy, not a canon list of named perks.'
 }elseif($id -in $physicalRoots){$tag='proposed_full_nerf';$reason='Dash, projectile-blocking or time-slowing ability; an additional physical-balance choice, not proof it needs an implant.'}
 elseif($id -in $sustainRoots){$tag='decision_sustain';$reason='Automatic combat healing/finisher sustain; optional stricter fragility policy, not the combat-implant rule.'}
 elseif($id -in $keepInt){$reason='Retain personal-link/access-point utility. Eye in the Sky is mixed: camera quickhack bonuses remain inert without a permitted deck; access-point live usability still needs verification.'}
 $descriptions=@(Localized $p.fields.loc_desc_key);$unresolvedLevels=@()
 foreach($level in $p.fields.levels){
  $levelRecord=$byHash[$level.hash]
  if($levelRecord -and $levelRecord.PSObject.Properties['fields']){$descriptions+=Localized ($levelRecord.fields.loc_desc_key)}
  else{$unresolvedLevels+=$level.hash}
 }
 $requires=@($p.fields.requiresPerks|ForEach-Object {$byHash[$_.hash].name})
 $rows[$name]=[ordered]@{id=$id;record=$name;name=$display;category=$category;ranks=@($p.fields.levels).Count;classification=$tag;reason=$reason;requires=$requires;description=@($descriptions|Where-Object {$_}|Select-Object -Unique);unresolved_level_references=$unresolvedLevels}
}
# Conservative whole-perk removal must include dependents, not leave an invalid
# purchased branch. This is a policy/record audit, NOT executable refund code.
do {
 $changed=$false
 foreach($row in $rows.Values){
  if($row.classification -in @('proposed_core','dependency_core')){continue}
  $blocked=@($row.requires|Where-Object {$rows.Contains($_) -and $rows[$_].classification -in @('proposed_core','dependency_core')})
  if($blocked.Count){$row.classification='dependency_core';$row.reason='Refund because a proposed blocked prerequisite is removed, not because this perk alone is a forbidden implant.';$changed=$true}
 }
}while($changed)
do {
 $changed=$false
 foreach($row in $rows.Values){
  if($row.classification -ne 'retain'){continue}
  $blocked=@($row.requires|Where-Object {$rows.Contains($_) -and $rows[$_].classification -in @('proposed_full_nerf','dependency_full_nerf')})
  if($blocked.Count){$row.classification='dependency_full_nerf';$row.reason='Whole-perk dependency of the proposed Dash/Lead and Steel physical-nerf roots.';$changed=$true}
 }
}while($changed)
foreach($row in $rows.Values){
 if($row.classification -eq 'retain' -and @($row.requires|Where-Object {$rows.Contains($_) -and $rows[$_].classification -eq 'decision_sustain'}).Count){
  $row.classification='decision_sustain_dependency';$row.reason='Would also require refund if its optional combat-healing prerequisite is removed.'
 }
}
foreach($id in $smart){
 # These overlap the quickhack system. Retain the tattoo decision marker even
 # where another proposed removal already entails a dependency refund.
 $rows['NewPerks.'+$id].Add('smart_exception_review',$true)
}
$receiptPath=Join-Path $workspace 'research/restriction_profiles/relic_r2_2/install_receipt.json';Pin $receiptPath
$receipt=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
foreach($file in $receipt.files){$path=Join-Path $receipt.game_root $file.relative;Pin $path;if($inputs[$path] -ne $file.sha256){throw 'Installed Relic source differs'}}
$summary=@($rows.Values|ForEach-Object {[pscustomobject]$_}|Group-Object classification|ForEach-Object {@{classification=$_.Name;perks=$_.Count;maximum_ranks=($_.Group|Measure-Object ranks -Sum).Sum}})
$report=[ordered]@{status='PROPOSED_OTHER_PERK_POLICY_NOT_IMPLEMENTED';utc=[DateTime]::UtcNow.ToString('o');active_perks=146;excluded_obsolete_record='NewPerks.Cool_Right_Perk_3_3';hp_target=100;hp_target_installed=$false;stamina_change_requested=$false;summary=$summary;perks=@($rows.Values);sources=$inputs;limits=@('Stock record dependencies and extracted 2.31 localization, not a live character purchase snapshot.','Classifications are recommendations, not user approval or canon perk names.','Smart-weapon/tattoo exception and optional sustain choices are not silently resolved.','Whole-perk proposal; partial-rank caps or reparenting utility perks are separate work.');game_writes=0;save_writes=0;runtime_code_changes=0}
foreach($path in $inputs.Keys){if((Get-FileHash -LiteralPath $path).Hash -ne $inputs[$path]){throw 'Input changed during audit'}}
$output=Join-Path $workspace ($base+'/other_perk_policy.json')
[IO.File]::WriteAllText($output,($report|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
$summary|ConvertTo-Json

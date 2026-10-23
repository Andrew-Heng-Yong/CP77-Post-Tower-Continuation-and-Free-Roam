param([string]$Revision='policy_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
$Python='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if($Revision -cnotmatch '^policy_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable output exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback'),(Join-Path $out 'original_readback')|Out-Null
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'plan02.json') -Raw|ConvertFrom-Json
$pins=[ordered]@{};$resources=[ordered]@{}
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
foreach($p in @('prealpha/sidejobs_s25/policy/build.ps1','prealpha/sidejobs_s25/policy/prepare.py','prealpha/sidejobs_s25/policy/scripts.py','prealpha/sidejobs_s25/policy/plan02.json','tools/build_phase2a.ps1')){Pin $p}
foreach($p in $plan.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw 'Pinned input drift'}}
function NarrowCondition($c,$paths){
 $count=0
 if($c -is [WolvenKit.RED4.Types.questLogicalCondition]){foreach($h in $c.Conditions){$count+=(NarrowCondition $h.Chunk $paths)}}
 elseif($c -is [WolvenKit.RED4.Types.questJournalCondition]){
  $t=$c.Type.Chunk
  if($t -is [WolvenKit.RED4.Types.questJournalEntryState_ConditionType] -and $t.Path.Chunk.ClassName.ToString() -ceq 'gameJournalQuest' -and $t.State.ToString() -ceq 'Failed'){
   if($paths -cnotcontains $t.Path.Chunk.RealPath.ToString()){throw 'Unexpected failed root'}
   $t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]::Inactive;$count++
  }
 }
 return $count
}
function RootInactive($path){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName='gameJournalQuest';$p.FileEntryIndex=2
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]::Inactive;$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
foreach($r in $plan.resources){
 $f=Read-Cr2wFile (Join-Path $WorkspaceRoot $r.source)
 $name=$r.depot.Replace('\','_')+'.json'
 Export-Cr2wJson $f (Join-Path $out ('original_readback/'+$name))
 foreach($change in $r.changes){
  if($change.graph -cne 'root'){throw 'Unreviewed nested preflight'}
  $node=Get-QuestNode $f.RootChunk.Graph.Chunk ([int]$change.node)
  $condition=$node.Condition.Chunk
  if($condition -isnot [WolvenKit.RED4.Types.questLogicalCondition] -or $condition.Operation.ToString() -cne 'AND'){throw 'Not an AND preflight'}
  $count=NarrowCondition $condition @($change.narrowed_roots)
  if($count -ne @($change.narrowed_roots).Count){throw 'Root delta count mismatch'}
  foreach($fact in $change.exclusion_facts){Add-RedHandle $condition.Conditions (New-FactCondition $fact 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
  if($change.PSObject.Properties.Name -contains 'added_root'){Add-RedHandle $condition.Conditions (RootInactive $change.added_root)}
 }
 $target=Join-Path (Join-Path $out 'source') $r.depot
 Write-Cr2wFile $f $target
 Export-Cr2wJson (Read-Cr2wFile $target) (Join-Path $out ('readback/'+$name))
 $resources[$r.depot]=(Get-FileHash -LiteralPath $target).Hash
}
& $Python (Join-Path $PSScriptRoot 'scripts.py') $out
if($LASTEXITCODE){throw 'Script transformations failed'}
$scripts=@(Get-Content (Join-Path $out 'script_replacements.json') -Raw|ConvertFrom-Json)
foreach($p in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash -cne $pins[$p]){throw 'Pinned source changed during build'}}
$m=[ordered]@{schema=1;status='BUILT_NOT_INSTALLED';revision=$Revision;resources=$resources;boots=@();source_pins=$pins;native_copies=@();mod_overrides=@($plan.mod_overrides);policy_plan='prealpha/sidejobs_s25/policy/plan02.json';native_changes=@($plan.resources);script_replacements=$scripts;live='NOT_TESTED'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($m|ConvertTo-Json -Depth 50),[Text.UTF8Encoding]::new($false))
Write-Output ('Built '+$resources.Count+' existing mod resource overrides and '+$scripts.Count+' script replacements')

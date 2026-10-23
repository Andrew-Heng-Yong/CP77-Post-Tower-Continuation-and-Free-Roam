param([string]$WorkspaceRoot=(Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
$tools=Join-Path $WorkspaceRoot 'tools'
. (Join-Path $tools 'build_phase2a.ps1') -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research/pre_alpha_clean/phone'
$target=Join-Path $WorkspaceRoot 'prealpha/phone'
$old=Get-Content (Join-Path $WorkspaceRoot 'research/gig_restoration/gig_phone_u9/manifest.json') -Raw|ConvertFrom-Json -AsHashtable
$pins=[ordered]@{}
foreach($f in $old.files){
 $path=Join-Path $WorkspaceRoot $f.source;$hash=(Get-FileHash -LiteralPath $path).Hash
 if($hash -ne $f.sha256){throw "Pinned predecessor changed: $path"};$pins[$f.source]=$hash
}
New-Item -ItemType Directory -Force $audit,(Join-Path $target 'scripts')|Out-Null
$depot='towercontinued\gig_phone_u9\support_wrapper.questphase'
$source=Join-Path $WorkspaceRoot ('build/GigPhoneU9/source/'+$depot)
if((Get-FileHash -LiteralPath $source).Hash -ne $old.resources[$depot]){throw 'Pinned phone wrapper changed'}
$f=Read-Cr2wFile $source;$g=$f.RootChunk.Graph.Chunk
$removed=@()
foreach($id in @(3,4)){
 $c=(Get-QuestNode $g $id).Condition.Chunk
 $indices=@();$before=$c.Conditions.Count
 for($k=0;$k -lt $before;$k++){
  $t=$c.Conditions[$k].Chunk.Type.Chunk
  if($t.GetType().Name -eq 'questVarVsVarComparison_ConditionType'){
   $pair=@($t.FactName1.ToString(),$t.FactName2.ToString())
   if(-not @($old.balances|Where-Object {$_[0] -ceq $pair[0] -and $_[1] -ceq $pair[1]}).Count){throw 'Unexpected variable comparison'}
   $indices+=,$k;$removed+=,@{node=$id;start=$pair[0];end=$pair[1]}
  }
 }
 if($indices.Count -ne 16){throw "Expected 16 historical equalities at $id, got $($indices.Count)"}
 for($k=$indices.Count-1;$k -ge 0;$k--){$c.Conditions.RemoveAt($indices[$k])}
}
# Revision two prevents a mixed old archive/new script from appearing ready.
(Get-QuestNode $g 2).Type.Chunk.Value=2
$destination=Join-Path $target ('resources/'+$depot)
Write-Cr2wFile $f $destination
Export-Cr2wJson (Read-Cr2wFile $destination) (Join-Path $audit 'support_wrapper.json')
$data=Get-Content (Join-Path $WorkspaceRoot 'redscript/PTFR_GigPhoneU9/GigPhoneDataU9.generated.reds') -Raw
$data=$data.Replace('// Generated only by build_gig_phone_u9.ps1; exact wrapper admission facts.','// Pinned U9 transient/legacy catalogue. Balance arrays are informational only in pre-alpha.')
[IO.File]::WriteAllText((Join-Path $target 'scripts/GigPhoneDataU9.generated.reds'),$data,[Text.UTF8Encoding]::new($false))
$resources=@(@{depot=$depot;source='prealpha/phone/resources/'+$depot;sha256=(Get-FileHash -LiteralPath $destination).Hash;predecessor_sha256=$old.resources[$depot]})
$report=[ordered]@{status='PREALPHA_PHONE_BUILT_NOT_INSTALLED';resources=$resources;removed_historical_equalities=$removed;revision=2;pinned_predecessor_files=$pins;unchanged_native_resources=@('towercontinued\gig_phone_u9\fixer_parent.questphase','towercontinued\gig_phone_u9\fixer_initializer.questphase','towercontinued\gig_phone_u9\fixer_cleanup.questphase');scope='Only support wrapper equality predicates removed; native phone scenes/controllers/reset untouched. No historical fact reset; source and resource outputs only.'}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($report|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
'PREALPHA_PHONE_BUILT_NOT_INSTALLED'

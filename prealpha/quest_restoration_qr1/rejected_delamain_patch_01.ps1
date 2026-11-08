param([string]$Candidate='candidate_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot $Candidate
$base=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'baseline.json') -Raw|ConvertFrom-Json -Depth 100
if(Test-Path -LiteralPath (Join-Path $C 'build_01.json')){throw 'Preserve built candidate'}
if([IO.Path]::GetFullPath($C) -ne (Join-Path $PSScriptRoot 'candidate_01')){throw 'Unexpected output'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$d='towercontinued\sidejobs_s29\phone\delamain.questphase'
$raw=Join-Path (Join-Path $C 'archive_source') $d
if((Get-FileHash -LiteralPath $raw).Hash -cne $base.private_resources.$d){throw 'Baseline payload changed'}
$file=Read-Cr2wFile $raw
Export-Cr2wJson $file (Join-Path $C 'delamain_before.json')
$removed=0
function RemoveCompetingFreshBranch($condition){
 if($condition -isnot [WolvenKit.RED4.Types.questLogicalCondition]){return}
 for($i=$condition.Conditions.Count-1;$i -ge 0;$i--){
  $child=$condition.Conditions[$i].Chunk
  if($child -is [WolvenKit.RED4.Types.questFactsDBCondition] -and $child.Type.Chunk -is [WolvenKit.RED4.Types.questVarComparison_ConditionType]){
   $v=$child.Type.Chunk
   if($v.FactName.ToString() -ceq 'PTFRS25_SQ025_FRESH_Issued'){
    if($condition.Operation.ToString() -cne 'OR' -or $v.ComparisonType.ToString() -cne 'Equal' -or [int]$v.Value.ToString() -ne 1 -or $condition.Conditions.Count -ne 2){throw 'Unexpected competing branch shape'}
    $condition.Conditions.RemoveAt($i);$script:removed++
   }
  }else{RemoveCompetingFreshBranch $child}
 }
}
foreach($id in @(1002,1003)){RemoveCompetingFreshBranch (Get-QuestNode $file.RootChunk.Graph.Chunk $id).Condition.Chunk}
if($removed -ne 2){throw "Expected two competing admission leaves, got $removed"}
Write-Cr2wFile $file $raw
Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $C 'delamain_after.json')
# Full current consolidated source; no old component merger or deployment script.
$archive=Join-Path $C 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{
 $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())
 if(-not $writer.WriteArchive([IO.DirectoryInfo]::new((Join-Path $C 'archive_source')),$stream)){throw 'Packing failed'}
}finally{$stream.Dispose()}
@{status='BUILT_QR1_NOT_INSTALLED';baseline=$base.candidate;changed_resources=@{depot=$d;before=$base.private_resources.$d;after=(Get-FileHash -LiteralPath $raw).Hash};removed_admission_leaves=$removed;xl_changed=$false;reds_changed=$false;new_resources=0;native_fact_writes_added=0;installed_game_writes=0;save_writes=0}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath (Join-Path $C 'build_01.json') -Encoding utf8NoBOM
'BUILT_QR1_NOT_INSTALLED'

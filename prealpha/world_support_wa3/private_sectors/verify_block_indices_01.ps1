Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'block_index_reference_01.json';if(Test-Path $out){throw 'Preserve index evidence'}
$old=@(Get-ChildItem -LiteralPath (Join-Path $ws 'prealpha/world_actions_wa2/candidate_01/archive_source') -Recurse -Filter '*.streamingblock' -File)
if($old.Count -ne 13){throw 'Old block inventory drift'}
$paths=@($old.FullName)+@((Join-Path $PSScriptRoot 'source_06/towercontinued/world_support_wa3/filtered_support.streamingblock'),(Join-Path $PSScriptRoot 'source_ep1_01/towercontinued/world_support_wa3/filtered_support_ep1.streamingblock'))
$rows=@();$pins=@()
foreach($path in $paths){
 $f=Read-Cr2wFile $path;$index=$f.RootChunk.Index;$oup=$index.Oup.ToString();$cell=$index.RldGridCell.ToString()
 if(!(($oup -ceq 'Base' -and $cell -ceq '7635822') -or ($oup -ceq 'EP1' -and $cell -ceq '8279898'))){throw 'Unexpected world block index'}
 $rows+=@{path=$path;oup=$oup;rldGridCell=$cell};$pins+=@{path=$path;sha256=(Get-FileHash $path).Hash}
}
$pins+=@{path=$PSCommandPath;sha256=(Get-FileHash $PSCommandPath).Hash}
@{status='PASS_NATIVE_BLOCK_INDEX_CONVENTION';old_blocks=13;new_blocks=2;rows=$rows;pins=$pins;runtime_proof=$false;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 15|Set-Content -LiteralPath $out -Encoding utf8NoBOM
@{status='PASS';old=13;new=2}|ConvertTo-Json

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$source=Join-Path $PSScriptRoot 'candidate_01/source'
$out=Join-Path $PSScriptRoot 'candidate_02/graph_exports_01'
if(Test-Path -LiteralPath $out){throw 'Preserve graph exports'}
[void][IO.Directory]::CreateDirectory($out)
$files=@(Get-ChildItem -LiteralPath $source -Filter '*.questphase' -Recurse -File)
if($files.Count -ne 9){throw 'Owner resource count drift'}
$proof=[Collections.Generic.List[object]]::new()
foreach($f in $files){
 $target=Join-Path $out ($f.BaseName+'.json')
 $file=Read-Cr2wFile $f.FullName
 Export-Cr2wJson $file $target
 $proof.Add([ordered]@{resource=$f.FullName;resource_sha256=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash;json=$target;json_sha256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash})
}
$result=[ordered]@{status='GRAPH_EXPORTS_FOR_STATIC_AUDIT';resources=$proof.Count;proofs=@($proof);game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'candidate_02/graph_export_proof_01.json'),($result|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;resources=$result.resources}|ConvertTo-Json

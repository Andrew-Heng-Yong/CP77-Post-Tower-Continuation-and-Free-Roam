param([string]$Output='reviews/ronald_01/raw_exports_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$planPath=Join-Path $PSScriptRoot 'reviews/ronald_01/plan.json';$plan=Get-Content -Raw -LiteralPath $planPath|ConvertFrom-Json -Depth 100
$O=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot $Output))
if(-not $O.StartsWith($PSScriptRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Review output containment'}
if(Test-Path -LiteralPath $O){throw 'Fresh review output required'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
[IO.Directory]::CreateDirectory($O)|Out-Null
$rows=@()
foreach($r in $plan.targets){
 if((Get-FileHash -LiteralPath $r.raw).Hash -cne $r.raw_sha256){throw 'Pinned source drift'}
 $file=Read-Cr2wFile $r.raw;$json=Join-Path $O ($r.label+'.json');Export-Cr2wJson $file $json
 $row=@{label=$r.label;raw=$r.raw;raw_sha256=$r.raw_sha256;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash;kind=$r.kind}
 if($r.kind -eq 'sector'){
  $buffer=Join-Path $O ($r.label+'.nodes.bin');[IO.File]::WriteAllBytes($buffer,$file.RootChunk.NodeData.Buffer.GetBytes());$row.buffer=$buffer;$row.buffer_sha256=(Get-FileHash -LiteralPath $buffer).Hash
 }
 $rows+=,$row
}
@{status='INDEPENDENT_READ_ONLY_RAW_READBACKS';targets=$rows;plan_sha256=(Get-FileHash -LiteralPath $planPath).Hash;code_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $O 'manifest.json') -Encoding utf8NoBOM
@{targets=$rows.Count;output=$O}|ConvertTo-Json -Compress

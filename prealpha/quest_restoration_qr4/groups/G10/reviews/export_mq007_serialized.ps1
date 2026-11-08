param([Parameter(Mandatory=$true)][string]$OutputDirectory)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=(Resolve-Path (Join-Path $PSScriptRoot '../../../../..')).Path
$out=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $out){throw 'Fresh readback output required'}
if(-not $out.StartsWith((Join-Path $ws 'prealpha/quest_restoration_qr4/groups/G10/reviews/MQ007_serialized'),[StringComparison]::OrdinalIgnoreCase)){throw 'Review output containment'}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$candidate=Join-Path $ws 'prealpha/quest_restoration_qr4/candidate_01'
$proposal=Get-Content -Raw -LiteralPath (Join-Path $ws 'prealpha/quest_restoration_qr4/groups/G08/regina_proposal_01/proposal.json')|ConvertFrom-Json -Depth 100
$patch=Get-Content -Raw -LiteralPath (Join-Path $candidate 'repair_mq007/patch.json')|ConvertFrom-Json -Depth 100
[IO.Directory]::CreateDirectory($out)|Out-Null
$inputs=@(@{label='native';raw=$proposal.native_source.binary;expected=$patch.native_sha256})
foreach($r in $patch.resources){
 $inputs+=,@{label=$r.prefix+'_before';raw=(Join-Path (Join-Path $ws 'prealpha/quest_restoration_qr3/candidate_01/archive_source') $r.depot);expected=$r.before}
 $inputs+=,@{label=$r.prefix+'_after';raw=(Join-Path (Join-Path $candidate 'archive_source') $r.depot);expected=$r.after}
}
$rows=@()
foreach($i in $inputs){
 $hash=(Get-FileHash -LiteralPath $i.raw).Hash;if($hash -ne $i.expected){throw ('Actual resource hash mismatch '+$i.label)}
 $json=Join-Path $out ($i.label+'.json');Export-Cr2wJson (Read-Cr2wFile $i.raw) $json
 $rows+=,@{label=$i.label;binary=$i.raw;sha256=$hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
}
@{status='INDEPENDENT_FRESH_BINARY_READBACK';resources=$rows;patch_sha256=(Get-FileHash -LiteralPath (Join-Path $candidate 'repair_mq007/patch.json')).Hash;runtime_changes=@()}|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $out 'sources.json') -Encoding utf8NoBOM
@{readbacks=$rows.Count;output=$out}|ConvertTo-Json

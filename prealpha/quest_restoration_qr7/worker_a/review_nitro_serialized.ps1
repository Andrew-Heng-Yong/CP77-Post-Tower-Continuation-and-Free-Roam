param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=(Get-Location).Path
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output|Out-Null
$p=Join-Path $w 'prealpha/quest_restoration_qr7/candidate_01/archive_source/towercontinued/sidejobs_s29/entries/mq060_nitro.questphase'
$expected='79FD3A440DFBCE6130AA5E5EA1D71E6E92BEAD27691C0AD0F59EFE7C94214784'
if((Get-FileHash -LiteralPath $p).Hash -ne $expected){throw 'Candidate drift'}
$json=Join-Path $Output 'fresh_candidate.json'
Export-Cr2wJson (Read-Cr2wFile $p) $json
@{source=$p;source_sha256=$expected;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash;scope='Independent actual binary readback only; no candidate writes'}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $Output 'manifest.json') -Encoding utf8NoBOM

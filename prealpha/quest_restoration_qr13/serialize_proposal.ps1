param([Parameter(Mandatory=$true)][string]$Plan,[Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=[IO.Path]::GetFullPath($Output)
if(-not $out.StartsWith([IO.Path]::GetFullPath($PSScriptRoot)+[IO.Path]::DirectorySeparatorChar) -or (Test-Path -LiteralPath $out)){throw 'Fresh QR13 output containment required'}
$proposal=Get-Content -LiteralPath $Plan -Raw|ConvertFrom-Json -Depth 100
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out|Out-Null
$rows=@()
foreach($r in $proposal.resources){
 if((Get-FileHash -LiteralPath $r.proposed_json).Hash -cne $r.proposed_json_sha256){throw 'Proposed JSON pin changed'}
 $raw=[IO.Path]::GetFullPath((Join-Path $out ('raw/'+$r.depot)))
 if(-not $raw.StartsWith($out+[IO.Path]::DirectorySeparatorChar)){throw 'Depot escapes private output'}
 $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],[IO.File]::ReadAllText($r.proposed_json),[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
 Write-Cr2wFile $dto.Data $raw
 $json=$raw+'.json';Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $rows+=@{depot=$r.depot;input=$r.proposed_json;input_sha256=$r.proposed_json_sha256;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;readback_json=$json;readback_json_sha256=(Get-FileHash -LiteralPath $json).Hash}
}
@{status='COORDINATOR_TYPED_PROPOSAL_READBACK_PENDING_INDEPENDENT_REVIEW';plan=$Plan;plan_sha256=(Get-FileHash -LiteralPath $Plan).Hash;resources=$rows;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;game_writes=0;save_writes=0;installed=$false;package_approved=$false}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
@{status='PROPOSAL_SERIALIZED_NOT_INSTALLED';resources=$rows.Count}|ConvertTo-Json

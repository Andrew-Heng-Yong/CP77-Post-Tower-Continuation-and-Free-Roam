param([Parameter(Mandatory=$true)][string]$InputJson,[Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=(Get-Location).Path
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output|Out-Null
$dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],[IO.File]::ReadAllText($InputJson),[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
$p=Join-Path $Output 'proposed_entry.NONPRODUCTION.questphase'
Write-Cr2wFile $dto.Data $p
$readback=Read-Cr2wFile $p
Export-Cr2wJson $readback ($p+'.json')
@{status='NONPRODUCTION_PRIVATE_ROUNDTRIP_ONLY';input=$InputJson;input_sha256=(Get-FileHash -LiteralPath $InputJson).Hash;raw=$p;raw_sha256=(Get-FileHash -LiteralPath $p).Hash;readback_json=$p+'.json';readback_sha256=(Get-FileHash -LiteralPath ($p+'.json')).Hash;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;candidate_writes=0;game_writes=0;source_approval=$false}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $Output 'manifest.json') -Encoding utf8NoBOM
Write-Output 'Private typed proposal serialized and read back. This is not approval or candidate integration.'

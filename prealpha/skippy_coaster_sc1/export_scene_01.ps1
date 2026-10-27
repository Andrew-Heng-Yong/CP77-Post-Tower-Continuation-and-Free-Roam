Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$C=Join-Path $PSScriptRoot 'candidate_04'
$sceneRel='towercontinued\sidejobs_s30\native\base\quest\minor_quests\mq006\scenes\mq006_02_finale.scene'
$raw=Join-Path (Join-Path $ws 'prealpha/world_workspots_w2/candidate_04/archive_source') $sceneRel
$out=Join-Path $C 'scene_before_01.json'
if(Test-Path -LiteralPath $out){throw 'Preserve exported scene'}
$file=Read-Cr2wFile $raw
Export-Cr2wJson $file $out
$round=Join-Path $C 'scene_roundtrip_01.scene'
$json=[IO.File]::ReadAllText($out)
$opt=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
$dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$json,$opt)
$copy=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$copy.RootChunk=$dto.Data.RootChunk
Write-Cr2wFile $copy $round
$a=(Get-FileHash -LiteralPath $raw -Algorithm SHA256).Hash;$b=(Get-FileHash -LiteralPath $round -Algorithm SHA256).Hash
@{status=if($a -ceq $b){'EXACT_ROUNDTRIP'}else{'REVIEW_REQUIRED'};raw_sha256=$a;roundtrip_sha256=$b;json_sha256=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $C 'scene_export_proof_01.json') -Encoding utf8NoBOM
if($a -cne $b){throw 'Scene roundtrip differs from installed source'}
@{status='EXACT_ROUNDTRIP';sha256=$a}|ConvertTo-Json

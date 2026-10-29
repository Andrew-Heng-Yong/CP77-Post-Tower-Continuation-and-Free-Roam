Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wa=Split-Path $PSScriptRoot -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
function ReadWorld([string]$path){
 $stream=[IO.File]::OpenRead($path)
 try{$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$file=$null;if($reader.ReadFile([ref]$file,$true).ToString() -cne 'NoError'){throw 'Read failed'};return $file}finally{$stream.Dispose()}
}
function HashBytes([byte[]]$bytes){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))}
function Json($object){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($object,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
$core=Get-Content -LiteralPath (Join-Path $wa 'combat_review/filters_core_spec_01.json') -Raw|ConvertFrom-Json -Depth 70
$extra=Get-Content -LiteralPath (Join-Path $wa 'combat_review/filters_additional_spec_01.json') -Raw|ConvertFrom-Json -Depth 70
$payload=Get-Content -LiteralPath (Join-Path $wa 'combat_review/payload_assessment_02.json') -Raw|ConvertFrom-Json -Depth 70
if($core.status -cne 'PASS_CORE_NEW_OWNER_TRIGGER_FILTER_SPEC' -or $core.owners -ne 222 -or $extra.groups.Count -ne 94 -or $payload.status -cne 'PASS_ADDITIONAL94_PASSIVE_SUPPORT_PAYLOADS' -or $payload.private_filter_ids.Count -ne 94){throw 'Filter audit incomplete'}
$blockReport=Get-Content -LiteralPath (Join-Path $wa 'environment_variants/extract_02/report_01.json') -Raw|ConvertFrom-Json -Depth 50
$blockHit=@($blockReport.hits|Where-Object {$_.depot.EndsWith('all.streamingblock') -and [IO.Path]::GetFileName($_.archive) -ceq 'ep1_1_nightcity.archive'})[0]
$b=ReadWorld $blockHit.raw
@($b.RootChunk.Descriptors|Where-Object {$_.Data.DepotPath.ToString() -ceq 'base\worlds\03_night_city\_compiled\default\quest_99f6247f1dc823a1.streamingsector'}|ForEach-Object {@{ref=$_.QuestPrefabNodeRef.ToString();variants=$_.Variants.Count;category=$_.Category.ToString()}})|ConvertTo-Json -Depth 8

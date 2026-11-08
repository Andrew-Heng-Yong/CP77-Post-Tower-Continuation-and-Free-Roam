Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent) -Parent) -Parent
$O=Join-Path $PSScriptRoot 's24_barrier_current'
if(Test-Path -LiteralPath $O){throw 'Fresh independent output required'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
[IO.Directory]::CreateDirectory($O)|Out-Null
$rows=@()
foreach($name in @('mq015','mq019')){
 $dep='towercontinued\sidejobs_s24\base\'+$name+'.questphase'
 $raw=Join-Path (Join-Path $W 'prealpha/quest_restoration_qr3/candidate_01/archive_source') $dep
 $r=Read-Cr2wFile $raw;$n=Get-QuestNode $r.RootChunk.Graph.Chunk 1003
 $json=Join-Path $O ($name+'.json');Export-Cr2wJson $r $json
 $rows+=,@{depot=$dep;source=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash;node1003_type=$n.GetType().Name;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
}
@{status='READ_ONLY_FRESH_CURRENT_BINARY_EXPORT';resources=$rows;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 40|Set-Content -LiteralPath (Join-Path $O 'sources.json') -Encoding utf8NoBOM
$rows|Select-Object depot,node1003_type|ConvertTo-Json

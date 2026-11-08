Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_01'
$O=Join-Path $C 'repair'
if(Test-Path -LiteralPath $O){throw 'Fresh repair evidence directory required'}
$p=Get-Content -LiteralPath (Join-Path $C 'repair_plan.json') -Raw|ConvertFrom-Json -Depth 30
$raw=Join-Path (Join-Path $C 'archive_source') $p.depot
if((Get-FileHash -LiteralPath $raw).Hash -cne $p.before){throw 'Unexpected predecessor bytes'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
[IO.Directory]::CreateDirectory($O)|Out-Null
$res=Read-Cr2wFile $raw
Export-Cr2wJson $res (Join-Path $O 'before.json')
$g=$res.RootChunk.Graph.Chunk
$s=Get-QuestSocket (Get-QuestNode $g 1004) 'True'
$d=Get-QuestSocket (Get-QuestNode $g 1005) 'In'
$t=Get-QuestSocket (Get-QuestNode $g 1008) 'In'
if($s.Connections.Count -ne 1 -or $t.Connections.Count -ne 0){throw 'Unexpected branch cardinality'}
$old=$s.Connections[0].Chunk
if(-not [object]::ReferenceEquals($old.Source.Chunk,$s) -or -not [object]::ReferenceEquals($old.Destination.Chunk,$d)){throw 'Unexpected source/destination'}
$found=-1
for($i=0;$i -lt $d.Connections.Count;$i++){if([object]::ReferenceEquals($d.Connections[$i].Chunk,$old)){if($found -ge 0){throw 'Duplicate connection'};$found=$i}}
if($found -lt 0){throw 'Missing reciprocal connection'}
# Only this connection changes. No nodes, native payloads or saved identifiers move.
$s.Connections.Clear();$d.Connections.RemoveAt($found)
[void](Connect-QuestSockets $s $t)
Write-Cr2wFile $res $raw
$again=Read-Cr2wFile $raw
Export-Cr2wJson $again (Join-Path $O 'after.json')
@{depot=$p.depot;before=$p.before;after=(Get-FileHash -LiteralPath $raw).Hash;removed_edge=$p.remove_edge;added_edge=$p.add_edge;review=$p.independent_review;game_writes=0;save_writes=0;not_installed=$true}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath (Join-Path $O 'patch.json') -Encoding utf8NoBOM
'SERIALIZED_PRECLAIM_QUARANTINE_NOT_INSTALLED'

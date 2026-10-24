$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$main=Join-Path $game 'archive/pc/mod/TowerContinued_PreAlpha.archive'
if((Get-FileHash -LiteralPath $main).Hash -cne '2FC245B128EFD1E6DEC9B6CF38FC037490578EC252E120FD40C57D24EFDDF255'){throw 'Installed main archive changed'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$ar=$null;[void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($main,$hs,[ref]$ar)
$stream=[IO.MemoryStream]::new()
try{$ar.Files[[uint64]17252179095229570458].Extract($stream);$digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream.ToArray()))}finally{$stream.Dispose()}
if($digest -cne 'AB65019BA1D3458BB038600D7F186FE18B2655861D101B2A6B909758C86D7D8F'){throw 'Current final boards differ from PA3; continuation requires new graph audit'}
$edges=(Get-Content -LiteralPath (Join-Path $ws 'prealpha/handoff_pa3/build/pa3_01/graph.json') -Raw|ConvertFrom-Json).all_edges
$required=@('173.CutSource -> 170.CutDestination','173.CutSource -> 171.CutDestination','174.False -> 175.In','175.Out -> 160.In','174.True -> 161.In')
foreach($edge in $required){if($edge -cnotin $edges){throw "Missing native timeout edge: $edge"}}
if(@($edges|Where-Object {$_ -like '160.*'}).Count -ne 0){throw 'Timeout recovery has an unreviewed outgoing edge'}
$result=[ordered]@{status='PASS_CURRENT_NATIVE_TIMEOUT_BRANCH';main_sha256=(Get-FileHash -LiteralPath $main).Hash;final_boards_sha256=$digest;proof_graph_sha256=(Get-FileHash -LiteralPath (Join-Path $ws 'prealpha/handoff_pa3/build/pa3_01/graph.json')).Hash;required_edges=$required;failure_node_outgoing_edges=0;game_writes=0}
$out=Join-Path $PSScriptRoot 'candidate_01/native_check_01.json'
if(Test-Path -LiteralPath $out){throw 'Fresh proof required'}
$result|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $out -Encoding utf8
$result|ConvertTo-Json -Depth 6

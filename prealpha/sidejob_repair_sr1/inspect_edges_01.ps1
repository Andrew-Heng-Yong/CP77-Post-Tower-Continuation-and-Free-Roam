$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$h=Get-Content (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw;$b=$h.IndexOf('function ClearB5(');$e=$h.IndexOf('$allRoots=@{};');. ([scriptblock]::Create($h.Substring($b,$e-$b)))
$p=Join-Path $ws 'diagnostics/restored_audit_20261025_01/installed_01/resources/10260615261550143857.questphase';$g=(Read-Cr2wFile $p).RootChunk.Graph.Chunk
$a=@(EdgesB5 $g|ForEach-Object {,@($_)})
$b=@(EdgesB5 $g|ForEach-Object {$_})
@{a_count=$a.Count;a_first=($a[0]|ConvertTo-Json -Depth 4);a_1006=@($a|Where-Object {$_[0] -eq 1006}).Count;b_count=$b.Count;b_first=($b[0]|ConvertTo-Json -Depth 4);b_1006=@($b|Where-Object {$_[0] -eq 1006}).Count}|ConvertTo-Json -Depth 5
